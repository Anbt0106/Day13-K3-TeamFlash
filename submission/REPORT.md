# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm: TeamFlash
- Repository URL: https://github.com/Anbt0106/Day13-K3-TeamFlash.git
- Commit SHA cuối:
- Thành viên và vai trò:

| STT | Họ và tên | Mã học viên |
|---|---|---|
| 1 | Nguyễn Văn Tuấn Anh | 2A202601813 |
| 2 | Bùi Thọ An | 2A202601883 |
| 3 | Lê Tuấn Cảnh | 2A202601127 |
| 4 | Nguyễn Đức Trọng | 2A202601291 |

## 2. Kết quả kỹ thuật

- Điểm `validate_logs.py` (CP0 - baseline): **30/100**
  - Total log records analyzed: 22
  - Records with missing required fields: 20
  - Records with missing enrichment (context): 20
  - Unique correlation IDs found: 0
  - Potential PII leaks detected: 0
  - Scorecard: [FAILED] Missing required fields | [FAILED] Correlation ID propagation | [FAILED] Log enrichment | [PASSED] PII scrubbing
  - Baseline log đã redact: `submission/evidence/cp0-baseline-log-redacted.jsonl`
- Điểm `validate_logs.py` (CP1 - sau khi thêm correlation ID, enrichment, PII scrubbing mở rộng): **100/100**
  - Total log records analyzed: 21
  - Records with missing required fields: 0
  - Records with missing enrichment (context): 0
  - Unique correlation IDs found: 10
  - Potential PII leaks detected: 0
  - Scorecard: [PASSED] Basic JSON schema | [PASSED] Correlation ID propagation | [PASSED] Log enrichment | [PASSED] PII scrubbing
  - Evidence: `submission/evidence/cp1-validate-logs.txt`, `submission/evidence/cp1-correlation-pair-redacted.jsonl`, `submission/evidence/cp1-pii-redaction.jsonl`
- Tổng số traces: **ít nhất 120** tại thời điểm chụp danh sách Langfuse; evidence: [`submission/evidence/langfuse-traces-list.png`](evidence/langfuse-traces-list.png).
- Số PII leak còn lại: **0**.
- Link/đường dẫn dashboard: [`submission/evidence/dashboard-cp2.html`](evidence/dashboard-cp2.html) — dashboard runtime tự refresh 30 giây, time range 60 phút và đủ 6 panel.

## 3. Logging và tracing

- Evidence correlation ID: [`submission/evidence/cp1-correlation-pair-redacted.jsonl`](evidence/cp1-correlation-pair-redacted.jsonl) — cặp `request_received`/`response_sent` dùng chung correlation ID và có đủ context.
- Evidence PII redaction: [`submission/evidence/cp1-pii-redaction.jsonl`](evidence/cp1-pii-redaction.jsonl) — email, số điện thoại và số thẻ được thay bằng marker redaction.
- Evidence validator: [`submission/evidence/cp1-validate-logs.txt`](evidence/cp1-validate-logs.txt).
- Evidence trace waterfall: [`submission/evidence/langfuse-trace-waterfall.png`](evidence/langfuse-trace-waterfall.png); CP3 trace ID `efadf05f7aee4adc14b23f81bbb51d94` được ghi trong [`submission/evidence/cp3-results.json`](evidence/cp3-results.json).
- Giải thích một span đáng chú ý: trong CP3, span `retrieve-context` (`3a7e66ee35591ec5`) kéo dài 2501 ms, trong khi `generate-response` chỉ 151 ms. Retrieval chiếm phần lớn latency và khoanh vùng nguyên nhân ở RAG thay vì LLM.

### Câu hỏi phản biện — CP1

**Khác biệt lớn nhất giữa log baseline (CP0) và log sau CP1:**
Ở CP0, các bản ghi API thiếu correlation ID và các trường enrichment (`user_id_hash`, `session_id`, `feature`, `model`, `env`), nên không thể liên kết `request_received` với `response_sent` của cùng request. Kết quả baseline chỉ đạt 30/100.

Sau CP1, mỗi request có một correlation ID duy nhất dạng `req-<8hex>` xuất hiện xuyên suốt các log liên quan nhờ `bind_contextvars`. Log cũng được enrich đầy đủ metadata để lọc và phân tích theo nhiều chiều. PII scrubbing quét các trường string/dict trong `event_dict`, không chỉ riêng payload. Kết quả validator đạt 100/100.

**Tại sao `clear_contextvars()` ở đầu middleware là bắt buộc:**
`structlog` dùng `contextvars` để giữ context của request. Nếu không xóa context cũ trước khi bind context mới, request sau có thể thừa hưởng correlation ID hoặc user context của request trước, gây nhầm lẫn và có nguy cơ rò rỉ dữ liệu. `clear_contextvars()` bảo đảm mỗi request bắt đầu với context sạch.

Kết luận CP1: **PASS**. Log API là JSONL hợp lệ, có `correlation_id`, `env`, `user_id_hash`, `session_id`, `feature`, `model`; các event của cùng request truyền đúng correlation ID và không còn PII nguyên văn theo validator.

## 4. Prompt versioning

- Prompt name:
- Version/label baseline:
- Version/label candidate:
- Trace ID của mỗi version:
- Bằng chứng đổi label hoặc rollback:

## 5. Dashboard, SLO và alerts

- Kết quả `validate_dashboard.py`: **HỢP LỆ: 6/6 panel**; evidence: [`submission/evidence/dashboard-validator.txt`](evidence/dashboard-validator.txt).
- Evidence dashboard: [`submission/evidence/dashboard-cp2.png`](evidence/dashboard-cp2.png) và [`submission/evidence/dashboard-cp2.html`](evidence/dashboard-cp2.html), sinh trực tiếp từ `data/logs.jsonl`; đặc tả tại [`docs/dashboard-spec.md`](../docs/dashboard-spec.md).
- SLO đã chọn và lý do: P95 ≤ 3000 ms, error rate ≤ 2%, quality mean ≥ 0.75 và cost ≤ 2.5 USD. Các ngưỡng bao phủ trải nghiệm người dùng, độ tin cậy, chất lượng và ngân sách.
- Alert rules và runbook: [`config/alert_rules.yaml`](../config/alert_rules.yaml) và [`docs/alerts.md`](../docs/alerts.md). Alert dựa trên triệu chứng/SLO, có severity, duration, owner và các bước Metrics → Traces → Logs.

## 6. Điều tra challenge

- Challenge ID: `day13-k3-observability-v1`; incident `rag_slow`; feature `refund`; threshold 2000 ms.
- Triệu chứng từ metrics: baseline P95 270 ms, incident P95 2697 ms (tăng 2427 ms, khoảng 9.99×), 5/5 request vượt 2000 ms. Error rate vẫn 0% và quality vẫn 0.86. Sau fix, P95 còn 166 ms và 0/5 request vượt ngưỡng.
- Trace ID liên quan: `efadf05f7aee4adc14b23f81bbb51d94`; `retrieve-context` span `3a7e66ee35591ec5` kéo dài 2501 ms; `generate-response` 151 ms.
- Log line/correlation ID liên quan: `req-744718ce` có `feature=refund`, `latency_ms=2673` sau `incident_enabled`; evidence: [`submission/evidence/cp3-related-log-redacted.jsonl`](evidence/cp3-related-log-redacted.jsonl).
- Root cause: khi `rag_slow` bật, `app/mock_rag.py::retrieve` chờ 2.5 giây. Trace xác nhận delay nằm tại retrieval span, không phải generation.
- Fix action: tắt `rag_slow` và chạy lại cùng 5 input chính thức; P95 phục hồi từ 2697 ms về 166 ms.
- Preventive measure: alert P95 theo SLO, retrieval timeout + fallback, metric riêng cho retrieval span, cache policy ổn định và runbook điều tra bằng correlation ID.
- Báo cáo/evidence đầy đủ: [`submission/evidence/cp3-investigation.md`](evidence/cp3-investigation.md) và [`submission/evidence/cp3-results.json`](evidence/cp3-results.json).

## 7. Đóng góp cá nhân

Với mỗi thành viên, ghi rõ nhiệm vụ và link commit/PR tương ứng.

| Thành viên | Phần việc | Commit/PR | Điều đã học |
|---|---|---|---|
| B | Uncomment/nâng cấp `scrub_event` toàn cục, thêm regex passport và `address_vn` trong `app/pii.py`, `app/logging_config.py` | Bổ sung commit/PR | Cách structlog xử lý processor pipeline theo thứ tự; tầm quan trọng của việc scrub mọi field chứ không chỉ payload |
| Thành viên D | QA CP1; Dashboard Spec/runtime; load test baseline; chủ trì CP3; điều tra Metrics → Traces → Logs; tổng hợp evidence/report/demo | `490b7fb` (CP1), commit CP2/CP3 bổ sung sau khi chốt | Cách kiểm chứng logging/PII, percentile/SLO và định vị root cause bằng span kết hợp correlation ID |
