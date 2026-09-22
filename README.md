# Morphogenesis

Independent prototype using Pydantic, SQLModel/SQLite and LangGraph. Packages live at the repository root. T0 provides business contracts, persistence and an independently checked three-bug Python exercise. The execution CLI and graph are owned by T2.

```powershell
$env:POETRY_VIRTUALENVS_IN_PROJECT = 'true'
uv tool run poetry install
npm ci --ignore-scripts
uv tool run poetry run python tools/contracts_check.py
uv tool run poetry run python tools/typecheck.py
uv tool run poetry run python -m build
npm run check:sdk
uv tool run poetry run python -m bootstrap prepare --workspace .runtime/sample
uv tool run poetry run python -m bootstrap verify --workspace .runtime/sample
```

The initial sample deliberately fails verification (exit 1). Only `sample.py` is writable by the task executor. The evaluator and its fixed cases remain outside that workspace; T2 must enforce the workspace boundary with the execution host sandbox. `verify` does not run an agent or repair the sample.

`contract_local`, `interface_live`, and `task_live` are independent. Local tests and SDK checks do not establish model task success or Hub acceptance. Missing sandbox Hub configuration means pending publication; no production publishing is enabled. Unknown usage is `null`, never an invented zero.

See [T0 API handoff](docs/tracks/t0.md), [plan](docs/PLAN.md), and [third-party notices](THIRD_PARTY_NOTICES.md).

The integrated Python wheel contains the root Python packages, fixed exercise, Node bridge script, visualization static files and demo resources. Build from an integrated checkout containing those packages. A wheel does **not** install Node.js, npm packages, the Codex CLI, or model credentials. The supported full setup retains this source checkout and runs `npm ci --ignore-scripts` here using the committed lock. Node resolves its dependencies from the bridge script's ancestor directories; installing the Python wheel in an unrelated directory does not make this checkout's `node_modules` visible to it.

To verify wheel contents separately, install the built wheel into a clean target with `uv pip install --no-deps --target tools/.wheel-site dist/morphogenesis-0.1.0-py3-none-any.whl`, then run `uv tool run poetry run python -I tools/check_distribution.py --site-dir tools/.wheel-site`. This uses the locked Python environment for third-party dependencies and asserts that every project module comes from the wheel target. Add `--check-node` only after the source checkout's `npm ci` has completed; it exercises the installed bridge script locally, without contacting Hub or a model.

`python tools/typecheck.py` checks every present root Python implementation with mypy strict. CI runs the complete checked-in pytest suite and this full implementation check. Runtime/demo commands are documented by their track owners; task_live remains unverified until those commands run successfully against the selected real execution host.
