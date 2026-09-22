# 前端重构集成轨（I）

2026-09-23；I 分支 `songconmaisaix31-design/morph-front-integration`，基线 `972d4bab8b7a86d11ae74b850fe013710b58ace5`。按协调者交付的精确 SHA 普通 `--no-ff` 合并，保留历史；只做集成胶水与 `tests/integration`，领域缺陷退回原 Worker。

## 合并清单

| 轨 | 来源分支 | 精确 SHA | 合并提交 | 冲突 |
|---|---|---|---|---|
| E EvoMap 只读闭环 | `songconmaisaix31-design/morph-front-evomap` | `8275f578ae2aaaf81a044beeaebd453d2e72f31a` | `fe09589` | 无 |
| T 真实拓扑视图 | `songconmaisaix31-design/morph-front-swarm` | `ee65171934595cc5fb21d608bc52a3e5f760c786` | `af740e9` | 无 |

待合并：S（协调者已发现 App.jsx 重复切换 effect，原 S Worker 返修中，等最终 SHA）、E 增量（`viz/server.py` 预存异常闭包 NameError 已退回原 E Worker，等增量 SHA）、P（浏览器参数收尾中）。

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
| `git merge --no-ff 8275f578…` / `… ee651719…` | 两轨均干净合并，无冲突，无胶水改动 |
| `python -m pytest tests/t5/test_evomap.py -q` | 18 passed |
| `python -m pytest tests/t5 tests/integration -q`（合并 T 后） | 36 passed，1 failed 为预存环境问题（见下） |
| `python -m viz.server --port 7799 --input demo/data/mock-run.json` 后 `curl /api/dashboard` | HTTP 200；保留 `provenance`、`acceptance`、`source_label` 等原有全部键 |
| `curl "/api/evomap"`（默认参数） | HTTP 200；首次 `state=live` 真实命中 Hub 返回真实社区 Gene 资产，相同查询再请求为 `state=cache`；`api_key_configured=false`、`local_pool=unconfigured` |
| `curl "/api/evomap?limit=99"`、`?type=Bad` | 均 HTTP 400 `invalid_query` |

live 标注：上表仅默认查询一次真实出站 GET（公开只读搜索，E 轨已授权的既有验证路径）；其余均为本地契约。回放/mock/live 未混用。

## 预存问题（非本次合并引入，已核对基线）

- `viz/server.py:136` 异常闭包 `lambda: empty_dashboard(f"输入未加载：{error}")` 在 `except` 块外访问被清除的 `error`，输入加载失败或缺少 `node_modules/echarts` 时 `/api/dashboard` 每次请求抛 `NameError`。基线 `972d4ba` 第 107 行已存在；协调者确认已退回原 E Worker，等 E 增量 SHA。
- `tests/integration/test_demo_environment.py::test_demo_excludes_sentinel_from_viewer_and_passes_executor_args` 在本机失败：`shutil.copy` 找不到 `C:\Python313\pyvenv.cfg`（本机 Python 安装无此文件）。在 E 轨合并前内容（`8275f57` worktree）复跑同样失败，属环境预存。
- `tests/t1` 38 errors + 5 failed：Node 桥子进程 `sdk_process_failed` 等，集中在 hub/bridge，与本次合并文件无交集（合并只触及 `viz/`、`tests/t5`、`docs/tracks`），判定为环境预存。
