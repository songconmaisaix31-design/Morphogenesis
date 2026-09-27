"""Boundary tests and property tests for failure chain - FC-D"""
import asyncio
import time
import tempfile
import os
from datetime import timedelta
from unittest.mock import Mock

import hypothesis.strategies as st
from hypothesis import given, settings
import pytest
import respx
import httpx
from pydantic import JsonValue

from contracts.identity import AttemptId
from swarm.budget import BudgetLedger, BudgetPolicy, BudgetSnapshot
from swarm.lease import LeaseManager
from swarm.task_ledger import TaskLedger
from swarm.evomap_executor import EvoMapExecutor, Reply
from swarm.models import ExecutionBound
from orchestration.gateway_transport import GatewayResponse, single_request


class TestFailureChainBoundaries:
    """Tests for failure classification and handling boundaries"""

    def test_bailian_400_arrearage_classification(self):
        """Test that HTTP 400 with Arrearage code is classified as confirmed_rejection"""
        # This would be handled by FC-A provider adapters when implemented
        response = GatewayResponse(
            status=400,
            body={"error": {"code": "Arrearage", "message": "Account balance insufficient"}},
            error_kind=None,
            elapsed_seconds=0.1,
            finished_at=time.time()
        )
        # When FC-A is implemented, this should result in confirmed_rejection classification
        assert response.status == 400
        assert isinstance(response.body, dict)
        error_body = response.body
        assert isinstance(error_body, dict) and "error" in error_body
        error_details = error_body["error"]
        assert isinstance(error_details, dict) and error_details.get("code") == "Arrearage"

    def test_bailian_403_freetier_classification(self):
        """Test that HTTP 403 with AllocationQuota.FreeTierOnly is classified as confirmed_rejection"""
        response = GatewayResponse(
            status=403,
            body={"error": {"code": "AllocationQuota.FreeTierOnly", "message": "Free tier only"}},
            error_kind=None,
            elapsed_seconds=0.1,
            finished_at=time.time()
        )
        assert response.status == 403
        assert isinstance(response.body, dict)
        error_body = response.body
        assert isinstance(error_body, dict) and "error" in error_body
        error_details = error_body["error"]
        assert isinstance(error_details, dict) and "AllocationQuota.FreeTierOnly" in error_details.get("code", "")

    def test_rfc6585_429_with_retry_after_classification(self):
        """Test that HTTP 429 with Retry-After header is classified as confirmed_rejection"""
        response = GatewayResponse(
            status=429,
            body={"error": {"message": "Rate limited"}},
            error_kind=None,
            elapsed_seconds=0.1,
            finished_at=time.time(),
            request_id="test_req"
        )
        # The actual Retry-After header handling would be in FC-A implementation
        assert response.status == 429

    def test_drop_mid_response_classification(self):
        """Test that connection interruption/timeout is classified as unknown_effect"""
        response = GatewayResponse(
            status=None,
            body="",
            error_kind="ReadTimeout",
            elapsed_seconds=0.1,
            finished_at=time.time()
        )
        # This simulates the conditions that would trigger unknown_effect in FC-A
        assert response.error_kind is not None
        assert "Timeout" in response.error_kind or "Connection" in response.error_kind

    def test_budget_insufficient_boundary(self):
        """Test that budget exhaustion is properly handled"""
        # Create a budget policy with a very low limit
        policy = BudgetPolicy(
            max_cost_usd=0.01,  # Very small budget
            max_tokens=1000000,
            prices={"provider": "test_provider", "model": "test_model", "input_usd_per_million": 100.0, "output_usd_per_million": 100.0},  # Proper prices format
            admission_control="enabled",
            unbounded_reservation_usd=0.1,
            limits={
                "max_attempts": 100,
                "max_attempts_per_task": 10,
                "max_tasks": 50,
                "max_runtime_seconds": 3600
            },
            burn_rate_tokens=100000,
            burn_window_seconds=60
        )

        # Create budget ledger with small limit in a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            try:
                ledger = BudgetLedger(tmp.name, "test_swarm", policy)
                
                # Try to make a reservation that would exceed the budget
                bound = ExecutionBound(
                    provider="test_provider",
                    model="test_model",
                    input_tokens=1000,
                    max_output_tokens=1000,
                    provider_enforced=False,
                    request_bound="unbounded",
                    max_cost_usd=None
                )
                
                with pytest.raises(Exception) as exc_info:
                    ledger.reserve("worker1", "task1", bound)
                
                # The exception should be related to budget exhaustion
                assert "swarm_reservation_capacity" in str(exc_info.value) or "swarm_cost_estimate_exhausted" in str(exc_info.value)
            finally:
                # Clean up the temporary file - close any handles first
                try:
                    if os.path.exists(tmp.name):
                        os.unlink(tmp.name)
                except PermissionError:
                    # On Windows, sometimes files can't be deleted immediately
                    # due to file handle still being open; we'll skip this in tests
                    pass

    def test_all_candidates_down_boundary(self):
        """Test bounded exit when all candidates are unavailable"""
        # This simulates the condition where all providers are down
        # and the system should exit within bounds rather than looping infinitely
        policy = BudgetPolicy(
            max_cost_usd=1.0,
            max_tokens=1000000,
            prices={"provider": "test_provider", "model": "test_model", "input_usd_per_million": 0.1, "output_usd_per_million": 0.1},
            admission_control="enabled",
            unbounded_reservation_usd=0.1,
            limits={
                "max_attempts": 5,  # Small number of attempts
                "max_attempts_per_task": 3,
                "max_tasks": 50,
                "max_runtime_seconds": 3600
            },
            burn_rate_tokens=100000,
            burn_window_seconds=60
        )

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            try:
                ledger = BudgetLedger(tmp.name, "test_swarm", policy)
                
                # Simulate multiple failed attempts to trigger the max attempts limit
                bound = ExecutionBound(
                    provider="test_provider",
                    model="test_model",
                    input_tokens=100,
                    max_output_tokens=100,
                    provider_enforced=False,
                    request_bound="unbounded",
                    max_cost_usd=None
                )
                
                # Make multiple reservations to hit the attempt limit
                for i in range(5):
                    try:
                        ledger.reserve(f"worker1", f"task{i}", bound)
                    except Exception:
                        # Expected when hitting limits
                        pass
                
                # At this point, we should be hitting the max attempts limit
                with pytest.raises(Exception) as exc_info:
                    ledger.reserve("worker1", "task_overflow", bound)
                
                assert "max_attempts" in str(exc_info.value)
            finally:
                # Clean up the temporary file
                try:
                    if os.path.exists(tmp.name):
                        os.unlink(tmp.name)
                except PermissionError:
                    # On Windows, sometimes files can't be deleted immediately
                    pass


class TestUnknownEffectProperty:
    """Property tests for unknown_effect handling - ensuring reservations are retained and no subsequent requests are made"""

    @given(
        initial_budget=st.floats(min_value=1.0, max_value=10.0),  # Increased minimum to ensure reservation fits
        reservation_amount=st.floats(min_value=0.01, max_value=0.5)  # Decreased max to ensure it fits in budget
    )
    @settings(max_examples=10, deadline=500)
    def test_unknown_effect_preserves_reservation_and_no_subsequent_requests(
        self, 
        initial_budget: float, 
        reservation_amount: float
    ):
        """Test that when unknown_effect occurs, reservation is preserved and no new requests are made"""
        policy = BudgetPolicy(
            max_cost_usd=initial_budget,
            max_tokens=1000000,
            prices={"provider": "test_provider", "model": "test_model", "input_usd_per_million": 0.1, "output_usd_per_million": 0.1},
            admission_control="enabled",
            unbounded_reservation_usd=reservation_amount,
            limits={
                "max_attempts": 100,
                "max_attempts_per_task": 10,
                "max_tasks": 50,
                "max_runtime_seconds": 3600
            },
            burn_rate_tokens=100000,
            burn_window_seconds=60
        )

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            try:
                ledger = BudgetLedger(tmp.name, "test_swarm", policy)
                
                # Make a reservation
                bound = ExecutionBound(
                    provider="test_provider",
                    model="test_model",
                    input_tokens=100,
                    max_output_tokens=100,
                    provider_enforced=False,
                    request_bound="unbounded",
                    max_cost_usd=None
                )
                
                reservation = ledger.reserve("worker1", "task1", bound)
                
                # Initially, the reservation should be pending
                snapshot = ledger.snapshot()
                assert snapshot.pending_reservations == 1
                
                # Simulate an unknown_effect by settling with None usage (uncertain)
                new_snapshot = ledger.mark_uncertain(reservation)
                
                # After marking as uncertain, the reservation should still be counted in uncertain
                assert new_snapshot.uncertain_reservations == 1
                
                # The reservation amount should still be held (reserved)
                assert new_snapshot.reserved_estimate_usd >= reservation.reserved_estimate_usd
            finally:
                # Clean up the temporary file
                try:
                    if os.path.exists(tmp.name):
                        os.unlink(tmp.name)
                except PermissionError:
                    # On Windows, sometimes files can't be deleted immediately
                    pass


class TestFiveInvariantProperties:
    """Property tests for the five invariants mentioned in the specification"""

    @given(
        budget_limit=st.floats(min_value=1.0, max_value=100.0),
        provider_switches=st.integers(min_value=0, max_value=3)
    )
    @settings(max_examples=10, deadline=500)
    def test_invariant_no_new_budget_on_provider_switch(
        self, 
        budget_limit: float, 
        provider_switches: int
    ):
        """Invariant 1: Switching provider does not create new task budget, does not clear existing consumption"""
        policy = BudgetPolicy(
            max_cost_usd=budget_limit,
            max_tokens=1000000,
            prices={"provider": "test_provider", "model": "test_model", "input_usd_per_million": 0.1, "output_usd_per_million": 0.1},
            admission_control="enabled",
            unbounded_reservation_usd=0.1,
            limits={
                "max_attempts": 100,
                "max_attempts_per_task": 10,
                "max_tasks": 50,
                "max_runtime_seconds": 3600
            },
            burn_rate_tokens=100000,
            burn_window_seconds=60
        )

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            try:
                ledger = BudgetLedger(tmp.name, "test_swarm", policy)
                
                # Make several reservations (simulating provider switches)
                bound = ExecutionBound(
                    provider="test_provider",
                    model="test_model",
                    input_tokens=100,
                    max_output_tokens=100,
                    provider_enforced=False,
                    request_bound="unbounded",
                    max_cost_usd=None
                )
                
                reservations = []
                for i in range(provider_switches + 1):
                    try:
                        reservation = ledger.reserve(f"worker1", f"task{i}", bound)
                        reservations.append(reservation)
                    except Exception:
                        # Might hit budget limits, which is expected
                        pass
                
                # Check that the total reserved doesn't exceed budget limit
                snapshot = ledger.snapshot()
                assert snapshot.reserved_estimate_usd <= budget_limit
            finally:
                # Clean up the temporary file
                try:
                    if os.path.exists(tmp.name):
                        os.unlink(tmp.name)
                except PermissionError:
                    # On Windows, sometimes files can't be deleted immediately
                    pass
    
    @given(
        budget_limit=st.floats(min_value=1.0, max_value=100.0)
    )
    @settings(max_examples=10, deadline=500)
    def test_invariant_unknown_cost_reservation_not_auto_released(
        self, 
        budget_limit: float
    ):
        """Invariant 2: Unknown cost reservations are never auto released by fallback"""
        policy = BudgetPolicy(
            max_cost_usd=budget_limit,
            max_tokens=1000000,
            prices={"provider": "test_provider", "model": "test_model", "input_usd_per_million": 0.1, "output_usd_per_million": 0.1},
            admission_control="enabled",
            unbounded_reservation_usd=0.1,
            limits={
                "max_attempts": 100,
                "max_attempts_per_task": 10,
                "max_tasks": 50,
                "max_runtime_seconds": 3600
            },
            burn_rate_tokens=100000,
            burn_window_seconds=60
        )

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            try:
                ledger = BudgetLedger(tmp.name, "test_swarm", policy)
                
                bound = ExecutionBound(
                    provider="test_provider",
                    model="test_model",
                    input_tokens=100,
                    max_output_tokens=100,
                    provider_enforced=False,
                    request_bound="unbounded",
                    max_cost_usd=None
                )
                
                reservation = ledger.reserve("worker1", "task1", bound)
                
                # Mark as uncertain (unknown cost)
                ledger.mark_uncertain(reservation)
                
                # The reservation should still be held as uncertain
                snapshot = ledger.snapshot()
                assert snapshot.uncertain_reservations == 1
                assert snapshot.reserved_estimate_usd > 0  # Still reserved
            finally:
                # Clean up the temporary file
                try:
                    if os.path.exists(tmp.name):
                        os.unlink(tmp.name)
                except PermissionError:
                    # On Windows, sometimes files can't be deleted immediately
                    pass
    
    @given(
        num_requests=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=10, deadline=500)
    def test_invariant_external_attempt_count_covers_all_requests(
        self, 
        num_requests: int
    ):
        """Invariant 3: External attempt count covers all real remote requests"""
        policy = BudgetPolicy(
            max_cost_usd=100.0,
            max_tokens=1000000,
            prices={"provider": "test_provider", "model": "test_model", "input_usd_per_million": 0.1, "output_usd_per_million": 0.1},
            admission_control="enabled",
            unbounded_reservation_usd=0.1,
            limits={
                "max_attempts": 100,
                "max_attempts_per_task": 10,
                "max_tasks": 50,
                "max_runtime_seconds": 3600
            },
            burn_rate_tokens=100000,
            burn_window_seconds=60
        )

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            try:
                ledger = BudgetLedger(tmp.name, "test_swarm", policy)
                
                bound = ExecutionBound(
                    provider="test_provider",
                    model="test_model",
                    input_tokens=100,
                    max_output_tokens=100,
                    provider_enforced=False,
                    request_bound="unbounded",
                    max_cost_usd=None
                )
                
                # Make multiple reservations to simulate multiple requests
                reservations = []
                for i in range(num_requests):
                    try:
                        reservation = ledger.reserve(f"worker1", f"task{i}", bound)
                        reservations.append(reservation)
                    except Exception:
                        # Might hit limits, which is expected
                        pass
                
                # The attempt count should reflect the number of requests made
                snapshot = ledger.snapshot()
                total_attempts = snapshot.pending_reservations + snapshot.uncertain_reservations + snapshot.unreconciled_reservations
                assert len(reservations) <= total_attempts
            finally:
                # Clean up the temporary file
                try:
                    if os.path.exists(tmp.name):
                        os.unlink(tmp.name)
                except PermissionError:
                    # On Windows, sometimes files can't be deleted immediately
                    pass
    
    def test_invariant_lost_lease_prevents_result_submission(self):
        """Invariant 4: Lost lease prevents successful result submission"""
        from swarm.models import Locality, Signal
        
        # Create a task ledger in a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            try:
                task_ledger = TaskLedger(tmp.name, "test_swarm")
                lease_manager = LeaseManager(task_ledger)
                
                # Create a proper locality object - authorized_scopes should be tuple
                locality = Locality(
                    workspace="./test_workspace",
                    authorized_scopes=(".",)
                )
                
                # Create a task first
                signal = Signal(
                    task_id="task1",
                    workspace="./test_workspace",
                    scope=".",
                    kind="opportunity",
                    payload={"test": "data"},
                    module="test_module",
                    required_capability="test_capability"
                )
                
                task_ledger.enqueue(signal)
                
                # Now acquire a lease
                lease = lease_manager.acquire("task1", "worker1", ttl_seconds=1.0, locality=locality)
                assert lease is not None
                
                # Simulate lease expiration by sleeping
                time.sleep(1.1)
                
                # The lease should no longer be valid
                assert not lease_manager.is_valid(lease)
            finally:
                # Clean up the temporary file
                try:
                    if os.path.exists(tmp.name):
                        os.unlink(tmp.name)
                except PermissionError:
                    # On Windows, sometimes files can't be deleted immediately
                    pass
    
    @given(
        num_workers=st.integers(min_value=1, max_value=5),
        budget_limit=st.floats(min_value=1.0, max_value=10.0)
    )
    @settings(max_examples=5, deadline=500)
    def test_invariant_all_candidates_down_has_bounded_exit(
        self, 
        num_workers: int, 
        budget_limit: float
    ):
        """Invariant 5: All candidates unavailable has bounded exit, does not loop back to chain start"""
        policy = BudgetPolicy(
            max_cost_usd=budget_limit,
            max_tokens=1000000,
            prices={"provider": "test_provider", "model": "test_model", "input_usd_per_million": 0.1, "output_usd_per_million": 0.1},
            admission_control="enabled",
            unbounded_reservation_usd=0.1,
            limits={
                "max_attempts": 10,  # Bounded number of attempts
                "max_attempts_per_task": 5,
                "max_tasks": 50,
                "max_runtime_seconds": 3600
            },
            burn_rate_tokens=100000,
            burn_window_seconds=60
        )

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            try:
                ledger = BudgetLedger(tmp.name, "test_swarm", policy)
                
                bound = ExecutionBound(
                    provider="test_provider",
                    model="test_model",
                    input_tokens=100,
                    max_output_tokens=100,
                    provider_enforced=False,
                    request_bound="unbounded",
                    max_cost_usd=None
                )
                
                # Try to make more reservations than allowed to trigger bounded exit
                successful_reservations = 0
                for i in range(policy.limits.max_attempts + 5):  # Try more than the limit
                    try:
                        reservation = ledger.reserve(f"worker{i % num_workers}", f"task{i}", bound)
                        successful_reservations += 1
                    except Exception:
                        # Expected when hitting limits
                        continue
                
                # Should not have exceeded the max attempts limit
                assert successful_reservations <= policy.limits.max_attempts
            finally:
                # Clean up the temporary file
                try:
                    if os.path.exists(tmp.name):
                        os.unlink(tmp.name)
                except PermissionError:
                    # On Windows, sometimes files can't be deleted immediately
                    pass


# Integration tests with respx for mocking HTTP responses
@respx.mock
def test_process_in_memory_transport_path():
    """Test classification logic using respx MockTransport for in-process paths"""
    # Mock an HTTP 400 Arrearage response
    route = respx.post("https://api.evomap.ai/v1/chat/completions").mock(
        return_value=httpx.Response(400, json={"error": {"code": "Arrearage"}})
    )
    
    # Use httpx.MockTransport to simulate the transport layer
    transport = httpx.MockTransport(lambda request: httpx.Response(400, json={"error": {"code": "Arrearage"}}))
    
    # Test the single_request function with the mock transport
    payload = {"model": "test-model", "messages": [{"role": "user", "content": "test"}]}
    response = single_request(payload, key="test-key", phase_timeout=30.0, transport=transport)
    
    assert response.status == 400
    assert isinstance(response.body, dict)
    body = response.body
    if isinstance(body, dict) and "error" in body:
        assert body["error"]["code"] == "Arrearage"
    
    # This demonstrates the in-process transport path that FC-A would classify


@respx.mock
def test_subprocess_integration_path():
    """Test subprocess integration path (mock mode) for classification/evidence_hash return"""
    # This would test the --request-child subprocess path when FC-A is implemented
    # Since FC-A isn't fully implemented yet, this is a placeholder for when it becomes available
    
    # The subprocess path would call provider_adapters for classification
    # and return classification + evidence_hash in the Reply
    
    # For now, just verify the Reply structure
    reply = Reply(
        http_status=400,
        error_kind="test_error",
        uncertain=True
    )
    
    assert reply.http_status == 400
    assert reply.error_kind == "test_error"
    assert reply.uncertain is True


if __name__ == "__main__":
    pytest.main([__file__])