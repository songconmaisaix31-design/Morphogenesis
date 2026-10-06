# readiness：本机 / 接口 / 账号三维健全度与可插拔接入

本轮范围：把"这个应用只能在本机跑"这一隐含前提拆掉。产品需要能回答三个互相独立的问题——**本机是什么**、**声明的接口是否可用**、**依赖的账号是否到位**——并且在**没有任何声明**时如实报告"未探测"，而不是沿用某台机器上被写死的状态。

## 一、为什么不是又一份"状态字段"

原实现的"本机状态"只存在于文档与部署脚本里（7527、7799、局域网地址等），属实例事实，不是产品能力。本轮新增 `readiness` 包，把这件事变成**共享契约 + 声明式接入**：

- 维度与状态词表在 `contracts/readiness.py`，与 `contracts/provenance.py` 的运行证据模型**完全分离**。readiness 不建立 `contract_local` / `interface_live` / `task_live` 任何一档。
- 探针集合默认**为空**：`ReadinessService(probes=())` 合法，三维全部 `not_run`。空集是要展示的状态，不是可以推断出结论的许可。
- 接入方式是**数据**（清单 JSON），不是改代码。任何机器、任何部署只要写自己的清单，不需要改本包。

## 二、契约

| 维度 | 语义 | 默认 |
|---|---|---|
| `machine` | 进程实际运行所在的宿主，运行时观测 | 内置探针，恒定可用 |
| `interface` | 一条**被声明**的接入面（公开 CLI 或 MCP 服务端）是否应答 | `not_run`，直到被声明 |
| `account` | 某条接入面所需的身份/凭据是否到位 | `not_run`，直到被声明 |

状态词表 `ProbeState`：`not_run`（未探测，无任何证据）/ `ok` / `degraded`（部分就绪）/ `blocked`（前置缺失：未安装、未配置）/ `failed`（探测失败）。

不变量（`ProbeResult` 校验，测试覆盖）：

- `not_run` 必须 `observed=false`；**任何其它状态都必须来自一次真实观测**。没有"默认通过"这条路。
- 子进程原始输出、凭据值、主机名、用户名、路径一律不进证据；证据值有长度上限。
- 聚合由 `dimension_states` + `overall_state` 纯函数决定，`EnvironmentReport` 的校验器会**重算** `dimensions` 与 `overall`，报告不可能与自己的证据不一致。
- 只有三个维度全部被覆盖且健康才是 `ok`；任何维度未覆盖或未执行，总体最高只能到 `degraded`。

## 三、三类接入路径

| 形态 | 适配器 | 说明 |
|---|---|---|
| 本机 | `LocalMachineProbe` | 唯一无需配置的探针：OS、Python、CPU、临时目录可写。不含主机名/用户名/路径 |
| 公开 CLI | `PublicCliProbe` | 只执行清单里**逐字声明**的 argv，`shell=False`，一次性调用，超时即失败 |
| Agent 友好 MCP | `AgentMcpProbe` | 直接实现已发布的 stdio 传输：`initialize` + `notifications/initialized` + 一次 `tools/list`。**不调用任何工具**，可声明 `require_tools` 校验必需工具集 |
| 账号 | `CredentialProbe` | 只报告声明的环境变量是否存在，报告布尔与缺失名，**从不读取或回显其值** |
| Wayfinder | 经上两者的清单接入 | Wayfinder 类平台按其已发布的 CLI（如 `wf`）与 MCP 入口接入。**本包不臆造任何子命令**，argv 必须由运营者按目标工具的发布契约填写 |

`env_mode` 决定子进程姿态：`isolated`（默认，复用 `bridge_node.environment.child_environment`，HOME/TEMP 重定向、环境变量清空、cwd 为一次性工作目录）或 `inherit`（以运营者身份运行，只有需要读取"我是否已登录"的账号探针才该用它）。

## 四、接入清单（参考清单可直接打印）

```bash
python -m readiness --example-manifest   # 或 morphogenesis readiness --example-manifest
```

```json
{
  "schema": "morph.readiness.manifest/1",
  "probes": [
    {"kind": "cli", "probe_id": "interface:wayfinder-cli", "subject": "interface",
     "command": "wf", "args": ["--version"], "report_version_line": true},
    {"kind": "mcp", "probe_id": "interface:wayfinder-mcp", "subject": "interface",
     "command": "wayfinder", "args": ["mcp", "knowledge"], "require_tools": [], "timeout_seconds": 20},
    {"kind": "cli", "probe_id": "account:wayfinder", "subject": "account",
     "command": "wf", "args": ["login", "status"], "nonzero_state": "blocked", "env_mode": "inherit"},
    {"kind": "credential", "probe_id": "account:evomap", "subject": "account", "names": ["EVOMAP_API_KEY"]}
  ]
}
```

清单严格校验并且**失败关闭**：未知 `kind`、未知字段、错误 schema、重复 `probe_id`、非法 `timeout_seconds`/`subject`/`env_mode`、非法数值环境变量，全部拒绝，未通过校验时**一个探针都不执行**。

环境变量：`MORPH_READINESS_MANIFEST`（清单路径）、`MORPH_READINESS_LOCAL`（默认 `1`）、`MORPH_READINESS_DISABLE`（逗号分隔，剔除探针）、`MORPH_READINESS_CACHE_SECONDS`（默认 60）、`MORPH_READINESS_BUDGET_SECONDS`（默认 45，超预算的探针保持 `not_run`）。已同步进 `.env.example`。

## 五、产品面

- **只读 HTTP**：`GET|HEAD /api/readiness`，由 `viz/server.py` 提供，返回 `morph.readiness/1`。非 GET/HEAD 405、请求体 413、无查询串日志，与其他只读端点一致。报告有 TTL 缓存与总预算，公共边缘代理另加 `2r/m` 限流（比 EvoMap 更紧，因为该端点可能启动子进程）。
- **CLI**：`python -m readiness`（等价 `morphogenesis readiness`）。`--fail-on` 默认 `failed,blocked` 时返回退出码 1，`not_run`/`degraded` 默认不算失败。
- **前端**：本轮**未**改动 React 面板，`/api/readiness` 已有契约与端点，面板展示属后续工作。

## 六、本轮实际验证

在本机 `.venv`（Python 3.12.13）执行：

- `pytest -q tests/readiness` → **70 passed**（32s）。
- 全量 `pytest -q` → **361 passed, 2 failed, 1 error, 790s**。三项问题与 readiness 无关，且已在**干净 HEAD 工作树**上原样复现：`t1/bridge/test_assets.py` 与 `t1/bridge/test_mcp.py` 为 Node 子进程 `sdk_timeout` / `mcp_timeout`，`integration/test_demo_environment.py` 为 `pwsh` 30s 超时；本机进程启动被环境拖慢，属既有环境问题，本轮不带入任何修复。
- `mypy --strict contracts readiness viz bootstrap tools bridge_node` → 38 files，no issues。
- `uv tool run poetry build` → sdist + wheel 成功；wheel 内含 `readiness/`（10 个模块）与 `contracts/readiness.py`。
- `python -I tools/check_distribution.py --site-dir .runtime/wheel-site` → `packages_from_wheel: 12`、资源齐全、安装态验证器拒绝坏样例。
- `python -m readiness` → `overall=degraded machine=ok interface=not_run account=not_run`（本机探针真实观测，接口/账号未声明）。
- `python -m readiness --no-local` → `overall=not_run`，`results=[]`，附"未声明任何探针"说明。
- 桩 MCP 服务端实测三条路径：握手成功 `ok`（server/version/工具数）、缺必需工具 `degraded`、不读 stdin 的慢服务端 `timeout → failed`。
- 隔离环境实测：ambient 变量在 `isolated` 下对子进程不可见，在 `inherit` 下可见（退出码 3 → `blocked`）。

未执行：`npm run check:sdk`、双平台 CI。

## 七、边界与未执行项

- **真实 Wayfinder 未接入**：本机没有可核验的 Wayfinder 账号与实例，参考清单中的 `wf`/`wayfinder` 命令只是**形态示例**，未执行、未声称通过。接入需要运营者提供实际 argv 与凭据。
- **公网部署未更新**：`deploy/Dockerfile`、`Dockerfile.dockerignore`、`nginx.conf`、`proxy.conf`、`smoke.py`、`package.py` 已同步到新包与第四只读端点，但未重建镜像、未发布、未对公网跑冒烟；`deploy/smoke.py` 的新增断言只在本地 Python viewer 上可验。
- **未执行**：`npm run check:sdk`（GEP SDK 契约探针）与双平台 CI。本机 `python -m build` 不可用（.venv 无 `poetry-core`，隔离构建环境无法联网），已改用 `uv tool run poetry build` 完成等价的 sdist/wheel 构建；新增包已同步加入 `pyproject.toml` `packages`、`tools/typecheck.py`、`tools/check_distribution.py`、`deploy/package.py`、`deploy/Dockerfile` 与 `deploy/Dockerfile.dockerignore`，CI 应同时验证。
- **readiness 与运行验收的关系**：四类证据不得互相替代。`interface` 健康不等于 `interface_live`，`account` 到位不等于任何一次任务成功。
- **仓库认知索引**：本轮新增包与文件改变了受 AOCI 管理的对象，但本会话内没有可用的 AOCI 工具，因此 `aoci.code.txt` / `aoci.meta.txt` 未做维护，索引处于待更新状态。
