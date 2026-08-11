# CP2 evidence checklist

## Included

- `dashboard-validator.txt`: successful result from `python scripts/validate_dashboard.py`.
- `docs/dashboard-spec.md`: six-panel dashboard specification with a 60-minute time range, 30-second refresh, units, and SLO thresholds.
- `dashboard-cp2.html`: standalone six-panel runtime dashboard generated from `data/logs.jsonl`.
- `cp3-results.json`: baseline, incident, recovery and Langfuse trace/span identifiers.
- `cp3-investigation.md`: complete Metrics → Traces → Logs investigation and remediation report.
- `cp3-related-log-redacted.jsonl`: verifiable incident and recovery log lines without raw PII.

## Capture after running the API with valid Langfuse credentials

- `langfuse-traces-list.png`: the Langfuse Traces view showing at least 10 recent traces.
- `langfuse-trace-waterfall.png`: one trace showing `chat-response`, `retrieve-context`, and `generate-response`, plus duration, user hash, session ID, and tags.
- `dashboard-cp2.png`: optional screenshot of the included HTML dashboard showing all six named panels, units, the 60-minute time range, and threshold/SLO lines.

Do not include Langfuse credentials, raw PII, or unredacted payloads in screenshots.
