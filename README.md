<div align="center">

# Morphogenesis

A fixed-size agent swarm where coordination and memory live in the environment — not in a central scheduler.

一个固定规模的多智能体蜂群：协调与记忆都交给环境，而不是交给中心调度器。

[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12%20%7C%203.13-blue.svg)](pyproject.toml)
[![Node](https://img.shields.io/badge/node-22.13%2B-green.svg)](package.json)
[![CI](https://github.com/songconmaisaix31-design/Morphogenesis/actions/workflows/check.yml/badge.svg)](https://github.com/songconmaisaix31-design/Morphogenesis/actions/workflows/check.yml)

<img src="docs/assets/img-20260923-193734.png" width="880" alt="Morphogenesis poster artwork" />

<sub>Poster artwork from `docs/assets/` — it is artwork, not a screenshot of the running system.<br/>`docs/assets/` 里的海报原图——它是美术作品，不是运行中的系统截图。</sub>

</div>

> **How to read this page / 怎么读这页**
> English first, then the same content in Chinese — not a summary, not a separate half. Parameters quoted here (τ, TTL, exploration rate) are the defaults in the source file named next to them.
> 每段英文在前、同一内容的中文紧跟在后；不是摘要，也没有单独的“中文版”。文中引用的参数（τ、TTL、探索率）都是对应源文件里的默认值。

---

## At a glance · 一眼看懂

| | |
|---|---|
| **Problem<br/>问题** | Two structural defects. A central scheduler is a single point of failure that every coordination message must pass through; and each agent's experience dies with its context window, so a bigger swarm is not a more capable one.<br/>两个结构性缺陷：中心调度器是单点故障，而且所有协调流量都过它；每个 Agent 的经验随上下文窗口消失，所以蜂群变大并不等于能力变强。 |
| **Fix<br/>做法** | Put both in the environment. A decaying pheromone field over SQLite holds preferences, a durable task ledger holds facts, leases arbitrate write authority, and budgets are reserved before work starts.<br/>把两者都交给环境：SQLite 上的可衰减信息素场保存偏好，持久任务账本保存事实，租约裁决写权，预算先预留再生效。 |
| **Cost<br/>代价** | Python 3.12–3.13 with Poetry and uv; Node 22.13+ only for the SDK check and the dashboard assets. No server to operate, no GPU.<br/>Python 3.12–3.13，配 Poetry 与 uv；Node 22.13+ 只用于 SDK 校验和 dashboard 静态资源。没有要运维的服务，不需要 GPU。 |
| **Not<br/>不是** | Not cross-machine decentralization. It is same-host, multi-process, trusted workers, one shared local persistence root.<br/>不是跨机器去中心化。它是同机多进程、可信 Worker、共享一份本地持久化。 |

## The idea · 思路

The name comes from Turing's 1952 paper on the chemical basis of morphogenesis: a symmetric, uniform state breaks into a stable structure under local reaction–diffusion rules, with no global designer. The biological prototype is *Physarum polycephalum* — a single cell that solves shortest-path and network-design problems by shaping its own tubes. The mechanism has a name: **stigmergy** — termites build without a blueprint, each one reacting only to traces left by others.

名字来自图灵 1952 年关于形态发生化学基础的论文：对称均匀的状态在局部反应—扩散规则下会自发破缺出稳定结构，不需要总设计师。生物学原型是绒泡菌——一个没有大脑的细胞，靠塑造自己的管道解出最短路径与网络规划问题。这个机制有名字：**共识主动性（stigmergy）**——白蚁筑巢没有图纸，每只只对其他白蚁留下的痕迹作反应。

That is the whole design rule here: no member has a global view, but the group remembers every member's successes and failures.

这就是这里唯一的设计规则：没有成员拥有全局视野，但群体记住了所有成员的成败。

| Noun · 名词 | Path · 路径 | Rule · 规则 |
|---|---|---|
| **Field<br/>场** | `swarm/pheromone.py`, `metabolism/decay.py` | Preferences decay on read, `w(t) = w0·e^(-Δt/τ)`, default `τ = 86400 s`. Nothing is written back just to age it.<br/>偏好读时衰减，`w(t) = w0·e^(-Δt/τ)`，默认 `τ = 86400 s`。不会为了“变老”而回写。 |
| **Ledger<br/>账本** | `swarm/task_ledger.py` | Task identity, state, dependencies and attempt counts are durable facts and never decay. Only routing preferences do.<br/>任务身份、状态、依赖与尝试次数是永久事实，不衰减；只有路由偏好衰减。 |
| **Router<br/>路由** | `swarm/router.py` | Softmax sampling over weights instead of a greedy argmax, with `exploration=0.05` and `beta=1.0` defaults. Each draw records its weights and probabilities.<br/>按权重做 softmax 抽样，而不是贪心取最大；默认 `exploration=0.05`、`beta=1.0`。每次抽样都记录权重与概率。 |
| **Lease<br/>租约** | `swarm/lease.py` | Write authority is a task-scoped TTL lease in SQLite (`ttl_seconds=30` default), with renew, release and handoff. It is not a file lock.<br/>写权是 SQLite 里按任务作用域的 TTL 租约（默认 `ttl_seconds=30`），支持续期、释放与移交。它不是文件锁。 |
| **Budget<br/>预算** | `swarm/budget.py`, `swarm/breaker.py` | Reserve → execute → settle. Unknown cost trips the breaker instead of being guessed as zero.<br/>先预留、再执行、最后结算。开销未知时触发熔断，而不是当成 0 猜过去。 |

The practical test of whether any of this is real: `prepare` then `verify` runs a fixed exercise with no model call, and the verifier is independent of the generator.

要验证这些是不是真的，最小一步是：`prepare` 之后跑 `verify`——固定练习、不调用模型，而且验证器独立于生成方。

## Two generations · 两代架构

Generation one is centralized orchestration: topology growth, experience metabolism, weighted routing, continuation/review and visualisation. It proved the biology-inspired mechanisms work but kept the dispatcher, so the single point of failure stayed. It still lives in `orchestration/`, `topology/` and `metabolism/`.

第一代是中心化编排：拓扑生长、经验代谢、权重选路、接续与复核、可视化。它验证了生物学机制本身成立，但保留了调度器，单点故障因此还在。代码仍在 `orchestration/`、`topology/`、`metabolism/` 里。

Generation two is the decentralized swarm in `swarm/`: a task ledger, a pheromone field, a router, leases, an autonomous worker loop, a budget ledger with a four-state breaker, an observer, and an optional Hub mirror. No dispatcher process sits in the middle.

第二代是 `swarm/` 里的去中心化蜂群：任务账本、信息素场、路由、租约、Worker 自主循环、预算账本与四态熔断器、观察者，以及可选的 Hub 镜像。中间不再有派发进程。

## Capabilities · 能力清单

| Kind · 类型 | Points at · 指向 | Verify · 验证 |
|---|---|---|
| Unified CLI<br/>统一入口 | `bootstrap/cli.py` — `check`, `prepare`, `verify`, `acceptance`, `rehearsal`, `readiness`, `serve`, `swarm`<br/>`bootstrap/cli.py`：`check`、`prepare`、`verify`、`acceptance`、`rehearsal`、`readiness`、`serve`、`swarm` | `morphogenesis <subcommand> --help` |
| Swarm core<br/>蜂群内核 | `swarm/` — 20 modules plus the `research/` and `observatory/` packages<br/>`swarm/`：20 个模块，外加 `research/` 与 `observatory/` 两个子包 | `python -m pytest tests -q` |
| Read-only dashboard<br/>只读看板 | `viz/` — local dashboard served by `python -m viz.server`<br/>`viz/`：由 `python -m viz.server` 提供的本地看板 | `morphogenesis serve` |
| Readiness snapshot<br/>健全度快照 | `readiness/` — host / interface / account dimensions<br/>`readiness/`：本机 / 接口 / 账号三个维度 | `morphogenesis readiness` |
| Research observatory<br/>科研观测台 | `src/env-observatory/` — FastAPI read-only observatory over a swarm state directory<br/>`src/env-observatory/`：对蜂群状态目录做只读投影的 FastAPI 观测台 | `python src/env-observatory/server.py --port <port>` |
| Deployment<br/>部署 | `deploy/` — Dockerfile, compose files, release packaging and a smoke check<br/>`deploy/`：Dockerfile、compose 文件、发布打包与冒烟检查 | `python deploy/package.py <commit> <out.tar.gz>` |
| Fixed rehearsal<br/>固定彩排 | `demo/run-demo.ps1` — `-AuthorizeLive`, `-Replay`, `-Mock` modes<br/>`demo/run-demo.ps1`：`-AuthorizeLive`、`-Replay`、`-Mock` 三种模式 | `.\demo\run-demo.ps1 -Mock` |

## Quickstart · 快速开始

### Requirements · 环境要求

Python 3.12–3.13 (`>=3.12,<3.14` in `pyproject.toml`), Poetry 2.x, uv, and Node 22.13+ for the SDK check and dashboard assets.

Python 3.12–3.13（`pyproject.toml` 里写的是 `>=3.12,<3.14`）、Poetry 2.x、uv，以及 Node 22.13+（用于 SDK 校验与看板静态资源）。

### 1. Install · 安装

Copied from `demo/README.md`; the same two commands appear in the CI workflow. Not re-run while writing this page.

命令抄自 `demo/README.md`，CI 工作流里也是这两条。写本页时没有重跑。

```powershell
$env:POETRY_VIRTUALENVS_IN_PROJECT = 'true'
uv tool run poetry install --no-interaction
npm ci --ignore-scripts
```

### 2. Run · 运行

```powershell
morphogenesis check                                  # pytest + strict mypy · 全量测试加严格 mypy
morphogenesis prepare --workspace .\tmp\exercise     # fixed exercise, no model call · 固定练习，不调用模型
morphogenesis verify  --workspace .\tmp\exercise     # independent verifier · 独立验证器复核
```

```powershell
morphogenesis swarm                                  # same entry as morphogenesis-swarm · 与 morphogenesis-swarm 同一入口
```

`morphogenesis` is the console script from `pyproject.toml` and is equivalent to `python -m bootstrap`. Forwarded subcommands pass their remaining arguments verbatim, so `--help`, exit codes and signal handling match `python -m <module>`.

`morphogenesis` 是 `pyproject.toml` 里的 console script，等价于 `python -m bootstrap`。转发的子命令把剩余参数原样交给对应模块，因此 `--help`、退出码与信号处理都和 `python -m <module>` 一致。

### 3. Verify · 验证

```powershell
uv tool run poetry run python -m pytest -q
uv tool run poetry run python tools/typecheck.py
```

Those two commands are exactly what the CI job runs before the build and SDK steps.

CI 在构建和 SDK 步骤之前跑的就是这两条。

## Documentation · 文档

| Doc · 文档 | Read it when · 什么场景读 |
|---|---|
| [demo/README.md](demo/README.md) | You are running the fixed rehearsal and need the authorization rules.<br/>要跑固定彩排、需要授权规则时。 |
| [docs/SWARM_PLAN.md](docs/SWARM_PLAN.md) | You need the plan behind the decentralized generation.<br/>需要去中心化那一代的计划时。 |
| [docs/SWARM_CONTRACTS.md](docs/SWARM_CONTRACTS.md) | You are changing a swarm contract.<br/>要改蜂群契约时。 |
| [docs/SWARM_RUNTIME.md](docs/SWARM_RUNTIME.md) | You want to know how a swarm run is assembled at runtime.<br/>想知道一次蜂群运行在运行时是怎么装配的。 |
| [docs/SWARM_BENCHMARK.md](docs/SWARM_BENCHMARK.md) | You are comparing routing strategies.<br/>要比较路由策略时。 |
| [docs/SWARM_ASSETS.md](docs/SWARM_ASSETS.md) | You are working on local assets and the Hub mirror.<br/>要处理本地资产与 Hub 镜像时。 |
| [docs/SWARM_REVIEW.md](docs/SWARM_REVIEW.md) | You want the review record, including the failures.<br/>想看复核记录，包括失败的那些时。 |
| [docs/ACCEPTANCE.md](docs/ACCEPTANCE.md) | You need the acceptance gates and their current colour.<br/>需要验收门禁及其当前状态时。 |
| [docs/STATUS.md](docs/STATUS.md) | You are tracing branch history and archived merges.<br/>要追查分支历史与归档合并时。 |
| [docs/DECISIONS.md](docs/DECISIONS.md) | You are questioning a decision and want the original reason.<br/>要质疑某个决策、想看当初理由时。 |
| [deploy/README.md](deploy/README.md) | You are packaging or deploying the read-only page and API.<br/>要打包或部署只读页面与 API 时。 |
| [docs/FRONTEND_REFACTOR_PLAN.md](docs/FRONTEND_REFACTOR_PLAN.md) | You are touching the dashboard front end.<br/>要动看板前端时。 |
| [AGENTS.md](AGENTS.md) | You are an agent picking up work in this repo.<br/>你是要在这个仓库接活的 Agent 时。 |

## Repository layout · 仓库结构

```text
bootstrap/            unified CLI, fixed exercise generator and verifier
contracts/            pydantic contracts shared across modules
persistence/          SQLite persistence helpers
swarm/                decentralized swarm: ledger, pheromone, router, lease, worker loop, budget, breaker
swarm/research/       research track: case, experiment, policy, records
swarm/observatory/    read-only projection providers over swarm state
orchestration/        generation-one centralized loop (acceptance, rehearsal, native agents)
topology/             generation-one topology growth
metabolism/           exponential decay used by the pheromone field
readiness/            host / interface / account readiness snapshot
viz/                  read-only local dashboard (server + static assets)
local_assets/         asset registry and reuse records
hub_client/            optional Hub client
bridge_node/           Node bridge for asset exchange
orca_provision/        isolated worktree provisioning
src/env-observatory/   FastAPI read-only observatory (separate from the public mirror)
demo/                 fixed rehearsal script and dashboard launcher
deploy/               Dockerfile, compose, release packaging, smoke check
tests/                156 Python files, 140 of them named test_*.py
docs/                 plans, contracts, acceptance records and track notes
tools/                typecheck, SDK check and distribution check
```

The file counts above are from the tree at the commit this page was written on; they are counts, not coverage.

上面的文件数是从写这一页时的提交目录里数出来的——是文件数，不是覆盖率。

## Status · 状态

Version `0.2.1` (`pyproject.toml` and `package.json` agree). The pipeline that has actually been wired is the `foundation` workflow in `.github/workflows/check.yml`: an ubuntu + windows matrix on Python 3.13 and Node 24, running `pytest -q`, `tools/typecheck.py`, `python -m build`, `npm run check:sdk`, and a wheel-site distribution check.

版本 `0.2.1`（`pyproject.toml` 与 `package.json` 一致）。真正接上的是 `.github/workflows/check.yml` 里的 `foundation` 工作流：ubuntu 与 windows 两个矩阵，Python 3.13 与 Node 24，跑 `pytest -q`、`tools/typecheck.py`、`python -m build`、`npm run check:sdk`，以及一次 wheel 安装后的分发包校验。

What this page deliberately does **not** claim:

本页刻意**不**主张的内容：

- The previous README quoted test totals (294, then 491 / 490 across platforms) and a "three assets published to the EvoMap Hub" result. Neither was re-verified while writing this page, so neither is repeated here. To get a current number, run `pytest -q` and read the summary line.<br/>上一版 README 引用过测试总数（294，后来是跨平台 491 / 490）以及“三项资产已发布到 EvoMap Hub”。写本页时两者都没有重验，所以这里都不再重复。要当前数字，就跑 `pytest -q` 读汇总行。
- The clone used for this rewrite is shallow (`depth 1`) and sits on branch `codex/morphogenesis-mainline`, so nothing here rests on commit history or tags.<br/>本次改写用的克隆是浅克隆（`depth 1`），分支是 `codex/morphogenesis-mainline`，因此本页没有任何结论依赖提交历史或标签。

Known limits, stated rather than hidden:

边界写出来而不是藏起来：

- Decentralization here is **intra-host**. Workers are trusted, share one local persistence root, and there is no cross-machine coordination to configure.<br/>这里的去中心化是**同机内**的：Worker 可信、共享一份本地持久化，没有跨机器协调要配。
- The budget module is bounded by an upstream interface. It degrades through parameter bounds, timeouts and post-hoc audit rather than exact upstream accounting.<br/>预算模块受上游接口限制，靠参数约束、超时熔断与事后审计降级保障，而不是精确的上游核算。
- EvoMap is optional. Offline, the local swarm still runs; nothing here requires a Hub.<br/>EvoMap 是可选的。离线时本地蜂群照常运行，这里没有任何东西依赖 Hub。
- `acceptance` and `rehearsal` call real models and need explicit authorization. `-Mock` and `-Replay` are labelled as such in the UI and are not evidence.<br/>`acceptance` 与 `rehearsal` 会调用真实模型，需要显式授权。`-Mock` 与 `-Replay` 在页面上都有标注，不能当证据。
- The scientific lineage is deliberately partial: the Physarum continuum model is discretised for engineering, and the paper's convergence results are not claimed to carry over.<br/>学术谱系是有意标注得保守的：绒泡菌的连续动力系统做了工程离散化，不宣称原论文的收敛性结论可以直接沿用。

## License · 许可

Apache-2.0. See [LICENSE](LICENSE) and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md); the front end carries its own notices under `viz/static/licenses`.

Apache-2.0。见 [LICENSE](LICENSE) 与 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)；前端自带声明，位于 `viz/static/licenses`。
