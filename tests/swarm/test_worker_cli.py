"""Runtime review/failure outcomes must reach the caller's exit status."""

import pytest

from swarm.cli import demo_config, main, process_worker
from swarm.worker_loop import Worker


@pytest.mark.parametrize("state", ["stopped", "needs_review"])
@pytest.mark.parametrize("entry", ["worker", "child"])
def test_failed_worker_exit_status(tmp_path, monkeypatch, state, entry):
    monkeypatch.setattr(Worker, "__init__", lambda self, *args, **kwargs: None)
    monkeypatch.setattr(Worker, "run", lambda self: {"state": state})
    if entry == "child":
        config = demo_config(tmp_path / "target", tmp_path / "state", 0, 1.0)
        with pytest.raises(SystemExit) as error:
            process_worker(config)
        assert error.value.code == 1
    else:
        assert main(["worker", "--target", str(tmp_path / "target"),
                     "--state", str(tmp_path / "state"), "--instance", "0",
                     "--scope", "module_0", "--max-cost-usd", "1", "--executor", "fixture"]) == 1
