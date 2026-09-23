# 封板夜 I：独立累计集成验收

2026-09-23，北京时间。工作区 `C:/Users/DW/orca/Morphogenesis`，唯一分支 `codex/morphogenesis-mainline`。本轮以验证和报告为主，没有新增分支、worktree、merge 或业务代码修改。

## 结论与精确版本

累计代码的本机全量测试、严格类型、构建、SDK、隔离 wheel 和 Node 分发检查全部通过。`4938bb9230cf3acaf2cff63774f743a8a20d5bad` 的 Windows / Ubuntu CI 两个平台及全部步骤均为 success。该结论是 I 软件累计验收，不将 G3/G4/G5 整体标为通过。

| 版本 | 本次确认 |
|---|---|
| 起始及全部本机软件 gate HEAD | `425d7e55b0cc8c3f2496a506b9f045fcb1b5fbfd`；起始及软件 gate 结束工作树 clean |
| 累计业务代码 | `4938bb9230cf3acaf2cff63774f743a8a20d5bad`，E 最终实现；与上述 HEAD 的差异仅为主控四份治理文档 |
| D / T 已包含报告 | `78dfdd9e39a513cd6c602dc78d4b3f3c76d2ee13` / `0d7191a43bbc783b2586baa33067269501c08562` |
| 实际公网部署代码 | `53bb52c31ab68655e2bca620508488d7f95e00e6`；不能冒称已重新部署最终 Hub 代码 |
| I 报告提交 | 仅本文件；完整 SHA 与远端核对由提交后终端回执记录，避免自引用 SHA；最终治理 HEAD 的 CI 由主控接管 |

主控消息 `msg_051ac3d6fcd8` 预授独占 Git slot：完成后仅显式暂存本报告，普通 commit/push，累计带上已提交的治理文档；主控不并发 push。没有触碰其他轨道代码、锁或治理文档。

## 本机命令、耗时与原始日志

证据根 `R=.runtime/freeze-integration/20260923-ctx3881`，解释器 `P=.venv/Scripts/python.exe`。每一行均有 `R/<名称>.json` 保存 argv、UTC 起止、墙钟耗时、退出码、开始/结束 SHA 和工作树，`R/<名称>.log` 保存完整 stdout/stderr。`run-gate.ps1` 仅为本次命令日志包装，不是产品代码。

所有 gate 仅在子进程设 `OPENBLAS_NUM_THREADS=1`、`OMP_NUM_THREADS=1`、`MKL_NUM_THREADS=1`、`PYTHONDONTWRITEBYTECODE=1`。`TEMP/TMP` 指向 R 下新建 temp；构建和安装另将 `PIP_CACHE_DIR/UV_CACHE_DIR` 指向 R 下绝对路径。未改全局环境或配置。

本机 Python **3.12.13**，Node **24.16.0**，npm **11.13.0**，uv **0.11.26**。CI Python 3.13 / Node 24 的结果另列，不能用本机环境替代。

| 日志名 | 项目根执行的精确命令（P/R 按上文展开） | 结果 | 墙钟秒 |
|---|---|---|---:|
| pytest | `P -B -m pytest -q -ra -p no:cacheprovider --basetemp R/temp/pytest --junitxml R/junit.xml` | exit 0，**294 passed / 0 failed / 0 errors / 0 skipped**；pytest 自报 88.52s | 89.888 |
| typecheck | `P -B tools/typecheck.py` | exit 0，**55 source files / 0 issues** | 0.717 |
| build | `P -B -m build --verbose` | exit 0，sdist + wheel 均成功 | 11.166 |
| sdk | `npm run check:sdk` | exit 0，SDK schema 1.14.0，schema/id/tampering 全通过，published=false | 0.464 |
| wheel-install | `uv pip install --python .venv/Scripts/python.exe --no-deps --target R/wheel-site dist/morphogenesis-0.1.0-py3-none-any.whl` | exit 0，仅安装本次 wheel 到全新隔离 target | 0.395 |
| distribution | `P -B -I tools/check_distribution.py --site-dir R/wheel-site --check-node` | exit 0，11 包均从 wheel 导入，资源、独立坏样本拒绝和 Node bridge 通过 | 1.816 |
| evidence-inspection | `P -B R/inspect-evidence.py` | exit 0，只读交叉复核原始回执、官方 SDK ID、JUnit、历史原件及 CI | 4.629 |
| evidence-extraction-corrected | 同上，只修正摘要输出文件名后重新只读提取 | exit 0，详细结果完整保存到 `R/evidence-details.json` | 1.216 |

项目 venv 初查缺 `poetry-core`，已先报告主控；消息 `msg_0cf514b08adb` 确认按现有 CI 的 `python -m build` 进行必要的临时隔离安装。实际 backend 为 **poetry-core 2.5.0**，使用环境既有包索引，完整版本日志保留；没有升级项目依赖、安装进 venv、修改任何锁或运行 npm install/ci。wheel 选择 I 自有忽略目录而非覆盖可能已有的 `tools/.wheel-site`，仍运行同一个分发检查器及 `--check-node`。Node 运行验证依赖当前锁定 `node_modules`，不能据此宣称脱离 Node 依赖的独立部署通过。

pytest 从 21:20:32 至 21:22:02 CST；其余本机 gate 于 21:22:58 前结束。所有适用软件 gate 均一次成功，没有隐藏失败或反复重跑。最初工具定位中的不存在路径、`importlib.metadata` 缺 poetry-core 及 CLI `ack --help` 不存在属于探查错误，终端保留；实际收信按 `check --ack <deliveryId>` 完成，没有误认测试失败。

## Windows / Ubuntu CI 与 Git 网络边界

`gh run view 35865484484 --json headSha,status,conclusion,url,jobs` 于 21:21:39–21:21:43 CST 成功保存到 `R/ci-code.log`。响应精确 headSha 为 `4938bb9230cf3acaf2cff63774f743a8a20d5bad`，结论 success；[完整运行](https://github.com/songconmaisaix31-design/Morphogenesis/actions/runs/35865484484)。

| 平台 | Job ID | 开始 / 结束 UTC | 本次读取结论 |
|---|---|---|---|
| Windows | `107195885391` | 13:12:39 / 13:16:48 | completed / success，pytest、type、build、SDK、wheel 安装、分发全部 success |
| Ubuntu | `107195885716` | 13:12:39 / 13:14:13 | completed / success，同上全部步骤 success |

报告制作前，`gh run list --commit 425d7e55b0cc8c3f2496a506b9f045fcb1b5fbfd` 返回空列表；该治理提交尚待网络恢复推送，因此不声称其已有独立 CI。主控已确认代码差异仅四份文档，无需为报告或治理文档重跑已通过的本机全量 gate。21:25 主控消息 `msg_91eacb7ec04b` 明确要求 I 报告推送后结算，不等待纯文档 CI；主控随后提交治理收口并核对最终 HEAD 双平台 CI，I 回执区分代码 SHA 与报告 SHA。

获取代码 CI 完整日志的两次有界读取分别返回 run API EOF（exit 1 / 5.175s）及 workflow API EOF（exit 1 / 41.444s），保留 `ci-code-logs`、`ci-code-logs-second-read` 两组 log/json。随后按主控验证过的 `HTTPS_PROXY=http://127.0.0.1:7890` 路由单次读取，仍为 run API EOF（exit 1 / 5.229s），保留 `ci-code-logs-proxy`，停止继续下载。因此 CI 逐用例计数/skip 未独立提取，不能编造；双平台及各步骤 success 以已成功保存的 exact-SHA JSON 为证。主控另报告 Git 默认 HTTPS `SSL_ERROR_SYSCALL`、命令局部 schannel 失败及 SSH publickey denied，均未修改凭据或关闭 TLS。主控实际验证的 Git 路由为单命令 `-c http.proxy=http://127.0.0.1:7890 -c http.sslBackend=schannel -c http.version=HTTP/1.1`；I 可沿此路由执行普通推送，无全局代理修改。

## 来源、失败关闭与真实证据复核

只读检查结果在 `R/evidence-details.json`，脚本不导入或执行 E/D 的 live runner，不调用 Hub、模型、付费接口、SSH 写入或安全组操作。第一次提取成功后摘要文件名与日志包装的元数据同名，后者覆盖了摘要；查读出现 KeyError 后仅修正自有忽略脚本的输出名，重新只读提取一次，保留两次退出0的日志。没有重跑产品测试或改变任何原件。

- 使用 Python AST 比对 `HubConfig.local_only` 与开工基线 `bd10f37c0ad378955210a1a76bd431f31a25ffee`，函数完整结构相同。锁、依赖声明及 `tests/t2/test_rehearsal.py` 相对该基线也无差异。现有完整回归包含禁止公网 HubConfig、凭据分离、HTTP 200 quarantine、缺 receipt、未知结果不重试、缓存 FETCH 不提升 live 和 mock 不能 REPORT live 等负例。
- 原 authenticated 证据 `recovery-evidence/authenticated-20260923-01/summary.json` 为 provenance=live、hello=1、heartbeat=1、固定节点一致，官方 MCP/Proxy 通过；continuous_tick/self_update=false。此为历史前置，不声称该旧 Proxy 进程当前仍在线。
- `asset-cycle-live-20260923-{01,02,04}` 各为唯一 publish HTTP 400、fetch/report=0/0；`-03` 是发送前资源失败，计数 0/0/0。没有将第三个目录误数为第三次网络发布或删除失败证据。
- `direct-live-20260923-01` 唯一真实 publish 为 **HTTP 200 / quarantine / newcomer_candidate**，计数 1/0/0；runner 原始 unknown 与独立 disposition 同时保留，不能视为 accepted。请求 `msg_1790167332976_8501df49`、HTTP ID `a2b3a3d7-d1ef-44c6-b687-8c233a45262c`、响应 `msg_1790167338046_00f46f86`、bundle `bundle_d4f8d679b30b5974` 与治理文档一致。
- 对 publish 原始 payload 的三个完整资产调用项目官方 `NodeAssetBridge.validate_asset`，三个 asset_id 全部匹配；当前旧版完整 schema 检查仍为 false，与已记录 wire 契约差异一致，未把哈希通过替代 schema 通过。三个 model_name 均为真实请求模型 `evomap-gpt-5.6-luna`。

| 资产 | SDK 验证通过的完整内容地址 |
|---|---|
| Gene | `sha256:c3862d97f0f2e93f06b250b9046b2f56fa6858afaa29102fe22d59ae934f9b6e` |
| Capsule | `sha256:a372fba521210354bdfcf22fcf499478f8a46a5ee8634b0da0c157edfcca0f78` |
| EvolutionEvent | `sha256:cd57f8d2a15363f8c6ae4af32799ab6705fedd396d72653ed8f5b2ef1be036ae` |

认证详情原件为 candidate、validation_status=noop、validation_credible=false、payload_ready=false、callable=false，HTTP ID `cc914342-b983-45e9-a8fb-3481d70d2bf8`。精确 FETCH 请求确实只包含上述同一 Gene：请求 `msg_1790168186661_01722cb8`、HTTP ID `5afdf2ed-b399-4081-9ca0-dad626ebcaa6`、响应 `msg_1790168190181_c4fa12da`；HTTP 200 / **confirm_required，3.36 credits 预览 / 余额 0**，返回资产=0，use=0，REPORT=0。持久化确认 token 为 `[REDACTED]`，未确认付费，不拿缓存或本地候选补齐远端正文。

## D / T 与历史网关边界

只读核对 D 原始 `smoke-public-53bb52c.json`：38 项；`browser-public-53bb52c/summary-replay.json`：72 passed / 0 failed，pageerror、console error、HTTP failure、外域请求均为空，唯一正常 `/api/evomap?` 浏览器 GET。dashboard 三态为 **replay / passed,not_run,not_run**；社区 search/categories=live，local_pool=unconfigured，两类来源分开。I 本轮没有重开公网浏览器或宣称重新完成截图观察，读取的是 D 已保存的真实验收材料。

主控新网络证据 `coordinator-network-verification.json` 与两个 smoke 日志记录 WLAN `172.20.10.2`、LAN 32 项 / 公网 38 项、exit 0、Hub/model 新调用=0；hotspot_human_confirmation=pending，代理虚拟网卡仍存在。因此旧 D 报告中的 WLAN `192.168.60.54` 已由主控较新证据取代，地址不能证明热点或第二设备验收。

第四轮原始 `C:/Users/DW/AppData/Local/Temp/morph-live4-98b36399c0324192b5af81f8077bc11d/morph-rehearsal-86e5351d49fe49a1b60ba0a4bb4c4e4e/rehearsal.json` 的标准 SHA-256 仍为 `f3639cd4e96edbe04cea63d4522df12cf16d84817bb84650a19885268b61c818`，226518 bytes，live/completed，2 个 succeeded 结果，tokens **887 + 1348 = 2235**，cost_usd 均 null。它是历史真实网关证据；本轮新增模型调用=0，没有跑新7527或发 Enter。

T 的既有 Gene 时间衰减竞态修复及延迟回归包含于全量294项；本轮未改测试、未增加 sleep、未重复其已经通过的单轨回归。领域缺陷不得由 I 越权修复；此次未发现需要退回的代码失败。

## 真实剩余限制与未执行操作

- **G3/G4 未通过**：候选未晋升、平台 noop/not-credible、余额0与费用确认门禁；尚无同 ID 完整远端正文、实际使用和真实 REPORT。官方 Proxy/SDK 对 Capsule.validation 的兼容差异仍存在；直连候选不等于 Proxy 兼容或 Hub sandbox 验收。
- **G5 整体未通过**：公网软件和历史 replay 已有证据，新7527独立网关凭据、热点人工确认、第二设备及现场单屏人工观看未完成。遵从主控最新单屏决定，**不要求外接投影**。
- 没有本轮新费用或 token 估算；未知仍为 null；G0 上游在途硬封顶、固定规模供给及真实接口的既有边界不因本次测试改变。
- 不部署最终 E 代码，不改变节点、秘密、账户、网络、安全组或远端数据；不触及 API sandbox/T4。不运行 `.runtime` 内 live runner，不操作主控所有7526/7799或原7844进程。
- 本报告提交前以 `gitleaks dir docs/tracks/freeze-integration.md --redact=100` 扫描自有报告，exit 0 / no leaks found；完整参数和脱敏日志保留。CI、Git 读取/推送的失败原件与成功核对分别保留。报告完整 SHA、推送状态由最终回执说明，最终治理 HEAD 的 CI 交主控，不能用较旧成功 run 冒充最终报告 run。写报告期间主控继续编辑 ACCEPTANCE 等治理文件，I 保留其 WIP，不暂存。
