# R1 唯一 I：精确集成与独立安装验收

本报告属于 Task `task_8f2c3d496f12` / Dispatch `ctx_7ab9bc21276f`，由最终 I 在独立 Orca 工作树完成。事实源是 `docs/source/Morphogenesis_Research_Swarm_Spec_v1.0_2026-10-02.md` 与 `docs/R1_PLAN.md`。验收范围是确定性契约与本机正式安装/HTTP/MCP/UI；mock 实验后端不提升为真实科研，AT07 真实隔离、L2、L3 和独立人工观察仍 NOT_RUN，不能据此宣称全 R1 退出 PASS。

## 1. 精确来源与普通合并

工作树：`C:/Users/DW/orca/workspaces/Morphogenesis/morph-r1-integration-1003`。分支：`songconmaisaix31-design/morph-r1-integration-1003`。开始时 HEAD 为主控治理 `b82140ddfe964f38c3525429fe95a8c6fbede1a5`，工作树干净。

| 输入 | SOURCE | REPORT / 治理 |
| --- | --- | --- |
| A 累积核心 | `d85aa95e8da406d598f3658492e3d615bba8a28f` | `524a81ed7ba0b3550f6ae029e316a56293901d12` |
| B 动态实验 | `230d283848c0879ff9c349096548d3810c4b1954` | `387338f49045f7be7a184b868f48f325cebd9cbd` |
| C 贡献与政策 | `56de8e3f5d2abd1e1ba02218b422f0aba9847ae2` | `8bc4c282ed4db8e2be0798509b28d984240b3a06` |
| Q 独立边界 | `953e5cf01f06dd2ed3c77f4cebb0f1c1a9bf1b6f` | `793661391738f5dadb2412af32c7188a60915c7d` |
| P 原领域交付 | `0da6273f54281f5e86231e31234f682598f68ba2` | `e1a327c940c1987e903972b39b040deb3fc9cf0a` |
| F 已构建静态资源 | `447d9e0aaa34cf0eaabc114c12f22496127e326a` | `fa6bfbda3849117ade2325b2d1cb378041344cb4` |
| 产品主控治理 | — | `d8ebca8c5a90d1c75cd8b88e43b413ac0c09a5fc` |

实际执行：

```text
git merge --no-ff --no-edit 524a81ed7ba0b3550f6ae029e316a56293901d12
git merge --no-ff --no-edit 793661391738f5dadb2412af32c7188a60915c7d
git push --set-upstream origin songconmaisaix31-design/morph-r1-integration-1003
git ls-remote origin refs/heads/songconmaisaix31-design/morph-r1-integration-1003
```

两个 merge 均无冲突；第一 merge 为 `70037c8`，最终核心 **SOURCE `2c63bc7c9e49edff28e26f5930a22d0415fadd65`**。上述核心 SOURCE/REPORT 与治理均经 `git merge-base --is-ancestor` 确认为祖先。相对 A d85，`swarm/`、`orchestration/`、`local_assets/`、Python/Node 锁、`tools/`、`.github/` 无差异；主控当前治理文件也未回退。I 没有接管任何领域实现或修改原测试。

SOURCE 在 2026-10-02 22:38 UTC 已推送，远端 exact，立即通知主控（`msg_eba9c7850292`）及原 P（`msg_71229e384078`）。随后 CI `37073582354` 针对该 SOURCE 开始；P 的 repin 不等待本机长测。本文是后继 REPORT，不能作为产品核心 pin。

## 2. 冻结边界与独立环境

全新短路径 `C:/r1i/i1003-2239`。核心归档由 `git -c core.autocrlf=false archive` 产生，Python `tarfile` 的 `filter='data'` 安全展开至 `core/`；`run-core/` 仅复制原 tests 与 pyproject，不含生产源码。没有借用 Owner venv/cache/node_modules，没有更改全局 Python、Git、provider、auth 或 HOME。

`logs/core-original-blobs.json` 对全部 **653** 核心归档普通文件逐一比较 `git cat-file --batch` 的原始 blob，完全相等，不作换行归一。旧 `7062a632b8c625c05b35bdec4c36fce63a31c2a4` 的以下 blob 在最终 SOURCE 未变：

| 路径 | 原 blob / 最终 blob |
| --- | --- |
| `orchestration/experiments/case.py` | `2a3684b68737628dbf9d4e320e6791adbb2f5665` |
| `orchestration/experiments/models.py` | `65fc677fdef6882e28952c60a46af0c653e7839c` |
| `local_assets/validate.py` | `e6c528695d701a60c09fb141f1b5d28c13eb3918` |
| `swarm/router.py` | `71c26b5afb66448e993d64cf057dac4bd82c604b` |
| `swarm/pheromone.py` | `90b825007e80bfb4a00ef8227ed57319467f4442` |

`swarm/feedback.py` 相对旧核心只增加 generated_plan 排除项，动态科学走独立版本化可信投影，不能当成旧 v0.1 reward。`swarm/research/case.py` 仅增加独立 generated seed 入口与 import，旧 registered seed 语义由原兼容测试继续约束。主线 `C:/Users/DW/orca/Morphogenesis` 只读 status 仍为既有 `docs/SWARM_SOL_PLAN.md` WIP，未写入。

另核对旧7062至最终SOURCE的`local_assets/snapshot.py`、`demo/research_case/`和`demo/research_cases/`无差异；主控b821至当前集成HEAD的历史`docs/STRATEGY_V01_ACCEPTANCE.md`无差异。历史冻结文本和原案例未被后继报告替换。

## 3. 最终产品组合与实际安装

原 P 最终 repin SOURCE 为 `c9fcc6e24500ff26cd6600dfa6719278f04b8cb5`，独立 REPORT `00fd40173736d715adf8f90e93dc8f8720cbf604`（包含主控产品治理 `e96a014740f0886db187ed3981459294e4cdc312`）。P 自验11 PASS/18.74s单列，I未用它代替独立验收。相对原0da运行代码只有核心pin，F447 frontend/static/tests-ui完全相同。

I 的私有 Python 为 **3.13.13**，venv `C:/r1i/i1003-2239/venv`。`uv export --frozen --no-emit-project` 导出产品原锁，97条lock记录；以私有 `UV_CACHE_DIR`、`UV_LINK_MODE=copy`、仅安装子进程 `GIT_CONFIG_COUNT=1/core.autocrlf=false` 安装。核心通过官方精确HTTPS VCS构建，产品从原始Git归档独立构建wheel后 `--no-deps --link-mode copy` 安装。原锁包安装后 `uv pip check` **96 packages compatible**，之后仅添加私有mypy1.20.2及其工具依赖。

`logs/installed-origins-bytes-first.json` 保留真实 `installed_core()`、core的direct_url `commit_id/requested_revision=2c63bc7…`、产品wheel的archive_info、实际site-packages导入路径及nlink1。全部 **132核心Python文件**（129包内文件加3个demo Python）、35产品Python，以及52个产品包文件逐字节匹配已核对原blob的归档。52中含13个实际static文件；Git static目录另有`.gitkeep`占位，共14，原安装测试明确不计占位文件。未mock installed_core、metadata、import origin或字节门。

正式 `morph-research setup-assets` 与 `doctor` 首次通过，原GEP SDK/schema1.14.0 ready_local，`models_experiments_hub_called=false`。`python -I core/tools/check_distribution.py --site-dir <venv>/Lib/site-packages --check-node` 首次通过13包导入、资源、原验证器和Node桥。

P 类型后继 SOURCE **`9e2718789cb67f8b829207e17dac4d95a88e59c9`**，核心pin不变；I新归档152文件再次与原Git blob相等。只修改`materials.py/r1_provider.py/web/server.py`三文件：stdout为空时终止自有读取子进程并沿既有错误拒绝、两个容器显式类型、可变长度错误码tuple注解；无cast/Any/ignore或schema/测试/锁变更。

P释放短窗口后，I从`product-9e27187/`归档独立构建新`dist-9e27187/`wheel，COPY替换自己venv的产品包；旧c9的归档、wheel、日志均保留。`final-installed-origins-bytes.json`重新核对全部132核心Python/35产品Python/52产品包文件、真实VCS与新wheel archive_info、site-packages导入和nlink1，全部通过。正式setup-assets/doctor再次通过，`pip-check-final.log`为 **100 compatible**（原96锁包加4个mypy工具包），不称锁中原有100包。

P类型返修 REPORT **`ad104f7c3555d04af4753c0601729f6dfef3c855`**。I独立核对SOURCE→该REPORT只改`docs/tracks/r1-product.md`；当时原P分支remote exact、工作树干净。P/F业务与报告均保留普通祖先链，I未写私库。

最终P文档 REPORT **`a7f657d18fae33fc2a4df92b5fcb60dcd7839c5d`**由原Owner/终端/工作树/分支在Task `task_4ceeb28295b5` / Dispatch `ctx_187f60b538c0`交付，普通含最终产品治理`b20c29ef35e9f627cb1cd9564a8542bf04c2357e`。I再次核对remote exact/HEAD一致、工作树干净及两个指定祖先；9e SOURCE→a7 REPORT只变`docs/PLAN.md`、三份R1治理及`docs/tracks/r1-product.md`，所有非docs文件零差异，runtime、README、static、原测试、锁和核心pin不变。该文档后继不构成新SOURCE，不重新打包安装或重跑已通过门；本报告的实际安装身份仍为受测9e/2c。

F工作树`C:/Users/DW/orca/workspaces/Morphogenesis-Research/research-r1-ui-1003`的`songconmaisaix31-design/research-r1-ui-1003`分支也经I只读核对：HEAD及remote均为`fa6bfbda3849117ade2325b2d1cb378041344cb4`，工作树干净。最终P的frontend、static和UI原测试相对F447无差异。

### 3.1 I 类型首失败与原Owner返修

I按原 `--follow-imports skip --ignore-missing-imports --check-untyped-defs`、mypy1.20.2执行c9全包，首 **14 errors / 9 files / 35 sources**。新增4项为`materials.py:177`可空stdout读取、`r1_provider.py:42/104`容器注解、`web/server.py:55`固定长度tuple赋值。原log `product-mypy-whole-first.log`保留，Handoff `msg_55c027e5ea0d`退回主控；主控在原P终端/工作树/分支新派Task `task_5df01d3615be` / Dispatch `ctx_108d5673e53c`，I未修改私库。

首次affected命令误写不存在的`r1_materials.py`，exit2（`product-mypy-affected-first.log`）；按真实`materials.py`更正后的原flags对19文件得到相同4错误（`product-mypy-affected-corrected.log`）。不是放宽ignore/exclude或改测试。

为区分原Python3.12.13证据与本次3.13.13，I在同一新私有mypy/Python环境静态复核原SOURCE `a25aa40bb0f5259799641fee378d09ccc5887054`：**原10 errors / 6 files / 24 sources**（`product-mypy-a25-correct-cwd.log`）。首次比较误从核心cwd运行、继承核心strict配置而产生230错误，原`product-mypy-a25-same-env.log`保留；随后从真实baseline归档cwd使用原flags，未改配置。该静态比较不是旧产品的重新运行验收。

`product-type-first-identities.json`逐条比较原10项的**文件、消息、错误类别和原表达式**完全一致，只允许已逐表达式验证的guard99→100位置变化。旧3.12日志的SimplePath[Any]在同环境旧源码和新源码都渲染为SimplePath，不能只靠相同数量当作基线。四新增错误单列，原全包RED不掩盖为green。

I实际后继9e的同flags检查覆盖原6债务文件之外的**全部29源文件，PASS**（`product-9e-mypy-affected-first.log`）；全包35文件保持**10 errors/6 files，exit1**（`product-9e-mypy-whole-first.log`）。`product-type-final-identities.json`核对该十条与上面的同环境旧源码逐消息/文件/位置映射相等、对应表达式未改，新错误0。不是全包strict通过。P自有Python3.12.13/mypy1.20.2对原c9的14/9及后继10/6、相关installed30 PASS13.48s仅列Owner证据，不代替I结果。

## 4. 最终 SOURCE 的适用验证

精确核心CI [37073582354](https://github.com/songconmaisaix31-design/Morphogenesis/actions/runs/37073582354) 的headSha是`2c63bc7c9e49edff28e26f5930a22d0415fadd65`，两平台原始运行均成功，没有重跑：

| 平台 / job | 完整原pytest | 其余原门 |
| --- | --- | --- |
| Linux / `111058370196` | **1565 PASS/16 SKIP/75 warnings/563.89s** | strict136、sdist/wheel、SDK、安装13包与资源/验证器均PASS |
| Windows / `111058370412` | **1566 PASS/15 SKIP/75 warnings/1974.60s** | strict136、sdist/wheel、SDK、安装13包与资源/验证器均PASS |

完整原log分别由`gh api repos/songconmaisaix31-design/Morphogenesis/actions/jobs/<job>/logs`获取，保存`core-ci-linux-job-first.log`与`core-ci-windows-first.log`；`core-ci-final.json`保留精确headSha及全部step结论，Windows最终job于2026-10-02 23:14:05 UTC结束。run尚进行时`gh run view --job --log`拒绝下载是日志访问限制，不是测试失败。Windows pytest实际32分54秒，不以预估25分钟替换；没有据耗时推断原因或性能达标。

core-only CI的产品专属Q模块会skip，不能将它们写成通过；I installed Q另外收集。最终报告后继只改文档，不将后继文档CI冒充此精确SOURCE的CI，也不需要因文档再执行同一科学测试。

以下产品完整Python、Q与实际UI门都使用最终installed 9e/2c组合；核心focused门使用同一不变的installed core2c。A旧组合CI与Q旧组合通过不代替本次验收。

I实际installed核心的原`test_stdio_dynamic.py`、research `test_case.py/test_registered_cases.py`、experiments `test_registered_cases.py`、`test_policy_score_v01.py`及`test_store_initialization.py`首轮 **65 PASS / 2 RED / 26.71s**，完整日志`core-installed-focused-first.log`。两个RED是中立测试根缺原`demo/research_case`数据，生产模块仍来自私有site-packages。将原归档`demo/`原样复制到中立目录后，仅对原失败两个节点用新basetemp复测，**2 PASS / 0.28s**（`core-installed-fixtures-second.log`）；未重跑65项或改原断言。它覆盖正式动态stdio、原两类案例、旧policy与SQLite初始化，不等于真实候选执行。

前端在独立`ui-build/`归档中执行`npm ci --ignore-scripts --no-audit --no-fund`（115 packages）及`npm run build`：**3907 modules / 15.69s PASS**。新构建的`index.html/assets/product.css/assets/product.js`与F447在冻结产品归档的原文件完全相等（`frontend-build-original-bytes.json`）。构建未覆盖冻结产品归档或已安装static；页面将使用已安装原F静态字节。

官方Codex0.159.0仅安装至I私有`native159/`（禁用npm scripts、私有cache和空npm配置），实际`--version`通过；只为后续legacy测试子进程PATH选择它。实际本机0.160元数据/parser门另列，任何原生科研模型启动仍NOT_RUN。

### 4.1 最终产品完整Python首轮与有限后继

固定真实installed产品9e/core2c，cwd为新`product-9e27187`归档（src布局），`python -I`仅将原测试根加入路径，没有加入生产src。环境指向精确`MORPH_FROZEN_ARCHIVE`/`MORPH_CORE_ARCHIVE`；BLAS/OMP/MKL=1。命令为：

```text
python -I -X utf8 -u -c "import sys,pytest; from pathlib import Path; sys.path.insert(0,str(Path.cwd())); raise SystemExit(pytest.main(sys.argv[1:]))" -q -rA --tb=short --basetemp C:/r1i/i1003-2239/full-9e-tmp
```

首轮 **222 PASS / 6 FAIL / 249.42s，exit1**，`product-full-9e-first.log`保留全部输出与成功项的采集时间。原旧MCP三个兼容失败、HostBinding、R1正式stdio、安装字节门、生成支持/反证/unknown三项均在这轮通过。新generated实际apply **8.458808s / SDK67次7.345742s**，inherit **2.393205s / SDK17次1.875994s**；仍不宣称p95或传播目标达标。

其中五个parser失败明确来自I环境将私有**local npm `.bin`**加入PATH，原核心注册器按受支持的npm前缀布局寻找`.bin/node_modules/@openai/codex/package.json`而失败。I改用同一已安装官方包实际`vendor/x86_64-pc-windows-msvc/bin/codex.exe`目录，只改后继测试子进程PATH；version0.159和原`resolve_executable`另存`native159-formal-resolution-second.log`，无源码/installed字节/测试/flags变化。

第六项`test_four_phases_real_runner_boundary_and_three_page_facts`原`interrupt-response.json`为`preflight_rejected / reason=unknown / native_started=false / exit_code=null`，尚无observation。原首轮异常原因未保存，仍**UNKNOWN**，不能由后继成功倒推为已知。原`fixtures/6ff5cc4be0db/...`完整保留，未重发该旧请求。

在全新`product-six-second-tmp`及新随机fixture根，仅复测原失败6项：**6 PASS / 25.33s，exit0**（`product-six-second.log`）。原非法transport拒绝、名字转义、权限allowlist、实际本地parser和四阶段mock边界均用原断言。未重复222项、未重写首轮为一次228全绿。

随后恢复普通PATH另测实际本机Codex **0.160.0**：`native160-metadata-first.json`保留原解析命令与version，两个原适配/实际本地`mcp get` parser测试 **2 PASS / 2.32s**（`native160-parser-first.log`）。测试为全新秘密为空的parser子进程配置，原测试核验不创建auth/sessions、父环境不变；没有模型、认证登录或科研执行。

### 4.2 Q 全部原守卫与正确收集范围

中立`run-core/`执行原整个目录：

```text
R1_SECURITY_INSTALLED=1
python -I -X utf8 -u -c "import sys,pytest; from pathlib import Path; sys.path.insert(0,str(Path.cwd())); raise SystemExit(pytest.main(sys.argv[1:]))" tests/integration/r1_security -q -rs --tb=short --basetemp C:/r1i/i1003-2239/q-final-tmp
```

**293 PASS / 3 SKIP / 80.79s，exit0**，`q-final-installed-first.log`。保持原`Popen/os.system/socket.connect/connect_ex`禁止guard、真实installed_core及产品factory；未设置R1_SECURITY_SOURCE/R1_PRODUCT_SOURCE，未修改Q目录或断言。A/B/C全部安全边界及P的factory、注册、资料、provider/resume/HostBinding、public export等均被收集；相对Q旧fbe/d85全275记录，当前目录还包括后继registered21，不能混用旧总数。

三个skip明确是`test_p_loop_boundaries.py:69/78/93`中已撤回unsafe product loop的历史测试，原native core loop integration仍NOT_RUN；没有将skip或未执行native模型说成通过。Q整个目录本轮没有产品模块级安装缺失skip。

### 4.3 前端完整fixture回归与实际installed观察分列

用前述已构建且等于F447原字节的独立`ui-build/`，直接执行`node frontend/node_modules/@playwright/test/cli.js test --config tests/ui/playwright.config.mjs`，避免pretest重复build。原one-worker/retries0/timeout30000，桌面1366×900、窄屏390×844，独立新`ui-fixture-first/`目录：**108 PASS / 6 SKIP / 1.1m，exit0**（`ui-fixture-first.log`）。这是明确使用fixture mock路由的UI回归，不是实际后台。六个skip是缺installed origin/seed的三个observer各两视窗；以下四个由正式服务独立执行，本轮另外两个installed输入observer仍NOT_RUN，不相加伪称全部114通过。

实际观察从最终私有安装的 `venv/Scripts/morph-research.exe serve --config <原p9 seed> --port <自有本机端口>` 启动；先前正式setup-assets/doctor已通过。原observer配置和两个spec均与F447逐字节相同，无route intercept、无替换后台、无写POST。原配置每例30秒/0重试/1 worker保持。

| 正式installed observer | 结果 | 新证据 |
| --- | --- | --- |
| 支持seed，两视窗原三页/DTO/键盘条件展开/采用/完整原始输出检查 | **2 PASS / 28.0s**（各13.2s、13.1s） | `logs/ui-support-observer-first.log`、`ui-support-first/` |
| 反证seed，两视窗原反证/贡献/无采用断言 | **2 PASS / 8.1s** | `logs/ui-refutation-observer-first.log`、`ui-refutation-first/` |

合计14张新截图。I实际查看桌面/窄屏三轴卡片和反证页面：mock标识、三轴、成员、默认收起的条件可见，反证贡献与无采用分开；原自动断言还核对无横向溢出、原条件值和0POST。该Agent视觉复核不冒称独立人工可理解性验收。

实际GET保存未经改写的成果包：

| 原始HTTP成果包 | 字节 | 原记录计数与边界 |
| --- | ---: | --- |
| `C:/r1i/i1003-2239/ui-support-export.json` | 292723 | 候选3、冻结计划4、评价3、复核1、贡献1、mock采用1、原始产物12 |
| `C:/r1i/i1003-2239/ui-refutation-export.json` | 202614 | 候选1、冻结计划2、评价2、复核1、贡献1、采用0、原始产物8 |

两包evaluation provenance均为mock，`raw_artifacts_truncated=false`；同次实际DTO也各保存。`logs/final-export-summary.json`只提取这些已有事实，不创造结果。旧p9两种子共14 SQLite数据库只读`mode=ro/query_only`前后行数映射相等（`p9-before.json/p9-after.json/p9-count-comparison.json`）；这是行数比较，不扩称完整DB字节/mtime证明。

服务启动/退出argv和时间见`ui-support-command.json/ui-refutation-command.json`；自有Popen服务树在观察/导出后以明确PID执行Windows`taskkill /T`，两次cleanup exit0，launcher终止exit1按受控清理记录，不把它写成服务运行失败。没有对其他进程执行stop。检查本私有路径匹配的Python/Node/browser和本轮7813/64141/65213监听均为空。

## 5. 历史 RED、后继范围和未知事实

- A d85 的原 CI `37062098247`：主控已核实 Windows1392/5skip、Linux1391/6skip，strict136/build/SDK/wheel 通过；它是旧 A 组合证据，不冒充 I SOURCE CI。
- B 本机原 worker180秒用例 `1 failed / 21 passed`，确切慢原因 **UNKNOWN**。后继独立 CI 通过不解释或抹去它；I 不无故本机再跑同一长套。
- Q 的实际 installed fbe72/d85 完整边界为 **272 PASS / 3 历史 SKIP**。B72 的原日志耗时 **4314.57s**，约72分钟工具返回空档，另有主控先前约50分钟空档；原因均 UNKNOWN，无性能达标声明。
- 主控在`msg_d4272bebc7e3`另记录第三次工具返回空档：最后delivery为2026-10-02 **23:18:58 UTC**，下一工具返回为2026-10-03 **00:25:29 UTC**，约**66分31秒，原因UNKNOWN**。这是主控观察的交互计时；原P在原终端继续文档任务，无重派、测试或科研重启，不改写上列pytest实际耗时。三个空档分别保留，不能算作测试通过速度或已知运行故障。
- Q 后继实际 installed 0da6273/d85 为164 Python原blob、真实非editable VCS origin、95依赖，以及 registered21/native22/resume13/Codex13/Claude7/factory11 共 **87 PASS / 21.74s**。这是相关后继门，不能写成0da全275已跑通过。
- P fbe72/d85 完整首轮 **221 PASS / 3 RED / 270.94s**；后继0dface相关集合 **88 PASS / 3 RED / 94.57s**；0da的原3兼容失败、HostBinding4、R1 stdio及字节门 **9 PASS / 14.86s**。原exact11、空字符串项目默认值及原build_launch HostBinding均保留，不把这些不同组合相加冒充一次完整通过。
- P 新 generated helper 首15秒等待超时原样保留；仅新增该测试获准60秒传输采集，旧15秒默认未变。先前后继 apply8.789717秒（SDK67次/7.658393秒）、inherit3.377263秒（SDK17次/2.826537秒）只是单次观测，不满足或证明 p95≤2秒 / 传播≤3秒。
- F 旧漏setup-assets导致聚合GET503、导航未就绪及反证selector首RED保留；F447后继实际页面支持2 PASS/29.9s、反证2 PASS/8.5s的主体为core cc2。I 的最终组合观察另外记录，保留原断言/30秒及0POST。
- A/P 历史 CRLF archive/VCS 安装字节门首RED和 A首次installed-root strict遮蔽失败保留。I 用新归档/缓存和原blob比较，不修补installed字节或降低字节门。

## 6. 只读历史种子、授权与人工剩余项

UI 使用 P 原 `C:/research-private/p9/test_configured_generated_revi0/serve.json`（支持）与 `.../test_configured_generated_revi1/serve.json`（反证），空间 `bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb`。原执行 subject 属历史 mock；新包正式 serve 只观察页面/导出，不重发未知请求，不复用或清空已有 basetemp。新包的 generated_by/安装身份不能改写原实验 subject。

无真实候选在宿主执行，无原生模型科研、真实沙箱/AT07探针、新云GPU、论文网络外发、Hub或部署；L2/L3/独立人工观察 NOT_RUN。mock 的评价、贡献与采用保留 mock，未知效果/用量/费用保持 unknown/null，不宣称科学优势或协作因果提升。

C 的全局 editable 清理是已发生的 **自动审批 blocked by policy，未清理**；I 不重试、不绕过。人工清单见 `docs/tracks/r1-policy.md`“C 全局 Python 安装事件”节：`C:/Python313/Scripts` 两个 Morphogenesis exe、`site-packages/morphogenesis.pth`、该dist-info八文件共11项；全局 opensandbox/opensandbox-code-interpreter/poetry-core 的旧依赖状态未知，不批量卸载。人工须先确认无进程使用，再核对原direct_url/RECORD/文件身份，只处理确证项；私有验收不等于全局恢复。

四项旧 Orca `release_unknown` 保持原未知状态，不编造释放或完成回执。I 仅关闭本轮自有服务/浏览器/测试子进程。

## 7. 最终交付状态

| 门与实际命令 | 结果与限制 |
| --- | --- |
| 精确core2c双平台CI：原`python -m pytest -q`、`tools/typecheck.py`、`python -m build`、`npm run check:sdk`及wheel安装/`check_distribution.py` | Windows1566 PASS/15 SKIP；Linux1565 PASS/16 SKIP；两端其余原门全PASS，完整数字见第4节 |
| I COPY/VCS安装：原锁`uv export --frozen --no-emit-project`、`uv pip install --link-mode copy`、产品`uv build --wheel`、原blob/import/direct_url检查 | 实际非editable/site-packages，最终9e/2c字节通过；100依赖兼容包含4个独立类型工具包 |
| 正式`morph-research setup-assets`、`doctor`、安装分发`check_distribution.py --check-node` | GEP SDK/schema就绪，原包/资源/验证器通过，无模型/Hub调用 |
| installed core原stdio/case/v0.1/init节点 | 首65 PASS/2 RED；补原fixture后的两个原失败节点2 PASS |
| installed product原完整`pytest -q -rA --tb=short` | 首222 PASS/6 FAIL；新fixture下仅原失败6项6 PASS；一个首preflight原因仍UNKNOWN |
| 原Q整个`tests/integration/r1_security`，`R1_SECURITY_INSTALLED=1` | 293 PASS/3历史SKIP，原守卫不变 |
| 产品原mypy flags，全部35源与无旧债务的29源 | affected29 PASS；whole保留原10 errors/6 files，非全包strict green |
| 原前端`npm ci`、`npm run build`及完整fixture Playwright配置 | build通过且产物等于F447；108 PASS/6 SKIP，明确mock路由 |
| 原installed Playwright配置，对最终正式serve的两p9种子/两视窗 | 原4 observer全通过，三页真实HTTP、原成果包、14截图、0 POST；另两个installed输入observer NOT_RUN |
| 实际Codex0.160原适配及本地parser两个节点 | 2 PASS；0.159仅私有legacy测试PATH，模型科研NOT_RUN |

全部本机原日志、首失败fixture、精确归档/wheel、截图及成果包保留在`C:/r1i/i1003-2239/`。I自有本机进程/监听已清理，原未知资源和C全局事件没有被操作。

已依次普通合并主控治理`548227763e4c8d50ecdb86de77196abf13c3b88b`、`6e778825f2db29152eafba3c73ec5e5600114072`和最后元数据追加`1f03d598372552c44bb19c6d49e4b606ddb753c8`；仅追加三个R1治理文档，历史段落保留。核心SOURCE至治理合并后HEAD的全部非`docs/`文件零差异，包含runtime、锁、原测试、SDK和构建配置。核心SOURCE仍为`2c63bc7c9e49edff28e26f5930a22d0415fadd65`，不因REPORT重新pin；P最终SOURCE9e/REPORT a7、F SOURCE447/REPORT fa6均已核对。

最终治理首个merge命令在Git保存工作状态前因本报告的intent-to-add索引条目被拒绝（`Entry ... not uptodate / Cannot save the current worktree state / stash failed`），未进入领域合并。只撤回该临时索引标记，核对报告文件字节未变，再执行同一普通merge成功为`7842da7`；没有stash丢弃、工作文件覆盖或领域冲突。

本文件所在的最后单独文档commit为I REPORT，其完整SHA由最终Orca交付回执列出；提交信息含`[skip ci]`，不重复已完成的精确SOURCE CI。最后执行`git diff --cached --check`、普通`git push`、`git ls-remote`对照本分支HEAD、`git status --porcelain`及`git diff --exit-code <SOURCE> HEAD -- . ':(exclude)docs/**'`核对，交付时remote exact、工作树干净且非文档零差异。原始Git命令结果保存在`C:/r1i/i1003-2239/logs/final-git-delivery.log`。

本次确定性契约与本机安装/HTTP/MCP/UI适用工程验收完成。所有首RED及UNKNOWN、SKIP、原十项类型债和性能限制按原身份保留；第6节的AT07/L2/L3、真实模型/沙箱/外发和独立人工观察等仍NOT_RUN，C人工恢复及旧未知资源仍未处理。没有推送main/tag或部署，不宣称全R1退出PASS。

## 8. 2026-10-03 17:32 同一 I 接续：核心阶段

本节属于原唯一 I 的连续核心阶段，Task `task_5f75f854b26e` / Dispatch `ctx_eceee077723b`；没有第二集成 Owner、worktree 或分支。先以原始 `git show 6cf280dd78db687dee45effdc805e5b46f17a744:docs/R1_PLAN.md` 读取主控 17:32 决策，再执行普通精确合并。用户 Spec 优先，原产品完整回归仍等 P 的实际人类 TTY receipt、AOCI 完成、最终核心 pin 和 F 最终合并。

开始时原分支 `songconmaisaix31-design/morph-r1-integration-1003` 干净，HEAD 为 `08b31b39c075571ffd247e2b591d657ce09b6b34`。原第1–7节、首 RED、UNKNOWN 和 `C:/r1i/i1003-2239/` 证据保持；本轮不读取或复用其环境。新日志目录为 `C:/r1i/i1003-core-1732/logs/`，无新的本机安装或科研运行。

### 8.1 精确来源、合并与 SOURCE

| 输入 | SOURCE | REPORT / 治理 |
| --- | --- | --- |
| A 累积核心与 AOCI | `8dd85c1f88698cd8a22d72b5575e45e9431c0ce0` | `d8af82791fecde1f3dadfbf9190d4cbfada80146` |
| B 官方冻结导出 | `5769005b09f1b756c94fdad0649a6b74690c0ca9` | `5aebd2eb7af774b3dc496ad9620548f6e7852e09` |
| C 正证据机会与选择 | `e82cae36038c386aec999642289ac1d78c82a9ed` | `52b8d26da04aec41ceb7e008445ef2f1dc088d53` |
| Q 独立边界 | `88d0cc28d1fdb3d89d62cdb1f1312078fc3c22b0` | `6ce5a23ea256affdf9fe8a71bbaabb66695f3631` |
| 主控治理 | — | `6cf280dd78db687dee45effdc805e5b46f17a744` |

每个 business SOURCE 均为其 REPORT 的祖先；四组 SOURCE/REPORT、主控治理和原 HEAD 共十个提交均经 `git merge-base --is-ancestor <sha> HEAD` 核验 exit0。A/C/Q 的 SOURCE→REPORT 仅本轨文档；B 的差异仅本轨报告、授权包和保留的原始离线日志。

依次执行 `git merge --no-ff --no-edit <REPORT/治理>`：A merge 为 `080acc0639ece16ca58d3236779e199d9721bac8`；B/C 已包含于 A，返回 Already up to date；Q merge 为 `dc2655acc974bfe1862c86a35b3fbadf3a9fc28d`；治理 merge 为 **最终核心 SOURCE `3a6a7e5fecd5bbead9d234fa22ae0735bed19beb`**。全部无冲突，不 cherry-pick、不 force、不接管领域或 Q 文件，没有 I 胶水修改。

最终 AGENTS、R1_PLAN、R1_STATUS、R1_ACCEPTANCE 与 root6cf 原 Git blob 完全一致。相对 A REPORT 的非 docs 差异仅来自 Q 的新增/受影响边界文件；原 I 报告与 `.github/workflows/check.yml` 在 SOURCE 冻结时未变。`final-ancestors.txt`、`A-to-final-nondocs.txt`、`governance-exact.txt` 和 `historical-I-workflow-protection.txt` 保存核对结果。

SOURCE 于 2026-10-03 09:33 UTC 普通 push，`git ls-remote` 证明远端 exact，原推送日志为 `core-source-push-first.txt` / `core-source-remote.txt`。首次本机证据收集命令因 PowerShell foreach 后直接接管道产生 ParserError，整条命令在执行前被拒绝；后继仅修正命令语法，随后 ACK、血缘检查和首次 push 成功，未触发重复 push 或 CI。

### 8.2 精确 SOURCE 的原双平台 CI

原 `foundation` push Run **`37113441786`**：<https://github.com/songconmaisaix31-design/Morphogenesis/actions/runs/37113441786>。`headSha` 为上述 SOURCE；Linux job `111175600084`，Windows job `111175600216`。只消费这一次实际运行，没有 dispatch、rerun 或重复 Owner 专项测试。

原工作流使用 Python3.13 / Node24，依次执行原 `uv tool run poetry install`、`npm ci --ignore-scripts`、完整 `uv tool run poetry run python -m pytest -q`、`python tools/typecheck.py`、`python -m build`、`npm run check:sdk`、wheel target 安装和隔离 `python -I tools/check_distribution.py --site-dir tools/.wheel-site --check-node`。首次实际 Run 已结束为 **failure**，attempt1 原样保留，没有重跑。

| 原门 | Linux `111175600084` | Windows `111175600216` |
| --- | --- | --- |
| 原锁安装、npm ci | PASS | PASS |
| 完整 pytest | **1742 PASS / 2 FAIL / 16 SKIP / 75 warnings，540.91s，exit1** | **CANCELLED**，没有完整统计，不能算 FAIL 或 PASS |
| strict / build / SDK / wheel install / distribution | workflow skipped / NOT_RUN | workflow skipped / NOT_RUN |

两项失败均为 Q 所有的 `tests/integration/r1_security/test_b_frozen_export_boundary.py::test_official_local_transport_constructs_without_environment_or_engine_connection`，分别参数 `unix:///var/run/docker.sock` 与 `npipe:////./pipe/dockerDesktopLinuxEngine`。第123行无条件 `from docker.transport import NpipeHTTPAdapter, UnixHTTPAdapter` 在 Linux 的官方 docker.transport 上抛出 `ImportError: cannot import name 'NpipeHTTPAdapter'`；连 unix 用例也在 `_transport` 调用和原断言之前失败。静态核查 B `_transport` 在 npipe 分支取 NpipeHTTPAdapter、unix 分支取 UnixHTTPAdapter，不能据测试 import 失败认定 unix 生产适配失败或真实 Engine 可用。

Windows 在 Linux失败后被原 matrix取消；原日志包含 cancellation期间pytest INTERNALERROR/KeyError和 `The operation was canceled`，保持原结果身份，不把取消堆栈变成完整 Windows失败或通过。原始完整 `gh run view --log` 字节保存为 `ci-original-first.log`，stderr为 `ci-original-first.stderr`；首失败原行摘录为 `ci-first-failure-excerpt.txt`，最终Run/step状态为 `ci-final-first.json`。原 run URL和job ID绑定本 SOURCE，而非某个 Owner旧 green。

已通过 Handoff `msg_23efbcd5dd55` 向主控交 exact SOURCE、原失败节点/行、原断言前失败、原日志及所有者。平台适用的官方 transport测试修正归**原 Q**；若进一步发现不支持endpoint的生产边界需要变更，归原 B。I 不修改 Q测试、平台断言、领域逻辑或 CI来绕过；核心阶段验收目前 **NOT_ACCEPTED**，后继源修正与验收仍待主控路由原 Owner。

### 8.3 AOCI 只读官方观察与原 A Handoff

使用原官方 rc17 二进制，显式 `--repo <I worktree>` 执行官方 `index agent guide --agent codex --json` 和 `check --json`。Guide exit0、`complete=true,next_action=none,stage=aligned`；Check exit0、`ok=true,findings=[]`。Guide 报告 structure/governance aligned、pending_transactions0、recovery_pending=false、third_party_conflict=false、network_accessed=false。原输出为 `aoci-I-guide-first.json` / `aoci-I-check-first.json`。

代码 Volume 目录仍为 `C:/Users/DW/orca/workspaces/Morphogenesis/morph-r1-research-1003/`。十个索引源码在最终 SOURCE 相对 A SOURCE 的原 Git 字节零差异；Guide 有五个 line_ending_only 条目，不能由此覆盖原 installed 字节门。上述返回只证明本次官方检查的机器观察，**I 的路径重新绑定、当前完整 cognition 和 freshness 仍 NOT_VERIFIED**。未执行 Overview/Attestation、init、baseline/路径/receipt 修改或迁移；未复制 A/P 本机 receipt。无索引源码 delta，路径迁移的必要性与官方维护交回原 A，由主控路由，不手工替换绝对路径。

### 8.4 产品最终合并位置：只读建议

仅使用 F checkout 的 Git 数据只读调查，未访问 P 冻结工作树文件、未运行 `C:/research-private/p-aoci-approve.ps1`、未写产品文件。P 当前 SOURCE `67721aaa815e706c51e0f80a1d15ab71e34b6880` 已为 F SOURCE `7bf17d195859a18960ee1ef933a920a286f73e61` / REPORT `c08566edc492e92adfc4e24a9e8de1c18b859e02` 的祖先，merge-base 正是 P677。F SOURCE→REPORT 仅 `docs/tracks/r1-ui.md`；P677→F REPORT 仅 F 所有的 UI、静态产物、UI 测试和报告。

建议主控待 P 实际 human receipt 和 AOCI 收口后，由**原 P** 在原产品分支普通精确合并 F REPORT，再按最终核心 SOURCE repin/lock 并交最终产品 SOURCE；任何 F 领域冲突交原 F。此建议不改变 P 当前受保护 Header/config/README/source，不先合并产品、不运行完整产品回归。原产品路径和血缘见 `product-worktree-location.txt` / `product-lineage-location.txt`。

早期 Handoff `msg_833cd194a39d` 交核心冻结与无冲突事实；`msg_316c74cb369b` 交 Run/job IDs、产品合并建议及 AOCI 路径限制。主控后继 `4b8aec899606626dd4780aee73aefa536ddef844` 仅追加 L2 问题/材料提议，不进入本 SOURCE、不改变授权；主控已明确无需合入冻结 SOURCE。

### 8.5 当前边界

本阶段只覆盖最终核心确定性 CI；产品最终组合完整 COPY 回归及 installed 输入/只读会话/支持反证 HTTP 页面仍 NOT_RUN。P human receipt 尚未出现，原十项产品类型债、原失败与未知事实保留。AT07、Docker/WSL/真实服务启动、真实候选、native 科研、L2/L3、外发、人工理解、main/tag/部署未执行；`task_live=NOT_RUN`。没有全局安装、认证、PATH、HOME/provider/hostconfig 改动；用量/费用与 token 节省 UNKNOWN。

本节交付为保留首 RED 的后继 docs-only REPORT，完整 SHA 由本次 Orca 回执列出。原 CI 实际结果齐备后 commit/push，提交带 `[skip ci]`，避免文档再次触发完整源码门；失败 SOURCE 不因 REPORT 改变，核心适用门未全通过，不能宣称该阶段完成或全 R1 PASS。

## 9. 同一 Task 的原 Q 返修与后继精确核心门

主控通过 `msg_4b2cbf661e7a` 恢复原 Q Owner，限制为其平台测试及报告；I Task/Dispatch 不变。主控 `msg_36b8c9f882d6` 接受 Q 修复 SOURCE `acb26f4af3535ff6b4136dcb5ef0f7fde526e2a3`，授权普通合入后继核心；Linux实际执行由 I 的组合 CI 负责。原失败 SOURCE3a6、Run37113441786、REPORTab39及全部断言前失败输出留在历史，不改写为后继绿。

Q 的源码差异只涉及上述平台测试22行：从官方 `docker.transport` 按平台获取真实 adapter；非 Windows 的 npipe 用例明确断言官方模块无 NpipeHTTPAdapter，并要求生产 `_transport` 实际抛出原 AttributeError，**没有 skip、假 adapter或真实 npipe可用声明**。unix/Windows npipe保持官方类身份、`trust_env=false`、`auth=None`，并精确断言受信 endpoint路径与base，原请求/进程守卫不变。生产实现、依赖/锁、CI、AOCI全未改变。

Q 两项原 Windows节点在其私有非 editable Aaec86安装上 **2 PASS / 0.45s**，136原 Git Python blob相等，Docker SDK7.2.0；不是 I 最终 SOURCE完整安装或 Linux结果。原证据随 SOURCE保存于 Q own `tests/integration/r1_security/evidence/q-transport-portability-windows2-first.txt` / `q-transport-portability-private-identity-first.txt`，I 未重跑。

Q 最初任务未携带 skip-ci，后继补充消息在 SOURCE push之后才被读取，造成额外原自动 CI `37114202636`。主控一次提交 cancel后，在 `msg_5dad41ad1f67` 确认该 Run completed/cancelled、两端job cancelled；没有完整套通过或重写历史。此事实由主控回执提供，不当成任何门的 PASS。

I 先原始 Git读取 root治理 `9e1e6f78b588ecb858ea9226126773cf0f071254` 的计划，核对相对 root6cf只改三个治理docs，再普通精确合并 Qacb及root9e，均无冲突。**后继核心 SOURCE `b480fca1b10a0b6a9c93f0d1801d38f267662461`** 于 09:50UTC普通push，remote exact/clean；首RED SOURCE、REPORTab39、Qacb/root9e均为祖先，governance原blob等于root9e。相对首SOURCE的非docs差异只有Q测试及其两份小证据；排除Q目录后的所有非docs路径零差异，I无领域/测试编辑。

新原 `foundation` push Run **`37114395256`**：<https://github.com/songconmaisaix31-design/Morphogenesis/actions/runs/37114395256>，`headSha=b480fca1b10a0b6a9c93f0d1801d38f267662461`；Linux job`111178257285`、Windows job`111178257446`。这是修正源码后的一次新完整组合门，不是旧Run rerun。早期 Handoff `msg_082ca31b2fe6` 已交主控 exact SHA/Run；现总Run及两个job均 **completed/success**，原日志两端checkout均为完整b480 SHA，不以Q Windows2绿替代。

| 原门 | Linux `111178257285` | Windows `111178257446` |
| --- | --- | --- |
| 完整 pytest | **1744 PASS / 16 SKIP / 75 warnings，521.84s** | **1745 PASS / 15 SKIP / 75 warnings，1575.82s** |
| 原 strict | **140 source files，PASS** | **140 source files，PASS** |
| 原 sdist/wheel build、SDK、wheel target install、distribution check | **全部 PASS** | **全部 PASS** |

两端SDK原JSON均为 `scope=contract_local,schema_version=1.14.0,schema_valid=true,asset_id_verified=true,tampering_rejected=true,published=false`；两端原distribution JSON均为 `scope=contract_local,packages_from_wheel=13,resources_present=true,installed_verifier=passed,node_dependency_check=true`。这是CI wheel本地分发门，不冒充最终产品COPY安装或科研。实际pytest耗时仅单次观测，不声称性能承诺通过；Windows耗时较长的原因仍UNKNOWN。

最初 `gh run view --job ... --log` 因总Run仍in_progress返回日志暂不可用，原stderr保存在 `successor-linux-original.stderr`，没有重写为测试失败；随后只读官方 job日志API实际下载已结束的Linux日志为 `successor-linux-api-original.log`，exit0。一次运行中的Windows job日志查询返回HTTP404 BlobNotFound，原 `successor-windows-api-live-attempt.log` / `.stderr` 保留，未重复查询运行中的日志或把404当pytest RED。Run结束后实际下载完整原始日志为 **`successor-ci-original.log`**，exit0；完整精确headSha、Run/job/原step结果为 **`successor-ci-final.json`**。两个job原install/pytest/strict/build/SDK/wheel/distribution步骤均success，核心双平台适用门现已齐备。Handoff `msg_8cbe42ba9811` 已交主控实际数字、原日志和首RED不变事实。

主控随后验收 Q 最终 docs-only REPORT `49c0b3ad49f9fa1b5ad7b493ec05187e5b148503`（直接 docs REPORT `76af665511cb4b31662df0f698fcf631bb96419e` 为Qacb后继）。I 再核对 Qacb→49只改 `docs/tracks/r1-boundaries.md` 后，以显式 `[skip ci]` 的普通merge合入为 `8d51a7c35b01f0dc67ec75ac933803d7df6445d5`；相对冻结 b480非docs零差异，后继SOURCE身份不变。该docs merge和最终I docs REPORT在结果齐备后一起push，不触发另一完整CI。

原命令及差异证据保留为 `C:/r1i/i1003-core-1732/logs/merge-Q-repair-first.txt`、`merge-root-successor-first.txt`、`successor-ancestors.txt`、`successor-nondocs-delta.txt`、`successor-production-protection.txt`、`successor-source-push-first.txt`、`successor-source-remote.txt`、`successor-ci-first-list.json`、`successor-ci-first-jobs.json`、`merge-Q-final-report-first.txt`及`Q-report-source-protection.txt`。

本阶段不复验未改动的AOCI：第8.3节的A绝对路径限制及 I freshness/cognition NOT_VERIFIED继续适用。P仍被冻结，最终产品COPY/HTTP/UI完整回归、AT07/native科研/L2等均NOT_RUN；HostConfig直接调用链的主控说明留待最终installed产品阶段，不能提前称产品验证完成。B后继L2审查材料仅文档准备，不改变运行授权或本次受测源码。

同一 I 的**核心阶段**已完成普通精确合并、原双平台完整CI、首RED保留和docs-only报告。最终核心SOURCE为b480，最后docs-only I REPORT的完整SHA由Orca交付列出；分支仍为 `songconmaisaix31-design/morph-r1-integration-1003`。最终报告提交带 `[skip ci]`，同Q49的docs merge一起普通push；交付检查包含 `git diff --cached --check`、SOURCE→REPORT非docs零差异、全部来源祖先、远端exact与clean，原命令记录为 `final-git-delivery.log`。本次无I领域/测试修改，无新本机环境/服务/科研；适用核心门通过不提升为产品最终组合、AOCI跨checkout认知或全R1退出PASS。
