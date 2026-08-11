# Alert va Runbook

Moi alert duoc dat theo trieu chung tac dong den nguoi dung hoac SLO, khong dat theo ten ham hay implementation noi bo.

## Alert 1

- Ten: ChatHighLatency
- Severity: warning
- SLI/SLO lien quan: `latency_p95_ms`, muc tieu P95 khong vuot 3.000 ms.
- Dieu kien kich hoat: `latency_p95_ms > 3000` trong 5 phut.
- Anh huong toi nguoi dung: phan hoi chat cham, co the dan den timeout va trai nghiem giam.
- Ba buoc kiem tra dau tien: (1) xem p50/p95/p99 va traffic tai `/metrics`; (2) mo trace cham de so sanh `retrieve-context` va `generate-response`; (3) doi chieu log cung `correlation_id` va thoi diem.
- Mitigation tam thoi: giam concurrency, tat incident gay cham, va rollback prompt neu latency tang sau khi doi label.
- Owner: metrics-oncall

## Alert 2

- Ten: ChatElevatedErrorRate
- Severity: critical
- SLI/SLO lien quan: `error_rate_pct`, SLO muc tieu duoi 2%.
- Dieu kien kich hoat: `error_rate_pct > 5` trong 3 phut.
- Anh huong toi nguoi dung: nguoi dung nhan loi 5xx hoac khong nhan duoc cau tra loi.
- Ba buoc kiem tra dau tien: (1) kiem tra `error_rate_pct`, `failed_requests` va `error_breakdown`; (2) loc `request_failed` theo `error_type`; (3) mo trace va log co cung `correlation_id` de khoanh vung buoc loi.
- Mitigation tam thoi: tat incident dang bat, giam load/concurrency, va chuyen sang duong fallback an toan neu dich vu phu thuoc loi.
- Owner: metrics-oncall

## Alert 3

- Ten: ChatDailyCostBudgetExceeded
- Severity: warning
- SLI/SLO lien quan: `daily_cost_usd`, ngan sach toi da $2.50/ngay.
- Dieu kien kich hoat: `daily_cost_usd > 2.5`.
- Anh huong toi nguoi dung: chua nhat thiet gay loi ngay lap tuc, nhung co nguy co vuot ngan sach va can gioi han tai nguyen.
- Ba buoc kiem tra dau tien: (1) kiem tra `total_cost_usd`, token input/output va traffic; (2) loc trace theo model, feature va prompt version; (3) doi chieu trace co output token bat thuong voi incident `cost_spike` va log lien quan.
- Mitigation tam thoi: giam max output tokens, tat feature co chi phi cao, va rollback prompt/model ve cau hinh tiet kiem hon.
- Owner: metrics-oncall
