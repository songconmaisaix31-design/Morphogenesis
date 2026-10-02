"""Q tests run against an explicitly selected owner checkout or exact archive.

Only this directory is collected. Never import owner test helpers or execute
generated candidates; process/network entry points are denied during tests.
"""
import asyncio
import os
from pathlib import Path
import socket
import subprocess
import sys

import pytest

target = Path(os.environ.get("R1_SECURITY_SOURCE", Path(__file__).resolve().parents[3])).resolve()
sys.path.insert(0, str(target))


@pytest.fixture(autouse=True)
def deny_candidate_execution_and_network(monkeypatch):
    # Windows' trusted stdlib loop creates a local self-pipe using socketpair.
    # Create it before installing the network guard; every test/tool call below
    # remains guarded, including loop-driven FastMCP invocation.
    loop = asyncio.new_event_loop()
    def denied(*args, **kwargs):
        raise AssertionError("Q forbids host process launch and external network")

    monkeypatch.setattr(subprocess, "Popen", denied)
    monkeypatch.setattr(os, "system", denied)
    monkeypatch.setattr(socket.socket, "connect", denied)
    monkeypatch.setattr(socket.socket, "connect_ex", denied)
    yield loop
    loop.close()
