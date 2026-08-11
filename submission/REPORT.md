# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm:
- Repository URL:
- Commit SHA cuối:
- Thành viên và vai trò:

## 2. Kết quả kỹ thuật

- Điểm `validate_logs.py` (CP0 - baseline): **30/100**
  - Total log records analyzed: 22
  - Records with missing required fields: 20
  - Records with missing enrichment (context): 20
  - Unique correlation IDs found: 0
  - Potential PII leaks detected: 0
  - Scorecard: [FAILED] Missing required fields | [FAILED] Correlation ID propagation | [FAILED] Log enrichment | [PASSED] PII scrubbing
- Điểm `validate_logs.py` (CP1 - sau khi thêm correlation ID, enrichment, PII scrubbing mở rộng): **100/100**
  - Total log records analyzed: 21
  - Records with missing required fields: 0
  - Records with missing enrichment (context): 0
  - Unique correlation IDs found: 10
  - Potential PII leaks detected: 0
  - Scorecard: [PASSED] Basic JSON schema | [PASSED] Correlation ID propagation | [PASSED] Log enrichment | [PASSED] PII scrubbing
  - Evidence: `submission/evidence/cp1-validate-logs.txt`, `submission/evidence/cp1-correlation-pair-redacted.jsonl`, `submission/evidence/cp1-pii-redaction.jsonl`
- Tổng số traces:
- Số PII leak còn lại: **0**.
- Link/đường dẫn dashboard:

## 3. Logging và tracing

- Evidence correlation ID: [`submission/evidence/cp1-correlation-pair-redacted.jsonl`](evidence/cp1-correlation-pair-redacted.jsonl) — cặp `request_received`/`response_sent` dùng chung correlation ID và có đủ context.
- Evidence PII redaction: [`submission/evidence/cp1-pii-redaction.jsonl`](evidence/cp1-pii-redaction.jsonl) — email, số điện thoại và số thẻ được thay bằng marker redaction.
- Evidence validator: [`submission/evidence/cp1-validate-logs.txt`](evidence/cp1-validate-logs.txt).
- Evidence trace waterfall:
- Giải thích một span đáng chú ý:

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

- Kết quả `validate_dashboard.py`:
- Evidence dashboard:
- SLO đã chọn và lý do:
- Alert rules và runbook:

## 6. Điều tra challenge

- Challenge ID:
- Triệu chứng từ metrics:
- Trace ID liên quan:
- Log line/correlation ID liên quan:
- Root cause:
- Fix action:
- Preventive measure:

## 7. Đóng góp cá nhân

Với mỗi thành viên, ghi rõ nhiệm vụ và link commit/PR tương ứng.

| Thành viên | Phần việc | Commit/PR | Điều đã học |
|---|---|---|---|
| B | Uncomment/nâng cấp `scrub_event` toàn cục, thêm regex passport và `address_vn` trong `app/pii.py`, `app/logging_config.py` | Bổ sung commit/PR | Cách structlog xử lý processor pipeline theo thứ tự; tầm quan trọng của việc scrub mọi field chứ không chỉ payload |
| Thành viên D | QA CP1: chạy load test, kiểm tra schema/enrichment, correlation ID, PII redaction, regression test và thu thập evidence | Commit CP1 QA evidence | Cách kiểm chứng structured logging và PII bằng validator, test tự động và đối chiếu event theo correlation ID |
