# 1–5 并发：同模型、同题目、实际框架运行器

本轮是 **Morphogenesis** 的批处理准确率与端到端效率试验，不是 SWA
原生集成验收，也不预设本产品获胜。保留此前 SWA 证据，不把两者混称。

## 固定协议

- 官方 GSM8K `3101c7d5072418e28b9008a6636bde82a006892c`（MIT）。测试集按
  `SHA256("morph-gsm8k-v1\n" + question)` 升序取 48 题；开发只用独立训练集 4 题。
  原混合 GSM8K/BBH 基准不修改。`selection.json` 在调用前固定样本与 prompt 哈希。
- 实际 Morphogenesis Worker/SQLite claim/租约/预算/校验/提交路径，对照实际
  AutoGen Core 0.7.5 消息运行时及 LangGraph 1.2.18 StateGraph/Send。
  每题唯一 scope，各并发度保持相同工作量；不是竞争共享文件的协作实验。
- 主试验为并发 1、2、3、4、5 × 3 框架 × 48 题，单次探索重复，最多 720 个请求。
  种子 20261030 打乱 15 个条件顺序，每次只运行一个条件。开发最多 12 个请求。
- 同一 StepFun `step-3.5-flash`、完全相同 system/user prompt、温度 0、输出上限
  4096、提供方默认 reasoning，无工具、自动重试或答案修复。模型不知道参考答案。
- 一个跨进程 gate 管理本试验生命周期请求预算和当前条件 c 的实际 HTTP 上限。
  条件切换须已排空，旧 gate 不再准入。不声称控制账户上其他应用或服务端 GPU 并行。
- HTTP 429、传输/超时/未知结果停止全部后续准入并排空已知请求，不自动重试。
  已知 `length`/`content_filter` 记录 truncated/filtered，计失败但继续剩余题目。
  数学错误与格式错误也不触发重试。未知 usage/账单费用保留 null。
- 评分使用官方首个 `#### (\-?[0-9\.\,]+)`、去逗号、严格字符串相等；另记单标记率。
  被截断/过滤的部分输出即使含正确答案也不计正确。中止条件不报告有效完整准确率或吞吐。
- 原生提交仅验证适配器生成的 `{"response": raw_text}` 存储结构，不含 gold；数学评分独立。
  原始模型结果先持久化，原生提交失败不得通过数学正确率伪装为运行成功。

## 复现

仓库 Python 3.12 环境还需 `autogen-core==0.7.5`、`langgraph==1.2.18`；
原生 GEP 路径需要 `npm ci --ignore-scripts`。版本和实际源文件哈希写入计划。
本云端完整 Python 依赖固定于 `tools/benchmark_requirements.lock.txt`，包含现有
SOCKS 代理所需的 `socksio==1.0.0`；可先 `uv pip install --python <python>
-r tools/benchmark_requirements.lock.txt`，再安装本仓库。传输构造/关闭预检无网络请求，
在读取凭据前运行，不关闭代理或 TLS 校验。

```sh
PY=.venv-benchmark/bin/python
SOURCE=/workspace/shared/gsm8k-pinned-20261030
OUT=/workspace/scratch/bba018a8e319/comparison-development
PYTHONPATH=. "$PY" tools/run_concurrency_comparison.py \
  --source "$SOURCE" --output "$OUT" --adapters-dir tools/benchmark_adapters \
  --mode development --prepare-only
```

执行命令将 `--prepare-only` 替换为 `--credential-stdin`，仅由授权主控用所属匿名
stdin 传入临时密钥；**禁止命令行参数、文件、shell 历史或环境日志包含密钥**。
生产测试使用新的输出目录及 `--mode pilot`。已尝试目录拒绝自动重放。

离线检查（模拟 HTTP 不是实际模型质量证据）：
原生运行目录必须位于源码树外，测试可使用系统临时目录；勿把 `TMPDIR` 设为源码内。

```sh
PYTHONPATH=. "$PY" -m pytest -q tests/swarm/test_benchmark_model.py \
  tests/swarm/test_benchmark_runtime.py tests/swarm/test_comparison_protocol.py \
  tests/swarm/test_comparison_runner.py
PYTHONPATH=. "$PY" tools/benchmark_adapters/validate_adapter_env.py
PYTHONPATH=.:tools/benchmark_adapters "$PY" -W error -m unittest discover \
  -s tools/benchmark_adapters -p test_adapters.py -v
"$PY" -m mypy --strict --explicit-package-bases swarm/benchmark_model.py \
  swarm/benchmark_runtime.py tools/benchmark_protocol.py tools/run_concurrency_comparison.py \
  local_assets/models.py local_assets/validate.py local_assets/promote.py
```

## 证据、解释与展望

输出包括计划/源码哈希、独立评分、每次请求的共同单调时钟/序号/返回边界、未知费用、
框架事件、Morph 原生 SQLite 收据与 Worker 退出状态、JSON/CSV。HTTP 峰值用实际
进入至返回的客户端区间，而非 Worker 数量推断。非流式试验不报告 first-token 延迟。

Morph 端到端计时包括新 Git/任务账本准备、验证及持久提交；两个对照使用其较简运行配置。
这些是明示配置的端到端比较，不能据此单独归因调度器开销。单次公开数据试验还受
污染、难度天花板、缓存、网络、提供方排队及顺序影响。只有实测才能支持优势声明。

展望：先用正确率、正确结果/分钟、实际失败恢复和可审计交付定位瓶颈；后续再预注册
共享资源冲突、跨任务依赖、故障注入与重复实验，检验 claim/租约/持久收据是否带来
可量化收益。当前独立题批处理不证明去中心化协作优越，也不以未来目标冒充已完成能力。
