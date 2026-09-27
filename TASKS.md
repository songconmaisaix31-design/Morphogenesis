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
