from __future__ import annotations

from app import incidents
from app.agent import LabAgent
from app.mock_llm import FakeLLM


def test_cost_optimization_caps_tokens_during_cost_spike() -> None:
    incidents.enable("cost_spike")
    try:
        # LLM without token limit
        llm = FakeLLM()
        uncapped = llm.generate("Test prompt")
        assert uncapped.usage.output_tokens >= 320

        # LLM with token limit (cost optimization)
        capped = llm.generate("Test prompt", max_tokens=150)
        assert capped.usage.output_tokens <= 150
    finally:
        incidents.disable("cost_spike")


def test_agent_caching_and_cost_savings() -> None:
    agent = LabAgent(max_tokens=150)
    res1 = agent.run("u01", "qa", "s01", "Explain cost optimization")
    assert res1.cost_usd > 0

    # Second identical query hits cache with 0 cost
    res2 = agent.run("u01", "qa", "s01", "Explain cost optimization")
    assert res2.cost_usd == 0.0
    assert res2.answer == res1.answer
