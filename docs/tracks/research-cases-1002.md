# C / Stage3 两类案例工程交付

本报告仅结算 C 域；扩展测试存在跨轨 RED，产品完整双平台与两类原生角色 task_live 尚未验收。

## 分支与冻结来源

- 原固定分支：`songconmaisaix31-design/morph-research-sandbox-0930`。
- WRITE_RELEASE：当前 Dispatch `ctx_6124e14d78b3`，root 消息 `msg_d9797c173387`。
- 准确基线：`90dd1bc418d3adfb9e3151fbde9f74635af25ef8`；远端核验后从原 clean HEAD `bb2cc073130d7da48d2c811fab218078639af124` ff-only，无 reset/force。
- 接口 SOURCE：`789181538c694d8677297b0e0bdfbf879bcc8138`，root 接受后 B/P 按此消费。
- 最终 SOURCE：`08b37827e6e6b48db93962611b1a79a230b1f2c1`，normal push、ls-remote exact、SOURCE clean；相对789仅补 `tests/experiments/test_registered_cases.py`，全部业务/打包输入同字节。
- 本 REPORT 仅新增本文件；SOURCE→REPORT 的业务路径应为空差异，最终完整 REPORT SHA 由提交回执记录，避免自引用。

## 实际改动与稳定接口

只改 `orchestration/experiments/**`、`demo/research_cases/synthetic_linear_regression/**`、
新增实验测试及 `docs/experiments/{registered-cases-1002.md,experiment-plan.schema.json}`。
无锁、依赖、core pyproject、tools、native/MCP、TaskLedger、B/P 文件或旧 checker 改动。

`orchestration.experiments.case.get_case(id)` 返回 frozen typed `CaseDefinition`。
`case_id=plan.criteria.version`；只注册 `nist-numacc4-v1`、`synthetic-linear-regression-v1`。
metadata 是 case_id/title/problem/claim/template_summary/file_policy_prefix/code_source/code_license/data_source/data_license。
`build_plan(role="author", order="original", directory=None)` 供可信宿主选择并冻结计划；
None 定位安装资源，显式 directory 直接包含该案例 code/data。未知 case、criteria/validator，
以及不匹配 code/data 在 backend create 前 fail closed，不让 native 工具输入改变科学标准。
NIST `public_case` 原签名/默认值不变。详细条件与调用方式见
[案例接口](../experiments/registered-cases-1002.md)。

NIST 数据、原候选 Python/notebook 字节及所有原数值阈值/1001行/ordering/Naive控制保持。
实际公式在 `experiments.nist`；`scientific.observations`/NIST常量仅兼容导出。
原 checker blob 保持 `39948d9615bce07b40b96eeaf5dfb263b993c6d3`。
原 NIST demo blobs：Python `bcf7570fb26b80510ad754e19b63a6405859102e`、
notebook `5b9d87229b390a29e924df11f7233815ceaec41a`、数据 `d209bb5bb3f4fa4fd9b99340b60e2b5290384684`。
旧默认 criteria/archival JSON 可读取；原 Notebook/Code Interpreter 协议与显式能力门不改变。
候选只允许同注册源码 LF/CRLF 两个表示，输入/归档仍严格核验原始字节 digest，不重写历史归档。

第二类为项目自有 **synthetic** 七点 CSV，Apache-2.0，版本1，无算法对照或外部发现主张。
`demo/research_cases/synthetic_linear_regression/{linear_regression.py,data.csv}` 安装后可用；
局部 `.gitattributes` 固定 CSV 字节，SHA256 `4311acdb54dce4b838645659523c9d45695b23e4555cf267911b4c163a00f3c6`。
候选调用 CPython3.12 `statistics.linear_regression`（PSF-2.0），项目代码 Apache-2.0，未复制实现。
原始 x=-3..3，y=1.5*x+2+(.25,-.25,0,0,0,-.25,.25)；trusted host Fraction 独立重算 OLS、
逐项残差及 SSE，预声明 slope=3/2、intercept=2、SSE=1/4，三个容差均1e-12；
拒 bool/nonfinite/缺失或伪造 residual/错误系数与摘要。标准不能被 model_copy 绕过。

两类复用同一个 Executor/backend/archive/read_result；SDK1.1.0、固定镜像、shlex.join、资源、
once/fencing/预算、known/unknown/cleanup、usage/cost 保持；仅扩展 typed criteria/assessment版本。
无新运行时、调度、Attempt/Manifest/完成证明系统。

## 环境与原始证据

独占私有根为 `C:/Users/DW/orca/workspaces/Morphogenesis/morph-research-cases-1002-state-6124e14d`。
新建 Python3.12.13 project/tooling/installed venv；Poetry2.5.1+export1.10.1 从原锁导出，
原 lock check 通过（既有 Poetry deprecation warnings），102个项目依赖按锁安装。
SDK/Code Interpreter1.1.0、nbclient0.10.4、nbformat5.10.4不变。
tooling Poetry-core2.5.0/build1.6.1 是本任务新环境，没有复用旧 venv。

下表日志名均相对私有根；所有失败日志与目录保留，后续结果不覆盖原失败。

| 实际检查/命令 | 结果与层级 | 原始记录 |
|---|---|---|
| 首 `pytest tests/experiments -q` | 62 pass /31.53s；contract_local | `pytest-source-01.log` |
| 首 `python tools/typecheck.py` | RED，旧/新demo同名experiment模块冲突；仅新候选改名 | `strict-source-01.log` |
| 次 strict | RED，locate_file SimplePath类型；补str路径转换 | `strict-source-02.log` |
| 修复过程适用 `pytest tests/experiments tests/research tests/local_assets -q` | 112 pass /210.32s，不能覆盖后来RED | `pytest-source-02.log` |
| 接口 SOURCE 域/strict | 67 pass /46.06s；119源文件pass | `pytest-source-04.log`, `strict-source-04.log` |
| 最终 SOURCE 新once/unknown/cleanup域回归 | 72 pass /46.37s | `pytest-source-05.log` |
| 789首次扩展原gate | **RED：116 pass/1 fail，618.16s**，原Git timeout ready fixture未准备 | `pytest-source-final.log` |
| 原focused fixture检查（HEAD08b；收到停止消息前已启动） | **RED：1 fail /15.96s**，同ready条件；不复跑洗绿 | `pytest-timeout-02.log` |
| 最终08b首次准确完整适用原gate | **RED：121 pass/1 fail，204.21s**，同跨轨Git fixture；C72全部通过 | `pytest-08b-first.log` |
| 08b git archive冻结后 `python tools/typecheck.py` | 119源文件pass，原strict gate无改动 | `strict-08b3782.log` |
| 789 git archive→首次Windows tar解包 | RED，中文pathname失败；原tar与部分目录保留，换新目录stdlib tarfile | `source-7891815.tar`, `source-7891815/`，terminal原输出 |
| 789首次隔离 `python -m build` | RED，继承pip镜像HTTP403 | `build-7891815.log` |
| 789新子进程官方PyPI隔离build | sdist+wheel pass，未改全局pip配置 | `build-7891815-02.log` |
| 08b精确冻结 `tooling/python -m build --no-isolation` | 新独占tooling满足build依赖；sdist+wheel pass | `build-08b3782.log` |
| 首installed private checker | RED：uv empty archive_info导致KeyError，尚未运行案例；只修私有checker | `installed-contract-08b3782.log` |
| 新installed private checker | fresh非editablewheel，两case同existingExecutor/read_result成功；**contract_local/mock** | `installed-contract-08b3782-02.log` |
| Git archive/wheel/site字节与资源 | 12文件真实相等；两case code/data在wheel+sdist，role仅role字段不同 | `git-wheel-site-08b3782.log`, installed日志 |

最终artifact目录 `build-08b3782/`：wheel SHA256
`328feefefc1909578f34046b48c8f93c980e2da4808c35caebe26512f6d06485`；sdist SHA256
`ad3e7827eebc93aa22be729636e6a0653f446cec3f952fa7637d9cddbb8c07f1`。
uv实际 direct_url 是本目录wheel URL，archive_info={}，installer-reported hash **未提供**。
验证真实Git archive/wheel/site字节、URL、包来源与非editable，不伪造该metadata。
installed两case输出/原始输入/SDK mock执行JSON/归档位于 `installed-contract-08b3782/`；
NIST variance error=1.1175870992530257e-10；synthetic slope/intercept/SSE error均0，SSE=.25。
这只说明离线mock合同与安装资源有效，不说明真实沙箱资源约束或科研闭环已通过。

## 跨轨与真实剩余限制

三个Git fixture RED均保留原 `tests/local_assets/test_git_timeout.py` 的 ready/output/0.2/argv/<3/TimeoutExpired
断言，未改该文件或 `local_assets.paths.py`，未无证据归因负载。root已交原B Owner仅准备fixture修复；
由I将其SOURCE与最终累计产品一起做新完整双平台验收，不能将C扩展原gate签为全pass。

CIM观察到两个自有失败fixture descendant，精确argv均为本私有root下ready路径与固定打印/sleep4代码：
focused02 PID57660（2026-10-01T20:23:53.149337+08），08b-first PID27872
（2026-10-01T20:27:22.057505+08）。核验正向身份后分别仅终止该PID；当前该PID不存在、ready仍false。
首次创建时间截断guard未匹配时未动作；最初效果不能反推为0。789原失败fixture唯一argv当前匹配0，
不表示历史无效果。未操作附着/未知进程、其他资源或历史sandbox。

本任务无真实认证/模型/服务/沙箱/Hub/native通道调用。原pytest official SDK/local stdio fixture
只用私有mock任务和临时ledger，root明确接受其contract_local分类。usage/cost均unknown/null，
历史失败/cleanup unknown、原case06与peer续租NOT_SATISFIED只读保持。
当前两类真实角色闭环、I新增第二类checker、最终完整双平台 **NOT_RUN / 待I**；
实际Notebook/Code Interpreter/资源enforcement不由此mock补验。C交付可供I准确合并，
不得据此宣称最终产品或task_live完成。
