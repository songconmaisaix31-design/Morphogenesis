# I：F+D 本地组合验收记录

2026-09-23。本文件只记录已执行的本地集成，不是部署操作交接。当前派发限定本地范围；主控此前部署交接说明被自动审批拒绝，本轨没有执行、重写或绕过该被拒绝操作。

- 从 `c68def4de25cedb48acd258bea614f7dff35cc16` 普通精确合入 F `d0724a6a2f32f2f03860bbab06ebb82266abdcaf`、D `50d13530a7a9c7b8d1e0cc4c258dc0186710b567`、治理 `f4349824f9934d8aae900823d40f3f537720b597` 与追加状态 `b258ddd749468cf49033915d54aa75563a6c7a6d`，均无冲突。
- 实际运行代码提交 `93efcaee903cb7350d946e99eb81861264344f6b`；分支 `songconmaisaix31-design/morph-gpt-reference-integration`。D 的服务、容器/代理/打包代码与测试保持原提交内容；I 只补主控授权的 favicon 入口声明及集成验证脚本。
- 原锁安装 Python/npm，前端构建通过；`python -m pytest tests/t5 tests/deployment -q` **67 passed**，`python -m mypy --strict viz/server.py` **1 source file success**。部署测试包含本地 Compose 配置解析和真实 loopback HTTP；没有启动或构建本轮组合容器。
- 7844 mock 参考 **131 项通过**，既有序幕脚本通过；切换真实服务端 `--replay` 后 **72 项通过**，1366×768 / 1920×1080 / 375×812 的五视图与详情实图、字体、API 对照、0 控制台/HTTP/页面错误。浏览器没有注入 dashboard 或 EvoMap。
- 第四轮单个历史文件 226518 bytes、mtime、SHA-256 前后完全一致。实际 API 为 `replay`、`contract_local=passed`、`interface_live=not_run`、`task_live=not_run`，未知费用为 null。
- 保留 `http://127.0.0.1:7844/#/workspace`；listener PID **45120**，launcher PID **41372**，cwd 为本工作树，Hidden 启动。F 7841、7799、7526、7527 均未操作。

完整命令、来源声明、失败与返修记录、截图和原件审计见 [前端集成报告](frontend-gpt-reference-integration.md)。本地证据根 `C:/Users/DW/AppData/Local/Temp/morph-gpt-reference-integration-20260923`；最终真实结果在 `real-replay-settled/summary-replay.json`。

**真实剩余限制：** D 单轨此前的本地容器验收可追溯至 D 报告，但最终 F+D 集成提交的容器构建/启动与公网均未验收。本轨未连接或修改云端服务器、安全组、已有共治容器，也未发布站点、发模型任务或写 Hub；上述未执行操作不计作完成，公网工作留待主控处理。用户提供快照及字体的再分发许可仍沿原第三方声明记录为未核实。
