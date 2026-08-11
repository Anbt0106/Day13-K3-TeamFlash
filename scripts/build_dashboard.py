from __future__ import annotations

import argparse
import html
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean

REPO_ROOT = Path(__file__).resolve().parents[1]


def percentile(values: list[float], value: int) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, math.ceil(value / 100 * len(ordered)) - 1))
    return ordered[index]


def load_records(path: Path) -> list[dict]:
    records: list[dict] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON on line {number}: {exc}") from exc
        if isinstance(value, dict):
            records.append(value)
    return records


def split_phases(records: list[dict]) -> dict[str, list[dict]]:
    phases = {"baseline": [], "incident": [], "recovery": []}
    current = "baseline"
    for record in records:
        event = record.get("event")
        incident_name = (record.get("payload") or {}).get("name")
        if event == "incident_enabled" and incident_name == "rag_slow":
            current = "incident"
            continue
        if event == "incident_disabled" and incident_name == "rag_slow":
            current = "recovery"
            continue
        phases[current].append(record)
    return phases


def summarize(records: list[dict]) -> dict:
    received = [row for row in records if row.get("event") == "request_received"]
    responses = [row for row in records if row.get("event") == "response_sent"]
    failures = [row for row in records if row.get("event") == "request_failed"]
    latencies = [float(row["latency_ms"]) for row in responses if row.get("latency_ms") is not None]
    quality = [float(row["quality_score"]) for row in responses if row.get("quality_score") is not None]
    errors = Counter(str(row.get("error_type", "unknown")) for row in failures)
    return {
        "requests": len(received),
        "responses": len(responses),
        "p50": percentile(latencies, 50),
        "p95": percentile(latencies, 95),
        "p99": percentile(latencies, 99),
        "error_rate": len(failures) / len(received) * 100 if received else 0.0,
        "errors": dict(errors),
        "cost": sum(float(row.get("cost_usd", 0)) for row in responses),
        "tokens_in": sum(int(row.get("tokens_in", 0)) for row in responses),
        "tokens_out": sum(int(row.get("tokens_out", 0)) for row in responses),
        "quality": mean(quality) if quality else 0.0,
    }


def bar(label: str, value: float, maximum: float, unit: str) -> str:
    width = min(100, value / maximum * 100) if maximum else 0
    return (
        f'<div class="bar-row"><span>{html.escape(label)}</span><div class="track">'
        f'<div class="fill" style="width:{width:.1f}%"></div></div>'
        f'<strong>{value:,.2f} {html.escape(unit)}</strong></div>'
    )


def build_html(source: Path, records: list[dict]) -> str:
    phase_rows = split_phases(records)
    phases = {name: summarize(rows) for name, rows in phase_rows.items()}
    overall = summarize(records)
    max_latency = max(3000.0, *(item["p95"] for item in phases.values()))
    generated = datetime.now(timezone.utc).isoformat(timespec="seconds")
    latency_bars = "".join(
        bar(name.title(), values["p95"], max_latency, "ms") for name, values in phases.items()
    )
    error_breakdown = ", ".join(f"{key}: {value}" for key, value in overall["errors"].items()) or "No request_failed events"
    phase_table = "".join(
        f"<tr><td>{name.title()}</td><td>{values['requests']}</td><td>{values['p95']:.0f} ms</td>"
        f"<td>{values['error_rate']:.2f}%</td><td>${values['cost']:.6f}</td><td>{values['quality']:.2f}</td></tr>"
        for name, values in phases.items()
    )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="refresh" content="30"><title>Day 13 AI Observability</title>
<style>
:root{{--bg:#07111f;--card:#101d30;--text:#e8f0fa;--muted:#91a4bd;--cyan:#35d3e3;--green:#49d17d;--amber:#f5b942;--red:#ff6577}}
*{{box-sizing:border-box}} body{{margin:0;background:linear-gradient(145deg,#07111f,#0b1830);color:var(--text);font:14px Segoe UI,Arial,sans-serif}}
main{{max-width:1440px;margin:auto;padding:24px}} header{{display:flex;justify-content:space-between;align-items:end;margin-bottom:18px}}
h1{{margin:0;font-size:28px}} .meta{{color:var(--muted);text-align:right}} .grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}}
.card{{background:var(--card);border:1px solid #223650;border-radius:14px;padding:18px;min-height:180px;box-shadow:0 10px 30px #0004}}
.card h2{{font-size:15px;margin:0 0 14px;color:#bcd0e8}} .value{{font-size:30px;font-weight:700}} .sub{{color:var(--muted);margin-top:8px}}
.ok{{color:var(--green)}} .warn{{color:var(--amber)}} .bar-row{{display:grid;grid-template-columns:70px 1fr 105px;gap:9px;align-items:center;margin:10px 0}}
.track{{height:10px;background:#223650;border-radius:8px;overflow:hidden}} .fill{{height:100%;background:linear-gradient(90deg,var(--cyan),var(--green))}}
table{{width:100%;border-collapse:collapse;margin-top:16px;background:var(--card);border-radius:12px;overflow:hidden}} th,td{{padding:10px;border-bottom:1px solid #223650;text-align:left}} th{{color:#9eb5cf}}
.threshold{{font-size:12px;color:var(--amber);margin-top:12px}} footer{{color:var(--muted);margin-top:14px}} @media(max-width:900px){{.grid{{grid-template-columns:1fr}}}}
</style></head><body><main>
<header><div><h1>Day 13 AI Observability</h1><div class="sub">Canonical source: {html.escape(str(source))}</div></div>
<div class="meta">Time range: Last 60 minutes<br>Refresh: 30 seconds<br>Generated: {generated}</div></header>
<section class="grid">
<article class="card"><h2>1. Latency percentiles</h2><div class="value">P95 {overall['p95']:.0f} ms</div><div class="sub">P50 {overall['p50']:.0f} ms · P99 {overall['p99']:.0f} ms</div>{latency_bars}<div class="threshold">SLO: P95 ≤ 3000 ms</div></article>
<article class="card"><h2>2. Request traffic</h2><div class="value">{overall['requests']} requests</div><div class="sub">Count of request_received · {overall['responses']} completed</div><div class="threshold">Threshold: ≥ 1 request/minute during load</div></article>
<article class="card"><h2>3. Error rate and breakdown</h2><div class="value {'ok' if overall['error_rate'] <= 2 else 'warn'}">{overall['error_rate']:.2f}%</div><div class="sub">{html.escape(error_breakdown)}</div><div class="threshold">SLO: error rate ≤ 2%</div></article>
<article class="card"><h2>4. Cost over time</h2><div class="value">${overall['cost']:.6f}</div><div class="sub">Total cost in active window</div><div class="threshold">Budget threshold: ≤ $2.50</div></article>
<article class="card"><h2>5. Input and output tokens</h2><div class="value">{overall['tokens_in']:,} / {overall['tokens_out']:,}</div><div class="sub">Input tokens / Output tokens</div><div class="threshold">Threshold: ≤ 50,000 tokens per field</div></article>
<article class="card"><h2>6. Quality proxy</h2><div class="value {'ok' if overall['quality'] >= .75 else 'warn'}">{overall['quality']:.2f}</div><div class="sub">Mean quality score (0–1)</div><div class="threshold">SLO: mean ≥ 0.75</div></article>
</section>
<table><thead><tr><th>Phase</th><th>Traffic</th><th>P95 latency</th><th>Error rate</th><th>Cost</th><th>Quality</th></tr></thead><tbody>{phase_table}</tbody></table>
<footer>Metrics → Traces → Logs. Use correlation IDs from the evidence file to drill down into the incident.</footer>
</main></body></html>"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a six-panel dashboard from JSONL logs")
    parser.add_argument("--input", type=Path, default=REPO_ROOT / "data" / "logs.jsonl")
    parser.add_argument("--output", type=Path, default=REPO_ROOT / "submission" / "evidence" / "dashboard-cp2.html")
    args = parser.parse_args()
    records = load_records(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(build_html(args.input, records), encoding="utf-8")
    print(f"Dashboard written to {args.output} ({len(records)} records, 6 panels)")


if __name__ == "__main__":
    main()
