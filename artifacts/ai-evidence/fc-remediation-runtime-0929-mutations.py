"""Scoped semantic mutations on an ignored source export; never on a live tree.

Run with the authorized existing Python: script.py <.runtime/source-export>.
All generated logs and test state stay beside that export, under .runtime.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


def main() -> None:
    source = Path(sys.argv[1]).resolve()
    runtime = source.parent
    assert runtime.name == ".runtime" and (source / "swarm/worker_loop.py").is_file()
    target = source / "swarm/worker_loop.py"
    original = target.read_bytes()
    assert b"\r\n" not in original
    original_hash = hashlib.sha256(original).hexdigest()
    env = dict(os.environ, PYTHONPATH=str(source), PYTHONDONTWRITEBYTECODE="1")
    recovery = "tests/swarm/test_unknown_effect_recovery.py"
    cost = "tests/swarm/test_reservation_cost_state.py"
    mutations = [
        ("effect-persistence", b"self.ledger.begin_execution(keeper.current, reservation.request_id)",
         b"pass  # mutation: omit the durable no-resend fact",
         [recovery + "::test_settled_unknown_effect_never_resends_after_process_restart",
          recovery + "::test_unknown_effect_after_real_lease_handoff_cannot_be_sent_by_successor"]),
        ("usage-only-cost", b"cost_state = self.budget.reservation_cost_state(reservation)",
         b'cost_state = "unknown" if result.uncertain else "settled"', [cost, "-k", "without_prices"]),
        ("aggregate-cost", b"cost_state = self.budget.reservation_cost_state(reservation)",
         b'cost_state = "unknown" if self.budget.snapshot().cost == "unknown" else "settled"',
         [cost, "-k", "prior_unknown"]),
    ]
    results = []

    def gate(name, args):
        command = [sys.executable, "-m", "pytest", "-q", *args,
                   "--basetemp=" + str(runtime / "test-state" / name), "-p", "no:cacheprovider"]
        with (runtime / (name + ".log")).open("wb") as log:
            result = subprocess.run(command, cwd=source, env=env, stdout=log,
                                    stderr=subprocess.STDOUT, timeout=180, check=False)
        return {"command": command, "exit": result.returncode,
                "log": str(runtime / (name + ".log"))}

    for name, needle, replacement, args in mutations:
        assert original.count(needle) == 1
        try:
            target.write_bytes(original.replace(needle, replacement))
            red = gate("mutation-" + name, args)
        finally:
            target.write_bytes(original)
            restored = target.read_bytes()
            assert restored == original
            assert hashlib.sha256(restored).hexdigest() == original_hash
        green = gate("restored-" + name, [recovery, cost])
        record = {"mutation": name, "original_sha256": original_hash,
                  "restored_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
                  "red": red, "green": green}
        results.append(record)
        (runtime / "mutation-results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
        print(json.dumps(record), flush=True)
        assert red["exit"] == 1, "Mutation was not caught as a test assertion failure"
        assert green["exit"] == 0, "Restoration must be green"


if __name__ == "__main__":
    main()
