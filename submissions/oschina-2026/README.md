# Morphogenesis｜OSChina 开源创新赛提交入口

本分支提交完整源码、可复现的 1–5 并发试验及实际产品优化。默认分支未合并。

## 评审入口

- [演示视频 MP4](https://raw.githubusercontent.com/songconmaisaix31-design/Morphogenesis/codex/oschina-submission-20261030/submissions/oschina-2026/demo.mp4)：已完成真实试验的数据回放，**不是重新运行模型的屏幕录像**。
- [交互回放 HTML](replay.html)：下载后用浏览器打开；自包含、无需密钥，不会发起模型请求。
- [实测摘要](RESULTS.md) / [完整 15 组合 CSV](results.csv)。
- [完整脱敏证据 ZIP](evidence.zip)：原始响应、冻结计划、原生审计/收据及独立分析；见 [SHA256 清单](ARTIFACTS.json)。
- [原始提交历史 bundle](source-history.bundle)：保留实际测试的本地精确提交；不含凭据。
- [固定协议](protocol.json) / [48 题选择与 prompt hash](selection.json) / [优化重放摘要](optimization-replay-summary.json)。

作品介绍 PDF 由正式提交材料另行提供；不会将尚未确认的文件地址写成已发布链接。

## 源码来源：原提交与公开提交不要混称

云端没有原生 Git 推送凭据，发布使用已授权 GitHub 连接器。连接器重建提交元数据，
但源码树逐字节一致，Git tree SHA 已核对：

| 用途 | 实验原始提交 | 对应公开源码提交 | 相同 Git tree |
|---|---|---|---|
| 720 次真实模型基线 | `eff9611f6c630f710bf47d723710c4dbe5e23ba4` | [`5e3dc5e`](https://github.com/songconmaisaix31-design/Morphogenesis/commit/5e3dc5e912dc963fe66c22a788b9311399421ffe) | `cd71640c497e343f8cb3d39bd8842886b713a084` |
| 后续本地 SDK 优化 | `a180172cf89c82ad802c5521e57e2ee790727f69` | [`622c81d`](https://github.com/songconmaisaix31-design/Morphogenesis/commit/622c81dd1f49165c57020a775be170af257b6c0c) | `19a792716246014e6ded17ed0eb7727419014d83` |

原始 `eff9611` / `a180172` 历史位于 bundle，不能将其当作已经直接发布的 GitHub commit URL。
在已有仓库（包含起点 `ddd2849afe330bf221d405dc2b91948c2416bd47`）执行：

```sh
git fetch /absolute/path/source-history.bundle refs/heads/codex/lazy-official-schema-20261030
git show eff9611f6c630f710bf47d723710c4dbe5e23ba4 --stat
```

## 复现步骤（Linux，Python 3.12 / Node 24）

先取得公开仓库，在新的自有目录使用基线源码，不覆盖已有工作：

```sh
git clone https://github.com/songconmaisaix31-design/Morphogenesis.git
cd Morphogenesis
git checkout --detach 5e3dc5e912dc963fe66c22a788b9311399421ffe
uv venv .venv-benchmark
uv pip install --python .venv-benchmark/bin/python -r tools/benchmark_requirements.lock.txt
uv pip install --python .venv-benchmark/bin/python -e .
npm ci --ignore-scripts
git clone https://github.com/openai/grade-school-math.git ../gsm8k-fixed
git -C ../gsm8k-fixed checkout --detach 3101c7d5072418e28b9008a6636bde82a006892c
PYTHONPATH=. .venv-benchmark/bin/python tools/run_concurrency_comparison.py \
  --source ../gsm8k-fixed --output ../comparison-prepare \
  --adapters-dir tools/benchmark_adapters --mode pilot --prepare-only
```

`--prepare-only` 不调用模型。真实执行需已有合法 StepFun 中国区 API 访问及费用授权；
主控通过匿名 stdin 提供临时密钥，再把最后参数换为 `--credential-stdin`。
**不要把密钥放入命令行参数、Git、文件、输出或日志。** 请求上限每次 pilot 720，
传输错误/429/未知结果立即停止，不自动重试。用新输出目录，不重放已有尝试。

源码树内禁止放原生运行状态。完整协议和离线检查命令见
[`docs/CONCURRENCY_COMPARISON.md`](../../docs/CONCURRENCY_COMPARISON.md)。
若要运行优化后源码，选择公开优化提交；它不等于模型基线的新一轮成绩。

## 结论与展望

Morphogenesis 从 1 到 5 Worker 的整批耗时由 574.078 降到 139.989 秒（4.10×），
严格正确率由 43/48 到 42/48。本轮 AutoGen Core 与 LangGraph 的端到端吞吐更快；
三种配置的持久化义务不同，不能将差异简单归因于架构本身。

产品实改是按需编译官方 GEP schema，未绕过验证、租约或不可变收据。
之后的固定响应原生重放局部管线中位耗时减少 12.46%，0 新增模型调用；
**该收益不能回填到此前 720 次模型实测时间。**

下一步以共享资源冲突、跨任务依赖和故障恢复的预注册重复实验检验持久协作收益，
并继续减少验证/提交成本。本轮独立数学题的单次探索试验不证明协作或架构全面优越。
CI 工作流已配置在 push/PR 上运行；是否通过以该公开提交的实际 Checks 为准，
不以局部测试或真实试验替代完整 CI。
