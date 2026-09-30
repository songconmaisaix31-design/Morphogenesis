"""Real owned descendants exercise Windows stdout/stderr inheritance on timeout."""
from pathlib import Path
import subprocess
import sys
import time

import pytest

from local_assets.paths import git


@pytest.mark.skipif(sys.platform != "win32", reason="CPython Windows timeout drains inherited pipes")
def test_git_timeout_does_not_wait_for_descendant_pipe_eof(tmp_path: Path, monkeypatch) -> None:
    helper = tmp_path / "owned_wrapper.py"
    helper.write_text(
        "import subprocess,sys,time\nfrom pathlib import Path\n"
        "code = \"import sys,time; from pathlib import Path; print('owned-stdout',flush=True); print('owned-stderr',file=sys.stderr,flush=True); Path(sys.argv[1]).write_text('descendant-created'); time.sleep(4)\"\n"
        "subprocess.Popen([sys._base_executable, '-c', code, sys.argv[1]], stdout=sys.stdout, stderr=sys.stderr)\n"
        "time.sleep(20)\n", encoding="utf-8")
    native_run = subprocess.run
    calls = []
    captured = []

    def owned_native_wrapper(argv, **kwargs):
        # Substitute only the executable fixture, keeping actual subprocess
        # handles, Windows reader threads, timeout and descendant inheritance.
        calls.append((argv, kwargs["timeout"]))
        try:
            return native_run([sys._base_executable, str(helper), str(tmp_path / 'ready')], **kwargs)
        except subprocess.TimeoutExpired as error:
            for name in ("stdout", "stderr"):
                target = kwargs.get(name)
                if target is not None:
                    target.seek(0)
                    captured.append(target.read())
                else:
                    captured.append(getattr(error, name))
            raise

    monkeypatch.setattr("local_assets.paths.subprocess.run", owned_native_wrapper)
    started = time.monotonic()
    with pytest.raises(subprocess.TimeoutExpired):
        git(tmp_path, "ls-tree", "-rz", "HEAD", timeout=0.2)
    assert (tmp_path / "ready").is_file(), "fixture did not reach descendant inheritance"
    assert b"owned-stdout" in captured[0] and b"owned-stderr" in captured[1]
    assert time.monotonic() - started < 3, "timeout waited for descendant stdout/stderr EOF"
    assert calls[0][0][-3:] == ["ls-tree", "-rz", "HEAD"]
    assert calls[0][1] == 0.2
