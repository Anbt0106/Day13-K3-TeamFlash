# Dashboard Spec — Day 13 AI Observability

## 1. Mục tiêu và phạm vi

Dashboard giúp phát hiện triệu chứng, đánh giá SLO và dẫn đường điều tra theo luồng Metrics → Traces → Logs. Nguồn dữ liệu chuẩn của sáu panel là `data/logs.jsonl`; Langfuse được dùng để mở trace và xem span sau khi dashboard phát hiện bất thường.

Contract có thể kiểm tra bằng máy nằm tại `config/dashboard.yaml`. Trường `query` trong contract là pseudocode mô tả phép tính, không phải câu lệnh dành riêng cho một công cụ dashboard.

## 2. Thiết lập chung

| Thuộc tính | Giá trị |
|---|---|
| Tên | Day 13 AI Observability |
| Nguồn dữ liệu | `data/logs.jsonl` |
| Time range mặc định | 60 phút |
| Refresh | 30 giây |
| Số panel chính | 6 |
| Múi giờ hiển thị | Nhất quán trên toàn dashboard; ghi rõ trên ảnh evidence |

Mỗi panel phải hiển thị tên, đơn vị và threshold/SLO line. Screenshot nghiệm thu phải nhìn thấy tên dashboard, time range và cả sáu panel.

## 3. Đặc tả panel

| ID | Tên panel | Event và field | Phép tổng hợp | Đơn vị | Threshold | Mục đích QA |
|---|---|---|---|---|---|---|
| `latency` | Latency percentiles | `response_sent.latency_ms` | P50, P95, P99 trên cửa sổ đang chọn | ms | P95 ≤ 3000 ms | Phát hiện tail latency; phải có P50 ≤ P95 ≤ P99 |
| `traffic` | Request traffic | `request_received` | Count theo phút và tổng request | requests/minute | ≥ 1 request/phút | Xác nhận hệ thống có traffic và làm mẫu số cho error rate |
| `errors` | Error rate and breakdown | `request_received`, `request_failed`, `error_type` | `request_failed / request_received * 100`; count theo `error_type` | percent | ≤ 2% | Phát hiện lỗi và phân loại nguyên nhân bề mặt |
| `cost` | Cost over time | `response_sent.cost_usd` | Sum theo phút và tổng trong cửa sổ | USD | Tổng ≤ 2.5 USD | Phát hiện chi phí tăng bất thường |
| `tokens` | Input and output tokens | `response_sent.tokens_in`, `tokens_out` | Tổng riêng input và output | tokens | Mỗi tổng theo field ≤ 50.000 | Giải thích biến động cost và độ dài đầu ra |
| `quality` | Quality proxy | `response_sent.quality_score` | Mean trong cửa sổ | score 0–1 | Mean ≥ 0.75 | Phát hiện suy giảm chất lượng phản hồi |

## 4. Quy tắc tính

- Chỉ dùng bản ghi có đúng `event` quy định cho từng panel.
- Bỏ qua giá trị `null` khi tính percentile, sum hoặc mean; không tự chuyển `null` thành 0.
- Error rate dùng số `request_received` làm mẫu số. Nếu mẫu số bằng 0, hiển thị `N/A`, không hiển thị 0%.
- Các percentile phải được tính trên `latency_ms`, không tính trên timestamp hoặc thời gian giữa hai dòng log.
- Tokens input và output phải hiển thị tách biệt.
- Quality phải giữ thang 0–1; nếu công cụ đổi sang phần trăm thì phải đổi cả đơn vị và threshold tương ứng trên giao diện, không sửa contract.
- Khi lọc theo `feature`, `env` hoặc `model`, ghi rõ filter đang áp dụng trên screenshot.

## 5. Tiêu chí nghiệm thu runtime

- Có dữ liệu trên cả sáu panel sau khi chạy load test.
- Traffic khớp số event `request_received` trong cùng time range.
- Latency, cost, tokens và quality chỉ lấy từ `response_sent`.
- Error rate và breakdown phản ánh đúng `request_failed` và `error_type`.
- Threshold/SLO line hiển thị đúng giá trị trong `config/dashboard.yaml`.
- Với practice incident `rag_slow`, P95 tăng rõ ràng so với baseline khi giữ nguyên input và concurrency.
- Có thể chọn một điểm bất thường, lấy correlation ID/trace ID và tìm được log liên quan.

## 6. Quy trình xác minh

```powershell
# Kiểm tra contract
python scripts/validate_dashboard.py

# Sinh baseline khi API đang chạy
python scripts/load_test.py --concurrency 5

# Practice incident
python scripts/inject_incident.py --scenario rag_slow
python scripts/load_test.py --concurrency 5
python scripts/inject_incident.py --scenario rag_slow --disable
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

Validator chỉ xác nhận cấu trúc contract. Dashboard chỉ được nghiệm thu hoàn toàn sau khi đã đối chiếu số liệu runtime và lưu ảnh trong `submission/evidence/`.

## 7. Evidence cần lưu

- Output `validate_dashboard.py` có dòng `HỢP LỆ: 6/6 panel`.
- Ảnh dashboard baseline đủ sáu panel.
- Ảnh dashboard khi bật incident, nhìn rõ thay đổi P95.
- Bảng số liệu baseline/incident/after-fix.
- Trace ID hoặc correlation ID của request bất thường và log line liên quan.
