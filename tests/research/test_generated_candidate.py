"""Seed a generated-candidate research task; no execution, model or sandbox."""

import sys
from pathlib import Path

from swarm.research.case import seed_generated_case
from tests.experiments.generated_helpers import make_poisson_plan


def test_seed_generated_case_never_executes(tmp_path):
    project = tmp_path / "project"
    state = tmp_path / "state"
    plan = make_poisson_plan()
    paths = seed_generated_case(project, state, python=Path(sys.executable), plan=plan,
                                swarm_id="swarm-gen-1")
    assert (project / "science" / "experiment.py").is_file()
    assert (state / "author-host.json").is_file()
    assert not (state / "experiments").exists()
    ledger_path = state / "tasks.sqlite3"
    assert ledger_path.is_file()
    # The plan is frozen in acceptance; the seeded task carries it without running.
    assert paths["base_revision"] == _head(project)


def _head(project: Path) -> str:
    from local_assets.paths import git
    return git(project, "rev-parse", "HEAD").decode().strip()
