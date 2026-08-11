# Checklist kiểm thử Logging và PII — CP1

## Chuẩn bị

- [ ] Chỉ dùng dữ liệu giả, không dùng PII thật.
- [ ] API đã được khởi động lại sau thay đổi logging.
- [ ] Ghi lại commit SHA hoặc nhánh đang kiểm thử.
- [ ] Giữ output test và log cần thiết trong `submission/evidence/`; không lưu `.env` hoặc secret.

## Test case

| ID | Dữ liệu thử | Kết quả mong đợi trong log |
|---|---|---|
| PII-01 | Email, ví dụ `qa.user@example.com` | Không còn email nguyên văn; xuất hiện marker như `[REDACTED_EMAIL]` |
| PII-02 | Số điện thoại thử nghiệm | Không còn số nguyên văn; xuất hiện marker redaction phù hợp |
| PII-03 | Số thẻ thử nghiệm do bài lab cung cấp | Không còn số nguyên văn; không lưu quá mức cần thiết |
| PII-04 | `user_id` trong request | Log chỉ có `user_id_hash`; không có user ID nguyên văn |
| PII-05 | Message không chứa PII | Nội dung an toàn không bị redaction sai ngoài dự kiến |
| PII-06 | Nhiều loại PII trong cùng message | Tất cả loại đều được scrub, không chỉ loại xuất hiện đầu tiên |
| PII-07 | PII trong request gây lỗi | `request_failed` vẫn không làm lộ PII |
| SEC-01 | Langfuse/API key trong môi trường | Không xuất hiện trong log, evidence hoặc Git diff |

## Kiểm tra schema và context

Với mỗi request, xác nhận:

- [ ] Có `ts`, `level`, `service`, `event`, `correlation_id`.
- [ ] Có `env`, `user_id_hash`, `session_id`, `feature`, `model` trên các event API liên quan.
- [ ] `request_received` và `response_sent`/`request_failed` dùng cùng `correlation_id`.
- [ ] Có ít nhất hai correlation ID khác nhau trong toàn bộ lần chạy.
- [ ] `correlation_id` không rỗng và không dùng chung cho mọi request.
- [ ] Log là một JSON object hợp lệ trên mỗi dòng JSONL.
- [ ] Không có secret hoặc PII nguyên văn trong `payload` và các preview.

## Lệnh regression test

```powershell
python scripts/load_test.py --concurrency 5
python scripts/validate_logs.py
python -m pytest -q
```

## Điều kiện đóng CP1

- [ ] `validate_logs.py` đạt tối thiểu 80/100.
- [ ] Không phát hiện PII leak.
- [ ] Không thiếu required field.
- [ ] Context/enrichment có mặt trên các event cần thiết.
- [ ] Các automated test liên quan đều pass.
- [ ] Evidence có thể đối chiếu và không chứa dữ liệu nhạy cảm.
- [ ] Nếu còn lỗi, đã ghi owner, mức độ, bằng chứng và trạng thái retest.
