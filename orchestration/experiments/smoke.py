"""One official CPU interface check, distinct from native-agent task acceptance."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import time
from typing import Any

from orchestration.experiments.backend import OpenSandboxBackend, OpenSandboxSession
from orchestration.experiments.case import public_case
from orchestration.experiments.executor import DIRECTORY, ExperimentExecutor, read_result
from orchestration.experiments.models import ExperimentContext, ExperimentPlan


class InterfaceBackend(OpenSandboxBackend):
    def __init__(self, archive: Path, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.archive = archive

    def create(self, plan: ExperimentPlan, context: ExperimentContext) -> OpenSandboxSession:
        session = super().create(plan, context)
        observations: dict[str, Any] = {"sandbox_id": session.id}

        def record() -> None:
            (self.archive / context.run_id / "interface.json").write_text(
                json.dumps(observations, indent=2), encoding="utf-8")

        try:
            observations["created_info"] = session.info()
            record()
            attached = self.connect(session.id)
            try:
                observations["connected_info"] = attached.info()
                try:
                    attached.destroy()
                    raise AssertionError("attached destruction must be rejected")
                except PermissionError:
                    observations["attached_destroy_rejected"] = True
            finally:
                attached.close()
            observations["renewal"] = session.renew(plan.resources.lifetime_seconds)
            session.upload(f"{DIRECTORY}/binary.bin", b"\x00\xff\x80\x01")
            observations["binary_roundtrip"] = session.download(f"{DIRECTORY}/binary.bin", 16) == b"\x00\xff\x80\x01"
            if observations["binary_roundtrip"] is not True:
                raise AssertionError("binary roundtrip mismatch")
            resource_code = ("from pathlib import Path;import json;"
                "print(json.dumps({n:Path('/sys/fs/cgroup/'+n).read_text().strip() "
                "for n in ['cpu.max','memory.max']}))")
            quotas = session.run(["python3", "-c", resource_code], 10, DIRECTORY)
            observations["resource_command"] = quotas.model_dump(mode="json")
            if quotas.exit_code != 0:
                raise AssertionError("cgroup inspection failed")
            quota_text = "".join(log.text for log in quotas.logs.stdout)
            limits = json.loads(quota_text)
            observations["resource_limits"] = limits
            quota, period = (int(part) for part in limits["cpu.max"].split())
            if quota / period != plan.resources.cpu or int(limits["memory.max"]) != plan.resources.memory_mib * 1024 * 1024:
                raise AssertionError("resource quota mismatch")
            command = session.start(["python3", "-u", "-c", "import time;print('cancel-probe');time.sleep(60)"], 20, DIRECTORY)
            observations["background_execution"] = command.model_dump(mode="json")
            if not command.id:
                raise AssertionError("background id missing")
            observations["command_status_before_cancel"] = session.command_status(command.id)
            session.cancel(command.id)
            deadline = time.monotonic() + 3
            status = session.command_status(command.id)
            # Read-only observation of the same command, never another run.
            while status.get("running") is True and time.monotonic() < deadline:
                time.sleep(0.1)
                status = session.command_status(command.id)
            observations["command_status_after_cancel"] = status
            if status.get("running") is not False:
                raise AssertionError("cancel completion unknown")
            observations["command_logs"] = session.command_logs(command.id)
            record()
            return session
        except Exception as error:
            observations["error_type"] = type(error).__name__
            record()
            try:
                session.destroy()
            finally:
                session.close()
            raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-dir", required=True, type=Path)
    parser.add_argument("--archive-root", required=True, type=Path)
    parser.add_argument("--run-id", default="interface-c-0930-01")
    parser.add_argument("--domain", default="127.0.0.1:8097")
    args = parser.parse_args()
    context = ExperimentContext(run_id=args.run_id, task_id="nist-numacc4-interface",
                                worker_id="c-sdk-interface", fencing_token=1)
    plan = public_case(args.case_dir)
    backend = InterfaceBackend(args.archive_root, domain=args.domain,
                               api_key=os.environ["OPENSANDBOX_SERVER_API_KEY"])
    result = ExperimentExecutor(backend).execute(plan, context, args.archive_root)
    loaded = read_result(args.archive_root, context.run_id, expected_plan=plan, expected_context=context)
    passed = (loaded.execution_state == "succeeded" and loaded.scientific.verdict == "passed"
              and loaded.cleanup_state == "destroyed" and loaded.remote_effect == "known")
    summary = {"interface_live": "passed" if passed else "failed", "task_live": "NOT_RUN",
               "provenance": result.provenance, "archive_path": result.archive_path,
               "sandbox_id": result.sandbox_id, "execution_state": result.execution_state,
               "scientific": loaded.scientific.model_dump(), "cleanup_state": result.cleanup_state,
               "remote_effect": result.remote_effect, "cost_usd": result.cost_usd, "usage": result.usage}
    (args.archive_root / context.run_id / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
