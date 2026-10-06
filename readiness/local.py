"""The one probe that needs no configuration: the host this process runs on.

A public deployment runs on machines this project has never seen, so the host
dimension is observed at runtime and never written down as a constant.
"""

from __future__ import annotations

import os
import platform
import tempfile
from dataclasses import dataclass

from contracts.readiness import ProbeResult, ProbeSubject


@dataclass(frozen=True)
class LocalMachineProbe:
    probe_id: str = "machine:host"
    subject: ProbeSubject = "machine"

    def probe(self) -> ProbeResult:
        cpus = os.cpu_count() or 0
        writable = _temp_writable()
        evidence = {
            "os": platform.system() or "unknown",
            "python": platform.python_version() or "unknown",
            "cpus": str(cpus),
            "temp_writable": "true" if writable else "false",
        }
        healthy = writable and cpus > 0
        return ProbeResult(
            probe_id=self.probe_id,
            subject=self.subject,
            state="ok" if healthy else "degraded",
            observed=True,
            detail=f"{evidence['os']} / Python {evidence['python']} / {cpus} CPU",
            evidence=evidence,
            notes=["只报告进程实际观测到的宿主事实；不含主机名、用户名与路径。"],
        )


def _temp_writable() -> bool:
    try:
        return os.access(tempfile.gettempdir(), os.W_OK)
    except OSError:
        return False
