"""Typed response contract for the read-only EvoMap endpoint.

The page consumes this JSON as EvoMap-sourced context, never as runtime
topology facts.  Only fields actually observed from the official Hub or the
local runtime store are represented; nothing is fabricated for display.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

EVOMAP_SCHEMA = "morph.evomap.readonly/1"
HUB_BASE_URL = "https://evomap.ai"
SEARCH_PATH = "/a2a/assets/semantic-search"

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
    local_pool: LocalPool
    boundaries: list[str]

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": EVOMAP_SCHEMA,
            "generated_at": self.generated_at,
            "hub": self.hub,
            "community_search": self.community_search.as_dict(),
            "local_pool": self.local_pool.as_dict(),
            "boundaries": self.boundaries,
        }
