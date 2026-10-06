"""Account readiness as a presence question, never a value read.

Most deployments can answer "is an account wired?" without spending a network
request: the credential is either injected into the process environment or it
is not.  Only names and counts are reported.
"""

from __future__ import annotations

import os
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from contracts.readiness import ProbeResult, ProbeSubject


@dataclass(frozen=True)
class CredentialProbe:
    """Report whether each declared environment variable is set."""

    probe_id: str
    names: Sequence[str]
    subject: ProbeSubject = "account"
    lookup: Mapping[str, str] | None = None

    def __post_init__(self) -> None:
        if not self.probe_id:
            raise ValueError("probe_id must not be empty")
        if not self.names or any(not name.strip() for name in self.names):
            raise ValueError("names must declare at least one non-empty variable")

    def probe(self) -> ProbeResult:
        source: Mapping[str, str] = self.lookup if self.lookup is not None else os.environ
        missing = [name for name in self.names if not (source.get(name) or "").strip()]
        present = len(self.names) - len(missing)
        evidence = {
            "code": "configured" if not missing else "missing",
            "present": f"{present}/{len(self.names)}",
        }
        if missing:
            evidence["missing"] = ",".join(missing)
        return ProbeResult(
            probe_id=self.probe_id,
            subject=self.subject,
            state="ok" if not missing else "blocked",
            observed=True,
            detail="凭据已注入进程环境" if not missing else f"缺少环境变量：{', '.join(missing)}",
            evidence=evidence,
            notes=["只报告环境变量是否存在；不读取、不记录、不回显其值。"],
        )
