# CP2 Dashboard Data Coverage

Ngày kiểm tra: 2026-08-11
Nguồn chuẩn: `data/logs.jsonl`

## Contract

```text
HỢP LỆ: 6/6 panel có trong dashboard contract.
```

## Runtime coverage

| Panel | Event/field | Dữ liệu xác minh | Trạng thái |
|---|---|---:|---|
| Latency | `response_sent.latency_ms` | 15 response của ba pha | READY |
| Traffic | `request_received` | 15 request | READY |
| Errors | `request_failed`, `error_type` | 0 failure; error rate 0% | READY cho rate; chưa có breakdown khác rỗng |
| Cost | `response_sent.cost_usd` | 15 response có cost | READY |
| Tokens | `tokens_in`, `tokens_out` | 15 response có cả hai field | READY |
| Quality | `quality_score` | 15 response có score | READY |

Dashboard runtime: `submission/evidence/dashboard-cp2.html`. Dashboard hiển thị sáu panel, time range 60 phút, refresh 30 giây, đơn vị và threshold/SLO. Bảng ba pha bên dưới cho phép đối chiếu baseline, incident và recovery.

Panel Errors hiển thị đúng 0% vì toàn bộ request CP3 thành công. Breakdown rỗng là trạng thái hợp lệ của batch này; cần dùng scenario `tool_fail` nếu buổi demo yêu cầu minh họa breakdown theo `error_type`.
