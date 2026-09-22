# T3 topology handoff

## Scope and evidence

`topology.TopologyEngine` is an in-memory, instance-level implementation of
the T0 `TopologyEngine` protocol.  Its tests are **contract_local** only: they
exercise real calls to this local implementation, but do not prove a model,
remote interface, or task run is live.

The update rule is the project heuristic
`D = (1 - lambda) * D + alpha * Q * s`, where `s` is the observed binary
success signal (`1` for success, `0` for failure). A failure therefore lowers
a positive weight by the same decay term; it is not a hidden negative-reward
variant of the formula. It makes no claim of convergence, optimality, or
automatic topology growth.

## T2 API and call order

Construct one engine per concrete routing source:

```python
engine = TopologyEngine(
    source=planner_0,
    connections=[Connection(src=planner_0, dst=builder_0, weight=1.0)],
)
target = engine.select(available_targets)  # AgentId | None
```

After executing the target, prefer the message-aware path:

```python
changed = engine.record_feedback(
    feedback=envelope,
    success=verified_success,
    route_source=planner_0,
    route_target=target,
)
```

`envelope.attempt.agent` must equal `route_target`; all three routing and
feedback identities are concrete `AgentId` values, never a Role.  The envelope
sender is the feedback reporter and is intentionally separate from the
routed edge endpoints, allowing an independent reviewer to report a builder's
attempt.  `record_feedback` returns `False` without mutation for either a
previous `msg_id` or a previous `AttemptId`; `record(attempt, success)` is the
protocol-compatible fallback and is idempotent by attempt.

Capability checks in `tests/t3/topology/test_engine.py` prove (locally) that a
single success or failure changes the subsequent `select()` result and that
both duplicate dimensions do not reward twice.

## Connection lifecycle

Only explicitly configured directed `Connection(src: AgentId, dst: AgentId)`
objects can be selected or updated.  `candidate_connections(targets)` merely
returns currently missing, distinct-target candidates in caller order,
deduplicated by target instance;
`add_connection(candidate)` is the separate, explicit admission step.  Thus
updating an existing edge never claims to create a new edge.

Finite updates do not imply a link becomes zero or disappears.  `prune()`
requires all of: weight below `prune_threshold`, at least
`low_activity_window` explicit `advance_idle_window()` calls (each decays an
active edge once by `1 - lambda`), and preservation of `min_active_outgoing`;
`required=True` links (including required review dependencies) are never
pruned for low weight.

All policy and connection numeric fields use frozen Pydantic contracts with
`allow_inf_nan=False` plus nonnegative/positive field bounds.  No graph
framework, persistence, scheduler, mock, or metabolism behavior is introduced.

## Lifecycle boundary

An engine instance is per run and intentionally in-memory. Its duplicate sets
are only valid for that process lifetime: a resumed T2 run must rebuild the
engine from its durable event/result history and replay already handled
feedback before accepting new feedback. This module does not claim cross-
process idempotence or persistence.
