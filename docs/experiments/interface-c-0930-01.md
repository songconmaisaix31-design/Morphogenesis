# 首次官方接口烟测：FAILED，原记录不改

执行代码候选 `6179d41b336443e915b76d4da87b5267bec5193a`。
命令：`python -m orchestration.experiments.smoke --case-dir demo/research_case --archive-root C:/Users/DW/AppData/Local/Temp/morph-sandbox-live-0930 --run-id interface-c-0930-01`。
返回 exit 1；provenance=live，interface_live=failed，task_live=NOT_RUN。

原archive：`C:/Users/DW/AppData/Local/Temp/morph-sandbox-live-0930/interface-c-0930-01`。
原 `result.json` 保持 execution_state/cleanup_state/remote_effect=unknown，exit/usage/cost=null，scientific=not_evaluated。
未知值没有补零；没有重建/重放该run，没有原生Agent或付费调用。

## 实际观察与后续事实

- 官方服务初始无API key拒绝startup，原 `service-first-start.log` 已保留；私有服务key原生认证恢复后再执行唯一一次smoke。
- sandbox ID `96c5f98a-a204-4a69-8830-b5a34a91618c`：create HTTP202；SDK ready/proxy ping、status/connect HTTP200。
- 同 ID 附着句柄 destroy 在调用远端前被拒绝，未误杀外部会话；renew HTTP200，expires_at从12:38:00.030113Z改为12:38:07.211974Z。
- 上传前目录创建 HTTP500；原错误 `strconv.ParseUint: parsing "448": invalid syntax`，request_id `2f6725c775fd409b899f757b2f96d57c`。
  原适配把 `0o700`（448）发到官方wire；发行SDK与execd要求700/600这样的八进制数字表示。
- smoke wrapper已对自有sandbox发送DELETE：服务记录 HTTP204、kill与remove完成。Executor未收到成功返回的session，因此原结果保守unknown，没有事后改绿。
- 后续只读GET同sandbox HTTP404（`DOCKER::SANDBOX_NOT_FOUND`），`post-cleanup-read.json`保存原响应；Docker按已知ID/标签只读核验无该容器。
- binary upload、cgroup资源核验、cancel、科研代码命令都尚未发送；原service完整日志无 `/command`，无metrics产物。
  因此不能宣称CPU判据在真实sandbox执行或实际CPU/memory enforcement已验证。

## 修复与运行边界

原Owner已把SDK wire参数改为700/600，并用实际官方1.1.0 FilesystemAdapterSync+MockTransport
检查目录JSON和二进制multipart。mock回归只属于contract_local，不能代替修复后的live。
read_result同时核验原始sandbox ID/metadata与宿主context；非script需fresh kernel ID和完整notebook产物。
修复后live交I在冻结修复SHA上运行独立案例，不能重放interface-c-0930-01。

官方服务、execd、CPython镜像全部固定digest；SDK1.1.0使用发行commit `b1a29cf93a823a95913f7943010febb3f29de05c`。
本轨没有停止其他容器、改Docker全局配置、复制HOME或接管Agent凭证。
