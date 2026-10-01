"""Project-authored synthetic candidate v1 (Apache-2.0).

Calls CPython 3.12 statistics.linear_regression (PSF-2.0); no upstream code copied.
This candidate reports raw values, never a scientific acceptance verdict.
"""

import csv
import json
from pathlib import Path
import statistics
import sys


def main() -> None:
    if sys.argv[2] != "original":
        raise ValueError("only_original_order")
    with Path(sys.argv[1]).open(encoding="ascii", newline="") as stream:
        rows = list(csv.DictReader(stream))
    xs = [float(row["x"]) for row in rows]
    ys = [float(row["y"]) for row in rows]
    slope, intercept = statistics.linear_regression(xs, ys)
    residuals = [y - (slope * x + intercept) for x, y in zip(xs, ys, strict=True)]
    output = {"count": len(xs), "slope": slope, "intercept": intercept,
              "residuals": residuals, "sse": sum(value * value for value in residuals)}
    Path("metrics.json").write_text(json.dumps(output, allow_nan=False), encoding="utf-8")


if __name__ == "__main__":
    main()
