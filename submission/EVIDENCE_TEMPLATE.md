# Evidence Template — QA & Incident Analysis

Sao chép các mục cần dùng vào `submission/REPORT.md`. Đặt ảnh và output đã lọc secret/PII trong `submission/evidence/`, rồi dùng đường dẫn tương đối.

## 1. Thông tin lần kiểm thử

- Người kiểm thử:
- Ngày/giờ và múi giờ:
- Commit SHA:
- Môi trường:
- Lệnh đã chạy:

## 2. CP1 — Logging và PII

- Điểm `validate_logs.py`:
- Tổng số log:
- Số correlation ID duy nhất:
- Số missing required fields:
- Số missing enrichment fields:
- Số PII leak:
- Evidence validator: `submission/evidence/...`
- Evidence cặp log cùng correlation ID: `submission/evidence/...`
- Evidence PII đã redact: `submission/evidence/...`
- Kết luận PASS/FAIL:
- Lỗi còn lại, owner và trạng thái retest:

## 3. CP2 — Dashboard

- Kết quả `validate_dashboard.py`:
- Dashboard/runtime URL hoặc đường dẫn:
- Evidence baseline: `submission/evidence/...`
- Evidence incident: `submission/evidence/...`

| Panel | Giá trị baseline | Giá trị incident | Threshold | PASS/FAIL |
|---|---:|---:|---:|---|
| Latency P95 | | | 3000 ms | |
| Traffic | | | 1 request/min | |
| Error rate | | | 2% | |
| Total cost | | | 2.5 USD | |
| Input/output tokens | | | 50.000 | |
| Quality mean | | | 0.75 | |

## 4. CP3 — Incident Challenge

- Challenge ID:
- Thời điểm bắt đầu/kết thúc:
- Feature bị ảnh hưởng:
- Triệu chứng từ metrics:
- Trace ID:
- Span bất thường và duration:
- Correlation ID:
- Log line hoặc đường dẫn evidence:
- Root cause:
- Fix action:
- Preventive measure:
- Evidence before/after: `submission/evidence/...`

## 5. Biên bản QA cuối

- [ ] `python scripts/validate_logs.py` đạt yêu cầu.
- [ ] `python scripts/validate_dashboard.py` hợp lệ.
- [ ] `python -m pytest -q` pass.
- [ ] Dashboard có đủ sáu panel và threshold.
- [ ] Report dẫn đúng đường dẫn evidence.
- [ ] Không có `.env`, secret hoặc PII trong Git.
- [ ] Đóng góp cá nhân có commit/PR kiểm chứng được.
