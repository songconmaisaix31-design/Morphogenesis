# Failure Chain Implementation Review

**Report Title:** Failure Chain Implementation Review - FC-A/B/C/D Integration

**Reviewer:** qwen-code (qwen3-coder-plus)
**Session:** qwen-code review session
**Date:** September 28, 2026

## Summary
This review evaluates the implementation of the failure chain components (FC-A, FC-B, FC-C, FC-D) in the Morphogenesis project. The review focuses on the adherence to the five invariants, breaker four-state transfer table, half-open probe token fencing, and the assessment of potential false positive test results (fake greens).

## Scope
- **Branch:** fc/review-only
- **Commit Range:** 348cf8d42719402a7a5fcc09595e5040f96fa5be..73e64cc70116ac658d85591d082c0684a4952c99
- **Files Reviewed:**
  - `orchestration/gateway_transport.py`
  - `orchestration/provider_adapters/`
    - `base.py`
    - `evomap.py`
    - `dashscope.py`
  - `swarm/evomap_executor.py`
  - `swarm/budget.py`
  - `swarm/worker_loop.py`
  - `swarm/failure_chain.py`
  - `swarm/breaker.py`
  - `swarm/fault_observations.py`
  - `tests/swarm/test_failure_chain_boundaries.py`

## Findings

### High Severity

#### 1. Potential Race Condition in Half-Open Probe Token Fencing
- **File:** `swarm/breaker.py`
- **Lines:** 598-621 (in `_finish_probe` method, and related token handling)
- **Trigger Condition:** Multiple workers simultaneously trying to report probe outcomes on the same suspended breaker.
- **Evidence:** The code relies on a token check in the UPDATE statement to ensure only the holder of the probe token can modify the breaker state. However, the token value used in the UPDATE is the one passed by the caller, not the current value in the DB. If a worker holds a token but takes too long to report the outcome, and another worker acquires a new token, the first worker's delayed report could potentially fail correctly, but the mechanism relies on precise timing and the uniqueness of the token value at the moment of acquisition.
- **Impact:** Could violate invariant 4 if a late probe outcome incorrectly modifies a breaker state that has since moved to a different worker.
- **Suggestion:** Ensure the fencing mechanism is robustly tested with concurrent probe attempts and that the token comparison in the UPDATE statement is strictly against the *current* token in the database at the moment of the update.

### Medium Severity

#### 1. Retry-After Header Parsing in GatewayResponse
- **File:** `orchestration/gateway_transport.py`
- **Lines:** 28, 43-67
- **Trigger Condition:** Server returns a Retry-After header in an unexpected format.
- **Evidence:** The `GatewayResponse` class captures the raw body and Retry-After header. The parsing logic is implemented in the provider adapters.
- **Impact:** Could lead to incorrect handling of rate limits if parsing fails.
- **Suggestion:** Add comprehensive tests for various Retry-After header formats and edge cases (malformed values, extremely large numbers).

#### 2. Classification Logic Completeness
- **File:** `orchestration/provider_adapters/evomap.py`, `orchestration/provider_adapters/dashscope.py`
- **Lines:** Various
- **Trigger Condition:** API returns an error format not explicitly handled by the adapters.
- **Evidence:** The adapters have specific checks for common error codes/reasons but fall back to generic classifications. This is generally acceptable but worth noting.
- **Impact:** Could lead to misclassification of certain failure types, affecting breaker logic.
- **Suggestion:** Ensure comprehensive coverage of known failure modes through tests and periodically review and update the classification logic based on real-world responses.

#### 3. Missing Explicit Tests for Subprocess Live Path
- **File:** `tests/swarm/test_failure_chain_boundaries.py`
- **Lines:** Various
- **Trigger Condition:** Need to verify classification and evidence_hash return in the actual subprocess live path (not just mock mode).
- **Evidence:** The test `test_subprocess_integration_path()` in the retrieved commit a821783 uses mock specs, which verifies the classification path for mock scenarios but doesn't fully test the live subprocess flow with real API calls.
- **Impact:** Could miss issues specific to the live subprocess execution environment.
- **Suggestion:** Add tests that exercise the subprocess path with real API calls (potentially in a controlled test environment) to ensure the classification and evidence_hash mechanisms work as expected in the live scenario.

### Low Severity

#### 1. Consistency in Error Handling
- **File:** Various
- **Trigger Condition:** Different parts of the system handle errors.
- **Evidence:** Some areas use broad exception handling (e.g., `except Exception:`), while others use specific exception types. This is generally acceptable given the nature of external API interactions.
- **Impact:** Minor maintenance concern.
- **Suggestion:** Where possible, use more specific exception types to improve debugging and error handling precision.

## Five Invariants Assessment

### 1. Switching provider does not create new task budget, does not clear existing consumption
- **Finding:** Confirmed. The budget reservation and tracking logic in `swarm/budget.py` ensures that reservations are tied to the task and accumulate appropriately regardless of provider switches. The `worker_loop.py` correctly manages reservations per task attempt.
- **Evidence:** `BudgetLedger.reserve()` and `BudgetLedger.settle()`/`mark_uncertain()`/`mark_unknown_rejection()` methods track costs per task, and the `worker_loop` processes each candidate in sequence while managing the reservation state.

### 2. Unknown cost reservations are never auto released by fallback
- **Finding:** Confirmed. The `mark_uncertain` and `mark_unknown_rejection` methods in `swarm/budget.py` ensure that reservations with unknown costs remain in the ledger with their hold intact.
- **Evidence:** `BudgetLedger.mark_uncertain()` and `BudgetLedger.mark_unknown_rejection()` do not release the reservation's cost from the budget; it remains as a hold until explicitly settled or cleared through other means.

### 3. External attempt count covers all real remote requests
- **Finding:** Confirmed. The attempt tracking is handled in `swarm/budget.py` via the reservation mechanism. Each call to `reserve` corresponds to a potential remote request attempt.
- **Evidence:** The `BudgetLedger.reserve()` method increments the attempt counter, and the reservation state (pending/uncertain/settled) tracks the lifecycle of each attempt.

### 4. Lost lease prevents successful result submission
- **Finding:** Confirmed. The `worker_loop.py` includes checks for lease validity (`keeper.check()`) throughout the execution and submission process. The `leases.submit()` method in `swarm/lease.py` also validates the lease.
- **Evidence:** Lease validation occurs in `_Renewal.check()` and `leases.submit()` which is called in the `worker_loop` before finalizing results.

### 5. All candidates unavailable has bounded exit, does not loop back to chain start
- **Finding:** Confirmed. The `worker_loop.py` implements the failure chain logic via `decide()` function in `swarm/failure_chain.py`. If all candidates are exhausted or suspended by the breaker, the loop exits based on energy limits, attempt limits, or budget constraints.
- **Evidence:** The candidate loop in `_process()` of `worker_loop.py` iterates through `chain_executors`, and the decision logic in `decide()` determines the action when a candidate fails. If all candidates are tried or blocked, the worker exits based on other constraints like energy or budget.

## Fake Green Assessment

- **Old dict/GatewayResponse fields:** The `GatewayResponse` class in `orchestration/gateway_transport.py` has been updated to include `retry_after` and `raw_body` fields, addressing the original issue.
- **Non-existent interfaces:** No obvious non-existent interfaces were found in the reviewed code.
- **Except swallowing assertions:** The error handling in `gateway_transport.py` and `evomap_executor.py` catches exceptions appropriately without suppressing important information for debugging.
- **Testing only ledger, not Worker:** The boundary tests in `test_failure_chain_boundaries.py` do test the budget ledger directly, but also include integration aspects that involve the worker loop logic.
- **Missing call_count:** The tests seem to cover the reservation counts and states adequately.
- **Mock live violation:** The tests distinguish between mock and live paths where appropriate. The subprocess mock tests are clearly labeled as such.
- **Test sensitivity:** The hypothesis tests in `test_failure_chain_boundaries.py` provide good coverage for various input combinations and invariant checking.

## Conclusion
The implementation of the failure chain components appears to be well-structured and addresses the specified requirements. The five invariants are largely upheld by the design. However, the potential race condition in the breaker's probe token fencing mechanism warrants closer attention and thorough testing. Overall, the code seems robust, but continuous monitoring and testing with real-world scenarios will be crucial for ensuring its reliability.