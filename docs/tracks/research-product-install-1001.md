# A1001 独立 product 安装验收

2026-10-01，原 A Owner / 原 terminal / 原 worktree。结算范围为 **contract_local 独立安装**，不代签 interface_live、task_live 或科研完整 checker。本次只新增本报告，未修改 process、product、core、测试、锁或 checker。

## 固定输入与环境

- Product：`9dd4addf4a141a42040574fef3b614ca62b22a57`，仓库 `C:/Users/DW/orca/workspaces/Morphogenesis-Research/research-product-1001`。
- Core：`cbc4dede782eb79b9c007520d96d7958857da0af`（CBC）。
- A 报告分支：`songconmaisaix31-design/morph-research-agents-0930`；起点 `46a1282b148fd8e03e2df85cb80de90957d64921`，开始时 clean。报告提交的完整 SHA、push/remote/clean 结果见本 Dispatch 最终 Handoff，不把该 SHA 当作 product 代码候选。
- 全新私有 sibling state（下文 `$S`）：`C:/Users/DW/orca/workspaces/Morphogenesis/morph-research-agents-install-1001-state-ctxb9ec0f8a8fcd`。
- Python：`C:/Python313/python.exe` 创建 `$S/venv`，实际 **3.13.13**；非 editable wheel 安装。所有正式命令从 `$S` 运行，不从源目录 import。
- process-local `UV_CACHE_DIR=$S/cache/uv`、`PIP_CACHE_DIR=$S/cache/pip`、`npm_config_cache=$S/cache/npm`、`TEMP/TMP=$S/temp`、`PYTHONUTF8=1`、`OPENBLAS_NUM_THREADS/OMP_NUM_THREADS/MKL_NUM_THREADS=1`。没有修改全局配置、认证环境、HOME、provider/model 或设置用于解析依赖的 NODE_PATH。
- 没有复用 P 的 env、node_modules、测试产物或之后的 working tree。VCS core 安装使用自己新 cache；Node 依赖由正式 setup-assets 安装到本 venv site-packages。

先阅读 AGENTS、固定 SHA README、`docs/tracks/product-1001.md`、`uv.lock` 和安装/配置/权限/运行模块；随后以固定 SHA archive 冻结全部 product 输入。所有运行时验证只依赖已安装 distribution。

## 安装命令与结果

以下为实际命令参数。`$P` 是上面的 product 仓库，`$S` 是上面的私有 state；环境变量仅在各 spawned PowerShell 进程中设置。日志均在 `$S/logs`，没有覆盖首份日志。

```powershell
git -C $P -c core.autocrlf=false archive --format=tar --output=$S/archives/product-9dd4add.tar 9dd4addf4a141a42040574fef3b614ca62b22a57
tar -xf $S/archives/product-9dd4add.tar -C $S/product-source
# 以下 uv export/build 的 cwd 为 $S/product-source
uv export --frozen --no-dev --no-emit-project --no-hashes --output-file $S/runtime-requirements.txt
uv venv $S/venv --python C:/Python313/python.exe
uv build --wheel --out-dir $S/dist
uv pip install --python $S/venv/Scripts/python.exe -r $S/runtime-requirements.txt $S/dist/morphogenesis_research-0.1.0-py3-none-any.whl
# 以下命令的 cwd 为 $S
& $S/venv/Scripts/morph-research.exe version
& $S/venv/Scripts/morph-research.exe setup-assets
& $S/venv/Scripts/morph-research.exe doctor
& $S/venv/Scripts/python.exe -I $S/verify_install.py
```

| 操作 | 实际结果 | 首份/最终日志 |
| --- | --- | --- |
| 冻结 export | exit 0，未改 uv.lock | `01-export.log` |
| 新 venv | exit 0，Python 3.13.13 | `02-venv.log` |
| wheel build | exit 0，product 0.1.0 wheel | `03-build.log` |
| frozen runtime install | 首次 exit 0，88 distributions | `04-install-first.log` |
| 正式 version | exit 0，实际 core CBC | `05-version.log` |
| 正式 setup-assets | 首次 exit 0，SDK ready_local | `06-setup-assets-first.log` |
| 正式 doctor | 首次 exit 0，asset_schema 1.14.0 / local_only | `07-doctor-first.log` |
| 独立 inventory/bridge 观察 | 观察脚本首轮失败保留；平台语义校正后 exit 0 | `08-install-verification-platform-aware.log` / `08-install-verification.json` |

首次安装没有 HTTP403、Git transport timeout 或依赖构建失败；未更换 index、依赖版本或认证方式。

`08-install-verification.json` 验证实际已安装 **88** 个 distributions 的集合和版本全部等于当前平台冻结 requirements/uv.lock；没有 dev 依赖混入。实际 `morphogenesis` 的 `direct_url.json`：

```json
{
  "url": "https://github.com/songconmaisaix31-design/Morphogenesis.git",
  "vcs_info": {
    "vcs": "git",
    "commit_id": "cbc4dede782eb79b9c007520d96d7958857da0af",
    "requested_revision": "cbc4dede782eb79b9c007520d96d7958857da0af"
  }
}
```

Product 的实际 `direct_url.json` 指向 `$S/dist/morphogenesis_research-0.1.0-py3-none-any.whl`，具有 `archive_info`，不是 editable。Core/product/bridge 模块和全部 distributions 的 location 均为 `$S/venv/Lib/site-packages`。

`python -I $S/verify_provenance.py` 首次 exit 0（`17-source-provenance-first.log` / `17-source-provenance.json`）：13 个 product 模块/Node manifest 在 archive、wheel 和实际 site-packages 的 bytes 均等于 **Git9dd 固定 blob**；README、pyproject、uv.lock、product 报告的 archive bytes 也等于固定 blob。已安装原 `experiment.py` / `NumAcc4.dat` bytes 等于 **CBC 固定 blob**。此检查只用 `git show SHA:path`，未读取后来 working tree 作为事实源，没有执行科学代码。

## 原 Node 桥的实际本地验证

setup-assets 使用原正式 `npm ci --ignore-scripts --no-audit --no-fund`，在本 venv site-packages 内装依赖，安装 receipt 为 `$S/venv/Lib/site-packages/research-assets-install.json`。实际桥脚本为 `$S/venv/Lib/site-packages/bridge_node/asset_bridge.mjs`，未借源 node_modules。

| 依赖 | 实际版本 | CBC lock license |
| --- | --- | --- |
| @evomap/gep-sdk | 1.14.0 | Apache-2.0 |
| ajv | 8.20.0 | MIT |
| ajv-formats | 3.0.1 | MIT |
| fast-deep-equal | 3.1.3 | MIT |
| fast-uri | 3.1.8 | BSD-3-Clause |
| json-schema-traverse | 1.0.0 | MIT |
| require-from-string | 2.0.2 | MIT |

7 个 product Node lock 条目完整对象均等于 CBC `package-lock.json` 对应条目，包含原 version、resolved、integrity、license；实际 node_modules/package.json version 也全部一致。完整 integrity 值在 `08-install-verification.json`，原 CBC lock 副本在 `$S/archives/core-package-lock.json`。

正式 doctor 实际调用原 `NodeAssetBridge.canonicalize` 和 `validate_asset`，不是 mock。额外独立观察记录两次真实 Node Popen：canonical 得到 `{"offline":"independent installed SDK smoke"}`；`{"type":"Gene"}` 得到 valid/schema_valid/asset_id_valid 全 false、schema_version 1.14.0。两次子进程都使用已安装桥脚本，原 bridge child_environment 将 NODE_PATH 显式清空，未使用非空 NODE_PATH。这里只验证现有 SDK 的本地依赖行为，没有 EvoMap 协议、Hub 或模型请求。

固定 product 来源依据：`src/morph_research/install.py:19` 安装边界、`:50` 实际 doctor、`:63` setup-assets；`src/morph_research/config.py:73` 实际 VCS commit 校验。相应 archive 和安装模块 bytes 已核对。

## 独立离线案例与正式入口

全新名字 **offline-install-a1001-01**，project/state/profile 均在 `$S`，与 I 将来的正式科研案例完全分开。case_directory 使用已安装 `$S/venv/Lib/site-packages/demo/research_case`，仍是原 core NIST NumAcc4 seed；未抽离科学模板。

Profile 只有 README 支持的字段：project/state/case_directory、同名 swarm_id、`sandbox_domain=127.0.0.1:9`、不存在的 `$S/offline-dummy-nonexistent.key`、变量名 `MORPH_RESEARCH_OFFLINE_DUMMY_KEY`、`codex_auth=inherited-selected` / `claude_auth=inherited-gateway`。这两项只是 **dummy 离线声明**，不证明已有 gateway 认证。主控消息 `msg_0d9d06af3766` 明确接受该离线声明，不修改后续正式 OAuth profile。未创建/读取真实 key 或复制令牌。

```powershell
& $S/venv/Scripts/morph-research.exe init --profile $S/offline-install-a1001-01-profile.json
& $S/venv/Scripts/morph-research.exe inspect --state $S/offline-install-a1001-01-state --phase interrupt
& $S/venv/Scripts/morph-research.exe inspect --state $S/offline-install-a1001-01-state --phase replication
& $S/venv/Scripts/morph-research.exe observe --state $S/offline-install-a1001-01-state
& $S/venv/Scripts/morph-research.exe run --state $S/offline-install-a1001-01-state --phase replication
& $S/venv/Scripts/python.exe -I $S/observe_installed_cli.py run --state $S/offline-install-a1001-01-state --phase replication
& $S/venv/Scripts/morph-research.exe observe --state $S/offline-install-a1001-01-state
& $S/venv/Scripts/python.exe -I $S/verify_offline.py
```

| 正式操作 | 实际结果 | 日志/归档 |
| --- | --- | --- |
| init | 首次 exit 0，prepared，models_or_experiments_run=false | `09-init-first.log` |
| author interrupt inspect | 首次 exit 0，Codex，probe=null，model_invoked=false | `10-inspect-author-first.log` / state `interrupt-inspection-launch.json` |
| peer replication inspect | 首次 exit 0，Claude，同上 | `11-inspect-peer-first.log` / state `replication-inspection-launch.json` |
| observe before | exit 0，只读原账本 | `12-observe-before-run.log` |
| 正式 run replication | **预期拒绝 exit 2**，`formal_role_dependency_not_completed` | `13-run-replication-first.log` |
| 同一已安装 console entrypoint 的调用观察 | 同样 exit 2；未 mock 被验 guard | `14-run-entrypoint-observed-first.log` / `14-run-entrypoint-call-counts.json` |
| observe after | exit 0，tasks/audit 与 before 完全一致 | `15-observe-after-run.log` |
| 独立配置/归档检查 | 观察脚本首轮 seed 预期错误保留，校正为原 seed 后 exit 0 | `16-offline-verification-after-seed-check.log` / `16-offline-verification.json` |

实际 inspection request/argv/HostBinding 已核对 CBC 原 `tests/integration/check_research_live.py` 的配置部分：作者 builder/0、peer reviewer/1 和继承 builder/2 绑定原 HostConfig、worker/swarm/workspace/配置路径；MCP command 使用本 venv Python，参数为原 `-m swarm.research --config ABS`，只构造计划，**未启动 MCP**。MCP 的 safe Python env 由正式入口设置，观察脚本没有补权限或关键 argv。

Codex request read-only，实际 argv 包含 never、default_permissions read-only、enabled11、default prompt、逐工具 approve、禁 shell/multi_agent/web 等原限制；Claude request dontAsk/exact11 allowedTools，actual argv strict MCP、`--tools ""`、禁 slash/hooks/chrome、只读 user settings。两者的 inspection budget 为 **895s/64 tools**，保留原 900s 的 5s margin；原账本 limits **3600s/每 task 最多3 attempts**，HostConfig 每 task ONE experiment。科学 plan/inputs/resources/criteria 没有重写。

Codex 0.159 原 catalogue 限制仍如实归档：exact11 是 permitted MCP calls，不声称全部可见工具总数为11；本轨没有模型越权或实际 live 工具隔离验收。

首次正式 console run 的拒绝保持原样。另用 CPython audit hook + call profiling **只观察** metadata 中的已安装 `morph-research = morph_research.cli:main`，传入相同 run 参数，没有函数 mock、环境认证修改、claim/approve/result/adoption 或 critical launch flag 补写。实际计数：

```json
{"require_phase_ready":1,"require_auth":0,"probe":0,"run_headless":0,"write_mcp_config":0,"sandbox_credential":0,"dummy_key_open":0,"subprocess.Popen":0,"socket.connect":0,"socket.bind":0,"os.system":0}
```

三任务仍 available、attempts/token=0、owner/result=null、effect_applied=false；原 audit 不变。没有 phase launch/native/probe/mcp/observation/ledger-audit 文件，experiments 目录为空。固定 product `src/morph_research/runner.py:122` 原依赖 guard 先于 `:123` auth 和 `:126` probe，`:168` 原拒绝语义确实执行；不是通过模拟外部执行来补绿。

## 首轮失败保留与范围限制

安装、正式 CLI、原 SDK 实际操作均首次成功；以下失败是**本轨新写的私有观察脚本错误**，不能删掉或当成产品 bug。所有当时脚本和失败日志均保留：

1. `08-install-verification-first.log` / `08-install-verification-first.py`：错误断言 NODE_PATH 必须不存在；原 CBC child_environment 明确 `NODE_PATH=""`。修正为验证非空注入为 false，未修改 bridge。
2. `08-install-verification-after-observer-correction.log` / `08-install-verification-second.py`：把 Windows Popen audit 的 argv 字符串按 POSIX list 处理。
3. `08-install-verification-final.log` / `08-install-verification-third.py`：Windows audit 的 executable 为 None，观察器错误调用 list2cmdline。按原 bridge 的实际 Node discovery 和 Windows audit 形状比对后通过；未更改原 Popen 或 argv。
4. `16-offline-verification-first.log` / `16-offline-verification-first.py`：误以为 inheritance 只依赖 replication；原 CBC seed 明确依赖 author+replication。校正观察预期以遵守原 seed，没有改原任务、依赖或任何已有断言/阈值。

所有校正只在自己的 sibling state 内；未调用任何模型、科研实验、MCP server、Docker/container、OpenSandbox API、Hub/EvoMap；没有运行 auth/version probe 或读取认证值。安装依赖时的 npm/PyPI/Git 访问不属于科研 live。

本轨未重跑 20 tests、pytest full、严格类型、构建门禁或任何 full/live checker；主控已明确不需要重复这些门禁，本轨补充的是独立 **runtime-only 88 deps** 安装证据。I 的原 core 全文门禁、product tests 和正式科研 case 不由本报告代签。

**本轨 NOT_RUN**：正式 OAuth/native request 兼容、真实模型/工具执行、三角色 full checker、科学输出/adoption、Hub/发布。inspection 仅 prepared；usage/cost/remote effect 没有本轨模型观测结果，保持未验证，不推断为零。正式科研 live 是否通过仍由 I 的真实档案和原 checker 判断。
