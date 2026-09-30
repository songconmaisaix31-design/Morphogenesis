"""One Windows startup barrier; the parent assigns its Job before sending argv.

This is a subprocess adapter, not an agent loop. It never selects or retries work.
"""

import json
from pathlib import Path
import subprocess
import sys


def main() -> int:
    # EOF before the single payload means the host never authorized native startup.
    line = sys.stdin.buffer.readline()
    if not line:
        return 1
    payload = json.loads(line)
    argv = payload["argv"]
    if not isinstance(argv, list) or not argv or not all(isinstance(arg, str) for arg in argv):
        raise ValueError("native argv must be an explicit string list")
    # A separate file/console means Python buffering of the gate cannot eat CLI stdin.
    try:
        with open(payload["stdin_path"] or "CONIN$", "rb") as stdin:
            child = subprocess.Popen(argv, stdin=stdin, shell=False)
            return child.wait()
    except OSError as exc:
        # An ordinary launch-error log, not a task status or completion proof.
        if payload.get("launch_error_path"):
            Path(payload["launch_error_path"]).write_text(type(exc).__name__, encoding="utf-8")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
