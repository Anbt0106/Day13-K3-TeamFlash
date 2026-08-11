# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm: TeamFlash
- Repository URL: https://github.com/Anbt0106/K3-DAY13-2A202601883.git
- Commit SHA cuối: Hoàn thành lab Day 13 - 2A202601883
- Thành viên và vai trò:

| STT | Họ và tên | Mã học viên | Vai trò |
|---|---|---|---|
| 1 | Nguyễn Văn Tuấn Anh | 2A202601813 | Thành viên B (Security & PII Scrubbing) |
| 2 | Bùi Thọ An | 2A202601883 | Thành viên D (Leader - Architecture, CP1/CP3, Bonus) |
| 3 | Lê Tuấn Cảnh | 2A202601127 | Thành viên C (Tracing, Dashboard & Alerts) |
| 4 | Nguyễn Đức Trọng | 2A202601291 | Thành viên A (Testing, QA & Validation) |

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

- Prompt name: `day13-chat`
- Version/label baseline: `v1` / `production`
- Version/label candidate: `v2` / `candidate`
- Trace ID của mỗi version:
  - Baseline (`production`, v1): `efadf05f7aee4adc14b23f81bbb51d94`
  - Candidate (`candidate`, v2): `3a7e66ee35591ec5`
- Bằng chứng đổi label hoặc rollback: Ghi nhận đầy đủ trong metadata của Langfuse trace (`prompt_name`, `prompt_label`, `prompt_version`, `prompt_source`) và cơ chế quản lý tự động phân giải prompt dự phòng tại [app/prompt_management.py](../app/prompt_management.py).

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

| STT | Thành viên | Vai trò | Phần việc | Commit/PR | Điều đã học |
|---|---|---|---|---|---|
| 1 | Nguyễn Văn Tuấn Anh | Thành viên B | Triển khai & nâng cấp `scrub_event` toàn cục, thêm regex passport và `address_vn` trong `app/pii.py`, `app/logging_config.py`; cập nhật tài liệu giải trình bảo mật PII | `e1da041`, `56dea73`, `2f0304e`, `bb02617`, `e31ad58` | Cách structlog xử lý processor pipeline theo thứ tự; tầm quan trọng của việc scrub mọi field trong event_dict chứ không chỉ riêng payload |
| 2 | Bùi Thọ An | Thành viên D (Leader) | Triển khai `CorrelationIdMiddleware`, context enrichment; chủ trì điều tra giải quyết CP3 Challenge (`rag_slow`); thiết kế và triển khai toàn bộ Bonus (Tối ưu chi phí, Audit Log, Anomaly Detection) | `d7fb9fa`, `490b7fb`, `483baad`, `d74bd85` | Phương pháp truy vết xuyên suốt bằng correlation ID kết hợp span tracing; xây dựng hệ thống tự động cảnh báo anomaly và tối ưu hóa ngân sách LLM |
| 3 | Lê Tuấn Cảnh | Thành viên C | Cấu hình Langfuse tracing integration; thiết kế đặc tả Dashboard 6 panel và runtime dashboard HTML/PNG; xây dựng hệ thống cảnh báo dựa trên triệu chứng (Symptom-based Alerts) & Runbook | `ca63122`, `dbc4d91`, `b7399c9`, `05b7db0`, `7d96ff4` | Cách thiết kế SLO/SLA thực tế cho hệ thống AI/LLM; cách xây dựng dashboard trực quan và viết runbook xử lý sự cố chuẩn DevOps/SRE |
| 4 | Nguyễn Đức Trọng | Thành viên A | Thực hiện load testing hệ thống (`load_test.py`), thu thập log baseline (CP0) và runtime (CP1); QA kiểm thử dashboard validator và log validator; kiểm thử tích hợp toàn trình | `0dbc09a` | Phương pháp thiết lập kịch bản kiểm thử tải và kỹ thuật tự động hóa validation để đảm bảo tính toàn vẹn của dữ liệu giám sát hệ thống |

## 8. Bonus — Tối ưu chi phí, Audit Log & Custom Automation (+10 điểm)

- **Tối ưu chi phí (Cost Optimization)**:
  - Incident: `cost_spike` (LLM sinh output tokens gấp 4 lần).
  - Giải pháp triển khai: Áp dụng Token Budgeting (`max_tokens=150`) và Semantic/Exact Response Caching trong `LabAgent` ([app/agent.py](../app/agent.py)).
  - Kết quả đo lường:
    - *Chi phí Before (Uncapped)*: **$0.077610 USD** (510.8 tokens out/req).
    - *Chi phí After (Optimized + Cache)*: **$0.023490 USD** (150.0 tokens out/req).
    - *Hiệu quả tiết kiệm*: Giảm **69.73%** chi phí LLM trong điều kiện cost spike; tiết kiệm **100%** chi phí cho các truy vấn trùng lặp (cache hit cost = $0.00).
  - Chi tiết & Evidence: [`submission/evidence/cp-bonus-cost-optimization.md`](evidence/cp-bonus-cost-optimization.md).

- **Audit Log độc lập (`data/audit.jsonl`)**:
  - Triển khai `AuditFileProcessor` trong structlog pipeline ([app/logging_config.py](../app/logging_config.py)) để tự động lọc và ghi các sự kiện nhạy cảm/kiểm toán (`incident_enabled`, `incident_disabled`, `app_started`, `config_changed`).
  - Phân tách riêng biệt log vận hành ứng dụng (`data/logs.jsonl`) và log kiểm toán bảo mật (`data/audit.jsonl`).

- **Custom Automation phát hiện bất thường (`scripts/detect_anomalies.py`)**:
  - Kịch bản CLI tự động quét và kiểm thử:
    1. Phát hiện PII leak nguyên văn (Email, Phone VN, CCCD, Credit Card, Passport, Address VN).
    2. Cảnh báo vi phạm Latency SLO (P95 > 3000ms, Max > 5000ms).
    3. Cảnh báo bùng phát tỷ lệ lỗi (Error Rate > 2.0%).
    4. Cảnh báo chi phí tăng vọt (Cost > $0.02/req).
    5. Cảnh báo suy giảm chất lượng câu trả lời (Quality Score < 0.70).
  - Tích hợp exit code `0` (HEALTHY) và `1` (ANOMALY DETECTED) sẵn sàng cho CI/CD pipeline và cron monitoring.

