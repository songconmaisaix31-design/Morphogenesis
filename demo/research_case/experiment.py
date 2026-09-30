"""NIST NumAcc4: Python standard library statistics versus naive cancellation.

This project-authored experiment uses CPython statistics; no upstream code copied.
"""

import json
from pathlib import Path
import statistics
import sys


def main() -> None:
    data = Path(sys.argv[1]).read_text(encoding="ascii").splitlines()[60:]
    values = [float(line) for line in data if line.strip()]
    if sys.argv[2] == "reverse":
        values.reverse()
    mean = statistics.mean(values)
    output = {"count": len(values), "mean": mean, "sample_variance": statistics.variance(values),
              "naive_variance": (sum(x * x for x in values) - sum(values) ** 2 / len(values)) / (len(values) - 1),
              "residuals": [x - mean for x in values]}
    Path("metrics.json").write_text(json.dumps(output, allow_nan=False), encoding="utf-8")


if __name__ == "__main__":
    main()
