"""Evidence dimensions are independent; replay never upgrades live acceptance."""

from typing import Literal, Self

from pydantic import model_validator

from contracts.base import Contract

Provenance = Literal["live", "replay", "mock"]
CheckState = Literal["not_run", "passed", "failed", "blocked"]


class Acceptance(Contract):
    contract_local: CheckState = "not_run"
    interface_live: CheckState = "not_run"
    task_live: CheckState = "not_run"
    provenance: Provenance = "live"
    original_run_uri: str | None = None

    @model_validator(mode="after")
    def validate_evidence(self) -> Self:
        if self.provenance == "replay" and not self.original_run_uri:
            raise ValueError("replay requires original_run_uri")
        if self.provenance != "live" and (
            self.interface_live == "passed" or self.task_live == "passed"
        ):
            raise ValueError("mock/replay cannot establish live acceptance")
        return self
