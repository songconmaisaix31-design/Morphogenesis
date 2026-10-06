#!/usr/bin/env python3
"""Supervise the environment observatory: keep it up, restart it when it dies.

Why this exists
---------------
The panel is meant to be left open for long stretches. It was observed to
disappear silently --- the child had no traceback, the log held only the startup
banner --- which is what an externally killed process looks like (machine sleep,
a parent shell teardown, an OOM kill). Losing the panel that way is a usability
bug, not a crash to debug, so the fix is supervision rather than more try/except.

What it does
------------
* starts ``server.py`` as a child with the inherited environment
* polls ``GET /api/health`` (a deliberately cheap endpoint: no SQLite, no
  subprocess) and restarts the child if the process died *or* if health fails
  repeatedly while the process still looks alive (wedged worker)
* exponential backoff so a genuinely broken config does not spin the CPU
* stops cleanly on Ctrl+C / SIGTERM and does not restart after that

Usage
-----
    python src/env-observatory/watchdog.py --port 8100
    python src/env-observatory/watchdog.py --port 8100 --health-interval 20

The server itself is unchanged: this only wraps it. Running
``python src/env-observatory/server.py`` directly still works.
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
SERVER = HERE / "server.py"

_stopping = False


def _log(message: str) -> None:
    stamp = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[watchdog {stamp}] {message}"
    print(line, flush=True)


def _on_signal(signum: int, _frame: object) -> None:
    global _stopping
    _stopping = True
    _log(f"received signal {signum}, shutting down")


def _health(port: int, timeout: float = 4.0) -> dict | None:
    url = f"http://127.0.0.1:{port}/api/health"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            if response.status != 200:
                return None
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, OSError, ValueError):
        return None


def _port_taken(port: int, host: str = "127.0.0.1") -> bool:
    """True when something already accepts connections on the port."""
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.settimeout(1.5)
        return probe.connect_ex((host, port)) == 0


def _wait_healthy(port: int, deadline_s: float) -> dict | None:
    """Poll /api/health until it answers, so the log can report the real serving pid.

    On Windows ``.venv\\Scripts\\python.exe`` is a forwarding shim that re-executes
    the real interpreter as a *child* process. The pid we get from Popen is the
    shim, not the process that owns the socket --- reporting the health payload's
    pid is the honest number, and the indirection is why they differ.
    """
    end = time.time() + deadline_s
    while time.time() < end and not _stopping:
        report = _health(port)
        if report is not None:
            return report
        time.sleep(1.0)
    return None


def _seed_dashscope_key() -> None:
    """Reuse the Bailian key the panel's Wayfinder POST needs, if it is present.

    Never overwrites an existing value and never logs the key itself.
    """
    if os.environ.get("DASHSCOPE_API_KEY"):
        return
    config = Path.home() / ".bailian" / "config.json"
    if not config.is_file():
        return
    try:
        data = json.loads(config.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return
    key = data.get("api_key") if isinstance(data, dict) else None
    if isinstance(key, str) and key.strip():
        os.environ["DASHSCOPE_API_KEY"] = key.strip()
        _log("DASHSCOPE_API_KEY picked up from ~/.bailian/config.json")


def _default_host_config() -> None:
    """Point the server at the state directory that ships beside it.

    The server 503s every /api/research/* route without this, which looks like a
    broken backend rather than a missing environment variable --- so fill it in
    when it is absent, and say so.
    """
    if os.environ.get("OBSERVATORY_HOST_CONFIG"):
        return
    candidate = HERE / ".state" / "host-config.json"
    if candidate.is_file():
        os.environ["OBSERVATORY_HOST_CONFIG"] = str(candidate)
        _log(f"OBSERVATORY_HOST_CONFIG -> {candidate}")
    else:
        _log(f"no host config at {candidate}; /api/research/* will degrade to 503")


def main() -> int:
    parser = argparse.ArgumentParser(description="Supervise the observatory server.")
    parser.add_argument("--port", type=int, default=int(os.environ.get("OBSERVATORY_PORT", "8100")))
    parser.add_argument("--health-interval", type=float, default=15.0,
                        help="Seconds between /api/health polls (default 15)")
    parser.add_argument("--health-grace", type=float, default=45.0,
                        help="Seconds to allow for startup / a slow first probe (default 45)")
    parser.add_argument("--unhealthy-limit", type=int, default=3,
                        help="Consecutive failed health checks before restarting a live process")
    parser.add_argument("--restart-delay", type=float, default=2.0,
                        help="Base delay before restart; doubles per consecutive failure")
    parser.add_argument("--max-restart-delay", type=float, default=60.0)
    parser.add_argument("--max-restarts", type=int, default=0,
                        help="Give up after N restarts (0 = never give up)")
    parser.add_argument("--log", default=None, help="Append server stdout/stderr here")
    args = parser.parse_args()

    signal.signal(signal.SIGINT, _on_signal)
    signal.signal(signal.SIGTERM, _on_signal)

    _seed_dashscope_key()
    _default_host_config()

    log_handle = None
    if args.log:
        Path(args.log).parent.mkdir(parents=True, exist_ok=True)
        log_handle = open(args.log, "a", encoding="utf-8", buffering=1)  # noqa: SIM115
        _log(f"server output -> {args.log}")

    child: subprocess.Popen | None = None
    restarts = 0
    backoff = args.restart_delay
    started_at = 0.0
    unhealthy = 0

    def spawn() -> subprocess.Popen:
        _log(f"starting server.py on port {args.port}")
        return subprocess.Popen(  # noqa: S603 - fixed argv, no shell
            [sys.executable, "-u", str(SERVER), "--port", str(args.port)],
            cwd=str(HERE.parent.parent),
            env=dict(os.environ),
            stdout=log_handle or None,
            stderr=log_handle or None,
        )

    def start_and_settle() -> tuple[subprocess.Popen, dict | None]:
        """Spawn, then wait for health so we can log the pid that really serves."""
        proc = spawn()
        report = _wait_healthy(args.port, args.health_grace)
        if report is not None:
            _log(f"serving: shim pid {proc.pid} -> socket pid {report.get('pid')} "
                 f"(service_ready={report.get('service_ready')})")
        else:
            _log(f"no healthy response within {args.health_grace:.0f}s "
                 f"(shim pid {proc.pid}); will re-check")
        return proc, report

    # 端口预检：端口被别人占着时反复 spawn 只会得到一个绑定失败的子进程和一堆
    # 无意义的重启日志，听起来像"崩溃"其实只是冲突。直接说清楚并退出。
    if _port_taken(args.port):
        owner = _health(args.port)
        if owner is not None:
            _log(f"port {args.port} already serves the observatory "
                 f"(socket pid {owner.get('pid')}). Refusing to start a second one.")
        else:
            _log(f"port {args.port} is taken by another process. "
                 f"Free it, or run with --port <other>.")
        return 2

    try:
        child, _ = start_and_settle()
        started_at = time.time()

        while not _stopping:
            time.sleep(args.health_interval)
            if _stopping:
                break

            alive = child.poll() is None
            if not alive:
                code = child.returncode
                _log(f"child exited with code {code}; restarting in {backoff:.0f}s")
                time.sleep(backoff)
                if _stopping:
                    break
                restarts += 1
                if args.max_restarts and restarts > args.max_restarts:
                    _log(f"hit --max-restarts={args.max_restarts}, giving up")
                    return 1
                if _port_taken(args.port) and _health(args.port) is None:
                    _log(f"port {args.port} is held by a process that does not answer "
                         f"/api/health; not restarting")
                    return 2
                child, _ = start_and_settle()
                started_at = time.time()
                unhealthy = 0
                backoff = min(backoff * 2, args.max_restart_delay)
                continue

            report = _health(args.port)
            if report is not None:
                unhealthy = 0
                backoff = args.restart_delay
                continue

            # 健康检查失败但进程还在：可能只是在启动/首次探测，给宽限期
            age = time.time() - started_at
            if age < args.health_grace:
                continue
            unhealthy += 1
            _log(f"health check failed ({unhealthy}/{args.unhealthy_limit}), uptime {age:.0f}s")
            if unhealthy < args.unhealthy_limit:
                continue
            _log("worker looks wedged; terminating and restarting")
            child.terminate()
            try:
                child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait(timeout=10)
            unhealthy = 0
    finally:
        if child is not None and child.poll() is None:
            _log("stopping server")
            child.terminate()
            try:
                child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                child.kill()
        if log_handle is not None:
            log_handle.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
