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

### 9.1 主控最后追加的 B docs-only 交接

初次CI结果报告 `24d0719b4a48e0b3814058342d8032318a75fb40` 已普通push且未生成新CI；交付前最后inbox的主控 `msg_f7845b80b998` 独立接受精确b480双平台工程门，并要求追加已验收的原B docs-only REPORT **`7f05cc795d2371f6b4d74656c25e8bc92e67db83`**（父 `456e55487bda7bb9112a5678399ebe2ee7d44c68`）后结算当前核心+docs阶段。

I 核对 B原REPORT5aeb→7f05只改 `docs/experiments/l2-poisson-review.md` 与 `docs/tracks/r1-experiments.md`，128行新增、无非docs差异；5aeb为7f05祖先。普通精确merge带 `[skip ci]`，无冲突，merge为 `0095ce658734c02d5cc249ddb20c3da3f2b4554a`；最终 b480→HEAD全部非docs零差异，原命令保存为 `merge-B-docs-final-first.txt`。随后仅追加本小节，再push最后 I docs-only REPORT，不新增或重跑CI。

B审查稿是 `question_prepared/reviewable_draft`，保留其18:09的CI观察身份；最终双平台通过以本报告第9节及原Run日志为准，不回写B文档的历史观察。Poisson问题、材料locator、正式调用链及待批准输入只作可审查准备，不提供完整候选实现或运行授权；材料身份来自原Owner/主控，不是I重新核验或正式导入。P human receipt/AOCI/finalpin、唯一最终产品回归、AT07、native科研和L2等仍NOT_RUN；当前核心+docs结算后I闲置，后续同Owner由主控另行接续。

## 10. 原唯一 I 的最终产品组合离线验收（2026-10-03）

本节为原 Owner、原树、原分支的后续产品阶段，Task `task_3a6652d6b5d6` / Dispatch `ctx_0d8a0826c9f7`。主控正式接纳原 P 业务组合后才安装和测试；不是第二集成者，也不重复第9节已通过的核心 CI 或 Owner 专项。此前核心 REPORT `1bce9f9f71c9a1c5e864263076ae879fcd67e31f` 的干净 HEAD 与全部历史报告、首失败保留。

### 10.1 受测身份与独立 COPY

| 身份 | 完整 Git SHA |
| --- | --- |
| 实际安装核心 SOURCE | **`b480fca1b10a0b6a9c93f0d1801d38f267662461`** |
| 实际安装最终产品 SOURCE | **`2b9bf73c93e732771ed3582f3bc7745ea8158b68`** |
| P 最终 docs-only REPORT | `c8d4197bac272cdf5f634bc7a56c87db19bfbebb` |
| P API SOURCE，产品祖先 | `67721aaa815e706c51e0f80a1d15ab71e34b6880` |
| F SOURCE，产品祖先 | `7bf17d195859a18960ee1ef933a920a286f73e61` |
| F REPORT，产品普通 merge 祖先 | `c08566edc492e92adfc4e24a9e8de1c18b859e02` |

I 实际核对上述 P/F 三个祖先、2b→c8 仅 `docs/tracks/r1-product.md`，P 远端分支精确 c8。产品 `CORE_SHA`、pyproject HTTPS VCS pin、uv.lock git source 和安装 `direct_url.vcs_info.commit_id/requested_revision` 均完整 b480；锁98记录，Docker SDK7.2.0。没有从 REPORT 选择运行来源，也没有安装原 P 的脏 AOCI WIP 树。

新短路径 **`C:/r1i/final-product-1855`** 在本轮开始时不存在。以命令局部 `core.autocrlf=false` 对两个精确 SOURCE 做 `git archive --format=tar`，原生 Python tarfile 解包，再经 `git ls-tree -r -z` / `git cat-file --batch` 逐文件比对原 blob：**核心720文件、产品161文件，全部字节相等，nlink1**。日志 `logs/archive-raw-git.json`；不用 Windows archive 的文本转换结果修补业务文件。

新 venv 为该目录下 `venv`，Python **3.13.13**；新 `uv-cache`、`npm-cache`、空私有 npm user/global config 和 COPY 安装，未复用 `C:/r1i/i1003-2239` 或 F 环境。原锁 `uv export --frozen --no-emit-project` 后精确 VCS 安装核心，产品原归档独立 `uv build --wheel`，wheel 再 `uv pip install --no-deps --link-mode copy`。首次 `uv pip check` **97 packages compatible**，添加独立 mypy1.20.2 的4个工具包后 **101 compatible**；后者不冒充原锁包数。

实际安装审计 `logs/installed-identity-first.json` 核对 **136核心Python、36产品Python、53产品资源** 全部原归档字节相等、均在新 site-packages、nlink1、无 editable，并确认只存在一个核心 distribution。产品 direct_url 如实为本轮 wheel URL 与 `archive_info:{}`，不手填 hash；实际 wheel SHA256 为 `1bdd52f08ee4bc55a0426762c5bd9fcda23c914ff3552ca9db57e18c9e41721a`。原 `setup-assets` / `doctor` 均通过，SDK schema1.14.0、本地 canonicalize/无效资产拒绝和注册输入就绪；其声明是 local_only / models_experiments_hub_called=false，不是科学运行。

为满足原测试已冻结的 native 配置解析器断言，仅在新 `native159` 私有目录通过 npm 官方包安装 `@openai/codex@0.159.0`，ignore-scripts；确认真实 vendor codex.exe 版本。只有本次 pytest 子进程 PATH 指向该私有 binary，原 parser subprocess 使用原测试创建的 secret-free CODEX_HOME，只运行版本及 `mcp get`，不请求模型、MCP服务或沙箱。父进程全局 PATH/HOME/auth/provider 未改。

### 10.2 一次完整产品门与类型身份

从本轮原产品归档 cwd 执行以下原完整命令，只有测试根加入 sys.path，生产模块保持安装来源；环境 `MORPH_FROZEN_ARCHIVE=.../product`、`MORPH_CORE_ARCHIVE=.../core`，BLAS/OMP/MKL线程1：

```text
C:/r1i/final-product-1855/venv/Scripts/python.exe -I -X utf8 -u -c "import sys,pytest; from pathlib import Path; sys.path.insert(0,str(Path.cwd())); raise SystemExit(pytest.main(sys.argv[1:]))" -q -rA --tb=short --basetemp C:/r1i/final-product-1855/full-product-first-tmp
```

**首次完整产品结果：256 PASS / 423.71s，exit0**；外层命令耗时428.762s。原 stdout/stderr合流字节为 `logs/full-product-first.log`，完整 argv/cwd/exit/耗时为 `logs/commands.jsonl`。没有完整门首 FAIL、没有第二遍完整门、没有 P28/F18/Q65 或旧专项复跑；旧222PASS/6FAIL与后续修复证据仍属第1–7节旧组合，不能代替本轮。

原 mypy1.20.2 flags `--follow-imports skip --ignore-missing-imports --check-untyped-defs`：**适用30源 PASS**；whole36源仍 **原10 errors / 6 files / exit1**，不是全包 strict green。对 guard、renewal、cases、checklist、install、auth 的十条逐文件、当前/原行映射、类别、完整消息及 a25/9e 原 Git 表达式比较均相同，新增错误0。基准 `a25aa40bb0f5259799641fee378d09ccc5887054` 与旧受测 `9e2718789cb67f8b829207e17dac4d95a88e59c9` 只读获取源表达式与旧身份文件，不运行旧测试。证据 `product-mypy-whole-first.log`、`product-mypy-applicable-first.log`、`product-type-identities-first.json`。

### 10.3 原前端及实际安装 HTTP/UI

新私有 `ui-build` 仅复制本轮原归档；新 npm cache、ignore-scripts 的原 `npm ci` 与 `npm run build` 首次均 PASS。产出的 **3静态文件与2b SOURCE逐字节相等**，不替换受测安装资源。原 Playwright `tests/ui/playwright.config.mjs`、workers1/retries0、msedge，desktop1366×900/narrow390×844：**126 PASS / 8 SKIP**，原输出1.5m、命令100.003s。8个条件 skip 为原 installed observers 未提供 origin 的明确 NOT_RUN；它们在下表正式安装观察中各执行一次，未回写原 fixture 输出。

以下均为本轮已安装包的正式 `morph-research serve --config <本轮私有JSON> --port <新loopback端口>`，无 route interception，串行新 owned server / 原 `tests/ui/r1-installed.config.mjs`，workers1/retries0、同两视窗。server/browser PID加原 handle CreationFileTime 入日志；cleanup只关闭自己存活的 Popen 树，均 exit0；serve被有意关闭后的exit1如实记录，不称自主正常退出。

| 原观察 | 首次原浏览器结果 | 实际来源与范围 |
| --- | --- | --- |
| 输入/资料/意见/envelope 三页 | **2 PASS / 6.1s** | 新断开后端配置；每视窗仅原4个产品登记POST，未抓取example.invalid资料、未批准科研envelope或执行科学 |
| member sessions / 输出 / 当前context | **2 PASS / 6.8s** | 本轮完整pytest留下的 `test_actual_http_sessions_bind*/serve.json`；项目p1、两成员/不同invocation/session精确闭合，仅GET/HEAD，mock/unknown保持原事实 |
| 支持/复核/贡献/消费与采用三页 | **2 PASS / 34.3s** | 本轮 `test_configured_generated_revi0/serve.json`，空间b×32，原mock持久记录；GET只读，不重发实验 |
| 反证/贡献/无采用 | **2 PASS / 10.2s** | 本轮 `test_configured_generated_revi1/serve.json`；succeeded/refuted/accepted独立显示，adoption_receipts为空，不由接受贡献推实际采用 |

四类 **8 PASS** 的原断言未改、没有浏览器重跑。`logs/ui-{input,sessions,support,refutation}-observer-first.log` 和对应 `*-command-first.json` 保存原命令、origin、fixture、进程身份、前后快照与清理。原截图位于 `ui-*-first/`；I查看了实际输入desktop、当前context narrow、反证narrow截图，仅作为机器页面观察，不是独立人类理解或 AOCI receipt。

会话前后完整 DTO 的离线比较差异0；unknown catalog仅新GET读取时间 `observed_at` 从1791026419.1448333变1791026426.8383627，其全部其他字段相同：state/activity_state unknown、provenance null、finished_at null。原fixture文件无变/无新增、SQLite表计数相同。支持/反证的**完整 DTO均前后相同**，持久文件字节/表计数无变，不能仅由backend binding相等推所有研究状态相同。

原会话观察已实际读取两成员context。为另留原HTTP原文，按主控追加指示补 investigator context/output 的独立GET，再仅补此前未保存的 **critic context单次GET**，未重跑浏览器或已采GET。`sessions-extra-get-investigator-context.json` / `critic-context-get-critic-context.json` 均 current_local_view，identity仍p1与对应member，historical_prompt/observed_input unknown。补GET前后**全部持久文件字节、mtime_ns和SQLite计数相同**，证据 `sessions-extra-get-command.json` / `critic-context-get-command.json`。这些是当前获准局部context，不代表历史完整原生prompt。

### 10.4 私有观察工具首错误保持原身份

本轮原产品 pytest、原 build 与原浏览器断言没有首 FAIL；以下额外私有取证工具首错误全部保留，未转换成领域修复或抹除失败：

- 安装审计首次假定本地 wheel 的 `archive_info.hashes` 必有，得到 `KeyError: hashes`；真实原 metadata为空archive_info。原工具输出逐字副本 `audit-helper-first-tool-output.txt` 明示是tool输出副本，后按真实URL、独立wheel字节与实际安装资源核对，不修改 direct_url。
- 类型身份工具首次仅按文件/消息匹配，auth两处同名config_args导致歧义断言；`type-identity-comparison-first.log`保留。随后加入原当前行身份，只重分析原mypy输出与Git表达式，不重跑mypy；修正分析为原十条身份相同。
- sessions追加工具首次比较含实时observed_at的完整unknown条目，exit1 `unknown record changed`；`ui-sessions-helper-first.log`、原command/raw均保留。源码r1_sessions.py:193明确time.time()，离线逐字段只该时间不同，完整DTO差异0。`ui-sessions-complete-facts-reanalysis.json`保留全部差异与持久事实；没有第二遍sessions浏览器。
- 补GET工具额外假定unknown输出必须 `complete=false`，首exit1保留于 `sessions-extra-get-helper.log`。真实raw为complete=true/has_more=false/partial_line=false；原r1_sessions.py:399定义的是当前受限文件窗口读尽，**不是原生进程EOF、活动确认或科学成功**。原ResearchSessions.jsx:100–112不用complete推完成或停止follow，仍定时只读GET；state/activity/provenance未知事实未变。主控 `msg_6b46c3b519a7` 只读确认该原接口语义，接纳为I工具误断言而非P/F缺陷；`unknown-window-complete-reanalysis.json`仅分析已采raw，没有重发GET或改原测试/模块。

私有 observer 的两个源码预像按已记录apply_patch精确转变重建为 `observe_installed.{input,sessions}-first-reconstructed.py`，`helper-version-provenance.txt`明确它们**不是当时预先保存的hash回执**；所有原失败输出、command JSON、HTTP响应仍原样。没有因为私有工具错误重新运行已绿完整门、浏览器或Owner专项。

### 10.5 普通文档闭合与真实限制

结果齐备后普通精确合入 C docs-only REPORT `1e2338a4de6bea019b0efe983c7a69a54b22b73e`（仅本轨报告27行），merge **`a8dcee4dc39fc79442ac25bad46d50ecd31627e4`**；再合入主控治理 **`96fbefd904826b563dc1c78a181fd424b7490701`**，merge **`3392d9ddfe1712c34a0f2f47b22970ba241a42b7`**。两次均无冲突、[skip ci]，C/root各远端精确SHA已核对。根R1_PLAN/R1_STATUS/R1_ACCEPTANCE三个blob与主控96完全一致，I没有独立重写治理。相对受测b480的全部非docs差异0，来源和断言未变，不产生新SOURCE或新核心CI。

随后仅追加本节，普通commit/push `[skip ci]` 到原 `songconmaisaix31-design/morph-r1-integration-1003`。本阶段 I docs-only REPORT 的**最终完整SHA、remote exact、clean与core/productSOURCE**在push后写入私有 **`C:/r1i/final-product-1855/FINAL_REPORT.md`** / `logs/git-final-closeout.json` 并通过原Dispatch交主控；不在提交内自嵌该提交SHA。第1–9节历史内容保留。

本阶段最终组合离线工程验收完成；whole原十项类型债仍RED身份，不称全包strict通过。核心Windows1745/15skip、Linux1744/16skip、strict140/build/SDK/wheel证据仅沿用已接纳的第9节原CI，没有复跑。P15正式AOCI Entry/维护、真实human receipt仍NOT_VERIFIED；撤回可选auto并恢复legacy是原P/主控事实，不把聊天全权限或preview变receipt。本轮不维护跨路径AOCI、不复制receipt/reinit/手改baseline/安装业务源码；A核心十源仍A-path-bound，I跨checkout认知freshness NOT_VERIFIED。C11单次隔离与三个全局依赖保留仅沿用原Owner/主控证据，I不改全局环境或清理其他进程。

本轮运行与观察属 contract_local/mock及真实本机installed接口工程证据；**task_live NOT_RUN，实际用量/费用/Token节省UNKNOWN**。未创建真实native science claim、科研候选沙箱或执行模型/科学请求；没有Docker/WSL、外部服务启动、AT07/L2、main/tag/deploy或外发。本机正式serve只用于用户已授权产品离线观察。AT07仍须本阶段后单独授权的实际无害隔离，真实隔离通过后再谈一次L2；人工理解与性能最优不由本轮自动验收产生。

## 11. 原唯一 I 的 B 实际代码后继累计工程与产品离线收口（2026-10-03）

本轮仍为原树、原分支、原 Owner，Task `task_33b99bbe70e8` / Dispatch `ctx_154fc9202fc1`；起点为已接纳且干净的 I REPORT `a67c0af1e27bea08a8e2ce426337f0608e62f216`。先 raw Git 读取主控 `381d955ea62ec99505263ecf7ed20adbc1b74e95` 的20:18决定、AGENTS与现行Spec。没有第二集成者、I领域/原测试/锁修改、cherry-pick、force push或人工治理改写。

### 11.1 普通精确来源与唯一实际运行组合

| 身份 | 完整 SHA |
| --- | --- |
| 原已通过核心 baseline | `b480fca1b10a0b6a9c93f0d1801d38f267662461` |
| B实际 SOURCE / REPORT | `fc866465aa52a3f09773bc79a0fab95bceedc3d9` / `f008e281e15d25c8950d7ddd05450fbe398653f1` |
| Q原测试 SOURCE / REPORT | `f2b81cd9c0e0623c224b0501580a19e3fc1d37da` / `f261c78a8181a4ce82a74bb41395cb35ee1e7b21` |
| A本轮仅docs REPORT，actual代码仍b480 | `1c40129e81362686fcba968e57809582c22dabfc` |
| 第一累计核心 SOURCE，首RED保留 | `e635b8ab3e79529403b527892e75ffb29674af0a` |
| Q两行平台fixture修复 SOURCE / docs REPORT | `3aa95d94828449fd92e6bb4fe6385178f3dac971` / `c4de24734f3f8d85446265d39ed6365a92e0d3ee` |
| **最终实际核心 SOURCE** | **`15de4959646df264530b978dfde9152552b9a76b`** |
| **实际产品运行 SOURCE** / 固定pin docs REPORT | **`c84e49bd8e926f50d2c057793e8789cf137b310a`** / `2a35b9aaa6769d8334017d5526c32ae52952a2ec` |
| 产品仅客户端测试后继 TESTSOURCE / docs REPORT | `756d5069e7739089f0e5ba1c33eebfb2657b03f0` / `eca3fd48c33fc602f1ddb3f45d91bd88e17b941b` |

普通merge B f008、Q f261、A 1c、root381形成e635；首RED退原Q后普通merge Q3aa95、root `fec6f1e29a2c07f1375d481f8cbf7e71cc482b77` 形成15de。两次实际代码集成SOURCE均普通push、远端exact/clean、最终commit无skip-ci，及时fullSHA Handoff原P；没有重跑失败原run。相对b480的全部非docs差异精确仅 `orchestration/experiments/at07_live.py`、`tests/experiments/test_at07.py` 与 `tests/boundary_review/test_at07_route_boundary.py`，分别等于B/Q原blob；全部指定业务来源祖先核对。e635→15de生产/依赖/锁零delta，只有Q平台夹具两行和主控治理。

最终 `poetry.lock` 原Git字节与b480相同，SHA256 **`87b335297f95b7bf72514691cb990db0d6441316be90c8cb726b016b9af025eb`**；不是从B旧锁或本机行尾hash填。15de的正式 `deploy/opensandbox/at07.config.toml` 原Git归档 **1013字节 / SHA256 `438fe04be51d07188b6bc4b26fbd85c2e7ce28dc02e31ed3af2a4cf27f3c0b79`**，I精准installed测试用它，不用CRLF工作树副本。workflow与baseline原字节相同。原命令/merge/祖先/remote事实见 `C:/r1i/successor-2018/logs/source-freeze-first.json` 与 `r2/logs/source-freeze-first.json`、`source-push-first.json`、两阶段merge原日志。

原P接纳15de后仅三pin普通更新c84；CORE_SHA、pyproject VCS、uv.lock及installed commit_id/requested_revision均完整15de。c84相对原2b的生产变化仅该coreSHA，原F SOURCE `7bf17d195859a18960ee1ef933a920a286f73e61` / REPORT `c08566edc492e92adfc4e24a9e8de1c18b859e02`、P API SOURCE `67721aaa815e706c51e0f80a1d15ab71e34b6880`、developer SOURCE `c7711f807e50ea4101ec6af231351e5c1037add6` / REPORT `94c7fc779770e8847f6366bac1a0a3dcaa134332`均为原普通祖先。六个developer文件实际原字节保持；不再次guard/reinit/复制receipt或手写baseline。

### 11.2 原双平台工程门及首RED

e635原自动Run **37122569886 / attempt1**：Linux **1823 PASS / 1 FAIL / 16 SKIP / 425.33s，pytest exit1**；Windows **CANCELLED**，后续type/build/SDK/wheel未完成。唯一失败为Q `test_untrusted_private_config_directory_cannot_reach_cli[junction]`，Linux模拟win32时缺 `stat.IO_REPARSE_TAG_MOUNT_POINT`。原Q仅补fixture常量和注释，未改no_links、拒绝tuple、CLI零调用或任何生产代码；原失败raw和Owner定向修复身份保留。I没有修领域、改原assertion、cancel或rerun该run。

15de原自动Run **37123370202 / attempt1**，head精确15de，两个job和全部原steps **SUCCESS**：

| 平台 | 原完整pytest | 原其他完整工程门 |
| --- | --- | --- |
| Windows，job111203705329 | **1825 PASS / 15 SKIP / 75 warnings / 1820.43s** | strict140、sdist/wheel、SDK schema1.14.0、wheel13packages/resources、installed_verifier与node_dependency_check全部通过 |
| Linux，job111203705442 | **1824 PASS / 16 SKIP / 75 warnings / 399.47s** | 同一原workflow的上述各门全部通过 |

原命令是 `uv tool run poetry run python -m pytest -q`、`python tools/typecheck.py`、`python -m build`、`npm run check:sdk`、`uv pip install --no-deps --target tools/.wheel-site ...whl` 与 `python -I tools/check_distribution.py --check-node`。原workflow未改，I没有本机复制完整核心门或绿CI重跑。第一run fullraw在 `logs/ci-full-first.log`，最终run fullraw在 `r2/logs/ci-full-first.log`；各自finalrun/jobs与capture argv/exit/time同时保存。SDK/wheel验证范围仍contract_local，published=false。

### 11.3 全新私有 COPY、实际字节与受影响installed验证

首次 `C:/r1i/successor-2018` 新e635/8c私有安装自然完成，尚未开启产品whole门就遇CI首RED；其env/cache/raw原样保留。最终组合使用全新独立 **`C:/r1i/successor-2018/r2`** COPY/env/cache/npm私有config；未复用旧 `i1003-2239`、F或1855环境。子进程BLAS/OMP/MKL1；typed argv/shell=False、process-local Git autocrlf=false、rawGit cat-file batch比较，不改global pip/auth/HOME/PATH/provider/hostconfig。

安装前两个原SOURCE `git archive` / 原生tarfile后逐blob比较：**core722文件、product165文件，全部字节相等/nlink1**。原锁98记录，`uv export --frozen --no-emit-project`，核心精确GitVCS noneditable COPY；产品独立wheel再 `uv pip install --no-deps --link-mode copy`。原locked兼容检查 **97 packages**；另加mypy1.20.2四工具包后 **101 compatible**。独立wheelSHA256 **`bc7f6a69a3268072b96ba463be52eb18a60103b2d11f16ce2a54575dd34379e0`**；product direct_url是真实本轮wheelURL/archive_info{}，不补metadata hash。

安装审计首次通过：**136 core Python**、原**13 packages**实际从新site-packages导入、**64 core原非Python资源**；产品 **53总生产文件 = 36 Python + 17非Python资源**，不是另有53个非Python文件。全部源归档与actual installed字节相同/nlink1、单core distribution、无editable；三pin与VCS commit_id/requested_revision全15de。原setup-assets/doctor均exit0：SDK1.14.0、ready_local/local_only、models_experiments_hub_called=false。

I仅从实际installed模块对两个受影响原testfiles执行一次，importlib模式、开始/结束均核对生产模块路径属于新venv：**106 PASS / 1 warning / 0.84s，exit0，外层7.022s**。Q_AT07_SERVER_CONFIG指向最终15de rawGit档案。原tests保留拦截process/probe/network边界，非真实AT07/Engine隔离。

仅为原冻结parser断言在r2私有npm安装官方Codex0.159.0，ignore-scripts、version验证；pytest仅子进程PATH指定vendor binary，原secret-free临时CODEX_HOME只version/mcp-get解析，不调用模型。证据 `r2/logs/archive-raw-git.json`、`installed-identity-first.json`、`installed-core-boundaries-first.log`、`commands.jsonl`及原各install/doctor日志。

### 11.4 一次完整产品首RED与原Owner测试窗口修正

原完整命令从r2原产品归档cwd、生产模块用installed：

```text
C:/r1i/successor-2018/r2/venv/Scripts/python.exe -I -X utf8 -u -c "import sys,pytest; from pathlib import Path; sys.path.insert(0,str(Path.cwd())); raise SystemExit(pytest.main(sys.argv[1:]))" -q -rA --tb=short --basetemp C:/r1i/successor-2018/r2/full-product-first-tmp
```

**首次完整结果：255 PASS / 1 FAIL / 539.16s，实际child exit1，外层542.527s**。唯一四phase/三页事实节点经原 `tests/test_web.py` urlopen(timeout15) 得到TimeoutError；未中断或再开whole，不用旧256代替。原short fixture实际在sys.prefix.parent/fixtures随机12位目录，原pytest tmp_path重定向后为空不表示未有后台效果。原P正式时间核对失败为**replication**：原client15s超时；晚到mock记录不使原HTTP/三页断言通过。server request→response-marker25.0316s不是完整HTTP客户端响应测量；native mock wall0.01245s不是真实科学性能。

原P新私有同原15s/原asserts复现 **1 FAIL / 53.43s**，instrumented真实inert child13.684s/run_from_ui14.191s后还有DTO投影。主控批准最小**测试工具**后继756：request helper仅加可选timeout默认15，只有四phase首POST显式900s，等待既有角色900s操作预算；业务、runner预算、409、secret、mock/task_live、全部事实断言未改，全部GET/其余255仍默认15。不是用户新增15s性能承诺的达标证明，也不吞真实timeout。P首RED及P修后单node1PASS72.29s保留为原Owner身份，不代I。

I以756做新私有rawGit165文件archive，生产53文件与已安装c84逐字节相同/nlink1，三pin不变，两文件所有原assert AST相同。**同15de+c84现装**仅该节点独立一次：**1 PASS / 75.32s，exit0，外层77.785s**，四phase及原三页/authority/secret/mock断言完整执行。原命令与raw在 `r2/test-repair/logs/independent-target-command-first.json` / `independent-target-first.log`；源差异/生产字节与原断言在 `test-source-diff-first.patch`、`test-source-identity-first.json`、`original-assertions-first.json`。没有重装、whole255/type/UI/浏览器/绿核心CI复跑；**不写whole256green**。原完整255/1与新测试SOURCE单node green分开列出。

原mypy1.20.2 flags `--follow-imports skip --ignore-missing-imports --check-untyped-defs`：**适用30源 PASS/exit0**；whole36仍 **10原错误/6文件/exit1**。逐文件/当前与原行映射/类别/消息/a25与9e原Git表达式identity相同，新增0；不称全包strict green。原whole/applicable stdout、actual argv/exit、比较在 `r2/logs/product-mypy-*-first.log` / `product-type-identities-first.json`。这些是当前组合的实测，后续test-only来源生产零delta才保持适用范围。

### 11.5 UI范围沿用、有界预览及私有工具首误判

c84/756对原2b frontend、UI tests及生产static原Git零delta；新安装资源额外实际逐字节相同。**只沿用前组合b480+2b/a67范围**：build14.91s、UI126PASS/8SKIP与原installed input/session/support/refute8PASS/两视窗/原截图raw；本轮没有新build/browser或新session/context验收，旧PASS不伪作本轮全产品结果。未知native事实和当前output窗口complete不转成进程EOF/科学完成。

按主控只读预览澄清，本轮用原observe_installed input配置方式提供**新installed**空私有断开页面 `http://127.0.0.1:51702/`，20:47:17–20:57:19 CST；allow_native_choicefalse、research_connections0、双auth/paidpending、sandbox127.0.0.1:1/keynull，child仅移除sandboxkey环境，不造科学记录/历史prompt/新权限。I只GET根HTML、不POST/浏览器重测；root另GET200/title事实已回报，**human understanding NOT_VERIFIED**。ownedPID54784/CreationFileTime134355052374425360，原截止后核对原handle身份只清理该Popen树，cleanup exit0，serve被有意关闭exit1如实记；wrapperexit0/604.739s。无延续/重开。原config/PID/source/argv/HTML/cleanup见 `r2/logs/preview-ready-first.json`、`preview-close-first.json`及raw。

私有工具/分析首误判原样保留并单独更正，未变领域失败或重跑whole：source检查首次误把684新增ownreport也算三pin，原assertion exit1/preimage/output副本保留，后按业务范围只三pin原字节核验；一次handoff误写product档案168，已按原archive记录纠正165；I先从旧inheritance缺launch推断失败阶段，原P时序证明该目录属于先前别案，已明确更正replication，原 `product-first-red-actual-fixtures.json` 不覆写，追加phase-correction与timing-qualification。原首whole/raw和真实exit1始终不变，晚到mock outcome不修饰原测试客户观察。

### 11.6 文档闭合与真实限制

结果齐备后普通精确合入Q docs REPORT `c4de24734f3f8d85446265d39ed6365a92e0d3ee`（merge `1249c63ed3e0ac93d836f6e6fa7ec79605420d98`）、主控治理 `bbd37668b38f8860c9b00d6909d74dcaf588a152`（merge `60115631219a7e5d26bda53eb92324872d195c78`）与B最终两docs REPORT `e40f7879f9598405486587dad936e9884ead15bc`（merge `09627694869d7e74a57a06a5268b5c1fe40cb053`），均无冲突/[skip ci]。Q/B原blob、根PLAN/STATUS/ACCEPTANCE三个blob与上述精确Owner/主控提交相同，I未独立改治理。最终B包准备真实AT07路线与同ID retained_stopped批准选项，实际Engine/target/probe/资源清理仍NOT_RUN；它不改变冻结业务源码或当前科学运行权限。全部SOURCE15de→REPORT非docs差异0；原merge argv/exit/commit/delta保存在 `r2/logs/merge-final-{Q,root,B}-first.log` / JSON。随后仅追加本节，普通commit/push [skip ci]。

本轮完成原SOURCE累计普通集成、原双平台全部工程门、新COPY/installed来源、一次完整离线首RED与原Owner测试工具修复后独立精准复验；结果按上述层级保留，不将255/1合写成whole256green。I最终docs-only REPORT完整SHA/remoteexact/clean/core/product/TESTSOURCE在push后保存 `C:/r1i/successor-2018/FINAL_REPORT.md` 并交原Dispatch，不在提交内自嵌本提交SHA。

A本轮只有docs/条件与成本覆盖限制，无新A源码修复或全FR13覆盖承诺；P六developer配置字节沿用不等于15语义Entry维护完成，P/A human receipt、I跨checkoutAOCI freshness/cognition仍NOT_VERIFIED。不复制receipt/reinit/reset/手写baseline或假Token节省。本轮仅contract_local/mock与实际本机installed离线工程证据，**task_live/真实AT07/native科学/候选实际执行/L2 NOT_RUN；实际费用/用量/Token节省UNKNOWN**。时长仅原实测样本，不证明性能最优。B包是待单独授权的可审查路线，未启动Engine/Docker/WSL/服务key/SDK真实create、候选/模型/科学调用、外发、main/tag/deploy；实际无害隔离全部通过之后才可能一次另授权L2。人工理解未回不PASS，不由本轮机器门补出新认知或运行权限。

## 12. 原唯一 I 的 API 1.54 后继累计工程与最终离线验收（2026-10-03）

原 Owner、树、分支保持；本次有效 Task `task_6d13ed8377e3` / Dispatch `ctx_2b9faf05e09a` / terminal `term_cc6a6c31-ae52-4fcf-a6f1-185db592c6b4`。旧 `ctx_34ec9acbe03a` 的 agent_readiness 首 timeout/未注入失败保留，旧handle/cap未用于完成。本轮起点是原已接受且clean的 REPORT `c5cdfc89e5a1e43ab49f9afc33a05a53d887e8ab`；先读本树AGENTS、用户Spec及root `ab663f6392c9499becea2f7c61bee6421a27fab3` 顶部22:09决定。没有新集成者、I领域/测试/锁/profile/workflow改动或治理手写。

### 12.1 实际 SOURCE、普通祖先与安装身份

| 身份 | 完整 SHA |
| --- | --- |
| 前组合实际核心 | `15de4959646df264530b978dfde9152552b9a76b` |
| B API实际 SOURCE / 首docs REPORT | `c3a905eaf79a869dffb5960da9c4afee1dc63c3e` / `08f2315dbc6a2396c4b55dd07a6d60f6fd115dfa` |
| **本轮唯一累计核心 SOURCE** | **`82201af4d3b369da827f6f22ff1d9c6b608c0108`** |
| **产品实际运行 SOURCE** / 首pin docs REPORT | **`d5d387a6f5c1778dffdd860986843826420edf5e`** / `0e936ceee4ff1e8aca1d2c8d3f0a77ae753e3639` |
| 原产品客户端测试来源 | `756d5069e7739089f0e5ba1c33eebfb2657b03f0`，已为d5祖先 |
| **产品最小测试修复 SOURCE** / 最终docs REPORT | **`c0dd0b9a9071f72d67f690bfe084cd60f30b13f4`** / `cbaf3dc8411575ec16f52121bf7e8351d887b54c` |

普通精确合入B c3 SOURCE、08 REPORT与root ab；最终含代码集成commit822无skip-ci，普通push后核远端exact/clean，立即fullSHA Handoff给root供原P repin。原SOURCE祖先、Owner blob与范围检查见 `C:/r1i/successor-2220/logs/source-freeze-first.json` 及 `merge-*-first`、`source-push-first`、`source-remote-first` 原记录。

相对15de/原I c5的非docs差异精确仅四个B原blob：`orchestration/experiments/generated.py` 的一行 `api_version: Literal["1.52", "1.54"] = "1.52"`；三个既有文件 `tests/experiments/{test_at07,test_frozen_export,test_generated_configuration}.py`。reader/export/at07_live/registry、锁、profile、compose与workflow原字节未变。原 `poetry.lock` SHA256仍 **`87b335297f95b7bf72514691cb990db0d6441316be90c8cb726b016b9af025eb`**；rawGit正式profile1013字节/SHA256 **`438fe04be51d07188b6bc4b26fbd85c2e7ce28dc02e31ed3af2a4cf27f3c0b79`**，默认/原绑定仍1.52。接受显式1.54并不证明真实Engine API绑定或隔离。

P d5只更新原三pin文件到822。c0dd仅两个原测试文件 initial claim从50ms改为600s，原renew50ms、真实sleep60ms、active600、unknown预算/并发/全部原assert AST不变；相对d5生产、UI、三pin、锁零delta。最终运行仍安装d5 wheel，测试原Git取c0dd；不从P docsREPORT取pin。P cbaf已在**原P仓库**核SOURCE祖先、own report-only、远端exact/clean，跨仓仅读证，不merge到core。

新私有主根 `C:/r1i/successor-2220/`：rawGit/core723文件、product165文件全部原blob/nlink1相等；全新env/cache，GitVCS非editable COPY核心822，独立产品wheel再no-deps COPY安装。原锁98记录、97包兼容，另加mypy1.20.2四工具包后101包兼容。wheel SHA256 **`bac6e0ab9e4d683cd90b560113c8bb7ee9788d8f0e4234a7f2550ffbe744d961`**；product direct_url实际为本轮wheelURL/archive_info{}，没有手补hash。

实际installed核对 **136 core Python、13 packages实际import、新venv prefix、64原core非Python资源**；产品 **53总生产文件=36 Python+17资源**。单core distribution、无editable、nlink1、rawGit字节相等，CORE_SHA/pyproject/uv.lock与core direct_url commit_id/requested_revision全822。原setup-assets与doctor首exit0（32.405s/12.385s），SDK1.14/ready_local/local_only/models_experiments_hub_called=false。证据 `logs/archive-raw-git.json`、`installed-identity-first.json`、`commands.jsonl`。

### 12.2 原自动 CI 与受影响 installed 门

仅本SOURCE原自动 `.github/workflows/check.yml` **Run37129204576 / attempt1 / head822 / push**；两job所有原步骤success，没有cancel/replay/rerun，也没有本机whole核心副本：

| 原job | pytest首次结果 | 原严格/构建门 |
| --- | --- | --- |
| Windows111220744248 | **1839 PASS / 15 SKIP / 75warnings / 1445.58s** | strict140、sdist/wheel、SDK1.14、wheel13包/资源/installed verifier/node全部PASS |
| Linux111220744098 | **1838 PASS / 16 SKIP / 75warnings / 492.89s** | 同上全部PASS |

原run/job JSON、actual收集命令与完整raw见 `logs/ci-final-first.json`、`ci-final-jobs-first.json`、`ci-full-first.log`、`ci-job-111220744{098,248}-first.log`、`ci-summary-first.json`。旧15de Run37123370202及所有历史首RED不重跑、不覆盖。

新installed仅B受影响三既有文件独立一次：**132 PASS / 1warning / 1.17s，exit0，外层8.663s**。原命令以newvenv `python -I -X utf8`、importlib模式、`-c core/pyproject.toml`，执行上述三文件，前后核模块来自installed；profile指向rawGit档案。原正负控制含显式1.54、legacy1.52、跨绑定拒绝与mockSDK/read transport；`installed-api154-observation-from-first-raw.json`只分析同一次raw，没有额外request。属于 **contract_local + 实际installed API配置调用工程观察**，非真实Engine/SDKcreate。B Owner原首6FAIL/29PASS/97deselected、修后131PASS/1FAIL漏mock provenance、修单项1PASS/1.69s、strict1source保留为Owner身份，不把它们写成B完整132重跑。

### 12.3 一次完整产品首RED、Owner修复与独立精准补验

本轮唯一完整产品命令，cwd为主根原product归档：

```text
C:/r1i/successor-2220/venv/Scripts/python.exe -I -X utf8 -u -c "import sys,pytest; from pathlib import Path; sys.path.insert(0,str(Path.cwd())); raise SystemExit(pytest.main(sys.argv[1:]))" -q -rA --tb=short --basetemp C:/r1i/successor-2220/full-product-first-tmp
```

**首次完整：254 PASS / 2 FAIL / 517.11s，child exit1，外层520.539s**。wrapper允许pytest exit1而返回0，不能当pytest PASS。原日志 `logs/full-product-first.log`、command JSONL和首F独立partial保留；具体原事实与限制见 `FIRST_RED.md` / `logs/product-first-RED-fixture-facts.json`，没有第二次whole。

1. 原并发 `test_simultaneous_real_requests_and_refresh_have_only_one_native_boundary` line168实际三409，原断言期待200/409/409。原fx01473a14唯一child LeaseLost/not_completed/exit2，与ready/interrupt/首次F时点相符，但fixture未编码nodeid，关联如实为证据推断；原HTTP三响应正文未保存，不重构。
2. 原 `test_unknown_science_hold_and_cumulative_budget_are_original_core` 的 interrupted_fixture renew50ms得到LeaseLost。唯一原无observation/无renewed的50ms claimed author token1、updated1791038553.6987135/expiry1791038553.7487135，精确attempted renew时刻MISSING。原DB+WAL只读字节复制，仅copy用SQLite mode=ro/query_only，原size/mtime/hash前后相等。

root退原P最小测试窗口修复c0dd，不I patch或弱化断言。P先instrumented私有诊断 **7PASS/35.54s** 只diagnostic；随后全新prefix、原Git未instrumented helper的正式 **7PASS/1warning/27.14s，外层33.824s**，原raw `C:/r1p/red-82201-ctx_d683c5c884de/logs/exact-targeted-first.log`。正式与诊断分列，不替I独立门。

I用全新短根 **`C:/r1i/i2220r/`**、新COPY/env/cache与未改c0dd rawGit测试，只两个原失败nodes独立一次：**1 PASS / 1 FAIL / 22.31s，exit1，外层27.799s**。预算node通过；并发仍三409，但新fx5b51d241原child为 **BridgeError/not_completed**，不是旧LeaseLost：PID58884/Creation15:05:04.003361Z/exit2；response preflight_rejected/unknown，author available/token0/无claim-renew、无native-boundary launch。原Node细stderr/error code未由CLI保存，明确 **MISSING**，不得用后续diagnostic伪作首次stderr。原log/command与只读copy `logs/bridge-first-facts.json` / `bridge-first-readonly-snapshot/` 全保留。

这个新prefix准备时遗漏原入口必需的Node SDK安装前提，是I工具准备错误。actual newsite无gep-sdk/ajv/ajv-formats/node_modules/setup receipt；原2220与P正式copy存在。原runner在probe/spawn前先doctor，原asset_bridge ESM必须导入这些包；生产字节相等并不证明运行依赖就绪。root明确授权仅新prefix复用既有 `morph-research setup-assets`，没有手搬Node模块、改桥/生产/断言/锁或增加新SOURCE。

该新prefix首次原setup **exit0/5.428s**，原包内npm manifests逐字节相同，locked npm ci/ignore-scripts仅7包、SDK1.14，原managed bridge/product installed bytes/mtime不变；原既有setup自带一次local canonicalize/validate正负smoke，models_experiments_hub_called=false。actualargv/原receipt见 `logs/new-prefix-sdk-setup-first-command.json`、`sdk-prerequisite-installed-facts.json`。受控child_environment使用新prefix内临时home/cache，没有全局配置变更。

随后只剩并发唯一node环境补齐后一次：**1 PASS / 7.68s，exit0，外层10.461s**，raw `logs/concurrent-after-sdk-prerequisite-first.log` / command JSON。已PASS预算不再跑、无whole/types/UI/CI/132重复。新fx55b6c5a2 ownedchild57620/Creation15:11:03.176733Z/exit0闭合；actual fixture counters native/auth/scientific/sandbox/backend全0、substitute_spawns1，原cancel returns true/false，无cancel error。原BridgeError fixture全部size/mtime/hash在补齐和补验后仍相等；`logs/final-target-and-product-report-facts.json`留精确SOURCE/REPORT/remote与层级。实际HTTP/runner/parser/cancel已执行，spawn明确mock，**不声称whole256green、真实产品科研e2e或task_live**。

### 12.4 类型债、UI沿用与私有工具首错误

原mypy1.20.2参数 `--follow-imports skip --ignore-missing-imports --check-untyped-defs`：**适用30源PASS/exit0/2.983s**；whole36仍 **10原错误/6文件/exit1/5.312s**。逐file/原当前行映射/类别/message/a25与9e原Git表达式核身份相同、新增0；不是仅count相同，不称whole strict green。原stdout/argv见 `logs/product-mypy-*-first.log` / `commands.jsonl`，身份比较 `product-type-identities-first.json`。

d5/c0dd对原2b的frontend/UI测试和static生产字节零delta，六portable dev文件原字节保持，新installed资源实际相等。因此仅按原范围沿用b480+2b/a67的 **build14.91s、UI126PASS/8SKIP、installed input/session/context/support/refute8条两视窗观察**；不是本轮新browser/build/preview/人工理解。新实际入口与API配置证据为本节installed原测试/HTTP补验，不以purepin/docs重绿UI；unknown/complete窗口事实不转EOF/科学成功。

新2220私有parser helper首次替换漏Windows反斜线，ROOT误指旧r2，原旧log exclusive `xb` 在subprocess.run之前抛FileExistsError。原工具输出逐字副本 `logs/parser-helper-first-tool-output-copy.txt`、helper首preimage、path correction/effects analysis保留；只修新helper后全新2220 npm官方Codex0.159/version成功，原测试仅version/mcp-get解析，无模型。控制流证明首失败未启动旧命令/写旧log/env/cache；没有旧树整体before snapshot，**不宣称整个旧树前后字节相等**。原旧mtime/hash与局部观察见 `private-path-failure-effects-analysis.json`。新BridgeError缺前提错误与原领域/测试RED分列，均未改历史。

### 12.5 普通文档收口与真实剩余边界

精确普通合入Q docs `1fb5f3dc6e4d9eb60a2df4be22819c97bd01d91c`、B两docs `6ea5e5dd81bdf53e33f46beed74f7382a804efaf`、C纠正后docs `61101810cb3e2425347bb1d3e38cb34759ddaf09`、root治理 `09c52988390ba4eace08f2eb4e3592682c8b15a2`；四merge分别 `1f1e97229d4893f124000c75eb5a2a5fb9db82e2`、`f493d4c55f33315ea1b4222d21531728bff784c2`、`d560f2e7a989b9d54008b5bb9ace86a803c1bf62`、`fd1f4b9a81bf78ae827ee3ad63ed06cac575f935`，均无冲突/[skip ci]。root三治理/Owner报告原blobs精确，SOURCE822至此全部非docs差异0；original argv/raw/身份见 `logs/merge-final-*-first` 与 `merged-docs-final-identity.json`。P跨仓report单独核验，不合入core，不产生第二SOURCE/pin/CI。

随后仅追加本节，普通commit/push `[skip ci]`。I最终docs-only REPORT完整SHA、remoteexact/clean、指定所有SOURCE祖先与原命令/日志索引在push后写入 **`C:/r1i/successor-2220/FINAL_REPORT.md`** / `logs/git-final-closeout.json` 并Handoff当前有效Dispatch；不在提交内自嵌自己的SHA。第1–11节及各原首失败保留。

本阶段完成唯一实际SOURCE集成、原双平台工程门、新独立安装/输入核对、一次产品完整首RED及最小Owner修复后独立补验。结果保持上述累计层级，不虚构一次whole全绿。真实AT07批准是root已核用户专项，原600s STOP/SDK0、实际egress/端口/UAC准备属原B/Q/root后续，本I不触Docker/WSL/Engine/FW/key/真实SDKcreate；静态packet、镜像准备或原mock不能代真实隔离PASS。无native科学、真实候选/模型、付费调用、外发或L2；真实无害隔离实际全PASS之后才可能另授权一次L2。

P/A正式AOCI语义维护/human receipt、I跨路径索引freshness仍NOT_VERIFIED；不复制receipt/reinit/reset/手写baseline，不假认知或Token节省。**task_live NOT_RUN；真实用量/费用/Token节省UNKNOWN**，时长只是上述样本，不证最优性能。人工理解未完成；未执行main/tag/deploy、L3/多用户/跨宿主/RSI或额外科学学科品牌评分，没有据此完整MVP/R1成功声明。

### 12.6 完成前checkpoint的晚到正式docs

上节首次docs REPORT `ffc2b76558d84e6f49d30e9b3355af0e4dda0398` 已普通push/remoteexact/clean，但尚未worker_done；完成前必须check的checkpoint收到并ACK root `msg_64fda42028e5` / `delivery_9d3613b24eda`。root直接接纳新SDK前提与唯一concurrent1PASS，另指示合入晚到已接纳Q REPORT **`739efdd10f538099039f2cdf335567802eac7f5a`** 与控制树最新治理 **`89df315ce7870fbc31616e2672e689f61ca1c446`** 顶部23:15。先rawGit读该PLAN再普通精确merge，分别 **`d6885e8d313729c25594c85b6ce66817d6c35eb2`** 与 **`d418673ebd9ffb73ec51c5dd99e876baab36a473`**，无冲突/[skip ci]。Q原blob、root三个治理原blob完全相等，SOURCE822至此非docs差异0，已合B6ea/C611保持祖先。Q静态核对仍未证明FW实际执行/UAC/真实隔离；原unknown不推PASS。

仅追加这次晚到docs说明，普通docs commit/push [skip ci]，**不是第二SOURCE或新pin/测试/CI**。ffc2和其首remote记录保留为前一docs闭合身份；权威最终I REPORT完整SHA与remoteexact/clean在 `C:/r1i/successor-2220/FINAL_REPORT.md` 末尾追加最新收口记录及 `logs/git-final-closeout-late.json`，不覆盖原证据。`merge-late-{Q,root}-first` / `merged-late-docs-identity.json`保存真实输入/argv/exit。所有本节测试、失败、限制与运行权限保持原身份。
