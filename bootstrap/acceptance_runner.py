"""Fixed independent cases. Invoked by verifier with python -I -S, never copied to executor."""

import importlib.util
import json
from pathlib import Path
import sys
from types import ModuleType
import unittest


class CheckpointResult(unittest.TextTestResult):
    """Report the actual unittest result, including failing subtests, as JSON."""

    def checkpoint_results(self) -> dict[str, bool | None]:
        failed = {test.id().split(" (")[0].rsplit(".", 1)[-1]
                  for test, _ in self.failures + self.errors}
        skipped = {test.id().split(".")[-1] for test, _ in self.skipped}
        return {name.removeprefix("test_"): None if name in skipped else name not in failed
                for name in ("test_clamp", "test_mean", "test_unique")}


class CheckpointRunner(unittest.TextTestRunner):
    def _makeResult(self) -> CheckpointResult:
        return CheckpointResult(self.stream, self.descriptions, self.verbosity)


def load_candidate(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("candidate_under_review", path)
    if spec is None or spec.loader is None:
        raise ValueError("candidate is not an importable Python module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(path: Path) -> bool:
    module = load_candidate(path)

    class AcceptanceCases(unittest.TestCase):
        def test_clamp(self) -> None:
            for value, lower, upper, expected in [
                (-2, 0, 5, 0), (9, 0, 5, 5), (3, 0, 5, 3),
                (0, 0, 0, 0), (-2.5, -4, -1, -2.5), (1, 1, 3, 1),
            ]:
                with self.subTest(value=value, lower=lower, upper=upper):
                    self.assertEqual(module.clamp(value, lower, upper), expected)
            with self.assertRaises(ValueError):
                module.clamp(1, 3, 2)

        def test_mean(self) -> None:
            for values, expected in [
                ([2, 4, 6], 4.0), ([7], 7.0), ([-1, 1], 0.0),
                ([0.5, 1.5], 1.0), ([-9, -3], -6.0),
            ]:
                with self.subTest(values=values):
                    self.assertAlmostEqual(module.mean(values), expected)
            with self.assertRaises(ValueError):
                module.mean([])

        def test_unique(self) -> None:
            for items, expected in [
                (["b", "a", "b", "c", "a"], ["b", "a", "c"]),
                ([], []), (["x", "x"], ["x"]), (["z", "a"], ["z", "a"]),
            ]:
                with self.subTest(items=items):
                    original = list(items)
                    self.assertEqual(module.unique(items), expected)
                    self.assertEqual(items, original)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(AcceptanceCases)
    result = CheckpointRunner(verbosity=2).run(suite)
    assert isinstance(result, CheckpointResult)
    print("MORPH_CHECKPOINTS=" + json.dumps({
        "tests_run": result.testsRun, "checks": result.checkpoint_results(),
    }))
    return result.wasSuccessful()


if __name__ == "__main__":
    raise SystemExit(0 if run(Path(sys.argv[1]).resolve()) else 1)
