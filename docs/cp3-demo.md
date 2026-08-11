# CP3 Demo Script — Thành viên D

Thời lượng mục tiêu: 3–4 phút.

## 1. Mở dashboard — 30 giây

Mở `submission/evidence/dashboard-cp2.html` và nói:

> Dashboard dùng `data/logs.jsonl` làm nguồn chuẩn, time range 60 phút, refresh 30 giây. Sáu panel bao phủ latency, traffic, errors, cost, tokens và quality. Contract đã qua validator 6/6.

Chỉ vào bảng so sánh ba pha ở cuối dashboard.

## 2. Metrics phát hiện triệu chứng — 45 giây

> Với cùng năm input chính thức của challenge, baseline P95 là 270 ms. Khi bật `rag_slow`, P95 tăng lên 2697 ms, tăng khoảng 9.99 lần và cả 5/5 request vượt ngưỡng 2000 ms. Error rate vẫn 0% và quality giữ 0.86, nên đây là latency incident chứ không phải lỗi request hay suy giảm chất lượng.

Evidence: `submission/evidence/cp3-results.json`.

## 3. Trace khoanh vùng — 45 giây

> Trace `efadf05f7aee4adc14b23f81bbb51d94` có end-to-end generation 3606 ms. Span `retrieve-context` mất 2501 ms, còn `generate-response` chỉ 151 ms. Vì retrieval chiếm phần lớn thời gian, vấn đề nằm ở RAG retrieval chứ không phải LLM generation.

Evidence CP2 UI: `langfuse-trace-waterfall.png`. CP3 trace/span ID và duration nằm trong `cp3-results.json`.

## 4. Logs chứng minh root cause — 45 giây

Mở `submission/evidence/cp3-related-log-redacted.jsonl`:

> Sau event `incident_enabled` với `rag_slow`, request feature `refund`, correlation ID `req-744718ce`, hoàn thành sau 2673 ms. Code tại `app/mock_rag.py::retrieve` chờ 2.5 giây khi incident bật. Con số này khớp span retrieval 2501 ms, nên đây là root cause có bằng chứng từ trace và log.

## 5. Fix và xác minh — 30 giây

> Fix tạm thời là tắt `rag_slow` rồi chạy lại đúng workload. P95 giảm từ 2697 ms xuống 166 ms và số request vượt 2000 ms giảm từ 5 về 0.

## 6. Phòng ngừa — 30 giây

> Nhóm đề xuất alert P95 theo SLO, timeout và fallback cho retrieval, metric riêng cho retrieval span, cache với nội dung policy ổn định và runbook Metrics → Traces → Logs.

## Câu hỏi có thể được hỏi

- **Tại sao không dùng average?** Average che khuất tail latency; P95/P99 phản ánh trải nghiệm request chậm.
- **Tại sao kết luận RAG?** Retrieval span 2501 ms, generation 151 ms, đồng thời code incident thêm đúng 2.5 giây tại retrieval.
- **Tại sao error rate vẫn 0%?** Request vẫn thành công nhưng phản hồi chậm; đây là latency degradation.
- **Correlation ID dùng làm gì?** Liên kết `request_received`, `response_sent` và trace metadata của cùng request.
- **Fix đã được xác minh thế nào?** Chạy lại cùng input sau khi disable incident; P95 về 166 ms và không còn request vượt threshold.
