# 官方来源、固定版本与许可证

| 依赖/数据 | 固定版本/来源 | 许可证与复用方式 |
|---|---|---|
| OpenSandbox 初始研究 | [089b59ad48af33fc2733de58bd1a39c687c93b0a](https://github.com/opensandbox-group/OpenSandbox/tree/089b59ad48af33fc2733de58bd1a39c687c93b0a) | Apache-2.0，TEMP clone 源码研究，未安装整个上游 |
| OpenSandbox SDK / Code Interpreter / server | PyPI 1.1.0；[release-1.1.0 / b1a29cf93a823a95913f7943010febb3f29de05c](https://github.com/opensandbox-group/OpenSandbox/tree/b1a29cf93a823a95913f7943010febb3f29de05c) | Apache-2.0，调用官方 SDK，部署官方 service/image；本地 config 从上游 Compose 适配并标注来源 |
| Python / statistics | CPython 3.12.13；[官方 variance](https://docs.python.org/3.12/library/statistics.html#statistics.variance) | PSF-2.0；调用标准库，不复制实现 |
| nbclient / nbformat | 0.10.4 / 5.10.4 | BSD-3-Clause；调用成熟 NotebookClient，不重写内核执行器 |
| NumAcc4 | [NIST 原始数据](https://www.itl.nist.gov/div898/strd/univ/data/NumAcc4.dat)，SHA256 `ca310dc767f5130f980f8280bbe69e26ba414a4d85a89fc11b6c767b828e5fe4` | NIST 科学参考数据，来源及限制按 [NIST licensing](https://www.nist.gov/open/copyright-fair-use-and-licensing-statements-srd-data-software-and-technical-series-publications)；仅保存公开构造数值及来源说明，无 NIST 背书 |

NumAcc4 的参考文献是 Simon, Stephen D. and Lesage, James P. (1989), Assessing the Accuracy of ANOVA Calculations in Statistical Software, Computational Statistics & Data Analysis 8:325–332。
[NIST certified values](https://www.itl.nist.gov/div898/strd/univ/certvalues/numacc4.html) 给出均值10000000.2、样本标准差0.1。
本轨只验证其中样本方差和均值，未验证自相关或扩展到任意科学主张。

SDK 审核路径：`sdks/sandbox/python/src/opensandbox/sync/sandbox.py`（create/connect/renew/kill/close）、
`sync/services/command.py`（argv、server timeout、interrupt/status/logs）、`models/execd.py`（nullable exit/complete/error）、
`sync/services/filesystem.py`（bytes upload/read_bytes_stream）、`models/sandboxes.py`（Volume/PVC）、
`sdks/code-interpreter/python/src/code_interpreter/sync/services/code.py`（create_context/run/interrupt）。
初始研究 SHA 的 interpreter.close 与发行1.1.0不同：严格按实际锁定 wheel API 调用，不套用未来 API。

官方版本承诺不代替后端实际能力；GPU、codeinterpreter镜像、nbclient内核和持久卷需单独启用与验收。
