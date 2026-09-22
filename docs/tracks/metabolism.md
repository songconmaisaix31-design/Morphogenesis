# T3M 本地经验缓存与使用状态

所有权为 `metabolism/**`、`mocks/**`、`tests/t3/metabolism/**` 和本文件。已经合并 T0 契约 `d0f5ac9bd75b8b8f1bc12d0d22b625d549833a71` 与持久化/锁 `32c897ae1b8b1f295bb3c79a3e349f9c4d8165b3`。依赖锁、公共契约和打包配置由 T0 维护。

## API（T2 / T1）

```python
from persistence import SQLiteStore
from metabolism import LocalMetabolism

store = SQLiteStore("runtime/run.sqlite")
memory = LocalMetabolism(store, run_id="actual-run-id")
memory.ingest(gene)                    # 桥传来的完整不可变 Gene 正文
memory.bind_attempt(attempt, ["python", "repair"])
genes = memory.inject(attempt.agent, budget=3)
# 执行器确实接收正文并报告采用的 gene_id 后，T2 校验采用集合，再调用：
memory.mark_used(genes[0].ref.gene_id, attempt)
```

- `ingest(Gene)` 只缓存调用方提供的正文，不进行官方 schema/hash 校验、GEP 演化或发布。T1 应先履行官方校验；同版本正文、asset_id、provenance、来源不允许变化。`resolve(GeneRef)` 返回完整正文，拒绝 asset_id 不符、未知和已归档版本。不能把底层 `SQLiteStore.get_gene` 当作公开生命周期解析入口。
- `bind_attempt(attempt, signals)` 绑定实例当前任务。`inject(agent,budget)` 必须先绑定；预算是**整条 Gene 数量**，不代表 token/模型费用。负数、布尔数拒绝，零返回空；适用筛选后排序，最多返回预算数。
- `signals_match` 中 `role:builder` 等为角色约束；其余为任务信号，与当前信号进行去空白、不区分大小写的精确相交。多个角色是 OR，多个普通信号是 OR，两类之间是 AND。空信号列表是通用。条件标注来自正文；无角色约束则不凭空推断。不是语义推理筛选。
- 同一 `run_id + task_id + role + instance + attempt` 注入结果固定，预算或信号改变会拒绝；再次注入返回原版本（过滤此后归档的正文）。新 attempt 才重新检索。每个 gene_id 只取已知最高版本，最高版本归档不回退旧版本。
- 注入仅记录提供正文，不代表采用。`mark_used(gene_id, attempt)` 必须匹配该 run 的完整 AttemptId 和注入清单；采用绑定清单里的确切版本，不会因后来 ingest 新版本错绑。重复采用不会增加计数、刷新时间或权重。不同 run 的同名 AttemptId 分开计数；进程重启后去重仍有效。已记录的采用在归档后重复调用仍是无副作用重放，新的归档采用拒绝。
- 本地机制不能证明模型认知上采用了经验，也不能独立鉴别调用者传来的 AttemptId 是否执行过。T2 负责将采用声明与真实执行/复核证据绑定，禁止在调用执行器前直接把全部注入项标为采用。

## 衰减、候选与本地一致性

`now` 与注入/采用/创建时间均为 UTC Unix **秒**。每个版本保存 `tau_seconds`，默认 86400 秒；起点为 ingest 时刻，首次及后续真实新采用将起点重置为采用时刻。公式 `w(t)=exp(-(t-anchor)/tau_seconds)`，半衰期为 `tau_seconds * ln(2)`，tau 不是半衰期。重复同一 now 不重复衰减，时间回退及非有限值拒绝。tau 保存到版本状态，重启时改变构造默认值不重新解释旧记录。`inject` 和 `archive` 会按当前 clock 计算权重；`snapshot` 只读持久化值并暴露 evaluated_at。

`merge_candidates()` 通过 FAISS 相似度产生适用条件相同的版本引用对，默认余弦阈值 0.9。返回的是候选，无内容合并、升级、谱系父子声明、GEP 演化或自动发布。最终算法归官方 MCP Server；候选消费方仍需官方算法、验证和发布批准流程。

SQLiteStore.engine 是唯一数据库入口，复用 T0 `GeneRow` 缓存，仅增加三个命名空间内 SQLModel 表：版本状态、注入批次、采用。操作使用 SQLite `BEGIN IMMEDIATE` 事务串行化跨实例读写；FAISS 索引在同一事务内按当前有效正文即时构造，使用后不保存。无第二份持久化向量状态或后台同步器。适合当前固定小规模原型，不宣称大规模高吞吐。

`archive()` 按当前时间归档 `weight < archive_threshold` 的版本，默认阈值 0.05；同一事务删除缓存正文、写永久停用标记。检索不持有跨操作索引，已归档正文不进入下一次索引；resolve、旧注入重放、另一个实例和全新进程均不能返回它。使用统计/引用/来源元数据仍保留给审计与谱系展示。返回去重排序的 gene_id；具体版本从 snapshot 查询。同版本重复 ingest 不得复活；真正的新版本可显式 ingest。

这只是**本地 SQLite/缓存/检索一致性**。没有跨 Hub、Evolver/MCP 记忆图的分布式原子事务，归档不调用远端、不删除官方资产，也不声称已同步。`GeneView.remote_archive_status` 固定 `not_synchronized`。桥后续重新取回被归档的相同版本也必须经过 metabolism，永久停用标记会拒绝；禁止绕过它直接写缓存。调用者已拿到的历史正文无法远程收回；后续执行前应重新 resolve。读/写事务失败会回滚，不通过远端盲目重试掩盖未知效果。

## 最小读 API（T5）

`snapshot() -> list[GeneView]`：`ref`（gene_id/version/asset_id）、provenance、original_run_uri、source_attempt、weight、use_count、injected_count、created_at、last_used_at、evaluated_at、tau_seconds、archived_at、remote_archive_status。按 gene_id/version 排序，包括归档元数据，无已归档正文。use_count 与 injected_count 跨共享数据库内各 run 累计；来源由 `source_attempt` 体现，不伪造 Gene 父子边。相似候选不是遗传谱系。

`usage_records() -> list[UseRecord]`：只返回构造时 run_id 的采用，含完整 AttemptId、精确 GeneRef、used_at、provenance。用于将图上计数链接到真实任务证据，但该本地记录本身不建立 task_live。

## 复用与来源

- FAISS CPU **1.15.1**（T0 锁；MIT），使用官方 `IndexFlatIP` 与 L2 归一化后的内积检索，没有手写向量索引。依据 [官方索引文档](https://github.com/facebookresearch/faiss/wiki/Faiss-indexes) 与 [FAISS 仓库](https://github.com/facebookresearch/faiss)。Windows wheel 已由 T0 实际安装，本轨测试亦运行真实 FAISS。
- 默认 embedding 调用 sklearn `HashingVectorizer` 的字符 2–4 gram，2048 维；词法特征有碰撞、无学习语义、无模型下载。也可构造时传入 `embedding: Callable[[Sequence[str]], numpy.float32二维数组]`，需全生命周期保持相同算法与维数。FAISS 排序使用余弦分数乘本地权重；预算截断前完成适用性筛选。
- SQLModel/SQLite/Pydantic 复用 T0 实际版本与持久化，未复制上游代码；scikit-learn **1.9.1**（BSD-3-Clause）及许可由 T0 `64064c3` 锁定，已合并。

## Mock 与验收边界

`mocks.gene_fixture` 只包装调用方给出的正文且强制 provenance=mock；`MockMetabolism` 复用真正本地机制但只接受 mock 数据。`UnimplementedExecutor` / `UnimplementedVerifier` 明确抛 NotImplementedError，不生成假执行或验证结果。live、mock、replay 不能交叉 ingest/resolve/检索；replay 额外要求 original_run_uri。测试里用于契约输入的 live 标记不代表远端真实经验或真实任务。

2026-09-22 Windows、独立 Poetry Python 3.12 环境验证：

- `uv tool run poetry install --no-interaction`：按 T0 锁安装成功，FAISS CPU 1.15.1 与 scikit-learn 1.9.1 为实际运行依赖。
- `uv tool run poetry run pytest tests/t3/metabolism tests/t0 -q`：**44 passed**（本轨 13 + T0 31）。覆盖精确 AttemptId/版本/run 采用去重、并发重复采用、预算与适用条件、来源隔离、真实 FAISS、本地进程重启后归档不可返回，以及故障事务回滚。
- `uv tool run poetry run mypy --strict metabolism mocks tests/t3/metabolism`：**通过，6 个文件**，具体实现及测试均检查。
- `uv tool run poetry run python tools/typecheck.py`：**通过，24 个文件**（当前 worktree 全部已存在实现）。
- `git diff --check`：通过。

此交付建立 contract_local；interface_live / task_live 尚未执行。未提供 Hub/Evolver 归档原子接口，也没有远端归档同步或真实模型采用验收。T0 初版打包配置只含地基模块；将 metabolism/mocks 加入最终打包由 T0 负责，不能把初版地基 wheel 当作已包含本轨的发布产物。
