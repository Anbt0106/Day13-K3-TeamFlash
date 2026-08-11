# Yêu cầu dashboard

Contract có thể kiểm tra bằng máy nằm tại `config/dashboard.yaml`. Hướng dẫn dựng và kiểm tra runtime nằm tại [DASHBOARD_SETUP.md](DASHBOARD_SETUP.md).

Dashboard chính cần đủ 6 nhóm thông tin:

1. Latency P50/P95/P99.
2. Traffic: request count hoặc QPS.
3. Error rate và breakdown theo loại lỗi.
4. Cost theo thời gian.
5. Tổng token input/output.
6. Quality proxy.

Tiêu chuẩn trình bày:

- Khoảng thời gian mặc định: 1 giờ.
- Tự refresh mỗi 15–30 giây nếu công cụ hỗ trợ.
- Có threshold hoặc SLO line.
- Ghi rõ đơn vị.
- Chỉ giữ 6–8 panel quan trọng ở lớp chính.
- Screenshot phải nhìn được tên panel và khoảng thời gian.

Kiểm tra contract trước khi chụp evidence:

```bash
python scripts/validate_dashboard.py
```

## CP2 dashboard implementation specification

Tool: Grafana, Langfuse dashboard, or an equivalent local dashboard. The runtime dashboard uses `data/logs.jsonl` as the canonical event source from `config/dashboard.yaml`; `/metrics` is used as a service-level snapshot and smoke check.

Default time range: last 60 minutes. Refresh interval: 30 seconds. Every panel displays its unit and the threshold/SLO line below.

| Panel | Source and calculation | Unit | Threshold / SLO line |
|---|---|---:|---|
| Latency percentiles | `response_sent.latency_ms`; P50, P95, P99 | ms | P95 <= 3000 ms |
| Request traffic | Count `request_received` by one minute | requests/minute | >= 1 request/minute during load test |
| Error rate and breakdown | `request_failed / request_received * 100`, grouped by `error_type` | percent | <= 2% |
| Cost over time | Sum `response_sent.cost_usd` by minute and for the active window | USD | <= $2.50 daily budget |
| Input and output tokens | Sum `response_sent.tokens_in` and `response_sent.tokens_out` | tokens | <= 50,000 per active window |
| Quality proxy | Mean `response_sent.quality_score` | score (0-1) | >= 0.75 |

Evidence to save in `submission/evidence/`:

- `dashboard-cp2.png`: all six named panels, visible 60-minute time range, units, and threshold/SLO lines.
- `dashboard-validator.txt`: output of `python scripts/validate_dashboard.py` showing `6/6 panel`.
