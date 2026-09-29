# H1 exact candidate quotes — AI preparation only

Candidate: `c552250c0d07f5f70f09eb0a5ab3c322195e34ec`. Not a model review; H1/H3 unsigned.

## H1-01: budget A/B: holds versus admitted

`c552250c0d07f5f70f09eb0a5ab3c322195e34ec:swarm/budget.py:77` through line 86.

```python
    def _snapshot(self, db: sqlite3.Connection, worker_id: str | None, now: float) -> BudgetSnapshot:
        swarm = db.execute("SELECT breaker FROM swarm_budgets WHERE swarm_id=?", (self.swarm_id,)).fetchone()
        rows = db.execute("SELECT status,tokens,estimate_usd,reserved_usd,request_bound,admitted_usd,usage_metering,cost FROM budget_reservations "
                          "WHERE swarm_id=?", (self.swarm_id,)).fetchall()
        uncertain = sum(row["status"] == "uncertain" for row in rows)
        pending = sum(row["status"] == "pending" for row in rows)
        holds = sum(float(row["reserved_usd"]) for row in rows if row["status"] != "settled")
        spent = sum(float(row["estimate_usd"]) for row in rows if row["estimate_usd"] is not None)
        tokens = sum(int(row["tokens"]) for row in rows if row["tokens"] is not None)
        usage_unknown = any(row["usage_metering"] == "unknown" for row in rows)
```

## H1-02: budget A: task attempt count

`c552250c0d07f5f70f09eb0a5ab3c322195e34ec:swarm/budget.py:164` through line 180.

```python
            if count[0] >= self.policy.limits.max_attempts:
                raise BudgetBlocked("max_attempts")
            task_count = db.execute("SELECT COUNT(*) FROM budget_reservations WHERE swarm_id=? AND task_id=?", (self.swarm_id,task_id)).fetchone()[0]
            if task_count >= self.policy.limits.max_attempts_per_task:
                raise BudgetBlocked("max_attempts_per_task")
            if not task_count and count[1] >= self.policy.limits.max_tasks:
                raise BudgetBlocked("max_tasks")
            state = self._snapshot(db, worker_id, now)
            if state.sleeping:
                raise BudgetBlocked(state.reason or "swarm_sleeping", state.sleep_seconds)
            # Only an in-flight ('pending') hold blocks another reservation for
            # the same task: it is the one state that means a request may still
            # be outstanding. Settled and uncertain reservations are terminal
            # facts; they keep their cumulative holds forever but never block a
            # new, separately-counted attempt on the same task budget.
            if db.execute("SELECT 1 FROM budget_reservations WHERE swarm_id=? AND (request_id=? OR (task_id=? AND status='pending'))",
                          (self.swarm_id, request_id, task_id)).fetchone():
```

## H1-03: budget A: same request or pending conflict

`c552250c0d07f5f70f09eb0a5ab3c322195e34ec:swarm/budget.py:179` through line 181.

```python
            if db.execute("SELECT 1 FROM budget_reservations WHERE swarm_id=? AND (request_id=? OR (task_id=? AND status='pending'))",
                          (self.swarm_id, request_id, task_id)).fetchone():
                raise BudgetBlocked("task_already_reserved_no_retry")
```

## H1-04: budget B: capacity admission

`c552250c0d07f5f70f09eb0a5ab3c322195e34ec:swarm/budget.py:192` through line 203.

```python
            spent = float(db.execute("SELECT COALESCE(SUM(admitted_usd),0) FROM budget_reservations "
                                     "WHERE swarm_id=?", (self.swarm_id,)).fetchone()[0])
            if self.policy.admission_control == "enabled" and spent + state.reserved_estimate_usd + reservation_amount > self.policy.max_cost_usd:
                raise BudgetBlocked("swarm_reservation_capacity", self.policy.burn_window_seconds)
            reservation = Reservation(reservation_id=uuid4().hex, swarm_id=self.swarm_id,
                                      worker_id=worker_id, task_id=task_id, bound=bound,
                                      reserved_estimate_usd=reservation_amount, created_at=now, request_id=request_id,
                                      request_bound=bound.request_bound, admission_control=self.policy.admission_control)
            db.execute("INSERT INTO budget_reservations VALUES (?,?,?,?,?,'pending',?,NULL,NULL,NULL,?,?,'unknown',?,?,'unknown',NULL,NULL)",
                       (reservation.reservation_id, self.swarm_id, worker_id, task_id,
                        reservation.model_dump_json(), now, reservation_amount, request_id, bound.request_bound,
                        self.policy.admission_control))
```

## H1-05: reservation-local cost state

`c552250c0d07f5f70f09eb0a5ab3c322195e34ec:swarm/budget.py:213` through line 225.

```python
    def reservation_cost_state(self, reservation: Reservation) -> Literal["reserved", "settled", "unknown"]:
        """Read one durable hold, never infer its cost from swarm aggregates.

        'settled' here means the ledger has settled a local estimate; it does
        not claim an observed provider bill. Unknown costs retain their holds.
        """
        with connection(self.path) as db:
            row = self._stored(db, reservation)
            if row["status"] == "pending":
                return "reserved"
            if row["status"] == "settled" and row["cost"] != "unknown":
                return "settled"
            return "unknown"
```

## H1-06: unknown rejection retains hold

`c552250c0d07f5f70f09eb0a5ab3c322195e34ec:swarm/budget.py:230` through line 251.

```python
    def mark_unknown_rejection(self, reservation: Reservation) -> BudgetSnapshot:
        """A confirmed provider rejection whose usage/cost stayed unobserved.

        The hold remains open (status 'uncertain', usage/cost 'unknown') and
        keeps counting toward admission capacity under the same task budget,
        but the swarm is not slept: the failure class is a known rejection, so
        a bounded chain switch stays admittable under cumulative holds. A
        genuine unknown effect still uses ``mark_uncertain``, which trips the
        swarm stop. Never fabricates a zero settlement.
        """
        reservation = Reservation.model_validate(reservation.model_dump())
        now = self._now()
        with self._transaction() as db:
            row = self._stored(db, reservation)
            if row["status"] != "pending":
                return self._snapshot(db, reservation.worker_id, now)
            if now < reservation.created_at:
                raise ValueError("time cannot move backwards")
            db.execute("UPDATE budget_reservations SET status='uncertain',settled_at=? WHERE reservation_id=?",
                       (now, reservation.reservation_id))
            return self._snapshot(db, reservation.worker_id, now)

```

## H1-07: budget B: late settle early return

`c552250c0d07f5f70f09eb0a5ab3c322195e34ec:swarm/budget.py:259` through line 280.

```python
    def settle(self, reservation: Reservation, usage: JsonValue) -> BudgetSnapshot:
        reservation = Reservation.model_validate(reservation.model_dump())
        reported = _usage(usage)  # Same strict nonnegative integer + consistent-total gateway parser.
        if reported is not None and reported.total_tokens > 2**63 - 1:
            reported = None  # Cannot persist safely as a SQLite integer; retain uncertain hold.
        now = self._now()
        settlement = json.dumps([reported.prompt_tokens, reported.completion_tokens, reported.total_tokens]) if reported else None
        with self._transaction() as db:
            row = self._stored(db, reservation)
            if row["status"] != "pending":
                if row["settlement"] is not None and settlement is not None and row["settlement"] != settlement:
                    raise ValueError("conflicting usage settlement")
                # Idempotent replay does not overwrite unknown evidence or charge twice.
                return self._snapshot(db, reservation.worker_id, now)
            if now < reservation.created_at:
                raise ValueError("time cannot move backwards")
            try:
                estimate = (self._estimate(reported.prompt_tokens, reported.completion_tokens)
                            if reported is not None else None)
            except (BudgetBlocked, OverflowError):
                estimate = None  # Keep valid observed tokens even if monetary evidence is missing.
            if reported is None:
```

## H1-08: budget B: unknown price and lower usage

`c552250c0d07f5f70f09eb0a5ab3c322195e34ec:swarm/budget.py:281` through line 313.

```python
                db.execute("UPDATE budget_reservations SET status='uncertain',settled_at=? WHERE reservation_id=?",
                           (now, reservation.reservation_id))
                if not self.policy.allow_unknown_usage:
                    self._trip(db, "unknown_usage")
            else:
                if estimate is None:
                    # Operator admission allowance is not a model price. Preserve
                    # the full hold while recording the independently known usage.
                    status = "unknown_cost_allowed" if self.policy.allow_unknown_cost else "uncertain"
                    db.execute("UPDATE budget_reservations SET status=?,usage_metering='verified',cost='unknown',"
                               "settled_at=?,tokens=?,settlement=? WHERE reservation_id=?",
                               (status, now, reported.total_tokens, settlement, reservation.reservation_id))
                    if not self.policy.allow_unknown_cost:
                        self._trip(db, "unknown_cost")
                else:
                    # Usage plus local prices is not a bill. Never free committed
                    # allowance on a lower estimate, even for an unbounded request.
                    admitted = max(estimate, reservation.reserved_estimate_usd)
                    db.execute("UPDATE budget_reservations SET status='settled',usage_metering='verified',cost='estimated',settled_at=?,tokens=?,estimate_usd=?,settlement=?,admitted_usd=? "
                               "WHERE reservation_id=?", (now, reported.total_tokens, estimate, settlement, admitted,
                                                          reservation.reservation_id))
                spent = db.execute("SELECT COALESCE(SUM(estimate_usd),0) FROM budget_reservations WHERE swarm_id=?",
                                   (self.swarm_id,)).fetchone()[0]
                violated = (reported.prompt_tokens > reservation.bound.input_tokens or
                            reported.completion_tokens > reservation.bound.max_output_tokens or
                            reported.total_tokens > self.policy.max_tokens)
                violated = violated or (reservation.bound.request_bound == "verified" and estimate is not None
                                        and estimate > reservation.reserved_estimate_usd)
                if violated:
                    self._trip(db, "provider_bound_violated" if reservation.bound.provider_enforced
                               else "request_token_limit_exceeded")
                elif estimate is not None and spent >= self.policy.max_cost_usd:
                    self._trip(db, "swarm_cost_estimate_exhausted")
```

## H1-09: task eligibility after restart

`c552250c0d07f5f70f09eb0a5ab3c322195e34ec:swarm/task_ledger.py:257` through line 266.

```python
    def _eligible() -> str:
        return ("(t.status IN ('available','partial','handoff') OR (t.status='claimed' AND t.expiry<=?)) AND t.attempts<? "
                "AND t.unconfirmed_request_id IS NULL "
                "AND NOT EXISTS (SELECT 1 FROM dependencies d LEFT JOIN tasks p ON p.swarm_id=d.swarm_id "
                "AND p.task_id=d.dependency_id WHERE d.swarm_id=t.swarm_id AND d.task_id=t.task_id "
                "AND (p.status IS NULL OR p.status!='completed')) "
                "AND NOT EXISTS (SELECT 1 FROM tasks c WHERE c.swarm_id=t.swarm_id AND c.task_id!=t.task_id "
                "AND (c.status='submitting' OR (c.status='claimed' AND c.expiry>?)) AND "
                "(c.scope=t.scope OR substr(c.scope,1,length(t.scope)+1)=t.scope||? "
                "OR substr(t.scope,1,length(c.scope)+1)=c.scope||?))")
```

## H1-10: durable send boundary and outcome confirmation

`c552250c0d07f5f70f09eb0a5ab3c322195e34ec:swarm/task_ledger.py:358` through line 393.

```python
    def begin_execution(self, lease: Lease, request_id: str) -> None:
        """Persist the no-resend fact before crossing the executor boundary.

        A crash, expired lease or voluntary handoff must not make an unconfirmed
        external request eligible again. This fact is independent of its cost.
        """
        if not request_id.strip():
            raise ValueError("request_id required")
        with self.transaction() as db:
            row = self._owned(db, lease)
            if row["unconfirmed_request_id"] is not None:
                raise TaskConflict("task has an unconfirmed external request")
            db.execute("UPDATE tasks SET unconfirmed_request_id=?,updated_at=? WHERE swarm_id=? AND task_id=?",
                       (request_id, self.now(), self.swarm_id, lease.task_id))
            self._event(db, lease.task_id, "execution_unconfirmed", {"request_id": request_id, "token": lease.token})

    def confirm_execution(self, lease: Lease, request_id: str) -> None:
        """Clear only this owned request after a confirmed external outcome."""
        with self.transaction() as db:
            row = self._owned(db, lease)
            if row["unconfirmed_request_id"] != request_id:
                raise TaskConflict("execution confirmation does not match request")
            db.execute("UPDATE tasks SET unconfirmed_request_id=NULL,updated_at=? WHERE swarm_id=? AND task_id=?",
                       (self.now(), self.swarm_id, lease.task_id))
            self._event(db, lease.task_id, "execution_confirmed", {"request_id": request_id, "token": lease.token})

    def _finish_attempt(self, db: sqlite3.Connection, lease: Lease, row: sqlite3.Row,
                        outcome: str, evidence: dict[str, JsonValue]) -> None:
        status = "failed" if row["attempts"] >= self.limits.max_attempts_per_task else "available"
        if row["unconfirmed_request_id"] is not None:
            status = "blocked"
        db.execute("UPDATE tasks SET status=?,owner=NULL,expiry=NULL,updated_at=? WHERE swarm_id=? AND task_id=?",
                   (status, self.now(), self.swarm_id, lease.task_id))
        db.execute("UPDATE task_attempts SET finished_at=?,outcome=?,evidence=? WHERE swarm_id=? AND task_id=? AND token=?",
                   (self.now(), outcome, _OBJECT.dump_json(evidence).decode(), self.swarm_id, lease.task_id, lease.token))
        self._event(db, lease.task_id, outcome, {"token": lease.token, "evidence": evidence})
```

## H1-11: worker reservation/send and usage

`c552250c0d07f5f70f09eb0a5ab3c322195e34ec:swarm/worker_loop.py:757` through line 825.

```python
                reservation = self.budget.reserve(self.worker_id, signal.task_id, bound,
                                                  request_id=f"{signal.task_id}:{lease.token}:{index}")
                self._active = reservation
                if deferred is not None:
                    # A switch factually happened only once the next request was admitted.
                    self._append_observation(deferred.model_copy(update={
                        "switched_to": candidate_identity(bound.provider, bound.model)}))
                    deferred = None
                self._status("executing")
                try:
                    keeper.check()
                    enter_phase("snapshot")
                    revision, head = snapshot_revision(self.target, signal.scope, self.state / "snapshots")
                    keeper.check()

                    execution_id = uuid4().hex
                    directory = self.state / "execution" / execution_id
                    consumption = self._consume(signal, keeper.current, attempt, revision, head, execution_id)

                    enter_phase("execute")
                    with keeper.lock:
                        self.ledger.begin_execution(keeper.current, reservation.request_id)
                    result = candidate_executor.execute(signal, attempt, self.target, directory,
                                                        base_revision=revision, base_head=head,
                                                        experience=consumption)
                    if consumption is not None and (
                        result.candidate != consumption.candidate or result.consumed_asset_ids != (consumption.asset_id,)
                    ):
                        consumption = None
                except BaseException:
                    self.budget.mark_uncertain(self._active)
                    self._active = None
                    raise

                usage = result.usage
                fact_fields = self._metadata_fact_fields(result)
                classification = fact_fields["classification"]
                enter_phase("settle")
                if result.uncertain and classification == CONFIRMED_REJECTION:
                    # Known rejection without observed usage: faithful unknown
                    # cost hold that keeps the chain admittable under it.
                    settled = self.budget.mark_unknown_rejection(self._active)
                else:
                    settled = (self.budget.mark_uncertain(self._active) if result.uncertain else
                               self.budget.settle(self._active, usage))
                cost_state = self.budget.reservation_cost_state(reservation)
                self._active = None
                self._status("settled")
                occurred_at = time.time()

                if (result.provenance != candidate_executor.provenance
                        or result.usage_source != candidate_executor.usage_source
                        or result.original_run_uri != candidate_executor.original_run_uri):
                    raise AssetSafetyError("execution_provenance_mismatch")

                if classification != "unknown_effect" and (not result.uncertain or classification == CONFIRMED_REJECTION):
                    keeper.check()
                    with keeper.lock:
                        self.ledger.confirm_execution(keeper.current, reservation.request_id)

                if result.uncertain and classification != CONFIRMED_REJECTION:
                    # Unknown effect (or non-rejection class) with unknown usage:
                    # the original reservation stays unknown/reserved and the
                    # chain stops; no fabricated zero, no further requests.
                    self._record_failure_fact(task_id=signal.task_id, request_id=reservation.request_id,
                                              index=index, provider=bound.provider, model=bound.model,
                                              classification=str(classification), fact_fields=fact_fields,
                                              cost_state=cost_state, occurred_at=occurred_at)
                    self._report_probe_outcome(breaker, guard.claims, success=False,
```

## H1-12: worker lease before commit

`c552250c0d07f5f70f09eb0a5ab3c322195e34ec:swarm/worker_loop.py:957` through line 977.

```python
                "completion_count": self.completed + 1, "feedback_started": False, "feedback_complete": False,
                "metadata": result.metadata,
                "usage": {"usage": _JSON.validate_python(parsed_usage.model_dump(mode="json"))}
                if parsed_usage else None,
            }
            self._status("submitting")
            enter_phase("lease_handoff")
            lease = keeper.handoff()
            self._pending["lease"] = _JSON.validate_python(lease.model_dump(mode="json"))
            enter_phase("submit")
            self.leases.submit(lease, result_id, result_data, apply=apply)
            enter_phase("finalize")
            self._finalize()
            outcome = "promoted"
            if self.mirror is not None:
                try:
                    self.mirror.enqueue(asset_id)
                except Exception:
                    pass
            return "completed"
        except BudgetBlocked as error:
```

## H1-13: breaker thresholds/Retry-After/matrix

`c552250c0d07f5f70f09eb0a5ab3c322195e34ec:swarm/breaker.py:163` through line 251.

```python
def _suspension_required(params: TransitionParams) -> bool:
    config = params.config
    if params.reason in config.direct_suspend_reasons and params.confirmed_rejections > 0:
        return True  # confirmed arrearage-class rejection bypasses sample floors
    return (
        params.sample_count >= config.failure_threshold
        and params.sample_count >= config.min_samples
    )


def _live_probe(params: TransitionParams) -> bool:
    return (
        params.worker_id is not None
        and params.worker_id == params.probe_owner
        and params.probe_expires_at is not None
        and params.probe_expires_at > params.now
    )


def cooldown_deadline(params: TransitionParams) -> float:
    """Known Retry-After hint verbatim; unknown stays unknown -> injected cooldown.

    Never fabricates 0: cooldown_seconds is validated > 0, and a hint that
    already lies in the past is the server's own statement, not a fabrication.
    """
    if params.retry_after_until is not None:
        return params.retry_after_until
    return params.now + params.config.cooldown_seconds


def transition(
    state: BreakerState, event: BreakerEvent, params: TransitionParams
) -> tuple[BreakerState, tuple[BreakerAction, ...]]:
    """Pure decision core: no I/O, no clock reads, no mutation.

    Returns the new state and the actions the durable store must apply. An
    unchanged state carries no actions. Only the four service-failure events
    exist; anything else (notably answer-correctness signals) is rejected.
    """
    # TODO-HUMAN-REVIEW: complete four-state transition table.
    if state not in _STATES:
        raise ValueError(f"unknown breaker state: {state!r}")
    if event not in _EVENTS:
        raise ValueError(
            f"unknown breaker event: {event!r}; only service-failure facts drive transitions"
        )

    if event == "aggregate":
        if state in ("suspended", "probing_recovery"):
            # Probe outcomes arrive via probe_* events; while suspended only a
            # strictly later server hint may extend the deadline (never shorten,
            # never re-trigger a fresh cooldown from stale in-window evidence).
            if (
                state == "suspended"
                and params.retry_after_until is not None
                and (params.cooldown_until is None or params.retry_after_until > params.cooldown_until)
            ):
                return "suspended", ("persist_state", "set_cooldown")
            return state, ()
        if _suspension_required(params):
            return "suspended", ("persist_state", "set_cooldown")
        if state == "insufficient_evidence" and params.sample_count >= params.config.min_samples:
            return "normal", ("persist_state",)
        return state, ()

    if event == "cooldown_expired":
        if state == "suspended":
            if params.cooldown_until is not None and params.cooldown_until <= params.now:
                return "probing_recovery", ("persist_state", "claim_probe_slot")
            return state, ()
        if state == "probing_recovery":
            # Owner died or restarted mid-probe: the slot is reclaimable once
            # its persisted TTL lapses, never before.
            if params.probe_expires_at is not None and params.probe_expires_at <= params.now:
                return "probing_recovery", ("persist_state", "claim_probe_slot")
            return state, ()
        return state, ()

    if event == "probe_success":
        if state == "probing_recovery" and _live_probe(params):
            return "normal", ("persist_state", "release_probe_slot", "reset_window")
        return state, ()

    # event == "probe_failure"
    if state == "probing_recovery" and _live_probe(params):
        return "suspended", ("persist_state", "release_probe_slot", "set_cooldown")
    return state, ()


```

## H1-14: breaker TTL window bound

`c552250c0d07f5f70f09eb0a5ab3c322195e34ec:swarm/breaker.py:127` through line 144.

```python
    callers can inject a narrower or wider vocabulary without editing this file.
    """

    window_seconds: float = Field(gt=0)
    aggregation_period_seconds: float = Field(gt=0)
    failure_threshold: int = Field(ge=1)
    min_samples: int = Field(default=5, ge=1)
    cooldown_seconds: float = Field(gt=0)
    probe_ttl_seconds: float = Field(gt=0)
    window_max_keys: int = Field(default=1024, ge=1)
    direct_suspend_reasons: frozenset[str] = frozenset({"arrearage", "billing_arrearage"})

    @model_validator(mode="after")
    def window_covers_aggregation(self) -> BreakerConfig:
        # TTLCache pitfall: a window shorter than the aggregation period would
        # drop samples before the next cycle can ever count them.
        if self.window_seconds < self.aggregation_period_seconds:
            raise ValueError("window_seconds must be >= aggregation_period_seconds")
```

## H1-15: breaker recovery aggregate filtering

`c552250c0d07f5f70f09eb0a5ab3c322195e34ec:swarm/breaker.py:477` through line 521.

```python
    def _apply_aggregate(
        self, aggregate: FaultAggregateLike, *, now: float
    ) -> BreakerChange | None:
        provider, reason = aggregate.provider, aggregate.normalized_reason
        with self._write() as db:
            current = self._view(provider, reason, self._row(db, provider, reason))
            # Re-read the durable boundary under the state write lock: an
            # aggregate or another worker's cache may predate probe success.
            if current.recovered_at is not None:
                filtered = (aggregate.after_recovery(current.recovered_at, current.recovery_sequence)
                            if isinstance(aggregate, RecoveryAggregateLike) else
                            aggregate if aggregate.first_occurred_at > current.recovered_at else None)
                if filtered is None:
                    self._window.pop((provider, reason), None)
                    return None
                aggregate = filtered
                self._window[(provider, reason)] = aggregate
            params = TransitionParams(
                now=now, reason=reason, config=self.config,
                sample_count=aggregate.sample_count,
                confirmed_rejections=aggregate.confirmed_rejections,
                retry_after_until=aggregate.retry_after_until,
                cooldown_until=current.cooldown_until,
                probe_expires_at=current.probe_expires_at,
                probe_owner=current.probe_owner,
            )
            new_state, actions = transition(current.state, "aggregate", params)
            if not actions:
                return None
            values = self._next_values(current, new_state, actions, params)
            self._upsert(db, provider, reason, values, now)
            change = BreakerChange(
                provider=provider, reason=reason, event="aggregate",
                from_state=current.state, to_state=new_state,
            )
            self._audit(db, provider, reason, "aggregate", change, {
                "sample_count": aggregate.sample_count,
                "confirmed_rejections": aggregate.confirmed_rejections,
                "retry_after_until": aggregate.retry_after_until,
                "cooldown_until": values["cooldown_until"],
                "actions": list(actions),
            }, now)
            return change

    @staticmethod
```

## H1-16: breaker atomic fresh token claim

`c552250c0d07f5f70f09eb0a5ab3c322195e34ec:swarm/breaker.py:569` through line 614.

```python
    def try_claim_probe(self, provider: str, reason: str, worker_id: str, *,
                        now: float | None = None) -> BreakerView | None:
        """Atomic half-open claim: at most one worker wins the single probe slot.

        Returns the fresh view for the winner and None for everyone else
        (cooldown not expired, slot already held, or lost the race).
        """
        if not worker_id.strip():
            raise ValueError("worker_id required")
        at = self._at(now)
        with self._write() as db:
            current = self._view(provider, reason, self._row(db, provider, reason))
            params = TransitionParams(
                now=at, reason=reason, config=self.config,
                cooldown_until=current.cooldown_until,
                probe_expires_at=current.probe_expires_at,
                probe_owner=current.probe_owner,
                worker_id=worker_id,
            )
            new_state, actions = transition(current.state, "cooldown_expired", params)
            if new_state != "probing_recovery" or "claim_probe_slot" not in actions:
                return None
            expires_at = at + self.config.probe_ttl_seconds
            # TODO-HUMAN-REVIEW: multi-worker half-open race — the guarded UPDATE
            # inside BEGIN IMMEDIATE plus token fencing admits exactly one winner.
            cursor = db.execute(
                "UPDATE breaker_states SET state='probing_recovery', probe_owner=?, "
                "probe_token=probe_token+1, probe_expires_at=?, updated_at=? "
                "WHERE swarm_id=? AND provider=? AND reason=? AND probe_token=? "
                "AND ((state='suspended' AND cooldown_until IS NOT NULL AND cooldown_until<=?) "
                "OR (state='probing_recovery' AND probe_expires_at IS NOT NULL AND probe_expires_at<=?))",
                (worker_id, expires_at, at, self.swarm_id, provider, reason,
                 current.probe_token, at, at),
            )
            if cursor.rowcount != 1:
                return None
            change = BreakerChange(
                provider=provider, reason=reason, event="cooldown_expired",
                from_state=current.state, to_state="probing_recovery",
            )
            self._audit(db, provider, reason, "probe_claimed", change, {
                "worker_id": worker_id,
                "probe_token": current.probe_token + 1,
                "probe_expires_at": expires_at,
            }, at)
            return self._view(provider, reason, self._row(db, provider, reason))
```

## H1-17: breaker token/owner/expiry and checkpoint

`c552250c0d07f5f70f09eb0a5ab3c322195e34ec:swarm/breaker.py:629` through line 695.

```python
    def _finish_probe(self, provider: str, reason: str, worker_id: str, event: str, *,
                      probe_token: int, retry_after_until: float | None,
                      now: float | None) -> bool:
        """Fenced probe outcome: only the live slot owner's report is applied.

        The caller must pass the probe_token it won from try_claim_probe; the
        UPDATE fences on that exact token. A same-worker stale result (the
        worker reclaimed after its TTL lapsed, so the token advanced) can no
        longer mutate the live slot's state.
        """
        if event not in ("probe_success", "probe_failure"):
            raise ValueError(f"not a probe outcome event: {event!r}")
        if probe_token < 1:
            raise ValueError("probe_token must be the token claimed via try_claim_probe")
        at = self._at(now)
        with self._write() as db:
            current = self._view(provider, reason, self._row(db, provider, reason))
            params = TransitionParams(
                now=at, reason=reason, config=self.config,
                retry_after_until=retry_after_until,
                probe_owner=current.probe_owner,
                probe_expires_at=current.probe_expires_at,
                worker_id=worker_id,
            )
            typed_event: BreakerEvent = event  # type: ignore[assignment]
            new_state, actions = transition(current.state, typed_event, params)
            if not actions or current.probe_token != probe_token:
                return False
            recovery_sequence = None
            if new_state == "normal":
                # Serialize the append boundary with JSONL writers. The breaker
                # transaction spans this short local read, never a model call.
                if self._recovery_store is not None:
                    recovery_sequence = self._recovery_store.checkpoint()
                fields = ("state=?, probe_owner=NULL, probe_expires_at=NULL, sample_count=0, "
                          "confirmed_rejections=0, cooldown_until=NULL, retry_after_until=NULL, "
                          "updated_at=?, recovered_at=?, recovery_sequence=?")
                args: tuple[object, ...] = (new_state, at, at, recovery_sequence)
            else:
                deadline = cooldown_deadline(params)
                fields = ("state=?, probe_owner=NULL, probe_expires_at=NULL, cooldown_until=?, "
                          "retry_after_until=?, updated_at=?")
                args = (new_state, deadline, retry_after_until, at)
            # TODO-HUMAN-REVIEW: same-owner stale probe — the fenced token is the
            # caller-claimed one, not the row's current token, so a late outcome
            # from a reclaimed (superseded) probe can never overwrite the live slot.
            cursor = db.execute(
                f"UPDATE breaker_states SET {fields} WHERE swarm_id=? AND provider=? AND reason=? "
                "AND state='probing_recovery' AND probe_owner=? AND probe_token=? "
                "AND probe_expires_at IS NOT NULL AND probe_expires_at>?",
                (*args, self.swarm_id, provider, reason, worker_id, probe_token, at),
            )
            if cursor.rowcount != 1:
                return False
            if "reset_window" in actions:
                self._window.pop((provider, reason), None)
            change = BreakerChange(
                provider=provider, reason=reason, event=typed_event,
                from_state=current.state, to_state=new_state,
            )
            self._audit(db, provider, reason, event, change, {
                "worker_id": worker_id,
                "retry_after_until": retry_after_until,
                "probe_token": probe_token,
                "recovery_sequence": recovery_sequence,
            }, at)
            return True
```

## H1-18: append order recovery watermark

`c552250c0d07f5f70f09eb0a5ab3c322195e34ec:swarm/fault_observations.py:104` through line 117.

```python
    def after_recovery(self, at: float, sequence: int | None) -> FaultAggregate | None:
        """Exclude the recovery snapshot and delayed pre-recovery events.

        File order disambiguates equal timestamps. Without a file checkpoint,
        only strictly later timestamps are known to be new evidence.
        """
        if not self.samples:
            return self if self.first_occurred_at > at else None
        samples = tuple(sample for sample in self.samples if (
            sample.occurred_at > at if sequence is None else
            sample.sequence > sequence and sample.occurred_at >= at
        ))
        return self.from_samples(self.provider, self.normalized_reason, samples) if samples else None

```

## H1-19: observation checkpoint

`c552250c0d07f5f70f09eb0a5ab3c322195e34ec:swarm/fault_observations.py:206` through line 218.

```python
    def checkpoint(self) -> int:
        """Capture append order under the same bounded lock as writers.

        This is a position in the existing JSONL, not a second event log. The
        last partial line also counts: append seals it before adding new facts.
        """
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with connection(self._lock_path, write=True, timeout=self.timeout_seconds):
            try:
                with self.path.open("rb") as source:
                    return sum(1 for _ in source)
            except FileNotFoundError:
                return 0
```

## H1-20: Worker routing fresh probe token

`c552250c0d07f5f70f09eb0a5ab3c322195e34ec:swarm/failure_chain.py:116` through line 149.

```python

    Suspended breakers are probed exactly once per evaluation: the atomic
    ``try_claim_probe`` admits at most one worker network-wide. A breaker
    already in ``probing_recovery`` is routable for its live slot owner or a
    winner atomically reclaiming an expired slot with a fresh fencing token.
    """
    claims: list[ProbeClaim] = []
    blocked: list[str] = []
    for view in breaker.views():
        if view.provider != provider:
            continue
        state = view.state
        if state in _ROUTABLE_STATES:
            continue
        if state == "suspended":
            claimed = breaker.try_claim_probe(provider, view.reason, worker_id, now=now)
            if claimed is None:
                blocked.append(view.reason)
            else:
                claims.append(ProbeClaim(provider, view.reason, claimed.probe_token))
            continue
        if state == "probing_recovery":
            claimed = breaker.try_claim_probe(provider, view.reason, worker_id, now=now)
            if claimed is not None:
                claims.append(ProbeClaim(provider, view.reason, claimed.probe_token))
            elif breaker.eligible(provider, view.reason, worker_id=worker_id, now=now):
                claims.append(ProbeClaim(provider, view.reason, view.probe_token))
            else:
                blocked.append(view.reason)
            continue
        blocked.append(view.reason)
    return GuardResult(routable=not blocked, claims=tuple(claims), blocked_reasons=tuple(blocked))


```

## H1-21: short SQLite transaction

`c552250c0d07f5f70f09eb0a5ab3c322195e34ec:swarm/task_ledger.py:41` through line 56.

```python
def connection(path: Path, *, write: bool = False, timeout: float = 10) -> Iterator[sqlite3.Connection]:
    db = sqlite3.connect(path, timeout=timeout, isolation_level=None)
    db.row_factory = sqlite3.Row
    try:
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA synchronous=FULL")
        db.execute("BEGIN IMMEDIATE" if write else "BEGIN")
        yield db
        if write:
            db.commit()
    except BaseException:
        if write:
            db.rollback()
        raise
    finally:
        db.close()
```
