from __future__ import annotations

import time
from dataclasses import dataclass

from structlog.contextvars import get_contextvars

from . import metrics
from .mock_llm import FakeLLM
from .mock_rag import retrieve
from .pii import hash_user_id, summarize_text
from .prompt_management import resolve_prompt
from .tracing import get_langfuse_client, observe, tracing_enabled


@dataclass
class AgentResult:
    answer: str
    latency_ms: int
    tokens_in: int
    tokens_out: int
    cost_usd: float
    quality_score: float


class LabAgent:
    def __init__(self, model: str = "claude-sonnet-4-5", max_tokens: int = 180) -> None:
        self.model = model
        self.max_tokens = max_tokens
        self.llm = FakeLLM(model=model)
        self._cache: dict[str, tuple[str, int, int]] = {}

    @observe(
        name="chat-response",
        as_type="generation",
        capture_input=False,
        capture_output=False,
    )
    def run(
        self,
        user_id: str,
        feature: str,
        session_id: str,
        message: str,
        correlation_id: str | None = None,
    ) -> AgentResult:
        started = time.perf_counter()
        docs = retrieve(message)
        langfuse_client = get_langfuse_client()
        prompt = resolve_prompt(
            langfuse_client,
            feature=feature,
            docs=docs,
            message=message,
            enabled=tracing_enabled(),
        )

        cache_key = f"{feature}:{message}"
        if cache_key in self._cache:
            answer_text, tokens_in, tokens_out = self._cache[cache_key]
            tokens_out = 0  # Cached response saves output generation tokens
            cost_usd = 0.0
            managed_prompt = prompt.managed_prompt
        else:
            response = self.llm.generate(prompt.text, max_tokens=self.max_tokens)
            answer_text = response.text
            tokens_in = response.usage.input_tokens
            tokens_out = response.usage.output_tokens
            cost_usd = self._estimate_cost(tokens_in, tokens_out)
            managed_prompt = prompt.managed_prompt
            self._cache[cache_key] = (answer_text, tokens_in, tokens_out)

        quality_score = self._heuristic_quality(message, answer_text, docs)
        latency_ms = int((time.perf_counter() - started) * 1000)

        trace_metadata = {
            "prompt_name": prompt.name,
            "prompt_label": prompt.label,
            "prompt_version": prompt.version,
            "prompt_source": prompt.source,
            "correlation_id": correlation_id
            or get_contextvars().get("correlation_id", "MISSING"),
        }
        langfuse_client.update_current_trace(
            name="chat-response",
            user_id=hash_user_id(user_id),
            session_id=session_id,
            tags=["lab", feature, self.model],
            input={"message": summarize_text(message)},
            output={"answer": summarize_text(answer_text)},
            metadata=trace_metadata,
        )
        langfuse_client.update_current_generation(
            model=self.model,
            metadata={
                "doc_count": len(docs),
                "query_preview": summarize_text(message),
                "prompt_name": prompt.name,
                "prompt_label": prompt.label,
                "prompt_version": prompt.version,
                "prompt_source": prompt.source,
                "prompt_fetch_error": prompt.fetch_error,
            },
            usage_details={
                "prompt_tokens": tokens_in,
                "completion_tokens": tokens_out,
            },
            cost_details={"total": cost_usd},
            prompt=managed_prompt,
        )

        metrics.record_request(
            latency_ms=latency_ms,
            cost_usd=cost_usd,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            quality_score=quality_score,
        )

        return AgentResult(
            answer=answer_text,
            latency_ms=latency_ms,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            cost_usd=cost_usd,
            quality_score=quality_score,
        )

    def _estimate_cost(self, tokens_in: int, tokens_out: int) -> float:
        input_cost = (tokens_in / 1_000_000) * 3
        output_cost = (tokens_out / 1_000_000) * 15
        return round(input_cost + output_cost, 6)

    def _heuristic_quality(self, question: str, answer: str, docs: list[str]) -> float:
        score = 0.5
        if docs:
            score += 0.2
        if len(answer) > 40:
            score += 0.1
        if question.lower().split()[0:1] and any(
            token in answer.lower() for token in question.lower().split()[:3]
        ):
            score += 0.1
        if "[REDACTED" in answer:
            score -= 0.2
        return round(max(0.0, min(1.0, score)), 2)
