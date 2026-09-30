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

The integrated execution entry is `uv tool run poetry run python -m orchestration.acceptance`. Check `--help` before running. Each fresh run makes one real model call through an installed, authenticated Codex CLI; the following are operator-run examples, not setup or automatic test commands. `--root` must be a new empty directory under the OS temporary directory, outside the checkout. Omitting it creates a fresh temporary root automatically.

```powershell
# One normal model run.
$normalRoot = Join-Path $env:TEMP ("morph-normal-" + [guid]::NewGuid().ToString("N"))
uv tool run poetry run python -m orchestration.acceptance --root $normalRoot --model gpt-5.6-luna --timeout 180

# A separate model run pauses after execution, then the same root resumes review.
$resumeRoot = Join-Path $env:TEMP ("morph-resume-" + [guid]::NewGuid().ToString("N"))
uv tool run poetry run python -m orchestration.acceptance --root $resumeRoot --model gpt-5.6-luna --pause-after-execute --timeout 180
uv tool run poetry run python -m orchestration.acceptance --root $resumeRoot --continue

# A further model run consumes the prior successful live run's experience and feedback.
$reuseRoot = Join-Path $env:TEMP ("morph-reuse-" + [guid]::NewGuid().ToString("N"))
uv tool run poetry run python -m orchestration.acceptance --root $reuseRoot --model gpt-5.6-luna --experience $normalRoot --timeout 180
```

`--continue` reopens the existing configuration/checkpoint and resumes remaining graph nodes; it does not authorize replay of an uncertain external action. `--experience` requires a previous independently verified live run, reads its proposal and reviewed events, and drives both experience injection and the declared prior-feedback routing experiment. This version has **no `--routing-from` option**. `--max-tokens` and `--max-cost-usd` configure limits, but the public CLI cannot enforce a hard token/dollar ceiling during a model call: tokens are checked after completion, cost stays unknown, and no automatic additional model consumption follows. Local outputs include result/events/genes/adoption JSON, SQLite state and independent review evidence under the chosen root. See [T2 evidence and limits](docs/tracks/t2.md); no additional model calls were made for this README/help check.
# 科研环境 MCP（2026-09-30）

独立入口：`python -m swarm.research --config ABS_TRUSTED_JSON`。宿主绑定原生 Agent 身份、scope 和 capabilities，Agent 自主发现并认领科研任务；运行不依赖 Orca。账本、租约和候选/验证/应用/adoption 复用现有实现。

启动配置、工具顺序与权限边界见 [科研 MCP 契约](docs/research/MCP_CONTRACT.md)。实验后端复用 `orchestration.experiments` 的官方 OpenSandbox SDK 与可信原始证据读取器；其接口由 C 轨交付，最终集成分支合入后使用。配置 `experiment_backend` 才加载该后端，未配置时发现与账本工具仍可独立启动。

科研经验必须同时通过静态文件安全检查、预注册实验判据和不同 worker/run/干净 sandbox 的真实复现，后续任务再验证条件并实际应用后才记录 adoption。mock/replay 保持科研 quarantine；exit0、检索和注入不算科学通过或采用。独立三态及本轨真实限制见 [B 轨报告](docs/tracks/research-space-0930.md)，当前 native 科研 task_live 等最终 I 验收。
