from __future__ import annotations

import json
from pathlib import Path

from scripts import detect_anomalies


def test_detect_anomalies_finds_pii_and_latency_spikes(tmp_path: Path) -> None:
    log_file = tmp_path / "test_logs.jsonl"
    records = [
        # Normal log
        {
            "ts": "2026-08-11T00:00:00Z",
            "level": "info",
            "service": "api",
            "event": "response_sent",
            "correlation_id": "req-11111111",
            "feature": "qa",
            "latency_ms": 200,
            "cost_usd": 0.001,
            "quality_score": 0.9,
            "payload": {"answer_preview": "Clean answer"},
        },
        # PII leak log
        {
            "ts": "2026-08-11T00:00:01Z",
            "level": "info",
            "service": "api",
            "event": "request_received",
            "correlation_id": "req-22222222",
            "feature": "qa",
            "payload": {"message": "My email is student@vinuni.edu.vn"},
        },
        # Slow request log exceeding SLO
        {
            "ts": "2026-08-11T00:00:02Z",
            "level": "info",
            "service": "api",
            "event": "response_sent",
            "correlation_id": "req-33333333",
            "feature": "refund",
            "latency_ms": 6000,
            "cost_usd": 0.002,
            "quality_score": 0.85,
            "payload": {"answer_preview": "Delayed response"},
        },
    ]

    log_file.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in records) + "\n",
        encoding="utf-8",
    )

    result = detect_anomalies.analyze_logs(
        log_path=log_file,
        latency_p95_slo=3000.0,
        latency_max_slo=5000.0,
    )

    assert result["healthy"] is False
    assert len(result["anomalies"]["pii_leaks"]) == 1
    assert result["anomalies"]["pii_leaks"][0]["correlation_id"] == "req-22222222"
    assert len(result["anomalies"]["latency_violations"]) == 1
    assert result["anomalies"]["latency_violations"][0]["correlation_id"] == "req-33333333"


def test_detect_anomalies_healthy_logs(tmp_path: Path) -> None:
    log_file = tmp_path / "healthy_logs.jsonl"
    records = [
        {
            "ts": "2026-08-11T00:00:00Z",
            "level": "info",
            "service": "api",
            "event": "response_sent",
            "correlation_id": "req-11111111",
            "feature": "qa",
            "latency_ms": 150,
            "cost_usd": 0.001,
            "quality_score": 0.95,
            "payload": {"answer_preview": "[REDACTED_EMAIL]"},
        },
    ]
    log_file.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in records) + "\n",
        encoding="utf-8",
    )

    result = detect_anomalies.analyze_logs(log_path=log_file)
    assert result["healthy"] is True
    assert len(result["anomalies"]["pii_leaks"]) == 0
    assert len(result["anomalies"]["latency_violations"]) == 0
