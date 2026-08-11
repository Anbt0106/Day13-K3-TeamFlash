from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.cli import configure_utf8_stdio
from app.metrics import percentile

PII_DETECTORS = {
    "email": re.compile(r"[\w.-]+@[\w.-]+\.\w+"),
    "phone_vn": re.compile(r"(?<!\d)(?:\+84|0)(?:[ .-]?\d){9}(?!\d)"),
    "cccd": re.compile(r"\b\d{12}\b"),
    "credit_card": re.compile(r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b"),
    "passport": re.compile(r"\b[A-Z]\d{7,8}\b"),
    "address_vn": re.compile(r"(?i)\b(?:số nhà|so nha|đường|duong|phường|phuong|quận|quan|huyện|huyen|tỉnh|tinh|thành phố|thanh pho)\b"),
}


def analyze_logs(
    log_path: Path,
    latency_p95_slo: float = 3000.0,
    latency_max_slo: float = 5000.0,
    error_rate_slo: float = 2.0,
    min_quality_slo: float = 0.70,
    max_cost_slo: float = 0.02,
) -> dict:
    if not log_path.exists():
        raise FileNotFoundError(f"Log file {log_path} does not exist.")

    records: list[dict] = []
    for line in log_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue

    if not records:
        return {"error": "No valid log records found."}

    total_records = len(records)
    api_requests = 0
    errors_count = 0
    latencies: list[int] = []
    costs: list[float] = []
    qualities: list[float] = []
    pii_anomalies: list[dict] = []
    latency_violations: list[dict] = []
    cost_anomalies: list[dict] = []
    quality_violations: list[dict] = []
    error_records: list[dict] = []
    error_types: Counter[str] = Counter()

    for rec in records:
        # Check PII leaks in raw payload & text
        raw = json.dumps(rec, ensure_ascii=False)
        detected_pii = [
            p_name for p_name, detector in PII_DETECTORS.items() if detector.search(raw)
        ]
        if detected_pii:
            pii_anomalies.append({
                "ts": rec.get("ts"),
                "correlation_id": rec.get("correlation_id", "unknown"),
                "event": rec.get("event", "unknown"),
                "pii_types": detected_pii,
            })

        event = rec.get("event")
        if event == "response_sent":
            api_requests += 1
            lat = rec.get("latency_ms", 0)
            cost = rec.get("cost_usd", 0.0)
            q = rec.get("quality_score", 1.0)
            cid = rec.get("correlation_id", "unknown")
            feature = rec.get("feature", "unknown")

            latencies.append(lat)
            costs.append(cost)
            qualities.append(q)

            if lat > latency_max_slo:
                latency_violations.append({
                    "correlation_id": cid,
                    "feature": feature,
                    "latency_ms": lat,
                    "reason": f"Latency {lat}ms exceeds max SLO {latency_max_slo}ms",
                })
            if cost > max_cost_slo:
                cost_anomalies.append({
                    "correlation_id": cid,
                    "feature": feature,
                    "cost_usd": cost,
                    "reason": f"Cost ${cost:.4f} exceeds cost SLO ${max_cost_slo:.4f}",
                })
            if q < min_quality_slo:
                quality_violations.append({
                    "correlation_id": cid,
                    "feature": feature,
                    "quality_score": q,
                    "reason": f"Quality {q} below minimum SLO {min_quality_slo}",
                })

        elif event == "request_failed" or rec.get("level") == "error":
            errors_count += 1
            err_type = rec.get("error_type", "UnknownError")
            error_types[err_type] += 1
            error_records.append({
                "ts": rec.get("ts"),
                "correlation_id": rec.get("correlation_id", "unknown"),
                "error_type": err_type,
            })

    total_api = api_requests + errors_count
    error_rate = (errors_count / total_api * 100) if total_api > 0 else 0.0
    p50 = percentile(latencies, 50) if latencies else 0.0
    p95 = percentile(latencies, 95) if latencies else 0.0
    p99 = percentile(latencies, 99) if latencies else 0.0
    avg_cost = sum(costs) / len(costs) if costs else 0.0
    total_cost = sum(costs)
    avg_quality = sum(qualities) / len(qualities) if qualities else 0.0

    anomalies_found = (
        len(pii_anomalies) > 0
        or p95 > latency_p95_slo
        or len(latency_violations) > 0
        or error_rate > error_rate_slo
        or len(cost_anomalies) > 0
        or (qualities and avg_quality < min_quality_slo)
    )

    return {
        "log_path": str(log_path),
        "total_records": total_records,
        "total_api_requests": total_api,
        "metrics": {
            "p50_ms": p50,
            "p95_ms": p95,
            "p99_ms": p99,
            "error_rate_pct": round(error_rate, 2),
            "total_errors": errors_count,
            "error_breakdown": dict(error_types),
            "avg_cost_usd": round(avg_cost, 6),
            "total_cost_usd": round(total_cost, 4),
            "avg_quality_score": round(avg_quality, 3),
        },
        "anomalies": {
            "pii_leaks": pii_anomalies,
            "latency_violations": latency_violations,
            "cost_spike_anomalies": cost_anomalies,
            "quality_violations": quality_violations,
            "error_records": error_records,
        },
        "healthy": not anomalies_found,
    }


def main() -> None:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(description="Automated Log Anomaly & SLO Violation Detector")
    parser.add_argument("--log-path", type=str, default="data/logs.jsonl", help="Path to JSONL log file")
    parser.add_argument("--latency-p95-slo", type=float, default=3000.0, help="P95 latency SLO in ms")
    parser.add_argument("--latency-max-slo", type=float, default=5000.0, help="Max latency threshold in ms")
    parser.add_argument("--error-rate-slo", type=float, default=2.0, help="Error rate SLO percentage")
    parser.add_argument("--min-quality-slo", type=float, default=0.70, help="Minimum acceptable quality score")
    parser.add_argument("--max-cost-slo", type=float, default=0.02, help="Max cost per request in USD")
    parser.add_argument("--json", action="store_true", help="Output results in raw JSON format")
    args = parser.parse_args()

    log_path = Path(args.log_path)
    if not log_path.exists():
        print(f"Error: {log_path} not found.")
        sys.exit(1)

    result = analyze_logs(
        log_path=log_path,
        latency_p95_slo=args.latency_p95_slo,
        latency_max_slo=args.latency_max_slo,
        error_rate_slo=args.error_rate_slo,
        min_quality_slo=args.min_quality_slo,
        max_cost_slo=args.max_cost_slo,
    )

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        sys.exit(0 if result.get("healthy") else 1)

    m = result["metrics"]
    a = result["anomalies"]

    print("================================================================")
    print("        AUTOMATED LOG ANOMALY & SLO DETECTION REPORT             ")
    print("================================================================")
    print(f"Log File:           {result['log_path']}")
    print(f"Total Log Records:  {result['total_records']}")
    print(f"Total API Requests: {result['total_api_requests']}")
    print("----------------------------------------------------------------")
    print("Key Metrics:")
    print(f"  - Latency P50 / P95 / P99: {m['p50_ms']}ms / {m['p95_ms']}ms / {m['p99_ms']}ms")
    print(f"  - Error Rate:              {m['error_rate_pct']}% ({m['total_errors']} errors)")
    print(f"  - Avg Cost / Total Cost:   ${m['avg_cost_usd']:.6f} / ${m['total_cost_usd']:.4f}")
    print(f"  - Avg Quality Score:       {m['avg_quality_score']}")
    print("----------------------------------------------------------------")
    print("Anomaly Check Results:")

    # PII Check
    if a["pii_leaks"]:
        print(f"  [ANOMALY] PII Leaks Detected: {len(a['pii_leaks'])} record(s)")
        for leak in a["pii_leaks"][:5]:
            print(f"    -> [{leak['correlation_id']}] Event: {leak['event']} | Types: {leak['pii_types']}")
    else:
        print("  [PASSED]  PII Scrubbing: Clean (0 leaks)")

    # Latency SLO Check
    if m["p95_ms"] > args.latency_p95_slo or a["latency_violations"]:
        print(f"  [ANOMALY] Latency SLO Violated: P95 ({m['p95_ms']}ms) > SLO ({args.latency_p95_slo}ms)")
        for lv in a["latency_violations"][:5]:
            print(f"    -> [{lv['correlation_id']}] Feature: {lv['feature']} | Latency: {lv['latency_ms']}ms")
    else:
        print(f"  [PASSED]  Latency SLO: P95 ({m['p95_ms']}ms <= {args.latency_p95_slo}ms)")

    # Error Rate Check
    if m["error_rate_pct"] > args.error_rate_slo:
        print(f"  [ANOMALY] Error Rate Spike: {m['error_rate_pct']}% > SLO ({args.error_rate_slo}%)")
        print(f"    -> Breakdown: {m['error_breakdown']}")
    else:
        print(f"  [PASSED]  Error Rate SLO: {m['error_rate_pct']}% <= {args.error_rate_slo}%")

    # Cost Check
    if a["cost_spike_anomalies"]:
        print(f"  [ANOMALY] Cost Anomalies Detected: {len(a['cost_spike_anomalies'])} request(s)")
        for ca in a["cost_spike_anomalies"][:5]:
            print(f"    -> [{ca['correlation_id']}] Cost: ${ca['cost_usd']:.4f}")
    else:
        print(f"  [PASSED]  Cost Budget: All requests within limits")

    # Quality Check
    if a["quality_violations"] or (m["avg_quality_score"] < args.min_quality_slo and result["total_api_requests"] > 0):
        print(f"  [ANOMALY] Quality Degradation: Avg {m['avg_quality_score']} < SLO ({args.min_quality_slo})")
    else:
        print(f"  [PASSED]  Quality Score: Avg {m['avg_quality_score']} >= {args.min_quality_slo}")

    print("================================================================")
    if result["healthy"]:
        print("  STATUS: HEALTHY - All SLOs and Security Policies PASSED")
        sys.exit(0)
    else:
        print("  STATUS: ANOMALIES DETECTED - Action Required")
        sys.exit(1)


if __name__ == "__main__":
    main()
