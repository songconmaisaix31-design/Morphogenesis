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

## 固定 c25 返修的独立安装验收（后续 Dispatch）

本节新增结果，前述 9dd 安装和观察器首失败保持原文、原文件。原 case01 配置失败、case02 真实工具入口失败及其 unknown/null、raw、UUID、clock、原 full checker RED 均未回写或重跑。本轮只验收 **installed prepared / contract_local**；进程成果、core、P 业务及 I state 全部只读。

### 固定来源和独立环境

- Product source：**`c25aa100ec6e10d8edc691f5c3154cebab365c86`**。
- Product report：**`c64e2b88696ef26453cc441903afa5a7e7536c20`**。实际 `git diff --name-only c25aa100... c64e2b...` 只有 `docs/tracks/product-1001.md`，不是另一业务候选。
- Core：**`cbc4dede782eb79b9c007520d96d7958857da0af`**（CBC）；Python/Node 锁 bytes 与 9dd、599 完全相同。
- 阅读固定 README/报告及主控 `morph-research-plan-1001/docs/RESEARCH_NEXT_ACCEPTANCE_1001.md`，然后从固定 Git archive 构建 wheel；未取后来 working tree 的模块或测试。
- 新私有 sibling state（本节 `$R`）：`C:/Users/DW/orca/workspaces/Morphogenesis/morph-research-agents-install-c25-1001-state-ctx22e488c4a387`。
- 全新 `$R/venv`，Python **3.13.13**，实际 wheel 非 editable、**`--link-mode copy`** 安装。只复用本 Owner 先前可信官方 UV cache：`C:/Users/DW/orca/workspaces/Morphogenesis/morph-research-agents-install-1001-state-ctxb9ec0f8a8fcd/cache/uv`；未复制任何 venv、其他 Owner env 或源 node_modules。
- process-local `TEMP/TMP=$R`，包含全部 basetemp/安装 state；BLAS/OMP/MKL=1、UTF8=1。没有更改全局 index/network、生产或父 terminal 的 HOME/身份/auth/provider/model。

### 实际命令与门禁

所有日志在 `$R/logs`；构建/export 的 cwd 为 `$R/product-source`，正式 CLI 和观察脚本的 cwd 为 `$R`。原测试从固定 archive 的 tests 运行，业务 import 为本 venv site-packages。

```powershell
git -C C:/Users/DW/orca/workspaces/Morphogenesis-Research/research-product-1001 -c core.autocrlf=false archive --format=tar --output=$R/archives/product-c25aa100.tar c25aa100ec6e10d8edc691f5c3154cebab365c86
tar -xf $R/archives/product-c25aa100.tar -C $R/product-source
uv export --frozen --no-emit-project --no-hashes --output-file $R/locked-test-requirements.txt
uv venv $R/venv --python C:/Python313/python.exe
uv build --wheel --out-dir $R/dist
uv pip install --link-mode copy --python $R/venv/Scripts/python.exe -r $R/locked-test-requirements.txt $R/dist/morphogenesis_research-0.1.0-py3-none-any.whl
& $R/venv/Scripts/morph-research.exe version
& $R/venv/Scripts/morph-research.exe setup-assets
& $R/venv/Scripts/morph-research.exe doctor
& $R/venv/Scripts/python.exe -I -m pytest -q -rA --basetemp=$R/pytest-original30-first --junitxml=$R/logs/08-pytest-original30-first.xml $R/product-source/tests
& $R/venv/Scripts/python.exe -I $R/verify_install.py
& $R/venv/Scripts/python.exe -I $R/verify_provenance.py
& $R/venv/Scripts/morph-research.exe init --profile $R/offline-install-a1001-c25-01-profile.json
& $R/venv/Scripts/morph-research.exe inspect --state $R/offline-install-a1001-c25-01-state --phase interrupt
& $R/venv/Scripts/morph-research.exe inspect --state $R/offline-install-a1001-c25-01-state --phase replication
& $R/venv/Scripts/morph-research.exe observe --state $R/offline-install-a1001-c25-01-state
& $R/venv/Scripts/python.exe -I $R/verify_prepared.py
```

| 本轮独立操作 | 首次实际结果 | 日志/记录 |
| --- | --- | --- |
| frozen export / fresh venv / build / copy install | 各 exit 0；**95** 个冻结 runtime+dev distributions | `01-export-first.log`、`02-venv-first.log`、`03-build-first.log`、`04-install-first.log` |
| 正式 version / setup-assets / doctor | 各 exit 0；CBC、ready_local、schema1.14.0 | `05-version-first.log`、`06-setup-assets-first.log`、`07-doctor-first.log` |
| 原 P24 + 6 最小回归 | **首次 exit 0 / 30 passed / 30.06s**，不改测试、fixture 或断言 | `08-pytest-original30-first.log` / `.xml` |
| installed inventory/原 SDK 实际检查 | exit 0，95 集合/版本全等 frozen lock，7 Node 锁一致 | `09-install-verification-first.log` / `08-install-verification.json` |
| immutable Git/archive/wheel/site byte 与 nlink | exit 0，13 产品文件 + 2 原 CBC 注册输入 | `10-source-provenance-first.log` / `10-source-provenance.json` |
| 正式 offline init / Codex inspect / Claude inspect / readonly observe | 各 exit 0，prepared；没有 native session | `11-init-first.log`、`12-inspect-codex-first.log`、`13-inspect-claude-first.log`、`14-observe-first.log` |
| 已生成正式 inspection 配置检查 | 首次 exit 0，probe=null/model_invoked=false/session=null | `15-prepared-inspection-first.log` / `15-prepared-inspection-verification.json` |

本轮安装没有 package 下载失败或续装，也没有改变 index/依赖来修复失败。历史安装/观察器/P/I 的首失败日志均保留；本轮预期旧 quoted-key/native invalid-transport RED 由原 parser 回归断言核验，不冒充生产 case01 已通过。

实际 core `direct_url.json` 的 `vcs_info.commit_id/requested_revision` 仍均为 CBC；product direct_url 指向本节自己的新 wheel，非 editable。实际 13 个 product 模块/Node manifests 的 Git c25 blob、archive、wheel、site-packages bytes 全等；两份已安装 `demo/research_case/experiment.py` / `NumAcc4.dat` bytes 全等 CBC Git blob。这 **15 份 installed 文件的 st_nlink 全为1**；没有借硬链接别人的安装树。另对固定 9dd/599 Git blob 核对 uv.lock 和两份 Node manifest bytes 完全一致。

7 Node lock 条目完整对象（version/resolved/integrity/license）仍等于 CBC lock；实际包版本与上文7行表相同。正式 setup-assets 在本环境 site-packages 安装后，实际 NodeAssetBridge canonicalization 和 invalid Gene schema/id rejection 均通过；独立观察的两次 Node Popen 使用已安装 `bridge_node/asset_bridge.mjs`，NODE_PATH 非空注入为 false，没有源 node_modules、SDK 算法或 EvoMap 协议替代。

### 返修语义、测试边界与未执行项

新 fixture 名字是 **offline-install-a1001-c25-01**，只是本地 init/inspection，profile 的两项 auth 均为 `pending`、key 文件不存在、变量名为 `MORPH_RESEARCH_OFFLINE_DUMMY_KEY`、domain 为 `127.0.0.1:9`。没有正式科研 case clock、真实模型 UUID 或 run 调用。只读 observe 的三 task 都 available/attempts0/owner/result null/effect_applied false；audit 没有 claim、execution_unconfirmed、research_execution，experiments/native/probe/MCP 配置/observation 文件未创建。

实际 Codex argv 由正式产品产生 `mcp_servers.morph_research.omit_tools_from=["deferred", "code_mode"]`，root inline TOML 禁用其他 server，无 dotted quoted phantom；memories=false、memory_tool alias 不在 argv，三个 code-mode flag、shell/agent 等原禁用项保持 false。required11/default prompt/逐工具 approve/read-only/never、原 HostBinding、venv MCP command、safe Python env、895s/64tools 和原 core limits 保持。Claude plan 仍 dontAsk/allowed11/strict MCP/空 tools/禁 hooks/slash/chrome，未修改身份、认证来源或模型。配置/测试通过只证明 installed prepared，不证明所选真实模型能调用 direct11 或完整 catalogue 仅11。

原 30 项测试包含真实现装 Codex **0.159.0** config parser 的旧 RED→新 PASS、literal 点/引号 server 与非法 transport 拒绝：仅测试子进程使用原 fixture 新建的无 secret/无 auth `CODEX_HOME`，只执行允许的 `--version` / `mcp get --json`。原 fixture 断言父环境不变、没有 auth.json 或 sessions；不是 auth probe、模型请求或 MCP server 启动，也没有给 production plan 补修复 flags。

新增6项按原 P 断言验证真实 raw envelope/原 guard、精确首启动 warning、重复/未知/near-miss/其它时序/顶层 error/turn.failed、合法11/stale 业务拒绝、原 outside trace，以及原 mock native 边界不伪造中断/成功和 unknown/null。原 24 项全部保留，mock 仍标 mock/not_run。获本次 TASK 批准的唯一真实离线 MCP 子进程回归只 initialize/list/discover/context 与越权 claim 拒绝；原测试确认 attempts0 且无 execution_unconfirmed，没有科研实验或 API。没有运行核心1104/full/CI、新算法、authprobe、模型、Docker、sandbox、Hub/EvoMap。

安装身份、第一份原30退出、SDK/双正式 inspection/只读 observe 和限制已薄 Handoff 给 root 与原 I `ctx_c6bb0ebb6ad6`；未重派/停止 I 或修改其 state。此后只追加本报告、commit/push，远端完整 SHA/clean 由最终本轨 Handoff 提供。

**本轮结论：独立固定 c25 安装和原30适用本地回归通过。** 真正 direct11 模型可达性、Claude OAuth/currentmodel 请求兼容、三角色完整科研 checker、科学结果及 adoption 均本轨 **NOT_RUN**；原 case01/02 RED、未知费用/用量/远端效果保持，不能由本地准备推断为零或正式 live 通过。

## 固定 4428 OAuth 准入返修的独立安装验收

本节为同 A Owner 的后续独立结果，原报告 `eabc4583f52963ee380a0857ba3ca934e348329e` 和全部历史日志保留。本轮仅追加本报告和全新自有 sibling state，不修改任何产品/core/process/测试/锁、其它文档或 I state。

### 固定来源、安装身份与原门禁

- Product SOURCE：**`4428fdadfb0a5dfe8adc9e04c7fd881784f2807e`**，原 `Morphogenesis-Research` 分支 `songconmaisaix31-design/research-product-1001`。
- P 后续 REPORT：**`d75bed7d4585797e47a5894ae7fd85f25f71bba6`**，通过原 P Handoff `msg_39f48b6896d4` 收到；本轨实际固定 Git diff 仅 `docs/tracks/product-1001.md`，并读取其固定 Case04 返修节。P 的首次 RED / 33-pass / fresh install 是作者历史证据，没有用来替代本轨独立运行。
- Core：**`cbc4dede782eb79b9c007520d96d7958857da0af`**（CBC）。本次源码中 permissions/guard、uv.lock、Node manifests 保持原固定版本；已与不可变 Git blob 核对。
- 本节私有根（下文 `$O`）：`C:/Users/DW/orca/workspaces/Morphogenesis/morph-research-agents-install-oauth-1001-state-ctx6b8aed6cdba5`。
- 新建 `$O/venv`，实际 CPython **3.13.13**，从本次 Git archive 构建 wheel 并 **copy-mode 非 editable** 安装，实际 **95** 个冻结 runtime+dev distributions。
- 只复用本 Owner 先前同锁官方 UV 下载 cache：`C:/Users/DW/orca/workspaces/Morphogenesis/morph-research-agents-install-1001-state-ctxb9ec0f8a8fcd/cache/uv`。未复制/激活旧 env、安装产物、node_modules 或测试输出；仅复用本 Owner 的观察器源码，新建所有本轮记录。CBC Node lock 从固定 Git blob重新读取。
- process-local `TEMP/TMP=$O`，所有 basetemp/state 在其下；UTF8=1、BLAS/OMP/MKL=1。没有改全局网络/index/HOME/account/provider/model、传实际 sandbox key、复制凭据或清理任何旧目录。

先阅读 AGENTS、固定产品 README/auth/runner/tests 和 root 的 `RESEARCH_NEXT_ACCEPTANCE_1001.md`，然后执行：

```powershell
git -C C:/Users/DW/orca/workspaces/Morphogenesis-Research/research-product-1001 -c core.autocrlf=false archive --format=tar --output=$O/archives/product-4428fdad.tar 4428fdadfb0a5dfe8adc9e04c7fd881784f2807e
tar -xf $O/archives/product-4428fdad.tar -C $O/product-source
# 以下 export/build 的 cwd 为 $O/product-source，UV_CACHE_DIR 为上述自有 cache
uv export --frozen --no-emit-project --no-hashes --output-file $O/locked-test-requirements.txt
uv venv $O/venv --python C:/Python313/python.exe
uv build --wheel --out-dir $O/dist
uv pip install --link-mode copy --python $O/venv/Scripts/python.exe -r $O/locked-test-requirements.txt $O/dist/morphogenesis_research-0.1.0-py3-none-any.whl
# 正式 CLI/观察器 cwd 为 $O；pytest 使用本次 archive 原 tests
& $O/venv/Scripts/morph-research.exe version
& $O/venv/Scripts/morph-research.exe setup-assets
& $O/venv/Scripts/morph-research.exe doctor
& $O/venv/Scripts/python.exe -I -m pytest -q -rA --basetemp=$O/pytest-original33-first --junitxml=$O/logs/08-pytest-original33-first.xml $O/product-source/tests
& $O/venv/Scripts/python.exe -I $O/verify_install.py
& $O/venv/Scripts/python.exe -I $O/verify_provenance.py
& $O/venv/Scripts/morph-research.exe init --profile $O/offline-install-a1001-oauth-01-profile.json
& $O/venv/Scripts/morph-research.exe inspect --state $O/offline-install-a1001-oauth-01-state --phase interrupt
& $O/venv/Scripts/morph-research.exe inspect --state $O/offline-install-a1001-oauth-01-state --phase replication
& $O/venv/Scripts/morph-research.exe observe --state $O/offline-install-a1001-oauth-01-state
& $O/venv/Scripts/python.exe -I $O/verify_prepared.py
& $O/venv/Scripts/morph-research.exe run --state $O/offline-install-a1001-oauth-01-state --phase replication
& $O/venv/Scripts/morph-research.exe observe --state $O/offline-install-a1001-oauth-01-state
```

| 本轨实际门禁 | 原退出/结果 | 本轮 `$O/logs` 原记录 |
| --- | --- | --- |
| frozen export / fresh venv / wheel build / copy install | 首次各 exit0；95 冻结分发包 | `01-export-first.log` 至 `04-install-first.log` |
| 正式 version / setup-assets / doctor | 首次各 exit0，CBC/ready_local/schema1.14.0 | `05-version-first.log` 至 `07-doctor-first.log` |
| **原30+3完整必要回归，仅跑一次** | **首次 exit0 / 33 passed / 25.60s**，没有删/弱化断言或改 fixture | `08-pytest-original33-first.log` / `.xml` |
| 实际安装 inventory/NodeBridge | 首次 exit0，95 集合及全部版本等于 frozen export/lock；7 个原 Node 锁一致 | `09-install-verification-first.log` / `08-install-verification.json` |
| 固定来源逐 bytes/nlink 核验 | 首次 exit0，实际仍13产品文件 + 2 CBC注册输入 | `10-source-provenance-first.log` / `10-source-provenance.json` |
| 正式 offline init / 双原生 runtime inspect / readonly observe | 首次各 exit0，prepared，auth pending，probe=null/model_invoked=false/session=null | `11-init-first.log` 至 `14-observe-first.log` |
| 真实已生成 inspection 的配置核对 | 首次 exit0，selection_only_not_auth_verified；原权限/身份/预算完整 | `15-prepared-inspection-first.log` / `15-prepared-inspection-verification.json` |
| pending profile 的正式 replication run | **预期 exit2**，`explicit_operator_auth_selection_required`，not_completed | `16-pending-replication-refusal-first.log` |
| 拒绝后正式 readonly observe | exit0，tasks/audit 与拒绝前完全一致 | `17-observe-after-refusal-first.log`；原 `14-observe-first.log` 对照 |

本轮没有安装或门禁失败后的重跑/续装。原 P false-positive 回归 RED（1 failed/30 deselected/17.85s）、case04真实认证失败及其它旧 RED 不删除、不回写；本轨首次33结果独立于 P 的33/19.55s。

### 实际 wheel/SDK/权限与认证边界

实际 core direct_url 的 Git commit/requested_revision 均为 CBC，product direct_url 指向 `$O/dist` 本次 wheel、非 editable。13 个产品文件的 **Git SOURCE / archive / wheel / site-packages bytes 全等**；本次 archive 原 `tests/test_product.py` bytes 也等于固定 SOURCE。CBC `experiment.py` 和 `NumAcc4.dat` 的 installed bytes 等于固定 Git blob；这15份 installed文件 **st_nlink全部为1**，注册输入在已安装 core 中、处于模型 workspace 外。未以 AST/CRLF 等价或源 import 替代实际安装证明。

uv.lock/两份 Node manifests 与原9dd/599固定 bytes一致，permissions/guard与c25固定 bytes一致；95已安装集合及版本全等当前平台冻结 lock。7个 Node 条目的完整 version/resolved/integrity/license 与CBC对应条目全等，实际包版本与上文7行表一致，完整元数据在本轮 inventory JSON。正式 setup-assets 只在本轮 site-packages 安装，NodeAssetBridge actual canonical 和 invalid Gene schema/id rejection成功；两次独立观察的 Node Popen只用本轮已安装 `bridge_node/asset_bridge.mjs`，没有非空 NODE_PATH、借旧 node_modules、SDK算法复制或新的EvoMap协议。

新离线 fixture 名字 **offline-install-a1001-oauth-01**，project/state/profile 全新、两runtime auth声明均 pending、sandbox key不存在、只有私有变量名和loopback dummy domain。正式init没有模型/实验，inspect由产品自己构造真实Codex/Claude请求、argv、HostBinding、venv MCP参数及安全env；原direct11/逐工具approve/defaultprompt/read-only/never、Claude dontAsk/strict/空tools/禁hook等均保持，895s/64tools及原core limits不变。观察脚本没有补任何关键参数、身份、授权、结果或adoption。没有创建正式科研clock或真实sessionUUID，没有实际 auth status/login。

pending profile的正式run在读取真实认证之前由原selection前置条件拒绝；**这个CLI结果不是 `formal_role_dependency_not_completed`，不冒称执行了更后的依赖guard**。原33中的 `test_role_dependency_refuses_model_start_until_actual_prior_phase_settles` 则按原测试使用无秘密selected声明fixture运行本轮installed原run，真实依赖拒绝先于普通probe/selected probe；两个边界分别保留，没有为让正式CLI产生另一错误修改其pending profile、手工claim/造completed账本或补flags。拒绝后无probe/selected-auth/MCP/native/launch/observation文件，三task仍available/attempts0/owner/result null/effect_applied false，audit完全一致。

新增3个认证回归在本轮installed业务上实际执行，但外部 status/probe 为无秘密 mock：ordinary true/selected false按真实正式settings/command/cwd/env匹配，先于key/MCP/native拒绝；父测试环境恢复，原unscoped证据与脱敏selected证据分列，任意identity/原stdout/stderr/secret sentinel不归档。API-key字段缺失与present null分开；oauth_token、helper/第三方、缺字段/非法JSON/timeout/IO及version/command/有效settings不匹配均fail closed。正面claude.ai/firstParty/no apiKeySource结果仅 **官方来源衍生的local fixture**，不证明当前账号有OAuth、服务器接受或模型可用。

原30项仍验证旧quoted-key真实parser RED→PASS、通知/错误窗口、合法11及真实越界停止、未知效果/中断不伪造等；真实Codex parser只在无auth的测试子进程CODEX_HOME执行允许的version/mcp-get，未登录或改生产HOME。原实际离线MCP测试只initialize/list/discover/context及越权claim拒绝，保持attempts0/无科研执行；不把它当作模型/科研实验。没有核心全量、CI、旧43family、外围健康测试或实际用户认证/模型/sandbox/Hub调用。

安装artifact、源码和实际33/25.60s退出已薄交root与原I，P摘要另行只读，未让其它Owner写本轨state。之后只做本报告commit/push，A REPORT完整SHA/remote exact/clean在最终Handoff中单列，不能把报告SHA当产品源码SHA。

**结论仅为4428固定wheel的独立installed prepared/contract_local通过。** 按root/D当时证据，真实正式OAuth未就绪，用户官方login尚无可用于本轨验收的回复，不能假定已经登录；本轨没有重新检测或代为login。真实正面OAuth/server/model请求和完整三角色科研checker均 **NOT_RUN**。case04作者实验passed/known/destroyed但源候选quarantine、Claude首次Notloggedin/tools0/unknown/null、原fullchecker缺inheritance RED及所有旧clock/raw不变，不能由本地成功fixture补绿；下一登录确认、同配置真实检查与科研case处置由root负责。
