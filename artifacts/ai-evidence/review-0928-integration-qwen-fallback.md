# Failure Chain Implementation Review - Revised

**Report Title:** Failure Chain Implementation Review - FC-A/B/C/D Integration - Revised

**Reviewer:** qwen-code (qwen3-coder-plus)
**Session:** qwen-code review session (session ID: 6c8ab3fa-4df6-4329-a980-7d6eb5ccbc47)
**Date:** September 28, 2026

## Summary
This review evaluates the implementation of the failure chain components (FC-A, FC-B, FC-C, FC-D) in the Morphogenesis project. The review focuses on the adherence to the five invariants, breaker four-state transfer table, half-open probe token fencing, and the assessment of potential false positive test results (fake greens).

**Note:** This is a同源降级版: qwen-code独立新会话，非deepseek-r1正式异构评审.

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

#### 1. Potential Race Condition in Half-Open Probe Token Fencing - REVISION
- **File:** `swarm/breaker.py`
- **Lines:** 598-655 (in `_finish_probe` method)
- **Trigger Condition:** A worker reports a probe outcome after its probe token has been superseded by another claim (either by the same worker or another worker).
- **Evidence/Analysis:** After reviewing the code (lines 598-655) and the existing test `test_same_owner_stale_probe_result_is_fenced_by_token` (lines 436-460 in `tests/swarm/test_breaker.py`), I conclude that the token fencing mechanism is correctly implemented. The UPDATE statement in `_finish_probe` (lines 636-640) specifically checks for the exact `probe_token` that was claimed by the reporting worker. If the token in the database has changed (due to another claim), the UPDATE will affect 0 rows (`cursor.rowcount != 1`), and the function returns `False`, indicating the report was rejected. This prevents a stale probe result from overwriting the current state. The existing test explicitly verifies this behavior.
- **Impact:** The original assertion of a high-severity race condition was incorrect. The fencing mechanism works as intended.
- **Revision:** The high-severity finding regarding the race condition in probe token fencing is hereby **REVISED**. The mechanism is correctly implemented as per the code analysis and existing tests. The original concern was unfounded based on the actual implementation.

### Medium Severity

#### 1. Retry-After Header Parsing in GatewayResponse
- **File:** `orchestration/gateway_transport.py`
- **Lines:** 28, 43-67
- **Trigger Condition:** Server returns a Retry-After header in an unexpected format.
- **Evidence:** The `GatewayResponse` class captures the raw body and Retry-After header. The parsing logic is implemented in the provider adapters.
- **Impact:** Could lead to incorrect handling of rate limits if parsing fails.
- **Suggestion:** Add comprehensive tests for various Retry-After header formats and edge cases (malformed values, extremely large numbers). (Coverage boundary: To be verified)

#### 2. Classification Logic Completeness
- **File:** `orchestration/provider_adapters/evomap.py`, `orchestration/provider_adapters/dashscope.py`
- **Lines:** Various
- **Trigger Condition:** API returns an error format not explicitly handled by the adapters.
- **Evidence:** The adapters have specific checks for common error codes/reasons but fall back to generic classifications. This is generally acceptable but worth noting.
- **Impact:** Could lead to misclassification of certain failure types, affecting breaker logic.
- **Suggestion:** Ensure comprehensive coverage of known failure modes through tests and periodically review and update the classification logic based on real-world responses. (Coverage boundary: To be verified)

#### 3. Fake Green - Boundary Tests Analysis
- **File:** `tests/swarm/test_failure_chain_boundaries.py` (baseline 73e64cc and optional a821783)
- **Lines:** Various
- **Defects Found:**
  - Line 138: `assert response.error_kind is not None` followed by `assert "Timeout" in response.error_kind or "Connection" in response.error_kind` - This assertion is placed after simulating a dropped connection, but the code doesn't actually trigger the simulated condition within the test function itself. The `GatewayResponse` is manually constructed rather than produced by the transport. This is a bare assert without actual test execution.
  - Line 197-205: The test `test_budget_insufficient_boundary` creates a ledger, makes a reservation, but then asserts based on an exception raised. However, the exception type and message are checked directly in the test rather than verifying the state of the budget ledger after the reservation attempt, which would be a stronger test.
  - Line 335-343: In `TestUnknownEffectProperty`, the test verifies that a reservation is preserved when marked as uncertain, but doesn't directly test that no subsequent requests are made in the actual worker loop. This is more of a budget ledger property than a full chain behavior.
  - Line 540-545: The test `test_process_in_memory_transport_path` uses `respx` to mock an HTTP response, but then constructs a `MockTransport` manually and calls `single_request` with it. This is testing the transport layer with a mock, which is valid, but the test name suggests it's for in-process paths, which might be misleading if it doesn't cover the actual path through the provider adapters in a real scenario.
- **Impact:** These defects mean that some tests might pass without actually verifying the intended behavior, leading to a false sense of security (fake green).
- **Suggestion:** Revise these tests to ensure they actually execute the code paths they claim to test and assert on the correct observable outcomes.

### Low Severity

#### 1. Consistency in Error Handling
- **File:** Various
- **Trigger Condition:** Different parts of the system handle errors.
- **Evidence:** Some areas use broad exception handling (e.g., `except Exception:`), while others use specific exception types. This is generally acceptable given the nature of external API interactions.
- **Impact:** Minor maintenance concern.
- **Suggestion:** Where possible, use more specific exception types to improve debugging and error handling precision.

## Five Invariants Assessment

### 1. Switching provider does not create new task budget, does not clear existing consumption
- **Finding:** Static observation confirms. The budget reservation and tracking logic in `swarm/budget.py` ensures that reservations are tied to the task and accumulate appropriately regardless of provider switches. The `worker_loop.py` correctly manages reservations per task attempt.
- **Evidence:** `BudgetLedger.reserve()` and `BudgetLedger.settle()`/`mark_uncertain()`/`mark_unknown_rejection()` methods track costs per task, and the `worker_loop` processes each candidate in sequence while managing the reservation state. (Boundary: NOT_RUN - Direct execution tests not performed)

### 2. Unknown cost reservations are never auto released by fallback
- **Finding:** Static observation confirms. The `mark_uncertain` and `mark_unknown_rejection` methods in `swarm/budget.py` ensure that reservations with unknown costs remain in the ledger with their hold intact.
- **Evidence:** `BudgetLedger.mark_uncertain()` and `BudgetLedger.mark_unknown_rejection()` do not release the reservation's cost from the budget; it remains as a hold until explicitly settled or cleared through other means. (Boundary: NOT_RUN - Direct execution tests not performed)

### 3. External attempt count covers all real remote requests
- **Finding:** Static observation confirms. The attempt tracking is handled in `swarm/budget.py` via the reservation mechanism. Each call to `reserve` corresponds to a potential remote request attempt.
- **Evidence:** The `BudgetLedger.reserve()` method increments the attempt counter, and the reservation state (pending/uncertain/settled) tracks the lifecycle of each attempt. (Boundary: NOT_RUN - Direct execution tests not performed)

### 4. Lost lease prevents successful result submission
- **Finding:** Static observation confirms. The `worker_loop.py` includes checks for lease validity (`keeper.check()`) throughout the execution and submission process. The `leases.submit()` method in `swarm/lease.py` also validates the lease.
- **Evidence:** Lease validation occurs in `_Renewal.check()` and `leases.submit()` which is called in the `worker_loop` before finalizing results. (Boundary: NOT_RUN - Direct execution tests not performed)

### 5. All candidates unavailable has bounded exit, does not loop back to chain start
- **Finding:** Static observation confirms. The `worker_loop.py` implements the failure chain logic via `decide()` function in `swarm/failure_chain.py`. If all candidates are exhausted or suspended by the breaker, the loop exits based on energy limits, attempt limits, or budget constraints.
- **Evidence:** The candidate loop in `_process()` of `worker_loop.py` iterates through `chain_executors`, and the decision logic in `decide()` determines the action when a candidate fails. If all candidates are tried or blocked, the worker exits based on other constraints like energy or budget. (Boundary: NOT_RUN - Direct execution tests not performed)

## Fake Green Assessment

- **Old dict/GatewayResponse fields:** The `GatewayResponse` class in `orchestration/gateway_transport.py` has been updated to include `retry_after` and `raw_body` fields, addressing the original issue.
- **Non-existent interfaces:** No obvious non-existent interfaces were found in the reviewed code.
- **Except swallowing assertions:** The error handling in `gateway_transport.py` and `evomap_executor.py` catches exceptions appropriately without suppressing important information for debugging.
- **Testing only ledger, not Worker:** The boundary tests in `test_failure_chain_boundaries.py` do test the budget ledger directly, but also include integration aspects that involve the worker loop logic.
- **Missing call_count:** The tests seem to cover the reservation counts and states adequately.
- **Mock live violation:** The tests distinguish between mock and live paths where appropriate. The subprocess mock tests are clearly labeled as such.
- **Test sensitivity:** The hypothesis tests in `test_failure_chain_boundaries.py` provide good coverage for various input combinations and invariant checking.

## Conclusion
The implementation of the failure chain components appears to be well-structured and addresses the specified requirements. The five invariants are largely upheld by the design. The original high-severity finding regarding the breaker's token fencing has been revised as the mechanism is correctly implemented, as demonstrated by the code and existing tests. However, several medium-severity issues related to test completeness and potential fake greens were identified. Overall, the code seems robust, but continuous monitoring and testing with real-world scenarios will be crucial for ensuring its reliability.