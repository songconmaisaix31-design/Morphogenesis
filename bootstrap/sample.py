from importlib.resources import files
from pathlib import Path


def prepare_workspace(workspace: str | Path) -> Path:
    """Materialize only the input exercise; never overwrite prior execution."""
    target = Path(workspace).resolve()
    if target.exists() and any(target.iterdir()):
        raise FileExistsError(f"workspace is not empty: {target}")
    target.mkdir(parents=True, exist_ok=True)
    fixtures = files("bootstrap").joinpath("fixtures")
    for name in ("sample.py", "TASK.md"):
        target.joinpath(name).write_text(
            fixtures.joinpath(f"{name}.txt").read_text(encoding="utf-8"), encoding="utf-8"
        )
    return target
