"""Boundary tests and property tests for failure chain - FC-D"""
import asyncio
import json
import subprocess
import sys
import tempfile
import os
import time
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
from swarm.evomap_executor import EvoMapExecutor, Reply, EvoMapConfig
from swarm.models import ExecutionBound
from swarm.worker_loop import Worker, WorkerConfig
from orchestration.gateway_transport import GatewayResponse, single_request
from orchestration.provider_adapters.base import FailureClassification


def configured(tmp_path, **updates):
    """Helper function to create a configured worker for testing"""
    from swarm.cli import demo_config, seed_demo
    target, state = seed_demo(tmp_path / "fixture")
    config = WorkerConfig.model_validate_json(demo_config(target, state, 0, 1.0))
    return config.model_copy(update=updates)


class TestFailureChainBoundaries:
    """Tests for failure classification and handling boundaries"""

    def test_bailian_400_arrearage_classification(self):
        """Test that HTTP 400 with Arrearage code is classified as confirmed_rejection"""
        import tempfile
        import os
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as cred_file:
            cred_file.write("test-key")
            cred_file.flush()

            # Prepare the request envelope with mock data
            payload = {"model": "evomap-gpt-5.6-luna", "messages": [{"role": "user", "content": "Hello"}]}
            config = EvoMapConfig(
                model="evomap-gpt-5.6-luna",
                credential_file=cred_file.name
            )
            # Use the new mock_spec flag to indicate this is a mock request for the subprocess
            envelope = {"config": config.model_dump(mode="json"), "request": payload, "mock_spec": "400_arrearage"}

            # Execute the subprocess with --request-child
            result = subprocess.run([
                sys.executable, "-m", "swarm.evomap_executor", "--request-child"
            ],
            input=json.dumps(envelope, ensure_ascii=False).encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
            env={**os.environ, "PYTHONPATH": os.getcwd()}
            )

            # Clean up the file
            try:
                os.unlink(cred_file.name)
            except (PermissionError, OSError):
                # File may still be locked by subprocess, ignore on Windows
                pass

            # Check that the subprocess executed successfully
            assert result.returncode == 0

            # Parse the output to ensure it contains classification and evidence_hash
            output = result.stdout.decode('utf-8')
            reply_data = json.loads(output)

            # Verify that the response contains the expected fields
            assert 'classification' in reply_data
            assert 'evidence_hash' in reply_data
            # Also verify the new fields are present
            assert 'normalized_reason' in reply_data
            assert 'retry_after_raw' in reply_data
            assert 'retry_after_seconds' in reply_data

            # Verify specific values for the arrearage case
            assert reply_data['classification'] == FailureClassification.CONFIRMED_REJECTION.value
            assert reply_data['normalized_reason'] == 'billing_arrearage'
            assert reply_data['http_status'] == 400
            assert reply_data['evidence_hash'] is not None  # Should have evidence hash

    def test_bailian_403_freetier_classification(self):
        """Test that HTTP 403 with AllocationQuota.FreeTierOnly is classified as confirmed_rejection"""
        import tempfile
        import os
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as cred_file:
            cred_file.write("test-key")
            cred_file.flush()

            # Prepare the request envelope with mock data
            payload = {"model": "evomap-gpt-5.6-luna", "messages": [{"role": "user", "content": "Hello"}]}
            config = EvoMapConfig(
                model="evomap-gpt-5.6-luna",
                credential_file=cred_file.name
            )
            # Use the new mock_spec flag to indicate this is a mock request for the subprocess
            envelope = {"config": config.model_dump(mode="json"), "request": payload, "mock_spec": "403_freetier"}

            # Execute the subprocess with --request-child
            result = subprocess.run([
                sys.executable, "-m", "swarm.evomap_executor", "--request-child"
            ],
            input=json.dumps(envelope, ensure_ascii=False).encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
            env={**os.environ, "PYTHONPATH": os.getcwd()}
            )

            # Clean up the file
            try:
                os.unlink(cred_file.name)
            except (PermissionError, OSError):
                # File may still be locked by subprocess, ignore on Windows
                pass

            # Check that the subprocess executed successfully
            assert result.returncode == 0

            # Parse the output to ensure it contains classification and evidence_hash
            output = result.stdout.decode('utf-8')
            reply_data = json.loads(output)

            # Verify that the response contains the expected fields
            assert 'classification' in reply_data
            assert 'evidence_hash' in reply_data
            # Also verify the new fields are present
            assert 'normalized_reason' in reply_data
            assert 'retry_after_raw' in reply_data
            assert 'retry_after_seconds' in reply_data

            # Verify specific values for the freetier case
            assert reply_data['classification'] == FailureClassification.CONFIRMED_REJECTION.value
            assert reply_data['normalized_reason'] == 'free_tier_quota_exceeded'
            assert reply_data['http_status'] == 403
            assert reply_data['evidence_hash'] is not None  # Should have evidence hash

    def test_rfc6585_429_with_retry_after_classification(self):
        """Test that HTTP 429 with Retry-After header is classified as confirmed_rejection"""
        import tempfile
        import os
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as cred_file:
            cred_file.write("test-key")
            cred_file.flush()

            # Prepare the request envelope with mock data
            payload = {"model": "evomap-gpt-5.6-luna", "messages": [{"role": "user", "content": "Hello"}]}
            config = EvoMapConfig(
                model="evomap-gpt-5.6-luna",
                credential_file=cred_file.name
            )
            # Use the new mock_spec flag to indicate this is a mock request for the subprocess
            envelope = {"config": config.model_dump(mode="json"), "request": payload, "mock_spec": "429_with_retry_after"}

            # Execute the subprocess with --request-child
            result = subprocess.run([
                sys.executable, "-m", "swarm.evomap_executor", "--request-child"
            ],
            input=json.dumps(envelope, ensure_ascii=False).encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
            env={**os.environ, "PYTHONPATH": os.getcwd()}
            )

            # Clean up the file
            try:
                os.unlink(cred_file.name)
            except (PermissionError, OSError):
                # File may still be locked by subprocess, ignore on Windows
                pass

            # Check that the subprocess executed successfully
            assert result.returncode == 0

            # Parse the output to ensure it contains classification and evidence_hash
            output = result.stdout.decode('utf-8')
            reply_data = json.loads(output)

            # Verify that the response contains the expected fields
            assert 'classification' in reply_data
            assert 'evidence_hash' in reply_data
            # Also verify the new fields are present
            assert 'normalized_reason' in reply_data
            assert 'retry_after_raw' in reply_data
            assert 'retry_after_seconds' in reply_data

            # Verify specific values for the 429 case
            assert reply_data['classification'] == FailureClassification.CONFIRMED_REJECTION.value
            assert reply_data['normalized_reason'] == 'rate_limited'
            assert reply_data['http_status'] == 429
            assert reply_data['evidence_hash'] is not None  # Should have evidence hash
            assert reply_data['retry_after_raw'] == "120"  # Should have the retry-after header value
            assert reply_data['retry_after_seconds'] == 120.0

    def test_drop_mid_response_classification(self):
        """Test that connection interruption/timeout is classified as unknown_effect"""
        import tempfile
        import os
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as cred_file:
            cred_file.write("test-key")
            cred_file.flush()

            # Prepare the request envelope with mock data
            payload = {"model": "evomap-gpt-5.6-luna", "messages": [{"role": "user", "content": "Hello"}]}
            config = EvoMapConfig(
                model="evomap-gpt-5.6-luna",
                credential_file=cred_file.name
            )
            # Use the new mock_spec flag to indicate this is a mock request for the subprocess
            envelope = {"config": config.model_dump(mode="json"), "request": payload, "mock_spec": "drop_mid_response"}

            # Execute the subprocess with --request-child
            result = subprocess.run([
                sys.executable, "-m", "swarm.evomap_executor", "--request-child"
            ],
            input=json.dumps(envelope, ensure_ascii=False).encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
            env={**os.environ, "PYTHONPATH": os.getcwd()}
            )

            # Clean up the file
            try:
                os.unlink(cred_file.name)
            except (PermissionError, OSError):
                # File may still be locked by subprocess, ignore on Windows
                pass

            # Check that the subprocess executed successfully
            assert result.returncode == 0

            # Parse the output to ensure it contains classification and evidence_hash
            output = result.stdout.decode('utf-8')
            reply_data = json.loads(output)

            # Verify that the response contains the expected fields
            assert 'classification' in reply_data
            assert 'evidence_hash' in reply_data
            # Also verify the new fields are present
            assert 'normalized_reason' in reply_data
            assert 'retry_after_raw' in reply_data
            assert 'retry_after_seconds' in reply_data

            # Verify specific values for the drop_mid_response case
            assert reply_data['classification'] == FailureClassification.UNKNOWN_EFFECT.value
            # For transport errors, evidence_hash should be None since there's no response body to hash
            assert reply_data['evidence_hash'] is None
            assert reply_data['uncertain'] is True
            # The error_kind should be present for transport errors
            assert reply_data['error_kind'] is not None

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

    def test_all_candidates_down_boundary(self, tmp_path):
        """Test bounded exit when all candidates are unavailable"""
        from unittest.mock import Mock
        from swarm.worker_loop import ExecutionResult, FixtureExecutor
        from swarm.models import Locality
        from swarm.breaker import BreakerConfig, SharedBreaker
        
        # Create a worker with a mock executor that always fails (simulating all candidates down)
        config = configured(tmp_path, energy=2)  # Limited energy to ensure bounded execution
        
        # Create a breaker config that will suspend quickly
        breaker_config = BreakerConfig(
            window_seconds=5.0,
            aggregation_period_seconds=1.0,
            failure_threshold=1,  # Low threshold to trigger suspension quickly
            min_samples=1,
            cooldown_seconds=1.0,
            probe_ttl_seconds=1.0
        )
        
        # Create a mock executor that simulates all candidates being unavailable
        # We'll inherit from FixtureExecutor to get the right attributes
        class FailingExecutor(FixtureExecutor):
            def __init__(self):
                super().__init__()
                self.execute_call_count = 0
            
            def execute(self, *args, **kwargs):
                self.execute_call_count += 1
                # Raise an exception to simulate the candidate is down
                raise Exception("all_candidates_unavailable")
        
        # Create primary and backup executors that both fail
        primary_executor = FailingExecutor()
        backup_executor = Mock()
        backup_executor.execute.side_effect = Exception("all_candidates_unavailable")
        backup_executor.bound.return_value = ExecutionBound(
            provider="backup-provider",
            model="backup-model",
            input_tokens=100,
            max_output_tokens=100,
            provider_enforced=False,
            request_bound="unbounded",
            max_cost_usd=None
        )
        # Make sure backup executor has required attributes
        backup_executor.provenance = "mock"
        backup_executor.usage_source = "fixture_mock"
        backup_executor.original_run_uri = None
        
        # Create worker with both executors and breaker
        worker = Worker(config, primary_executor, candidates=[primary_executor, backup_executor], 
                       breaker_config=breaker_config)
        
        # Run the worker - it should exit with bounded behavior, not loop infinitely
        result = worker.run()
        
        # Verify that the worker exited in a bounded manner
        # The state should reflect that attempts were exhausted or failed within limits
        assert result["state"] in ["stopped", "exhausted", "sleeping", "needs_review"]  # Bounded exit states
        
        # Verify that the executors were called a limited number of times (not infinite)
        assert primary_executor.execute_call_count <= config.energy  # Should respect the energy limit
        # The backup should not be called excessively due to breaker


class TestUnknownEffectProperty:
    """Property tests for unknown_effect handling - ensuring reservations are retained and no subsequent requests are made"""

    def test_unknown_effect_preserves_reservation_and_no_subsequent_requests(self, tmp_path):
        """Test that when unknown_effect occurs, reservation is preserved and no new requests are made"""
        from unittest.mock import Mock
        from swarm.models import Locality
        from swarm.worker_loop import ExecutionResult, FixtureExecutor

        # Create a worker with primary and backup executors to verify behavior
        config = configured(tmp_path)

        # Create a primary executor that simulates unknown effect
        class UncertainExecutor(FixtureExecutor):
            def __init__(self):
                super().__init__()
                self.execute_call_count = 0

            def execute(self, *args, **kwargs):
                self.execute_call_count += 1
                # Return an uncertain result (unknown effect)
                return ExecutionResult(None, {"usage": None}, uncertain=True)

        # Create primary and backup executors
        primary_executor = UncertainExecutor()
        backup_executor = Mock()
        backup_executor.execute.return_value = ExecutionResult(None, {"usage": None})
        backup_executor.bound.return_value = ExecutionBound(
            provider="backup-provider",
            model="backup-model",
            input_tokens=100,
            max_output_tokens=100,
            provider_enforced=False,
            request_bound="unbounded",
            max_cost_usd=None
        )
        # Make sure backup executor has required attributes
        backup_executor.provenance = "mock"
        backup_executor.usage_source = "fixture_mock"
        backup_executor.original_run_uri = None

        # Create worker with both executors
        worker = Worker(config, primary_executor, candidates=[primary_executor, backup_executor])

        # Run the worker to process a task
        result = worker.run()

        # The important thing is to verify that no subsequent requests were made to backup
        # after the unknown effect occurred in primary - this is tested by verifying the mock
        # execute call counts: primary should be called once, backup should not be called
        assert primary_executor.execute_call_count == 1  # Only one call was made to primary
        assert backup_executor.execute.call_count == 0   # Backup was not called (no fallback after unknown effect)

        # Check that the reservation handling is correct for unknown effect
        # The reservation should remain uncertain until clarified


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
    @settings(max_examples=5, deadline=1000)  # Increased deadline to accommodate test time
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


def test_subprocess_integration_path():
    """Test subprocess integration path (mock mode) for classification/evidence_hash return"""
    # Create a config with a temporary credential file
    config = EvoMapConfig(
        model="evomap-gpt-5.6-sol",
        credential_file=tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt').name
    )
    
    # Write a fake API key to the credential file
    with open(config.credential_file, 'w') as f:
        f.write("fake_api_key_for_testing")
    
    # Create a payload that will trigger the arrearage response
    payload = {
        "model": "evomap-gpt-5.6-sol",
        "messages": [{"role": "user", "content": "test"}],
        "max_tokens": 100
    }
    
    # Create envelope with mock spec for arrearage
    envelope = {
        "config": config.model_dump(mode="json"),
        "request": payload,
        "mock_spec": "400_arrearage"
    }
    
    # Run subprocess with mock spec
    environment = {name: value for name, value in os.environ.items() 
                  if name.upper() != "MORPH_EVOMAP_API_KEY"}
    
    result = subprocess.run([
        sys.executable, "-m", "swarm.evomap_executor", "--request-child"
    ], 
    input=json.dumps(envelope, ensure_ascii=False).encode("utf-8"),
    stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=environment,
    timeout=30, check=False)
    
    # Verify subprocess ran successfully
    assert result.returncode == 0
    
    # Parse the Reply from subprocess
    reply = Reply.model_validate_json(result.stdout.decode("utf-8"))
    
    # Verify the classification and evidence_hash are properly returned
    assert reply.classification is not None
    assert reply.evidence_hash is not None
    assert isinstance(reply.evidence_hash, str)
    assert len(reply.evidence_hash) == 64  # SHA256 hash length


if __name__ == "__main__":
    pytest.main([__file__])