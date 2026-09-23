"""Local health only: never queries EvoMap or starts a task."""

import json
from urllib.request import urlopen

with urlopen("http://127.0.0.1:7500/api/dashboard", timeout=3) as response:
    data = json.load(response)
    assert response.status == 200
    assert data["acceptance"]["interface_live"] == "not_run"
    assert data["acceptance"]["task_live"] == "not_run"
    if data["provenance"] not in {"mock", "replay"}:
        # Existing empty_dashboard uses provenance=live but contains no evidence.
        assert not any(data[key] for key in ("events", "genes", "adoptions", "metrics", "result", "rehearsal"))
