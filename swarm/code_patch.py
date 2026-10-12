"""Data-only patch admission for the fixed repair task, with no model calls."""

from __future__ import annotations

from pydantic import Field

from contracts.base import Contract
from contracts.identity import AttemptId
from local_assets.models import Candidate, FileChange, SampleValidationPolicy
from local_assets.sample_validation import inspect_sample
from local_assets.validate import blast_radius, inspect_candidate


class SamplePatch(Contract):
    changes: tuple[FileChange, ...] = Field(min_length=1, max_length=1)


def candidate_from_patch(patch: SamplePatch, policy: SampleValidationPolicy, *,
                         attempt: AttemptId, scope: str, base_revision: str,
                         base_head: str) -> Candidate:
    """Bind untrusted patch bytes to host identities before materialization.

    Provider invocation/usage remains the bounded Executor owner's job. Send
    only the task description and input source to the provider, never acceptance.
    """
    candidate = Candidate(attempt=attempt, scope=scope, base_revision=base_revision,
                          base_head=base_head, changes=patch.changes,
                          declared_files=1, declared_lines=0)
    files, lines = blast_radius(candidate)
    candidate = candidate.model_copy(update={"declared_files": files, "declared_lines": lines})
    inspect_candidate(candidate)
    inspect_sample(candidate, policy)
    return candidate
