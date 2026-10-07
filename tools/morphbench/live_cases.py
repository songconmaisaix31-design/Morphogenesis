"""Original, bounded local code-defect tasks; no provider or scheduler here.

Only public specifications and buggy source may enter a model request. Acceptance
stays in the installed product's independent fixed-sample-v1 runner.
"""
from __future__ import annotations

from dataclasses import dataclass


PUBLIC_SPEC = (
    "Repair sample.py, preserving these signatures. clamp(value, lower, upper) "
    "returns value limited to the inclusive interval; reversed bounds raise ValueError. "
    "mean(values) returns the arithmetic mean; an empty list raises ValueError. "
    "unique(items) returns first occurrences in input order without mutating input. "
    "Use only pure Python functions, no imports, IO, tools, decorators, or runtime introspection."
)

_CLAMP = '''def clamp(value, lower, upper):
    if lower > upper:
        raise ValueError("reversed bounds")
    return max(lower, min(value, upper))
'''
_MEAN = '''def mean(values):
    if not values:
        raise ValueError("empty values")
    return sum(values) / len(values)
'''
_UNIQUE = '''def unique(items):
    result = []
    for item in items:
        if item not in result:
            result.append(item)
    return result
'''


@dataclass(frozen=True)
class Defect:
    name: str
    family: str
    source: str


def _source(clamp: str = _CLAMP, mean: str = _MEAN, unique: str = _UNIQUE) -> str:
    return "\n".join((clamp, mean, unique))


DEFECTS = (
    Defect("clamp-reversed", "clamp", _source(clamp=_CLAMP.replace(
        '    if lower > upper:\n        raise ValueError("reversed bounds")\n', ""))),
    Defect("clamp-interval", "clamp", _source(clamp=_CLAMP.replace(
        "max(lower, min(value, upper))", "min(lower, max(value, upper))"))),
    Defect("mean-denominator", "mean", _source(mean=_MEAN.replace(
        "len(values)", "(len(values) + 1)"))),
    Defect("mean-empty", "mean", _source(mean=_MEAN.replace(
        'raise ValueError("empty values")', "return 0"))),
    Defect("unique-duplicates", "unique", _source(unique='''def unique(items):
    return list(items)
''')),
    Defect("unique-order", "unique", _source(unique='''def unique(items):
    result = []
    for item in items:
        if item not in result:
            result.append(item)
    return result[::-1]
''')),
)

BY_NAME = {case.name: case for case in DEFECTS}
# Experience generation starts with all three functions defective. Its approved
# solution is obtained from the model, not seeded as the transfer reference.
GENERATION_CASE = Defect("generation-composite", "composite", _source(
    clamp=BY_NAME["clamp-interval"].source.split("\ndef mean", 1)[0] + "\n",
    mean=_MEAN.replace("len(values)", "(len(values) + 1)"),
    unique='''def unique(items):
    return list(items)
'''))
BY_NAME[GENERATION_CASE.name] = GENERATION_CASE
# Arrival intervention is fixed independently of observed success.
PHASES = (
    ("clamp-reversed", "clamp-interval", "clamp-reversed", "mean-denominator"),
    ("unique-duplicates", "unique-order", "unique-duplicates", "mean-empty"),
    ("unique-order", "unique-duplicates", "unique-order", "mean-denominator"),
)
# All styles are truthful, task-relevant help; none deliberately damages answers.
PROFILES = {
    "boundaries": "Review interval boundaries, invalid inputs and comparison direction.",
    "arithmetic": "Review aggregation, denominator handling and empty collections.",
    "order": "Review stable ordering, deduplication and input preservation.",
}
PROFILE_ORDER = (("boundaries", "arithmetic", "order"),
                 ("boundaries", "arithmetic", "order"),
                 ("order", "arithmetic", "boundaries"))


def model_material(name: str) -> dict[str, str]:
    case = BY_NAME[name]
    return {"instruction": PUBLIC_SPEC, "source": case.source}
