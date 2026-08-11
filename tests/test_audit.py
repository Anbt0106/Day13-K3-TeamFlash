from __future__ import annotations
import json
from pathlib import Path
from fastapi.testclient import TestClient

from app import logging_config
from app.main import app


def test_audit_log_captures_incident_and_control_events(monkeypatch, tmp_path: Path) -> None:
    audit_path = tmp_path / "audit.jsonl"
    monkeypatch.setattr(logging_config, "AUDIT_LOG_PATH", audit_path)

    with TestClient(app) as client:
        # Enable incident
        res = client.post("/incidents/cost_spike/enable")
        assert res.status_code == 200

        # Disable incident
        res = client.post("/incidents/cost_spike/disable")
        assert res.status_code == 200

    assert audit_path.exists()
    records = [json.loads(line) for line in audit_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    events = [r.get("event") for r in records]
    assert "incident_enabled" in events
    assert "incident_disabled" in events
    for r in records:
        assert "ts" in r
        assert "level" in r
        assert r.get("service") in ("control", "day13-observability-lab")
