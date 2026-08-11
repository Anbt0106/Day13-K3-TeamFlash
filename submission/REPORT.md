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
  - Evidence: `submission/evidence/cp1_validator_score.txt`, `submission/evidence/cp1_log_sample.jsonl`
- Tổng số traces:
- Số PII leak còn lại: 0 (kiểm tra tay bằng `grep "@"`, `grep "4111"` không có kết quả; `grep "REDACTED"` có kết quả)
- Link/đường dẫn dashboard:

## 3. Logging và tracing

- Evidence correlation ID: xem `submission/evidence/cp1_log_sample.jsonl` — mọi log trong cùng 1 request (`request_received`, `response_sent`) có chung `correlation_id` dạng `req-<8hex>` (vd. `req-40f22b3f`), sinh tại `app/middleware.py` (`CorrelationIdMiddleware`) và bind qua `structlog.contextvars`.
- Evidence PII redaction: cùng file trên — trường `message_preview` chứa `[REDACTED_EMAIL]` thay vì email thật; kiểm tra tay bằng `grep -i "@" data/logs.jsonl` và `grep "4111" data/logs.jsonl` không trả về kết quả nào, còn `grep "REDACTED" data/logs.jsonl` có kết quả.
- Evidence trace waterfall:
- Giải thích một span đáng chú ý:

### Câu hỏi phản biện — CP1

**Khác biệt lớn nhất giữa log baseline (CP0) và log sau CP1:**
Ở CP0, mọi bản ghi log đều có `correlation_id = "MISSING"` (không có cách nào liên kết các log `request_received` và `response_sent` của cùng một request lại với nhau), thiếu hoàn toàn các trường enrichment (`user_id_hash`, `session_id`, `feature`, `model`, `env`), và dù `message_preview` đã che PII sơ bộ, nhưng các trường log khác (nếu có dữ liệu nhạy cảm thô) chưa được xử lý vì thiếu processor `scrub_event`. Kết quả baseline chỉ đạt 30/100.

Sau CP1, mỗi request có một `correlation_id` duy nhất dạng `req-<8hex>` xuất hiện xuyên suốt toàn bộ log của request đó (nhờ `bind_contextvars` trong middleware), cho phép truy vết toàn trình (traceability) — tìm mọi log liên quan đến một request cụ thể chỉ bằng cách lọc theo `correlation_id`. Log cũng được enrich đầy đủ metadata (`user_id_hash`, `session_id`, `feature`, `model`, `env`) giúp lọc/phân tích theo nhiều chiều. PII scrubbing được mở rộng để quét mọi trường string/dict trong `event_dict`, không chỉ riêng `payload`. Kết quả: 100/100.

**Tại sao `clear_contextvars()` ở đầu middleware là bắt buộc:**
`structlog` dùng Python `contextvars` để lưu context (như `correlation_id`, `user_id_hash`...) dùng chung cho mọi log phát sinh trong một request, mà không cần truyền tham số thủ công qua từng hàm. Tuy nhiên, trong một ứng dụng ASGI/FastAPI xử lý nhiều request đồng thời (hoặc tái sử dụng cùng một task/thread qua các request nối tiếp), nếu không xóa context cũ trước khi bind context mới, request sau có thể vô tình "thừa hưởng" context của request trước đó — ví dụ log của request B lại mang `correlation_id` hoặc `user_id_hash` của request A. Đây chính là rò rỉ dữ liệu (data leakage) giữa các request, cực kỳ nguy hiểm khi context chứa thông tin định danh người dùng. Gọi `clear_contextvars()` ngay đầu `dispatch()` đảm bảo mỗi request luôn bắt đầu với một "chiếc túi" (context) hoàn toàn sạch, tránh nhầm lẫn danh tính giữa các request khác nhau.

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

Thành viên	Phần việc	Commit/PR	Điều đã học
B	Uncomment/nâng cấp scrub_event toàn cục, thêm regex passport & address_vn trong app/pii.py, app/logging_config.py Cách structlog xử lý processor pipeline theo thứ tự; tầm quan trọng của việc scrub mọi field chứ không chỉ payload
