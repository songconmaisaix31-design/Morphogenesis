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
