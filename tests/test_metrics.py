from app import metrics
from app.metrics import percentile, snapshot


def test_percentile_basic() -> None:
    assert percentile([100, 200, 300, 400], 50) >= 100


def test_snapshot_error_rate_pct() -> None:
    metrics.TRAFFIC = 10
    metrics.ERRORS.clear()
    metrics.ERRORS["RuntimeError"] = 2
    metrics.ERRORS["TimeoutError"] = 3
    # TRAFFIC records requests received, including requests that later fail.
    # total errors = 5, total requests = 10 => error_rate = 50%
    snap = snapshot()
    assert snap["error_rate_pct"] == 50.0
    assert snap["failed_requests"] == 5
    assert snap["traffic"] == 10

