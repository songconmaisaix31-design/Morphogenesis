# 前端重构集成轨（I）

2026-09-23；I 分支 `songconmaisaix31-design/morph-front-integration`，基线 `972d4bab8b7a86d11ae74b850fe013710b58ace5`。按协调者交付的精确 SHA 普通 `--no-ff` 合并，保留历史；只做集成胶水与 `tests/integration`，领域缺陷退回原 Worker。

## 合并清单

| 轨 | 来源分支 | 精确 SHA | 合并提交 | 冲突 |
|---|---|---|---|---|
| E EvoMap 只读闭环 | `songconmaisaix31-design/morph-front-evomap` | `8275f578ae2aaaf81a044beeaebd453d2e72f31a` | `fe09589` | 无 |
| T 真实拓扑视图 | `songconmaisaix31-design/morph-front-swarm` | `ee65171934595cc5fb21d608bc52a3e5f760c786` | `af740e9` | 无 |
| P WebGL2 黏菌首页 | `songconmaisaix31-design/morph-front-physarum` | `f5448b8f59ce7a592fc0bf38de002a47b333672d` | `af1578d` | 无 |
| E 最终增量（降级 loader 修复 + categories） | 同上 | `4da31ebd2988cffc9a204bba6c6d82230014feed` | `3b0bd00` | 无 |

待合并：S（App.jsx 重复切换 effect 返修 + 手动 q/type 搜索与真实结果呈现，等协调者最终 SHA）。协调者明确：勿用旧 SHA 提前声称完成；浏览器验收需覆盖至少两类有效查询、类别数据真实来源，以及首屏标题覆盖下的 pointermove 与连续切换。

## `/api/evomap` 集成审查结论

- 端点 `GET /api/evomap`（`morph.evomap.readonly/1`）为服务端只读闭环：社区搜索走官方公开只读 `GET https://evomap.ai/a2a/assets/semantic-search`（与锁定的 `@evomap/gep-mcp-server` 1.7.0 同路由），单次请求不重试，进程内按查询键缓存（TTL 300s），状态明确区分 `live / cache / stale_cache / error`。
- 输入边界与官方 MCP 工具 schema 一致：`q` 1–500 字符、`type` 仅 Gene/Capsule、`limit` 1–50；越界返回 `400 {"schema","error":"invalid_query","detail"}`，远端响应文本不进入报告，错误为固定码。
- `MORPH_EVOMAP_API_KEY` 只以布尔 `api_key_configured` 报告配置与否，从不读取、发送或记录密钥；本机未配置时如实为 `false`。
- `local_pool` 以 stdlib sqlite3 `mode=ro` 打开运行存储，Gene 正文经共享 `contracts.resolution.Gene` 契约重验；未配置 `--evomap-store` 时如实 `unconfigured`。字段白名单投影，未知键丢弃不补全。
- 响应含固定 `boundaries` 声明：EvoMap 是来源上下文，不是本项目运行拓扑/任务事实，符合计划"页面不得将其写成运行拓扑事实"。
- 结论：无需集成胶水改动；`viz/server.py` 路由接入（`urlsplit` + `parse_qs`，`max_num_fields=8`）与既有 `/api/dashboard` 互不影响。

## 验证命令与结果

全部从本 I worktree 运行；Node 依赖 `npm ci --ignore-scripts --no-audit --no-fund` 安装，锁文件未变。验证服务器只用 7799 端口，未触碰 7526/7527。

| 命令 | 实际结果 |
|---|---|
| `git merge --no-ff 8275f578…` / `… ee651719…` / `… f5448b8f…` / `… 4da31ebd…` | 四轨均干净合并，无冲突，无胶水改动 |
| `python -m pytest tests/t5/test_evomap.py -q` | 18 passed |
| `python -m pytest tests/t5 tests/integration -q`（合并 T 后） | 36 passed，1 failed 为预存环境问题（见下） |
| 同上（合并 E 最终增量后） | 41 passed，同 1 个预存环境失败 |
| `python -m viz.server --port 7799 --input demo/data/mock-run.json` 后 `curl /api/dashboard` | HTTP 200；保留 `provenance`、`acceptance`、`source_label` 等原有全部键 |
| `curl "/api/evomap"`（默认参数） | HTTP 200；首次 `state=live` 真实命中 Hub 返回真实社区 Gene 资产，相同查询再请求为 `state=cache`；`api_key_configured=false`、`local_pool=unconfigured` |
| `curl "/api/evomap?limit=99"`、`?type=Bad` | 均 HTTP 400 `invalid_query` |
| 全新服务进程 7802 首请求 `curl "/api/evomap?q=repair&limit=1"` | search 与 categories 均 `live`；第二请求均 `cache`，live→cache 状态机正确 |
| `curl "/api/evomap?q=topology&type=Gene&limit=3"`（E 增量后） | HTTP 200；`community_categories` 真实 Hub 计数（by_type: Gene 2509437 / Capsule 2505905 / EvolutionEvent 2094531；by_gene_category: optimize 376082 / repair 342783 / innovate 269904），`hub.categories_endpoint` 如实标注 |

live 标注：上表真实出站仅为公开只读 `semantic-search` 与 `categories` 的 GET（E 轨已验证授权的既有路径，无密钥、无写操作）；其余均为本地契约。回放/mock/live 未混用。验证只用 7799/7801/7802 动态端口，结束后已全部关闭；7526/7527 未触碰。曾观察到一次首请求 categories 误标 `cache`，受控复验（进程内双请求 + 全新真实服务进程首请求）均未复现，判定为该次 7799 进程残留请求的观测假象而非代码缺陷。

## 预存问题（非本次合并引入，已核对基线）

- `viz/server.py` 异常闭包 `lambda: empty_dashboard(f"输入未加载：{error}")` 在 `except` 块外访问被清除的 `error`，输入加载失败或缺少 `node_modules/echarts` 时 `/api/dashboard` 每次请求抛 `NameError`。基线 `972d4ba` 第 107 行已存在；已由 E 增量 `f354f11` 修复（`degraded_loader` 立即绑定原因字符串），集成侧复核通过。
- `tests/integration/test_demo_environment.py::test_demo_excludes_sentinel_from_viewer_and_passes_executor_args` 在本机失败：`shutil.copy` 找不到 `C:\Python313\pyvenv.cfg`（本机 Python 安装无此文件）。在 E 轨合并前内容（`8275f57` worktree）复跑同样失败，属环境预存。
- `tests/t1` 38 errors + 5 failed：Node 桥子进程 `sdk_process_failed` 等，集中在 hub/bridge，与本次合并文件无交集（合并只触及 `viz/`、`tests/t5`、`docs/tracks`），判定为环境预存。

## 待裁决的契约偏差（已报协调者，是否退回 E 由协调者定）

- `morph.evomap.readonly/1` 文档写明 `cache_age_seconds: null = 本次为 live`；实测 `live` 响应携带**负数** `cache_age_seconds`（`now` 在 HTTP 获取前取值、`fetched_at` 在获取后取值，差为负）。不影响 `state` 字段判断，但消费方若按文档用 `null` 判 live 会误判。属 E 轨领域代码，未擅自修改。
