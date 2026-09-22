"""Server-side, read-only EvoMap data loop for the dashboard.

Two independent sources, each labelled with its real origin:

- ``community_search``: the official Hub's public read-only endpoint
  ``GET https://evomap.ai/a2a/assets/semantic-search`` (the same route the
  locked ``@evomap/gep-mcp-server`` 1.7.0 uses for ``gep_search_community`` /
  ``gep_list_genes``).  Verified live on 2026-09-22 to return HTTP 200 with
  no Authorization header.  One attempt per fetch, never a retry, results are
  cached in-process so the page cannot poll the Hub.
- ``local_pool``: a read-only SQLite projection of the runtime ``genes`` and
  ``metabolism_gene_state`` tables, revalidated against the shared ``Gene``
  contract.

``MORPH_EVOMAP_API_KEY`` is only inspected for presence (reported as a
boolean); it is never sent, logged or returned because the search route is
public and authenticated behaviour is unverified.
"""

from __future__ import annotations

import json
import os
import sqlite3
import threading
import time
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

import httpx
from pydantic import JsonValue, TypeAdapter, ValidationError

from contracts.resolution import Gene
from viz.evomap_models import (
    ERROR_CONNECTION,
    ERROR_MALFORMED,
    ERROR_STORE_MISSING,
    ERROR_STORE_UNREADABLE,
    ERROR_TIMEOUT,
    ERROR_TOO_LARGE,
    ERROR_TRANSPORT,
    HUB_BASE_URL,
    SEARCH_PATH,
    CommunitySearch,
    EvomapReport,
    LocalPool,
)

MAX_RESPONSE_BYTES = 1024 * 1024
MAX_LIMIT = 50
DEFAULT_LIMIT = 10
MAX_QUERY_CHARS = 500
MAX_GENES = 200
ASSET_TYPES = ("Gene", "Capsule")
DEFAULT_QUERY = "repair"

# Only keys actually observed in the Hub's live response (2026-09-22 probe,
# recorded in docs/tracks/frontend-evomap.md). Unknown keys are dropped, not
# renamed; missing keys stay absent.
_ASSET_SCALARS = frozenset({
    "kind", "asset_id", "asset_type", "local_id", "url", "status",
    "source_node_id", "source_node_alias", "author", "model_name", "trust_tier",
    "created_at", "chain_id", "related_asset_id", "trigger_text", "tags",
    "short_title", "nl_summary", "domain", "compute_saved", "signature",
    "confidence", "success_streak", "call_count", "view_count", "reuse_count",
    "gdi_score", "gdi_score_mean", "gdi_intrinsic", "gdi_usage",
    "gdi_usage_lower", "gdi_social", "gdi_social_lower", "gdi_freshness",
    "upvotes", "downvotes", "agent_rating_avg", "agent_rating_count",
    "callable", "payload_ready", "has_strategy", "has_capsule",
    "validation_status", "validation_credible", "similarity",
})
_ASSET_OBJECTS = frozenset({"payload", "verification"})

_OBJECT = TypeAdapter(dict[str, JsonValue])

BOUNDARIES = [
    "community_search 来自 EvoMap Hub 公开只读接口 /a2a/assets/semantic-search；不是本项目的运行拓扑或任务事实。",
    "local_pool 是本地运行存储的只读投影；archived Gene 正文按 T3M 规则已被本地移除。",
    "服务端每次获取仅一次请求、无自动重试；命中进程内缓存时标注 cache/stale_cache。",
    "MORPH_EVOMAP_API_KEY 只报告是否配置；公开搜索不需要也未使用该密钥。",
    "搜索接口的费用与配额未知；不得把本端点当作轮询来源。",
]


class EvomapQueryError(ValueError):
    """Browser-supplied search parameters outside the documented contract."""


class _FetchError(RuntimeError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def validate_query(q: str | None, asset_type: str | None, limit: str | None) -> dict[str, Any]:
    """Bound browser input exactly like the official MCP tool schema does."""
    query = (q if q is not None else DEFAULT_QUERY).strip()
    if not 1 <= len(query) <= MAX_QUERY_CHARS:
        raise EvomapQueryError("q must be 1..500 characters")
    if asset_type is not None and asset_type not in ASSET_TYPES:
        raise EvomapQueryError("type must be Gene or Capsule")
    try:
        count = int(limit) if limit is not None else DEFAULT_LIMIT
    except ValueError:
        raise EvomapQueryError("limit must be an integer") from None
    if not 1 <= count <= MAX_LIMIT:
        raise EvomapQueryError(f"limit must be 1..{MAX_LIMIT}")
    params: dict[str, Any] = {"q": query, "limit": count}
    if asset_type is not None:
        params["type"] = asset_type
    return params


def _project_asset(item: Any) -> dict[str, Any] | None:
    if not isinstance(item, dict):
        return None
    projected: dict[str, Any] = {}
    for key in _ASSET_SCALARS:
        value = item.get(key)
        if isinstance(value, (str, int, float, bool)) or value is None:
            if key in item:
                projected[key] = value
    for key in _ASSET_OBJECTS:
        value = item.get(key)
        if isinstance(value, dict):
            projected[key] = dict(value)
    return projected if projected else None


class EvomapService:
    """One shared, lock-guarded service per dashboard server process."""

    def __init__(
        self,
        *,
        store_path: Path | None = None,
        cache_ttl_seconds: float = 300.0,
        timeout_seconds: float = 15.0,
        transport: httpx.BaseTransport | None = None,
        clock: Callable[[], float] = time.time,
        environ: Mapping[str, str] | None = None,
    ) -> None:
        if cache_ttl_seconds <= 0 or timeout_seconds <= 0:
            raise ValueError("cache_ttl_seconds and timeout_seconds must be positive")
        self.store_path = store_path
        self.cache_ttl_seconds = cache_ttl_seconds
        self.timeout_seconds = timeout_seconds
        self._transport = transport
        self._clock = clock
        self._environ = os.environ if environ is None else environ
        self._lock = threading.Lock()
        self._cache: dict[tuple[str, str | None, int], tuple[float, CommunitySearch]] = {}

    def report(self, q: str | None, asset_type: str | None, limit: str | None) -> EvomapReport:
        params = validate_query(q, asset_type, limit)
        key = (params["q"], params.get("type"), params["limit"])
        with self._lock:
            cached = self._cache.get(key)
        now = self._clock()
        if cached is not None and now - cached[0] <= self.cache_ttl_seconds:
            return self._build(params, self._with_state(cached[1], "cache", now), now)
        try:
            fresh = self._fetch(params)
        except _FetchError as error:
            if cached is not None:
                stale = self._with_state(cached[1], "stale_cache", now, error=error.code)
                return self._build(params, stale, now)
            empty = CommunitySearch(
                state="error", query=params, fetched_at=None,
                cache_ttl_seconds=self.cache_ttl_seconds, cache_age_seconds=None,
                error=error.code, search_status=None, provider=None, count=0, assets=[],
            )
            return self._build(params, empty, now)
        with self._lock:
            self._cache[key] = (now, fresh)
        return self._build(params, self._with_state(fresh, "live", now), now)

    def _with_state(
        self, search: CommunitySearch, state: str, now: float, *, error: str | None = None
    ) -> CommunitySearch:
        fetched_at = search.fetched_at
        return CommunitySearch(
            state=state, query=search.query, fetched_at=fetched_at,
            cache_ttl_seconds=search.cache_ttl_seconds,
            cache_age_seconds=(now - fetched_at) if fetched_at is not None else None,
            error=error, search_status=search.search_status, provider=search.provider,
            count=search.count, assets=search.assets,
        )

    def _build(self, params: dict[str, Any], search: CommunitySearch, now: float) -> EvomapReport:
        return EvomapReport(
            generated_at=now,
            hub={
                "base_url": HUB_BASE_URL,
                "endpoint": SEARCH_PATH,
                "auth": "public_read_observed_no_credentials_sent",
                "api_key_configured": bool(self._environ.get("MORPH_EVOMAP_API_KEY", "").strip()),
            },
            community_search=search,
            local_pool=self._local_pool(),
            boundaries=BOUNDARIES,
        )

    def _fetch(self, params: dict[str, Any]) -> CommunitySearch:
        """Exactly one GET against the official public search route; no retry."""
        raw = bytearray()
        status: int | None = None
        try:
            with httpx.Client(
                transport=self._transport, trust_env=False, follow_redirects=False,
                timeout=httpx.Timeout(self.timeout_seconds),
            ) as client:
                with client.stream("GET", HUB_BASE_URL + SEARCH_PATH, params=params) as response:
                    status = response.status_code
                    for chunk in response.iter_bytes():
                        remaining = MAX_RESPONSE_BYTES - len(raw)
                        raw.extend(chunk[:remaining])
                        if len(chunk) > remaining:
                            raise _FetchError(ERROR_TOO_LARGE)
        except _FetchError:
            raise
        except httpx.TimeoutException:
            raise _FetchError(ERROR_TIMEOUT) from None
        except (httpx.ConnectError, httpx.NetworkError):
            raise _FetchError(ERROR_CONNECTION) from None
        except httpx.HTTPError:
            raise _FetchError(ERROR_TRANSPORT) from None
        if status != 200:
            raise _FetchError(f"http_{status}")
        try:
            body = _OBJECT.validate_json(bytes(raw), strict=True)
        except (ValidationError, ValueError):
            raise _FetchError(ERROR_MALFORMED) from None
        raw_assets = body.get("assets")
        if not isinstance(raw_assets, list):
            raise _FetchError(ERROR_MALFORMED)
        assets = [p for p in (_project_asset(item) for item in raw_assets) if p is not None]
        search_status = body.get("search_status")
        provider = body.get("provider")
        count = body.get("count")
        return CommunitySearch(
            state="live", query=params, fetched_at=self._clock(),
            cache_ttl_seconds=self.cache_ttl_seconds, cache_age_seconds=None, error=None,
            search_status=search_status if isinstance(search_status, str) else None,
            provider=provider if isinstance(provider, str) else None,
            count=count if isinstance(count, int) and count >= 0 else len(assets),
            assets=assets,
        )

    def _local_pool(self) -> LocalPool:
        if self.store_path is None:
            return LocalPool(
                state="unconfigured", source=None, error=None, genes=[],
                notes=["未配置 --evomap-store；本地池视图关闭。"],
            )
        return read_local_pool(self.store_path)


def read_local_pool(path: Path, *, max_genes: int = MAX_GENES) -> LocalPool:
    """Open the runtime SQLite store read-only and project shared Gene rows.

    stdlib sqlite3 in mode=ro keeps the viz process dependency-free for this
    view and guarantees no writes, including no journal/WAL side effects from
    opening the file.
    """
    resolved = path.resolve()
    if path.is_symlink() or not resolved.is_file():
        return LocalPool(
            state="error", source=None, error=ERROR_STORE_MISSING, genes=[],
            notes=["本地存储文件不存在；保持空态而非推断。"],
        )
    try:
        connection = sqlite3.connect(
            f"file:{resolved.as_posix()}?mode=ro", uri=True, timeout=2.0,
        )
    except sqlite3.Error:
        return LocalPool(
            state="error", source=None, error=ERROR_STORE_UNREADABLE, genes=[],
            notes=["本地存储无法以只读方式打开（可能被占用或损坏）。"],
        )
    try:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        states: dict[tuple[str, int], dict[str, Any]] = {}
        if "metabolism_gene_state" in tables:
            rows = connection.execute(
                "SELECT gene_id, version, provenance, original_run_uri, created_at,"
                " weight, use_count, archived_at FROM metabolism_gene_state"
            ).fetchall()
            for gene_id, version, provenance, run_uri, created, weight, used, archived in rows:
                states[(str(gene_id), int(version))] = {
                    "state_provenance": provenance,
                    "original_run_uri": run_uri,
                    "created_at": created,
                    "weight": weight,
                    "use_count": used,
                    "archived_at": archived,
                }
        genes: list[dict[str, Any]] = []
        invalid = 0
        if "genes" in tables:
            body_rows = connection.execute(
                "SELECT gene_id, version, body FROM genes"
                " ORDER BY gene_id, version LIMIT ?",
                (max_genes,),
            ).fetchall()
            for gene_id, version, body in body_rows:
                try:
                    gene = Gene.model_validate_json(body)
                except (ValidationError, ValueError):
                    invalid += 1
                    continue
                entry: dict[str, Any] = {
                    "gene_id": gene.ref.gene_id,
                    "version": gene.ref.version,
                    "asset_id": gene.ref.asset_id,
                    "provenance": gene.provenance,
                    "signals_match": list(gene.signals_match),
                    "strategy": list(gene.strategy),
                    "avoid": list(gene.avoid),
                    "verification": list(gene.verification),
                }
                state = states.get((str(gene_id), int(version)))
                if state is not None:
                    entry.update(state)
                genes.append(entry)
        cached = {(str(gene_id), int(version)) for gene_id, version, _ in
                  (body_rows if "genes" in tables else [])}
        archived_without_body = sorted(
            key for key, state in states.items()
            if state["archived_at"] is not None and key not in cached
        )
        notes = ["本地 SQLite 只读投影；Gene 正文经共享契约重验。"]
        if invalid:
            notes.append(f"{invalid} 行正文未通过共享契约，已剔除。")
        if archived_without_body:
            notes.append(
                f"{len(archived_without_body)} 个已归档版本无本地正文（T3M 归档即删除缓存），不显示。"
            )
        return LocalPool(
            state="ok" if genes else "empty",
            source=f"sqlite:{resolved.name}", error=None, genes=genes, notes=notes,
        )
    except sqlite3.Error:
        return LocalPool(
            state="error", source=None, error=ERROR_STORE_UNREADABLE, genes=[],
            notes=["本地存储读取失败（锁定或 schema 不符）。"],
        )
    finally:
        connection.close()


def _json_default(value: Any) -> Any:
    raise TypeError(f"not JSON serializable: {type(value).__name__}")


def dumps_report(report: EvomapReport) -> bytes:
    return json.dumps(report.as_dict(), ensure_ascii=False, default=_json_default).encode("utf-8")
