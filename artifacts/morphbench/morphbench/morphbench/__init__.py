"""MorphBench — a benchmark suite for decentralized scientific agent swarms.

MorphBench is designed to be *the same benchmark* layer that peer products
(BioML-Bench / ProteinGym / GPT-training-optimization / MLR-Bench /
ScienceAgentBench) report on, extended with swarm-native mechanism metrics
that Morphogenesis claims (no central scheduler, experience metabolism,
fault tolerance, stigmergy coordination).
"""
from .core import TaskSpec, RunOutcome, leaderboard_percentile
from .tasks import TASKS, REGISTRY, list_tasks, get_task
from .runner import run_suite, SuiteReport

__all__ = [
    "TaskSpec",
    "RunOutcome",
    "leaderboard_percentile",
    "TASKS",
    "REGISTRY",
    "list_tasks",
    "get_task",
    "run_suite",
    "SuiteReport",
]
__version__ = "1.0.0"
