# Morphogenesis 执行约定

用户当前指令优先于开发包。业务事实源为 `docs/source/README_包内说明.md` 列出的现行文档；v1 仅存档。

- 核心原则：官方实现优先、成熟开源依赖优先，只自研差异化机制和必要适配。引用或复制代码记录来源、版本、许可证；不自行重写调度器、Attempt 系统、Manifest、哈希或完成证明系统。文档所需 AttemptId 只是数据身份，使用 Pydantic，不扩建基础设施。
- 当前一页计划和文件所有权见 `docs/PLAN.md`。每条轨道固定一个 Agent、一个 Orca worktree、一个分支。只能修改该轨 write_paths；跨轨请求通过 Handoff。
- 主 Agent 只维护计划、状态、决策和验收。开发、测试、文档、返修由原 Worker 完成；最后由集成 Agent 合并，只改少量导入、配置、类型和路由胶水，领域问题退回原 Worker。
- 优先复用既定 Python / LangGraph / Pydantic / SQLModel / SQLite / httpx / MCP / 官方 GEP SDK / ECharts 技术栈，不为并行改目录。锁文件由 T0 独占。
- 每阶段 commit，完成 push。禁止 force push、覆盖历史、丢弃其他贡献。秘密与本地运行产物不得入库。
- contract_local、interface_live、task_live 分开；模拟、回放、生成代码、单测通过均不可冒充真实运行验收。未知远端效果不自动重试。
- Hub 沙箱信息未提供：只联调本地隔离 stub，显示待发布。ORCA 运行时供给接口未提供：使用固定规模蜂群。T4 可选进化不进入当前核心闭环。
- 最终仅报告完成内容、分支和 SHA、验证命令与结果、真实限制、未执行或人工操作。
