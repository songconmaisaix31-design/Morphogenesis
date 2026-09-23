# E 轨：EvoMap 官方接口核对与安全只读闭环（2026-09-22；2026-09-23 新增资产点击详情接口）

write_paths：`viz/evomap_models.py`、`viz/evomap_service.py`、`viz/server.py`、`tests/t5/test_evomap.py`、本文件。

## 来源核验（官方实现优先）

| 依赖 | 版本 | 许可证 | 用途 |
|---|---|---|---|
| `@evomap/gep-sdk` | 1.14.0（锁文件） | Apache-2.0 | 仅 schema/哈希；本轨未新增使用 |
| `@evomap/gep-mcp-server` | 1.7.0（锁文件） | Apache-2.0 | 核对官方 Hub 路由：`src/remote.js` 的 `searchCommunity`/`listGenes` 走 `GET /a2a/assets/semantic-search` |

官方 SDK 对该路由的事实（`remote.js`）：GET、参数 `q`（截断 500 字符）、`type`（Gene/Capsule）、`outcome`、`limit`（1–50）、`include_context`；Bearer 用用户级 API key；SDK 自带最多 4 次瞬态重试——**本轨不采用重试**（项目约定：未知远端效果不自动重试）。

## 实测结论（live，2026-09-22）

1. `GET https://evomap.ai/a2a/assets/semantic-search?q=repair&type=Gene&limit=2` **无任何 Authorization 头即 HTTP 200**，返回真实社区资产。即该搜索是公开只读接口；闭环不需要密钥，也不需要任何付费 Chat Completions 调用。
2. 顶层字段实测为 `assets / count / derived_queries / provider / search_status`；单资产 47 个字段的完整清单以 `viz/evomap_service.py` 的 `_ASSET_SCALARS`/`_ASSET_OBJECTS` 白名单为准（逐字段来自真实响应，未臆造；未知新字段丢弃不展示）。
3. 是否计费/配额：未知（响应与官方包内均无说明）。缓解：进程内缓存（默认 TTL 300s，按查询键）、页面不轮询、单次获取仅一次请求。
4. 未验证（不臆造）：鉴权后的差异行为、`include_context=true` 的增量字段、单资产全文拉取路由、`/a2a/memory/*` 及一切写路由（publish/hello/revoke 等均未触碰）。
5. `MORPH_EVOMAP_API_KEY` 当前环境未配置；代码只报告配置布尔值，从不读取发送或记录密钥。Hub 沙箱（`MORPH_HUB_URL`）仍未提供，A2A hello/publish/fetch 保持待发布。
6. `GET https://evomap.ai/a2a/assets/categories` **无任何 Authorization 头即 HTTP 200**（2026-09-22 本机实测，600 字节），字段为 `by_type[{type,count}]`（Gene/Capsule/EvolutionEvent）与 `by_gene_category[{category,count}]`。这是面向浏览的社区统计上下文：**不参与运行拓扑，类别计数不得当作本项目指标**。同搜索一样：恰好一次请求、无重试、进程内缓存。
7. 资产详情三路由（2026-09-23 本机实测，均为只读 GET、无 Authorization 即 200；与官方 wiki `05-a2a-protocol` REST 表一致）：
   - `GET /a2a/assets/:id`：单资产详情；比搜索响应多 `lineage{ancestors,children}`、`fork_count`、`iteration_count`、`bundle_capsule`、`user_vote`；未知 id 返回 404 `{"error":"asset_not_found"}`。
   - `GET /a2a/assets/:id/timeline`：任意资产可用；`{asset_id, asset_type, events[{type,timestamp,description,data?}], total}`。
   - `GET /a2a/assets/:id/branches`：仅 Gene；`{gene_asset_id, gene_summary, branches[{node_id,node_alias,capsule_count,avg_gdi,avg_confidence,success_rate,best_capsule{asset_id,gdi_score,summary,created_at},capsules[{asset_id,gdi_score,confidence,status,outcome,summary,created_at}]}], total_capsules, total_branches}`；对 Capsule 返回 404 `{"error":"asset_not_found_or_not_gene"}`（因此服务端只在 detail 判定为 Gene 后才请求该路由）。
   - 未知格式 id（含空格符号）同样 404；官方 404 提示确认 id 应为 `sha256:...` 格式，本轨据此将入站校验收紧为 `^sha256:[0-9a-f]{64}$`。

## `/api/evomap` 响应契约（`morph.evomap.readonly/1`）

`GET /api/evomap?q=<1..500字符>&type=<Gene|Capsule>&limit=<1..50>`，三个参数均可选（默认 `q=repair`、`limit=10`、无 type）。越界返回 `400 {"schema","error":"invalid_query","detail"}`。

```jsonc
{
  "schema": "morph.evomap.readonly/1",
  "generated_at": 0.0,                 // Unix 秒
  "hub": {
    "base_url": "https://evomap.ai",
    "endpoint": "/a2a/assets/semantic-search",
    "categories_endpoint": "/a2a/assets/categories",
    "auth": "public_read_observed_no_credentials_sent",
    "api_key_configured": false        // 仅布尔；密钥值不出现在任何输出
  },
  "community_search": {
    "state": "live | cache | stale_cache | error",
    "query": {"q": "repair", "limit": 10, "type": "Gene"},
    "fetched_at": 0.0,                 // null = 从未成功
    "cache_ttl_seconds": 300.0,
    "cache_age_seconds": 0.0,          // null = 本次为 live
    "error": null,                     // 固定码：timeout / connection_failed /
                                       // transport_error / http_<status> /
                                       // malformed_response / response_too_large
    "search_status": "found",          // Hub 原样透传
    "provider": "v2-pipeline",         // Hub 原样透传
    "count": 10,
    "assets": [/* 白名单投影：asset_id, asset_type, status, short_title,
        nl_summary, trigger_text, gdi_* 评分, upvotes/view_count 等计数,
        payload/verification 原样对象；绝不补全缺失字段 */]
  },
  "community_categories": {
    "state": "live | cache | stale_cache | error",
    "fetched_at": 0.0,                 // null = 从未成功
    "cache_ttl_seconds": 300.0,
    "cache_age_seconds": 0.0,          // null = 本次为 live
    "error": null,                     // 与 community_search 同一套固定码
    "by_type": [{"type": "Gene", "count": 2509437} /* …strict 校验后原样计数 */],
    "by_gene_category": [{"category": "repair", "count": 342783} /* … */]
  },
  "local_pool": {
    "state": "ok | empty | unconfigured | error",
    "source": "sqlite:metadata.db",    // null = 未配置
    "error": null,                     // store_missing / store_unreadable
    "genes": [/* 共享 Gene 契约重验后的正文投影 + metabolism_gene_state
        的 weight/use_count/archived_at/original_run_uri（存在才带）*/],
    "notes": ["…"]
  },
  "boundaries": ["…"]                  // 面向页面的固定边界声明
}
```

给 S 轨的接线要点：`community_search`、`community_categories` 与 `local_pool` 都是 **EvoMap 上下文数据，不是运行拓扑事实**；按 `state` 显示来源标注（live/cache/stale_cache/error 与 sqlite 本地池），error 时展示固定错误码即可，不要自行翻译远端文本。`community_categories` 的计数是 Hub 社区统计，只能作为浏览上下文展示，不得接入拓扑图或当作本项目验收/代谢指标。密钥永远不会出现在响应里。

## `/api/evomap/asset` 响应契约（`morph.evomap.asset/1`，资产点击触发）

`GET /api/evomap/asset?id=<asset_id>`，`id` 必填且严格校验 `^sha256:[0-9a-f]{64}$`；不符返回 `400 {"schema":"morph.evomap.asset/1","error":"invalid_asset_id","detail"}`，校验失败不发任何 Hub 请求。

```jsonc
{
  "schema": "morph.evomap.asset/1",
  "generated_at": 0.0,                 // Unix 秒
  "hub": {
    "base_url": "https://evomap.ai",
    "asset_endpoint": "/a2a/assets/{asset_id}",
    "timeline_endpoint": "/a2a/assets/{asset_id}/timeline",
    "branches_endpoint": "/a2a/assets/{asset_id}/branches",
    "auth": "public_read_observed_no_credentials_sent",
    "api_key_configured": false
  },
  "asset_id": "sha256:…",
  "asset_detail": {                    // GET /a2a/assets/:id 的白名单投影
    "state": "live | cache | stale_cache | error",
    "fetched_at": 0.0, "cache_ttl_seconds": 300.0,
    "cache_age_seconds": 0.0,          // null = 本次为 live
    "error": null,                     // 与 /api/evomap 同一套固定码；Hub 404 = http_404
    "asset": {/* 与搜索资产同白名单 + 详情多出的 lineage/fork_count/
        iteration_count/bundle_capsule/user_vote；error 时为 null */}
  },
  "asset_timeline": {                  // GET /a2a/assets/:id/timeline（任意资产）
    "state": "live | cache | stale_cache | error",
    "fetched_at": 0.0, "cache_ttl_seconds": 300.0, "cache_age_seconds": 0.0,
    "error": null,
    "asset_type": "Gene",
    "events": [{"type": "promoted", "timestamp": "…", "description": "…", "data": {}}],
    "total": 2
  },
  "gene_branches": {                   // GET /a2a/assets/:id/branches（仅 Gene）
    "state": "live | cache | stale_cache | error | not_applicable | unknown",
    // not_applicable = detail 判定非 Gene；unknown = detail 不可用无法判定；
    // 两种状态都不发 branches 请求
    "fetched_at": 0.0, "cache_ttl_seconds": 300.0, "cache_age_seconds": 0.0,
    "error": null,
    "gene_summary": "…",
    "branches": [{"node_id", "node_alias", "capsule_count", "avg_gdi",
        "avg_confidence", "success_rate",
        "best_capsule": {"asset_id", "gdi_score", "summary", "created_at"},
        "capsules": [{"asset_id", "gdi_score", "confidence", "status",
            "outcome", "summary", "created_at"}]}],
    "total_capsules": 1,
    "total_branches": 1
  },
  "boundaries": ["…"]
}
```

限时限量：按 `asset_id` 进程内缓存（TTL 与搜索相同，默认 300s）；成功结果 TTL 内重复点击不再请求 Hub，首次失败结果不会阻止用户下一次点击重新获取；每次点击最多 3 次只读 GET（detail + timeline + 仅 Gene 的 branches）；缓存上限 64 个资产、超限逐出最旧。三个区块均为 EvoMap 社区上下文，**不是运行拓扑事实**；该端点由点击触发，页面不得轮询。契约已于实现前通过 ORCA handoff 冻结发给 S（dispatch:ctx_25e311a54485）与 I（dispatch:ctx_fe967b0ca4b7）。

## 服务端行为

- `viz/server.py` 新增 `--evomap-store <metadata.db>`；不配置时 `local_pool.state=unconfigured`，社区搜索与类别统计不受影响。输入或锁定的 ECharts 缺失时走降级空仪表盘（`degraded_loader`），`/api/dashboard` 始终返回 200 降级响应而非 500。新增 `GET /api/evomap/asset?id=…`（点击触发的资产详情；严格 id 校验，400 `invalid_asset_id`）。
- 远端获取：httpx、`trust_env=False`、不跟随重定向、15s 超时、1 MiB 响应上限、每个区块恰好一次请求（无重试）；错误码固定化，远端响应文本不进日志不进响应。
- 缓存：进程内；搜索按 `(q,type,limit)` 键，类别统计单键共享；资产视图按 `asset_id` 键、三区块同键分槽（上限 64 个资产，超限逐出最旧）。成功结果 TTL 内标注 `cache`；首次失败不缓存，下一次手动点击重新获取；TTL 后失败且有旧成功值时标注 `stale_cache` 并带错误码。
- 本地池：stdlib `sqlite3` `mode=ro` 只读打开（含不写 journal/WAL），正文逐条经共享 `Gene` 契约重验；不通过的行剔除并计数说明；已归档无正文版本按 T3M 规则不显示。
- 线程安全：单服务实例 + 锁；页面并发不放大 Hub 请求数。

## 测试与验收边界

- `tests/t5/test_evomap.py`（40 项）：MockTransport 覆盖成功投影/无凭据发送/缓存/独立键/超时/429/503/畸形/超大/参数校验（mock 范围，零真实 Hub 请求）；categories 区块覆盖严格字段校验（缺字段/字符串计数/布尔计数/空名/负数均 fail-closed 为 `malformed_response` 且不影响搜索区块）、stale_cache 恢复、无凭据发送；资产视图覆盖严格 id 校验（8 种非法 id 均在校验阶段拒绝、零请求）、Gene 三路由投影与无凭据、Capsule 不发 branches（not_applicable）、404 固定码与手动重试重新请求、TTL 内成功缓存命中零新请求、独立资产键、timeline/branches 畸形 fail-closed 且不影响 detail、无 asset_id 的 capsule 剔除、detail 回声 id 不符判 malformed、stale_cache 恢复、契约形状；真实临时 SQLite 覆盖本地池 ok/missing/unreadable/归档剔除（真实本地读，无网络）；真实本机 HTTP 覆盖 `/api/evomap` 与 `/api/evomap/asset` 路由契约/400/dashboard 降级回归。
- 全量 `pytest`：238 通过、2 失败——失败项 `tests/integration/test_demo_environment.py` 与 `tests/t1/bridge/test_mcp.py` 在干净基线 `972d4ba` 上同样失败（环境变量缺失与 Windows 控制台编码），与本轨无关。
- `python tools/typecheck.py`：55 文件 strict 通过。
- live/mock 边界：本轨全部真实 Hub 请求均为只读 GET、无 POST、无模型调用、无密钥参与。2026-09-22 累计 8 次（搜索/categories 核对与集成）；2026-09-23 资产详情新增：接口核对 9 次（搜索取 id 2 次、detail 2 次含一次 TLS 握手失败重发、timeline 2 次、branches 2 次、未知/畸形 id 3 次）+ 真实服务端端到端 7 次（Gene 3 区块 + Capsule 2 区块 + 未知 id 2 区块；同资产第二次点击全部命中 `cache` 未新发请求）。
- 端到端实测（2026-09-22）：`--evomap-store` 指向真实 `SQLiteStore` 写出的 `metadata.db`，`GET /api/evomap?q=repair&type=Gene&limit=2` 返回 `live` 社区数据 + `ok` 本地池（`gene_repair_boundary` 正文与策略完整）；`type=Mutation` 返回 400 `invalid_query`。
- categories 端到端实测（2026-09-22）：真实服务端 `GET /api/evomap?q=repair&limit=2` 返回 `community_categories.state=live`，`by_type` 三类计数与 curl 直连一致，响应中无任何密钥；同机 `--input` 指向不存在文件时 `GET /api/dashboard` 返回 200 降级空仪表盘（`输入未加载：…`），不再因 except 块变量清除抛 NameError/500。
- 资产详情端到端实测（2026-09-23）：真实服务端 `GET /api/evomap/asset?id=<真实 Gene>` 返回三区块 `live`（detail 51 个白名单字段含 `lineage`/`bundle_capsule`，timeline 2 事件，branches 1 分支 1 capsule），第二次点击三区块全部 `cache` 且带真实 `cache_age_seconds`；真实 Capsule 返回 detail/timeline `live` + branches `not_applicable`（未发 branches 请求）；未知 sha256 id 返回 detail/timeline `error=http_404` + branches `unknown`；`id=gene_abc` 返回 400 `invalid_asset_id`。

## 遗留限制

- 搜索接口费用/配额未知；接入真实页面前如需高频刷新应降低 TTL 或改手动刷新，不做轮询。资产详情三路由费用/配额同样未知；成功结果按资产缓存，首次失败由后续手动点击重新获取，页面不得轮询或自动重试。
- 鉴权端点（hello/fetch/publish/memory）全部未触碰：无 Hub 沙箱、无密钥、且多数为写路由，保持待发布。
- 详情路由的 `?detailed=true` / `?fields=…` 增量行为未验证、未使用；本轨只代理默认响应并做白名单投影。
- 本机首次 curl 出现过一次 TLS 握手失败（schannel，第二次成功）；服务端不重试，该场景会如实显示 `connection_failed`/`transport_error`。
