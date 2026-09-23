"""Local health only: never queries EvoMap or starts a task."""

import json
from pathlib import Path
import sys
from urllib.request import urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from viz.adapter import validate_dashboard_snapshot


def main() -> None:
    with urlopen("http://127.0.0.1:7500/api/dashboard", timeout=3) as response:
        data = json.load(response)
        assert response.status == 200
        validate_dashboard_snapshot(data)


if __name__ == "__main__":
    main()
