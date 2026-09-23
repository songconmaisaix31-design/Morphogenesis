"""Typed response contract for the read-only EvoMap endpoint.

The page consumes this JSON as EvoMap-sourced context, never as runtime
topology facts.  Only fields actually observed from the official Hub or the
local runtime store are represented; nothing is fabricated for display.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

EVOMAP_SCHEMA = "morph.evomap.readonly/1"
ASSET_VIEW_SCHEMA = "morph.evomap.asset/1"
HUB_BASE_URL = "https://evomap.ai"
SEARCH_PATH = "/a2a/assets/semantic-search"
CATEGORIES_PATH = "/a2a/assets/categories"
ASSETS_PATH = "/a2a/assets"
ASSET_DETAIL_PATH = "/a2a/assets/{asset_id}"
ASSET_TIMELINE_PATH = "/a2a/assets/{asset_id}/timeline"
ASSET_BRANCHES_PATH = "/a2a/assets/{asset_id}/branches"

# Fixed, sanitized error codes; remote response text never enters the report.
ERROR_TIMEOUT = "timeout"
ERROR_CONNECTION = "connection_failed"
ERROR_TRANSPORT = "transport_error"
ERROR_MALFORMED = "malformed_response"
ERROR_TOO_LARGE = "response_too_large"
ERROR_STORE_MISSING = "store_missing"
ERROR_STORE_UNREADABLE = "store_unreadable"


@dataclass(frozen=True)
class CommunitySearch:
    """One bounded, cache-annotated read of the official public asset search."""

    state: str  # live | cache | stale_cache | error | disabled
    query: dict[str, Any]
    fetched_at: float | None
    cache_ttl_seconds: float
    cache_age_seconds: float | None
    error: str | None
    search_status: str | None
    provider: str | None
    count: int
    assets: list[dict[str, Any]]

    def as_dict(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "query": self.query,
            "fetched_at": self.fetched_at,
            "cache_ttl_seconds": self.cache_ttl_seconds,
            "cache_age_seconds": self.cache_age_seconds,
            "error": self.error,
            "search_status": self.search_status,
            "provider": self.provider,
            "count": self.count,
            "assets": self.assets,
        }


@dataclass(frozen=True)
class CommunityCategories:
    """One bounded, cache-annotated read of the official public category counts.

    Browsing context only: the counts are Hub community statistics, never
    run-topology facts or project metrics.
    """

    state: str  # live | cache | stale_cache | error
    fetched_at: float | None
    cache_ttl_seconds: float
    cache_age_seconds: float | None
    error: str | None
    by_type: list[dict[str, Any]]
    by_gene_category: list[dict[str, Any]]

    def as_dict(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "fetched_at": self.fetched_at,
            "cache_ttl_seconds": self.cache_ttl_seconds,
            "cache_age_seconds": self.cache_age_seconds,
            "error": self.error,
            "by_type": self.by_type,
            "by_gene_category": self.by_gene_category,
        }


@dataclass(frozen=True)
class LocalPool:
    """Read-only projection of the local runtime Gene store."""

    state: str  # ok | empty | unconfigured | error
    source: str | None
    error: str | None
    genes: list[dict[str, Any]]
    notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "source": self.source,
            "error": self.error,
            "genes": self.genes,
            "notes": self.notes,
        }


@dataclass(frozen=True)
class EvomapReport:
    generated_at: float
    hub: dict[str, Any]
    community_search: CommunitySearch
    community_categories: CommunityCategories
    local_pool: LocalPool
    boundaries: list[str]

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": EVOMAP_SCHEMA,
            "generated_at": self.generated_at,
            "hub": self.hub,
            "community_search": self.community_search.as_dict(),
            "community_categories": self.community_categories.as_dict(),
            "local_pool": self.local_pool.as_dict(),
            "boundaries": self.boundaries,
        }


def _block_dict(block: _BlockMeta) -> dict[str, Any]:
    return {
        "state": block.state,
        "fetched_at": block.fetched_at,
        "cache_ttl_seconds": block.cache_ttl_seconds,
        "cache_age_seconds": block.cache_age_seconds,
        "error": block.error,
    }


@dataclass(frozen=True)
class _BlockMeta:
    state: str  # live | cache | stale_cache | error (+ per-block extras)
    fetched_at: float | None
    cache_ttl_seconds: float
    cache_age_seconds: float | None
    error: str | None


@dataclass(frozen=True)
class AssetDetail(_BlockMeta):
    """One bounded, cache-annotated read of ``GET /a2a/assets/:id``.

    ``asset`` is the same observed-field whitelist projection the search block
    uses, plus the detail-only keys observed live (lineage, fork_count,
    iteration_count, bundle_capsule, user_vote); None when state is error.
    """

    asset: dict[str, Any] | None

    def as_dict(self) -> dict[str, Any]:
        return {**_block_dict(self), "asset": self.asset}


@dataclass(frozen=True)
class AssetTimeline(_BlockMeta):
    """One bounded, cache-annotated read of ``GET /a2a/assets/:id/timeline``.

    Events are strictly validated: each must carry string type / timestamp /
    description; ``data`` passes through only when it is an object.
    """

    asset_type: str | None
    events: list[dict[str, Any]]
    total: int

    def as_dict(self) -> dict[str, Any]:
        return {
            **_block_dict(self),
            "asset_type": self.asset_type,
            "events": self.events,
            "total": self.total,
        }


@dataclass(frozen=True)
class GeneBranches(_BlockMeta):
    """One bounded, cache-annotated read of ``GET /a2a/assets/:id/branches``.

    Extra states: ``not_applicable`` (detail succeeded and the asset is not a
    Gene; no request sent) and ``unknown`` (detail unavailable, so Gene-ness is
    undetermined; no request sent).
    """

    gene_summary: str | None
    branches: list[dict[str, Any]]
    total_capsules: int | None
    total_branches: int | None

    def as_dict(self) -> dict[str, Any]:
        return {
            **_block_dict(self),
            "gene_summary": self.gene_summary,
            "branches": self.branches,
            "total_capsules": self.total_capsules,
            "total_branches": self.total_branches,
        }


@dataclass(frozen=True)
class AssetView:
    """Click-triggered per-asset context; never runtime-topology facts."""

    generated_at: float
    hub: dict[str, Any]
    asset_id: str
    asset_detail: AssetDetail
    asset_timeline: AssetTimeline
    gene_branches: GeneBranches
    boundaries: list[str]

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": ASSET_VIEW_SCHEMA,
            "generated_at": self.generated_at,
            "hub": self.hub,
            "asset_id": self.asset_id,
            "asset_detail": self.asset_detail.as_dict(),
            "asset_timeline": self.asset_timeline.as_dict(),
            "gene_branches": self.gene_branches.as_dict(),
            "boundaries": self.boundaries,
        }
