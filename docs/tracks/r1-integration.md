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
