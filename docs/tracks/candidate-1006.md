# 候选交付版本：核心提交 + 产品版本（2026-10-06）

本文回答一个问题：**哪一个提交同时含有主线产品、观测台、readiness 与科研后继修改，
并且双平台检查都通过。** 答案是候选分支 `morph-candidate-1006` 的一个精确提交。

## 1. 为什么不是任何一条现有分支

两条分支自 `605cf48`（2026-09-24 验收基线）分叉，此后互不合并：

| 分支 | 末端 | 包含 | 不包含 |
|---|---|---|---|
| `codex/morphogenesis-mainline` | `31016f7` | `readiness/` 包与 `contracts/readiness.py`、统一 CLI `morphogenesis`、重写 README、AOCI-CODE 宿主集成、09-24 验收与 10-06 readiness 记录 | `swarm/`、`swarm/research/`、`src/env-observatory/`、`local_assets/` |
| `songconmaisaix31-design/morph-r1-research-1003` | `d23ff83`（本地）/ `6f44471`（远端） | 去中心化蜂群 `swarm/`、科研 `swarm/research/`、研究应用 `src/env-observatory/`、观测台 readiness `swarm/observatory/`、科研后继 `108935b`、FC/DSH 收口 | `readiness/` 包、统一 CLI 里除 `swarm` 外的主线子命令、主线 09-24 之后的产品提交 |

因此：

- **不能**因为一条分支叫 mainline 就假定它含全部成果——它连 `swarm/` 都没有；
- **也不能**直接用科研分支——它缺主线 `readiness` 包与 09-24 之后的产品提交，
  而且自 `108935b` 起双平台 CI 一直是 RED（`37137185631` 起每次 4 failed）。

## 2. 逐项核对：哪些属于同一个交付版本

| 来源项 | 是否属于本交付版本 | 依据 |
|---|---|---|
| 主线核心 `605cf48`（09-24 review/Sol 验收基线） | 是 | `git merge-base --is-ancestor` 已确认是候选提交的祖先 |
| 主线 `31016f7` 三维 readiness（包 + `/api/readiness` + CLI） | 是 | 产品面能力，已随合并进入候选树 |
| 最新观测台 `6f44471` + `d23ff83`（Agent 运行环境、看护、声明式 readiness） | 是 | 观测台是科研轨产品，源码在 `src/env-observatory/`，依赖 `swarm.research`，必须与其同版本交付 |
| 观测台 readiness `swarm/observatory/`（`d23ff83`） | 是，与主线 `readiness/` 并存 | 两者服务不同应用：前者服务观测台 ASGI 服务，后者服务 `viz/server.py` 与 `morphogenesis readiness`；模块路径不冲突 |
| 科研后继 `108935b`（L2 review 缺口：criteria/probes/execution_bound/operator auth） | 是（含一次必要的测试适配，见第 4 节） | 它加了 `live_mode_requires_verified_probes` 不变量，属于安全强化，保留；受影响的冻结安全测试按同一语义改写 |
| 科研后继 `acb26f4`（Docker 传输平台可用性） | 是 | 修的是官方 SDK 平台可用性导致的首轮 CI RED |
| `decentralized-swarm` 分支独有内容 | 不在本版本 | 其内容已经以提交形式并入科研分支（`86ade3d` 等），主线/科研两条线都不再需要单独合它 |
| 人工门禁项（真实 Wayfinder 接入、AT07 真实隔离、L2/L3、公网镜像重建与发布） | 否 | 未执行，见第 6 节限制 |

## 3. 核心提交与产品版本组合

| 项 | 值 |
|---|---|
| 候选分支 | `morph-candidate-1006` |
| 核心提交（SOURCE） | `2cf904214340680c158e3a3e5d8361340a30c4fd` |
| 提交构成 | 合并 `a958723`（两侧合流）→ `ef80619`（L2 不变量的测试适配）→ `4038c6d`（观测台 shell 修复）→ `2cf9042`（Windows 三进程屏障窗口） |
| 两个父提交 | `d23ff83`（科研/观测台）+ `31016f7`（主线/readiness） |
| 产品版本 | `morphogenesis 0.1.0`（`pyproject.toml` 未改版本号；CI 工作流里写死了 `dist/morphogenesis-0.1.0-py3-none-any.whl`，用 PEP 440 local version 会直接破坏 CI） |
| 产品标识 | 版本号 + 构建它的核心提交 SHA + wheel/sdist SHA-256（见第 5 节）。本机 wheel 在 `4038c6d` 上构建；`4038c6d → 2cf9042` 只改测试文件，打包进 wheel 的源码逐字未变，CI 在 `2cf9042` 上另行完成 build 与安装态检查 |
| 分发内容 | 根包 `contracts persistence bootstrap bridge_node hub_client orca_provision orchestration topology metabolism mocks readiness viz swarm local_assets` |

新增顶层包必须同步 7 处，本候选已全部同步：`pyproject.toml` packages、
`tools/typecheck.py` PACKAGES、`tools/check_distribution.py` PACKAGES、
`deploy/package.py` PYTHON_PACKAGES、`deploy/Dockerfile` COPY、
`deploy/Dockerfile.dockerignore`、只读路由（`deploy/nginx.conf` + `deploy/proxy.conf`
注释 + `deploy/smoke.py` 断言）。

## 4. 安全问题：修复了什么

### 4.1 观测台 Wayfinder 追问曾把用户输入拼进 shell（已修）

`src/env-observatory/server.py` 的 `POST /api/wayfinder/ask` 原实现：

```python
quoted = question.replace("\\", "\\\\").replace('"', '\\"')
command = 'pi -p "' + quoted + '"'
subprocess.run(command, shell=True, ...)
```

转义只处理反斜杠与双引号，没有处理 shell 元字符（Windows cmd.exe 的 `& | ^ %`
与换行，POSIX 的 `` $ ` ;``）。任何能访问该端点的调用者都可以追加第二条命令，
而该子进程的 **环境变量里带着 `DASHSCOPE_API_KEY`**（`_pi_env` + `_dashscope_key`）。

修复：问题作为**单个 argv 元素**以 `shell=False` 传入；`pi` 用 `shutil.which`
解析（Windows 走 PATHEXT，仍能找到 `pi.cmd`）；未安装时直接返回
`pi_not_installed`，不再起进程。新增两条测试锁定该行为（恶意串作为单元素到达、
未安装时不起进程）。

### 4.2 已核对但未发现问题的面

- 凭据入库：全树扫描 `sk-`、`AKIA`、`BEGIN ... PRIVATE KEY`、`api_key=`/`node_secret=`
  等样式，仅命中 gitignore 的 `.runtime/` 依赖缓存；`.env.example` 只有空键。
- 子进程：`readiness/`、`swarm/`、`orchestration/`、`local_assets/` 内无 `shell=True`；
  CLI/MCP 探针按声明 argv 执行（`shell=False`）。
- 只读端点：`viz/server.py` 与观测台均为 GET/HEAD（观测台仅 `/api/wayfinder/ask`
  为 POST）、拒绝请求体、带 nosniff / DENY / no-referrer；`deploy/nginx.conf`
  给 `/api/readiness`、`/api/swarm`、`/api/evomap` 各自独立限流。
- 静态文件：观测台 `/{name}` 走白名单 + `is_relative_to` 校验；`/api/research/replay/{task_id}`
  拒绝含 `/` 的标识。
- 凭据探针只读存在性，不读值（`readiness/credential.py`、观测台 credential provider）。

## 5. 验证（双平台 CI 为准，本机定向复核）

### 5.1 双平台 CI（`foundation` workflow，同一精确 SHA）

| 运行 | SHA | ubuntu-latest | windows-latest | 原始计数 |
|---|---|---|---|---|
| [37455855201](https://github.com/songconmaisaix31-design/Morphogenesis/actions/runs/37455855201) | `4038c6d` | **success** | failure | ubuntu 全绿；windows `1 failed, 1876 passed, 15 skipped`，失败项 `tests/swarm/test_worker_evomap.py::test_three_process_data_requests_and_exact_cross_member_adoption`（`BrokenBarrierError`，三进程退出码 `[1,1,1]`） |
| [37459928011](https://github.com/songconmaisaix31-design/Morphogenesis/actions/runs/37459928011) | `2cf9042` | **success**：`1876 passed, 16 skipped in 559.23s` | **success**：`1877 passed, 15 skipped in 1621.53s` | 屏障窗口 60s/180s → 300s/900s 之后重跑；两平台 `check_distribution` 均为 `packages_from_wheel: 14` |

CI 每一步都跑：`uv tool run poetry install` → `npm ci --ignore-scripts` → `pytest -q` →
`tools/typecheck.py` → `python -m build` → `npm run check:sdk` → wheel 装入隔离 site →
`tools/check_distribution.py --check-node`。

### 5.2 本机（Windows 11，`.venv` 3.12.13）定向复核

| 命令 | 结果 |
|---|---|
| `.venv/Scripts/python.exe tools/typecheck.py` | **156 源文件 / 0 errors** |
| `uv tool run poetry check --lock` | 通过（合并后 pyproject 与锁一致，仅有既有弃用告警） |
| `uv tool run poetry build` | wheel + sdist 成功；wheel 1023503 B，SHA-256 `c20b3e3bceab9e3f9079f630181f467749d8556a3da829d0a9ba3da7de04969c` |
| `uv pip install --no-deps --target <隔离 site> dist/morphogenesis-0.1.0-py3-none-any.whl` + `python -I tools/check_distribution.py --site-dir <隔离 site> --check-node` | **14 包**从 wheel 导入、资源齐备、安装态 verifier passed、Node 依赖 true |
| `npm run check:sdk` | 官方 1.14.0 schema/hash/防篡改通过，published=false |
| `pytest tests/readiness`、`tests/observatory`、`tests/integration/r1_security/test_a_docker_export_handoff.py` | 70 / 58 / 5 passed |

**本机不作为门禁**：本机全量跑到约 13% 时，`tests/integration/r1_security/test_a_dynamic_mcp.py`
的 MCP/Node 子进程用例不返回（单独跑 900s 仍未结束）；`tests/swarm` 的多进程用例在本机沙箱下
也成片失败（`spawn` 子进程写受保护路径/被沙箱拦截）。这与本机此前记录的"Node 子进程与 `pwsh`
spawn 超时"同源，CI 两平台均通过，故以 CI 为准，本机只作上述定向复核。

## 6. 真实限制（不翻绿）

- 真实 Wayfinder / 真实 MCP 接入未部署：任何 manifest 都还没上线，`interface`
  与 `account` 两维在默认部署下就是 `not_run`，这不是"可用"。
- 观测台新接入健全度卡片没有做浏览器实看；没有真实 Wayfinder/MCP 清单部署。
- AT07 真实隔离导出、L2/L3、公网镜像重建与发布、现场人工验收均未执行。
- AOCI 索引（`aoci.*.txt`、`.aoci/*`）在合并中**整侧取主线版本**，机器管理文件未被手改；
  合并后的 `swarm/`、`swarm/observatory/`、`readiness/` 等条目尚未纳入索引，
  需在具备 AOCI MCP 工具时用 `aoci_maintain` / `aoci_overview` 重新生成。
- 未知用量/费用保持 `null`；`not_run` 只表示未探测，不建立验收档位。
