"""D-selected semantic changes; ignored archive only, restore exact bytes finally."""
import json
import os
from pathlib import Path
import subprocess
import sys

source, state, sha = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve(), sys.argv[3]
assert source.name == "candidate-src" and source.parent.name == ".runtime"
assert state.parent == source.parent and not state.is_relative_to(source)
probe = Path(__file__).with_name("fc-remediation-independent-0929-focused.py")
old_tests = source / "tests/swarm/test_failure_chain_runtime.py"
cases = [
    ("effect-persistence", "swarm/worker_loop.py",
     "self.ledger.begin_execution(keeper.current, reservation.request_id)", "pass  # D mutation: no persistent unknown-effect fence",
     probe, "test_unknown_settled_effect_restart_and_handoff"),
    ("ttl-worker-guard", "swarm/failure_chain.py",
     'if state == "probing_recovery":\n            claimed = breaker.try_claim_probe(provider, view.reason, worker_id, now=now)',
     'if state == "probing_recovery":\n            claimed = None', probe, "test_ttl_worker_boundary_fences_both_old_results"),
    ("history-watermark", "swarm/breaker.py", "if current.recovered_at is not None:",
     "if False and current.recovered_at is not None:", probe, "test_recovery_watermark_old_history_and_equal_time_new_faults"),
    ("equal-time-new-fault", "swarm/fault_observations.py", "sample.sequence > sequence and sample.occurred_at >= at",
     "sample.sequence > sequence and sample.occurred_at > at", probe, "test_recovery_watermark_old_history_and_equal_time_new_faults"),
    ("dashscope-5xx", "orchestration/provider_adapters/dashscope.py", "if status_code >= 500:",
     "if status_code >= 600:", probe, "test_adapter_status_priority and dashscope and 503"),
    ("evomap-5xx", "orchestration/provider_adapters/evomap.py", "if status_code >= 500:",
     "if status_code >= 600:", probe, "test_real_gateway_request_count and 503"),
    ("cost-from-usage", "swarm/worker_loop.py", "cost_state = self.budget.reservation_cost_state(reservation)",
     'cost_state = "unknown" if result.uncertain else "settled"', probe, "test_current_reservation_cost_and_retained_hold"),
    ("cost-from-global", "swarm/worker_loop.py", "cost_state = self.budget.reservation_cost_state(reservation)",
     'cost_state = "unknown" if settled.cost == "unknown" else "settled"', probe, "test_current_reservation_cost_and_retained_hold"),
    ("original-suspended-transition", "swarm/breaker.py",
     'if _suspension_required(params):\n            return "suspended", ("persist_state", "set_cooldown")',
     'if _suspension_required(params):\n            return "normal", ("persist_state",)',
     old_tests, "test_worker_observation_suspends_provider_and_routes_later_candidate"),
]
state.mkdir(parents=True, exist_ok=True)
env = dict(os.environ, PYTHONPATH=str(source), PYTHONDONTWRITEBYTECODE="1",
           TEMP=str(state), TMP=str(state), OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1", MKL_NUM_THREADS="1")
rows = []
start = int(sys.argv[4]) if len(sys.argv) > 4 else 0
for index, (name, relative, before, after, tests, selected) in enumerate(cases):
    if index < start:
        continue
    path = source / relative
    original = path.read_bytes()
    tracked = subprocess.check_output(["git", "show", f"{sha}:{relative}"])
    assert original == tracked, relative
    assert original.count(before.encode()) == 1, (name, "nonunique mutation target")
    def run(label):
        cmd = [sys.executable, "-m", "pytest", str(tests), "-q", "--tb=short", "-k", selected,
               "--basetemp", str(state / (str(index) + label[0]))]
        result = subprocess.run(cmd, cwd=source, env=env, capture_output=True, text=True, timeout=180)
        (state / (name + "-" + label + ".log")).write_text(result.stdout + result.stderr, encoding="utf-8")
        return result.returncode, result.stdout + result.stderr
    try:
        path.write_bytes(original.replace(before.encode(), after.encode()))
        red, red_log = run("red")
    finally:
        path.write_bytes(original)
        assert path.read_bytes() == original == tracked
    green, green_log = run("restored")
    row = dict(name=name, file=relative, selection=selected, red_exit=red, restored_exit=green,
               byte_restored=True, red_tail=red_log.splitlines()[-4:], green_tail=green_log.splitlines()[-2:])
    rows.append(row)
    (state / "summary.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(json.dumps(row), flush=True)
    assert red == 1 and "FAILED" in red_log and green == 0, row
