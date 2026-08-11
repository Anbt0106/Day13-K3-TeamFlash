# Báo cáo Bonus — Tối ưu chi phí & Audit Log & Custom Automation

## 1. Tối ưu chi phí (Cost Optimization)

### 1.1. Bối cảnh sự cố
Khi bật incident `cost_spike` (`python scripts/inject_incident.py --scenario cost_spike`), LLM nhân gấp 4 lần lượng output tokens sinh ra cho mỗi request. Điều này dẫn tới:
- `tokens_out` trung bình tăng từ ~125 tokens lên >510 tokens/request.
- Chi phí LLM (`total_cost_usd`) tăng vọt gấp 4 lần.

### 1.2. Đề xuất & Giải pháp triển khai
Nhóm triển khai kết hợp 2 kỹ thuật tối ưu hóa chi phí:
1. **Token Budgeting / Max Output Tokens Cap**: Giới hạn cứng `max_tokens=150` trong `LabAgent` và `FakeLLM.generate()`, ngăn chặn hiện tượng runaway token generation khi có cost spike.
2. **Response Caching (Exact & Semantic Query Caching)**: Lưu cache các câu trả lời cho các query tương tự/lặp lại theo `feature` và `message`. Khi cache hit, request trả về ngay lập tức với cost = $0.00 và latency ~0ms.

### 1.3. Kết quả đo lường (Before vs After)

| Chỉ số | Baseline (Bình thường) | Before (Cost Spike Uncapped) | After (Cost Optimized + Cache) | Hiệu quả cải thiện |
|---|---|---|---|---|
| **Tổng chi phí (Total Cost USD)** | $0.0197 | **$0.0776** | **$0.0235** | **Giảm 69.73% chi phí** |
| **Output Tokens trung bình** | 124.9 tokens | **510.8 tokens** | **150.0 tokens** | **Kiểm soát trong ngưỡng an toàn** |
| **Cache Hit Cost** | N/A | N/A | **$0.0000** | **Tiết kiệm 100% chi phí cho repeat queries** |

---

## 2. Nhật ký kiểm toán riêng biệt (Audit Log)

### 2.1. Thiết kế & Triển khai
- Cấu hình biến môi trường `AUDIT_LOG_PATH=data/audit.jsonl`.
- Tạo processor `AuditFileProcessor` trong structlog pipeline (`app/logging_config.py`).
- Tự động bắt và ghi nhận các sự kiện nhạy cảm/quan trọng của hệ thống:
  - `incident_enabled` & `incident_disabled` (kèm trạng thái incident).
  - `config_changed` (thay đổi cấu hình hệ thống).
  - `app_started` (khởi động dịch vụ).
- Đảm bảo tách biệt log vận hành thông thường (`data/logs.jsonl`) và log kiểm toán tuân thủ bảo mật (`data/audit.jsonl`).

### 2.2. Mẫu bản ghi Audit Log (`data/audit.jsonl`)
```json
{"service": "control", "payload": {"name": "cost_spike"}, "event": "incident_enabled", "correlation_id": "req-2b5e0768", "level": "warning", "ts": "2026-08-11T04:53:15.750136Z"}
{"service": "control", "payload": {"name": "cost_spike"}, "event": "incident_disabled", "correlation_id": "req-4c0c113a", "level": "warning", "ts": "2026-08-11T04:53:15.752571Z"}
```

---

## 3. Tự động hóa phát hiện bất thường (Custom Automation)

### 3.1. Mô tả kịch bản (`scripts/detect_anomalies.py`)
Script tự động phân tích `data/logs.jsonl` và phát hiện các vi phạm SLO / sự cố bảo mật:
- **PII Leak Detector**: Kiểm tra độc lập toàn bộ log xem có dữ liệu nhạy cảm chưa được che (Email, Phone VN, CCCD, Thẻ tín dụng, Passport, Địa chỉ VN).
- **Latency SLO Checker**: Đánh giá P95, P99 và Max Latency so với ngưỡng SLO quy định (P95 ≤ 3000ms, Max ≤ 5000ms).
- **Error Rate Spike Detector**: Cảnh báo khi tỷ lệ lỗi vượt ngưỡng cho phép (Error Rate > 2%).
- **Cost Spike Detector**: Phát hiện các request có chi phí bất thường vượt ngân sách ($ > 0.02 USD/req).
- **Quality Score Guard**: Cảnh báo khi điểm chất lượng phản hồi trung bình giảm dưới 0.70.

### 3.2. Chạy kiểm tra thực tế
```bash
python scripts/detect_anomalies.py --log-path data/logs.jsonl
```
Kết quả trả về mã thoát `0` (HEALTHY) nếu đạt mọi tiêu chuẩn hoặc `1` (ANOMALY DETECTED) để tích hợp vào CI/CD pipeline và hệ thống giám sát tự động.
