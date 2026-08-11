# CP3 Incident Investigation — K3

## Scope

- Challenge: `day13-k3-observability-v1`
- Incident: `rag_slow`
- Affected feature: `refund`
- Challenge threshold: 2000 ms
- Workload: the same five official challenge queries in every phase

## Metrics → Traces → Logs

### Metrics

| Phase | Requests | P50 | P95 | P99 | > 2000 ms | Error rate | Quality |
|---|---:|---:|---:|---:|---:|---:|---:|
| Baseline | 5 | 176 ms | 270 ms | 270 ms | 0 | 0% | 0.86 |
| `rag_slow` active | 5 | 2673 ms | 2697 ms | 2697 ms | 5 | 0% | 0.86 |
| After disable | 5 | 153 ms | 166 ms | 166 ms | 0 | 0% | 0.86 |

P95 increased by 2427 ms (about 9.99×) while the incident was active. Traffic, error rate and quality did not degrade, so the symptom is isolated latency rather than failure or answer-quality regression.

### Trace

- Trace ID: `efadf05f7aee4adc14b23f81bbb51d94`
- Correlation ID: `req-9864732e`
- Session: `k3-challenge-trace-evidence`
- End-to-end generation: 3606 ms
- `retrieve-context` span ID: `3a7e66ee35591ec5`, duration 2501 ms
- `generate-response` span duration: 151 ms

The retrieval span accounts for most of the request time and is about 16.6× slower than generation. This localizes the issue to RAG retrieval rather than the mock LLM.

### Logs

`cp3-related-log-redacted.jsonl` shows `incident_enabled` for `rag_slow`, followed by a `refund` response with correlation ID `req-744718ce` and latency 2673 ms. After `incident_disabled`, the same query pattern completed in 165 ms. The evidence contains no raw PII.

## Root cause and action

Root cause: when `rag_slow` is enabled, `app/mock_rag.py::retrieve` sleeps for 2.5 seconds before returning documents. The trace confirms a 2501 ms `retrieve-context` span, matching the injected delay.

Fix action: disable `rag_slow`, then rerun the same official workload. P95 recovered from 2697 ms to 166 ms and requests above 2000 ms fell from 5 to 0.

Preventive measures:

1. Alert when P95 latency exceeds 3000 ms for five minutes and route to the AI Platform on-call owner.
2. Add a retrieval timeout below the request SLO and return a safe fallback when retrieval exceeds it.
3. Track `retrieve-context` duration separately by feature and environment.
4. Cache stable refund-policy retrieval results and monitor cache hit rate.
5. Use the runbook sequence: confirm traffic/error metrics, open the slow trace, filter logs by correlation ID, mitigate, then rerun the same workload.
