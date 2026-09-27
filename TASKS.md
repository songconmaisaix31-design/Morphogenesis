# TASKS.md — FC 轮任务账本

## 依赖申请区（五轨对 pyproject.toml/poetry.lock 只读，缺依赖在此登记，由队长批量执行）

| 依赖 | 所属轨 | 用途 | dev 组 |
|---|---|---|---|
| （空，待轨登记） | | | |

## FC-A 第 0 步探测记录（人类队长拍板 + AI 代跑核实，已固化）

结论：httpx 路线成立；live 请求走子进程；respx 仅能注入进程内路径；分类在子进程内完成。

证据锚点：

- `orchestration/gateway_transport.py:14` `import httpx`
- `orchestration/gateway_transport.py:43` `httpx.Client(transport=..., trust_env=False, follow_redirects=False, timeout=...)`
- `orchestration/gateway_transport.py:22-30` `GatewayResponse` 字段（无 Retry-After、无 raw body 字段）
- `swarm/evomap_executor.py:92-132` `_request()`（调用 `single_request`，进程内/mock 路径）
- `swarm/evomap_executor.py:135-149` `_child()`（`--request-child` 子进程入口，读 cred 文件后调 `_request`）
- `swarm/evomap_executor.py:209-224` `_send()`（live 走 `subprocess.run`；mock 走进程内 `_request`）

裁定：raw body 不出子进程；回传 `classification` + `evidence_hash`；FC-A 写权窄增补
`swarm/evomap_executor.py` 两处（见 QWEN.md [FC-A 写权扩展]）。

## FC-A 首次交付复核与返修（2026-09-27）

- 收到 worker_done：原 task_021476b9728f / ctx_908e3cf0b7a5，远端分支
  fc/failure-classify@e4396407e87e8745f8bfeff448343ecf6b6edd5f 已核实。生命周期
  completed/succeeded 仅是 Worker 自报结算，主控业务验收未通过；不集成。
- 该提交额外引入 uv.lock（3 行，基线不存在），违反锁文件/写权边界。由原
  Worker 在普通后续提交中撤销自己新增文件，不改其他锁文件、不重写历史。
- 最初工作树 Python 执行 tools/typecheck.py 失败：No module named mypy；
  随后原 Worker 真实终端回执已执行 Poetry install，84 源文件类型检查、
  tests/orchestration/ 的 19 项定向测试通过；尚无合格全量 pytest 回执。
- 独立只读复现：分类器接受 JSON null 抛 TypeError，message=null 抛
  AttributeError；_request 的非 UTF-8 响应抛 UnicodeDecodeError；HTTP 400
  Arrearage 的流在部分 body 后 ReadTimeout，Reply 却为 confirmed_rejection
  （uncertain=true）。均是进程内 MockTransport，无远端调用。
- 未实现 Retry-After HTTP-date/整数/未知解析；当前所谓 integration 测试仅
  进程内 _request 调用，无实际 spawn --request-child 回传证明。
- 返修仍归同一个 FC-A 原终端、worktree、branch。新 task_5853a2c3a4b9 /
  ctx_3993f67114a8；旧 Dispatch 已撤权，不复用旧身份。新 preamble 通过
  native Qwen Ctrl+Q 入队并读回“1 queued”；等待真正执行和修复回执。
- FC-C 仍由原 Qoder Worker 开发；FC-D/E 暂等 A 接口返修，最终集成未执行。
- 紧接原任务第二条 worker_done：19fe837b5aafdecfcc963ed90dc518071c9b6511
  仅删除 uv.lock（已推送终端回执），没有修复领域代码。本次独立执行工作树
  `.venv/Scripts/python.exe tools/typecheck.py`：84 源文件通过；
  `.venv/Scripts/python.exe -m pytest -q tests/orchestration`：19 passed in
  7.28s。上述已知缺陷与缺失需求仍阻止验收；第二条消息已读取并确认。
- 新返修 preamble 已从队列进入 native 模型新回合，屏幕读回完整新任务及
  processing 状态；不是仅记录终端输入接受。

## 最新并行开发与已知引擎阻塞

- 用户要求继续五轨并行开发及桌面报告。A 原会话达到 100 轮后保留 WIP、
  退出并原会话 resume，进程上限改 400；接续 ctx_b8e62d8a7999。D 首次
  Windows shell 配置错误后绕过 Poetry 执行全局 pip（原生记录可见安装了
  hypothesis/respx/time-machine 等）；立即停止，未盲目卸载共享包。随后
  launcher 设置 POETRY_VIRTUALENVS_IN_PROJECT=true，同一 D 会话 resume 到
  ctx_1bbdc67b67ba，实际执行 uv tool run poetry install；不以全局包为验收。
- A/D 分别真实返回 DashScope HTTP 400 账户状态异常/欠费拒绝。没有再次
  调用、创建替代 Key、充值或自动模型切换；两个 Dispatch 已 fenced/stopped，
  原工作树 WIP 保留，Task blocked。引擎替代选择已向用户提出，尚待答复。
- A 当前 WIP 的 subprocess 测试曾加 except Exception: pass，能吞掉断言；
  主控已中断该回合并退回修复。explicit mock child seam 已开始编写，但尚未
  最终验收。D 当前草稿存在 assert True/占位和错误账本调用，尚未测试、提交或
  接受，不能混为真实五不变量验证。
- E dsh/DashScope deepseek-r1 实际有模型与工具事件、provider usage，但首轮
  结束后没有报告文件或 Commit；末尾声称写入 $MARTIFACT_FILE$ 未由文件系统
  验证，且不按五不变量原文评审，未验收。ctx_588d14022e7e 已停止，不重发
  同一欠费账户调用。原 native session 与响应证据保留在忽略的运行目录。
- C Qoder 仍开发/验证；主控独立 strict 82 文件通过，尚等最终完整回执。
  欠费原因 A billing_arrearage / C arrearage 不一致已退回 C 对齐。
- 独立集成 worktree morph-fc-integration-0927 已按本轮计划创建，分支
  songconmaisaix31-design/morph-fc-integration-0927，基于治理提交 37b5b6b。
  没有集成 Worker 开工或领域合并，等最终领域交付。
