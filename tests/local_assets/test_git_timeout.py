"""Real owned descendants exercise Windows stdout/stderr inheritance on timeout."""
from pathlib import Path
import subprocess
import sys
import time

import pytest

from local_assets.paths import git


@pytest.mark.skipif(sys.platform != "win32", reason="CPython Windows timeout drains inherited pipes")
def test_git_timeout_does_not_wait_for_descendant_pipe_eof(tmp_path: Path, monkeypatch) -> None:
    import _winapi
    from orchestration.native_agents.windows_job import WindowsJob

    helper = tmp_path / "owned_wrapper.py"
    helper.write_text(
        "import subprocess,sys,time\nfrom pathlib import Path\n"
        "deadline = time.monotonic() + 120\n"
        "while not Path(sys.argv[2]).is_file():\n"
        "    if time.monotonic() >= deadline: raise TimeoutError('fixture ownership gate')\n"
        "    time.sleep(0.01)\n"
        "code = \"import os,sys,time; from pathlib import Path; Path(sys.argv[2]).write_text(str(os.getpid())); print('owned-stdout',flush=True); print('owned-stderr',file=sys.stderr,flush=True); Path(sys.argv[1]).write_text('descendant-created'); time.sleep(4)\"\n"
        "subprocess.Popen([sys._base_executable, '-I', '-S', '-c', code, sys.argv[1], sys.argv[3]], stdout=sys.stdout, stderr=sys.stderr)\n"
        "time.sleep(20)\n", encoding="utf-8")
    native_run = subprocess.run
    native_popen = subprocess.Popen
    calls = []
    captured = []
    owned_roots, owned_jobs, descendant_handles = [], [], []
    phases, descendant_exitcodes = {}, []
    spawn_gate, descendant_pid = tmp_path / "start-descendant", tmp_path / "descendant.pid"

    class ReadyPopen(native_popen):
        def __enter__(self):
            process = super().__enter__()
            phases["popen_enter"] = time.monotonic()
            owned_roots.append(self)
            (tmp_path / "wrapper.pid").write_text(str(self.pid))
            job = WindowsJob()
            owned_jobs.append(job)
            job.assign(self.pid)
            phases["job_assigned"] = time.monotonic()
            # The helper cannot spawn before its newly owned Job is assigned.
            # Cleanup is after the timed assertions, so it cannot hide EOF drain.
            spawn_gate.touch()
            # subprocess.run enters its real process context before starting
            # communicate(timeout). Cold fixture startup is a separate bounded
            # phase, not part of the 0.2-second communication timeout. It still
            # counts toward the original total elapsed <3-second assertion.
            deadline = time.monotonic() + 120
            while not (tmp_path / "ready").is_file():
                if self.poll() is not None:
                    raise RuntimeError("owned fixture exited before descendant readiness")
                if time.monotonic() >= deadline:
                    raise TimeoutError("owned fixture readiness deadline")
                time.sleep(0.01)
            # Hold the actual live descendant handle; PID reuse/name matching
            # never authorizes cleanup. SYNCHRONIZE | QUERY_LIMITED_INFORMATION.
            handle = _winapi.OpenProcess(0x100000 | 0x1000, False, int(descendant_pid.read_text()))
            descendant_handles.append(handle)
            assert _winapi.GetExitCodeProcess(handle) == 259, "owned descendant was not live at communication start"
            phases["descendant_ready"] = time.monotonic()
            return process

    def owned_native_wrapper(argv, **kwargs):
        # Substitute only the executable fixture, keeping actual subprocess
        # handles, Windows reader threads, timeout and descendant inheritance.
        calls.append((argv, kwargs["timeout"]))
        try:
            # The fixture uses only stdlib: official isolated/no-site flags
            # avoid loading unrelated installed packages in both real children.
            return native_run([sys._base_executable, "-I", "-S", str(helper), str(tmp_path / 'ready'),
                               str(spawn_gate), str(descendant_pid)], **kwargs)
        except subprocess.TimeoutExpired as error:
            phases["native_timeout"] = time.monotonic()
            for name in ("stdout", "stderr"):
                target = kwargs.get(name)
                if target is not None:
                    target.seek(0)
                    captured.append(target.read())
                else:
                    captured.append(getattr(error, name))
            raise

    monkeypatch.setattr("local_assets.paths.subprocess.run", owned_native_wrapper)
    monkeypatch.setattr("local_assets.paths.subprocess.Popen", ReadyPopen)
    started = time.monotonic()
    try:
        with pytest.raises(subprocess.TimeoutExpired):
            git(tmp_path, "ls-tree", "-rz", "HEAD", timeout=0.2)
        assert (tmp_path / "ready").is_file(), "fixture did not reach descendant inheritance"
        assert b"owned-stdout" in captured[0] and b"owned-stderr" in captured[1]
        assert time.monotonic() - started < 3, "timeout waited for descendant stdout/stderr EOF"
        assert calls[0][0][-3:] == ["ls-tree", "-rz", "HEAD"]
        assert calls[0][1] == 0.2
        phases["assertions_complete"] = time.monotonic()
    finally:
        # Only Jobs assigned to the freshly created fixture root are stopped.
        # Production Git cleanup is untouched, and all original assertions run
        # before cleanup so inherited pipes cannot be made artificially green.
        try:
            for job in owned_jobs:
                try:
                    job.terminate()
                finally:
                    job.close()
            for process in owned_roots:
                if process.poll() is None:
                    process.kill()
                process.wait(timeout=3)
            for handle in descendant_handles:
                assert _winapi.WaitForSingleObject(handle, 3000) == 0, "owned descendant cleanup did not finish"
                exitcode = _winapi.GetExitCodeProcess(handle)
                descendant_exitcodes.append(exitcode)
                assert exitcode != 259
            phases["cleanup_complete"] = time.monotonic()
        finally:
            for handle in descendant_handles:
                _winapi.CloseHandle(handle)
            # Raw local fixture diagnostics, including first failures. Neither
            # scientific evidence nor an approval/completion record is emitted.
            records = [f"root_pid={process.pid} root_exitcode={process.returncode}" for process in owned_roots]
            if descendant_pid.is_file():
                records.append("descendant_pid=" + descendant_pid.read_text())
            records.extend(f"descendant_exitcode={code}" for code in descendant_exitcodes)
            records.extend(f"{name}_seconds={tick - started:.6f}" for name, tick in phases.items())
            (tmp_path / "fixture.log").write_text("\n".join(records) + "\n", encoding="utf-8")
