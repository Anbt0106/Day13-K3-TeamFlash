import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_dashboard_builder_renders_six_panels_and_incident_phases(tmp_path: Path) -> None:
    log_path = tmp_path / "logs.jsonl"
    output_path = tmp_path / "dashboard.html"
    records = [
        {"event": "request_received"},
        {"event": "response_sent", "latency_ms": 100, "cost_usd": 0.01, "tokens_in": 10, "tokens_out": 20, "quality_score": 0.9},
        {"event": "incident_enabled", "payload": {"name": "rag_slow"}},
        {"event": "request_received"},
        {"event": "response_sent", "latency_ms": 2600, "cost_usd": 0.01, "tokens_in": 10, "tokens_out": 20, "quality_score": 0.9},
        {"event": "incident_disabled", "payload": {"name": "rag_slow"}},
        {"event": "request_received"},
        {"event": "response_sent", "latency_ms": 120, "cost_usd": 0.01, "tokens_in": 10, "tokens_out": 20, "quality_score": 0.9},
    ]
    log_path.write_text("\n".join(json.dumps(row) for row in records), encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "build_dashboard.py"), "--input", str(log_path), "--output", str(output_path)],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    dashboard = output_path.read_text(encoding="utf-8")
    assert dashboard.count('<article class="card">') == 6
    assert "P95 2600 ms" in dashboard
    assert "Baseline" in dashboard
    assert "Incident" in dashboard
    assert "Recovery" in dashboard
