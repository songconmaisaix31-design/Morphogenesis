# FC Runtime Acceptance Criteria

This document outlines the acceptance criteria for the Failure Classification (FC) runtime implementation in the Morphogenesis swarm system.

## Overview

The FC runtime implements a robust failure classification and provider switching mechanism that ensures:

1. Proper classification of different failure types
2. Shared state management across workers
3. Intelligent provider switching based on failure patterns
4. Preservation of budget and lease constraints
5. Accurate accounting of costs and usage

## Core Components

### 1. Failure Classification System

The system classifies failures into four categories:

- **CONFIRMED_REJECTION**: Confirmed rejections from providers (e.g., rate limiting, billing issues)
- **UNKNOWN_EFFECT**: Failures where the effect is unknown (e.g., timeouts, connection issues)
- **BUDGET_EXHAUSTED**: Cases where budgets are exhausted
- **CAPABILITY_MISMATCH**: Situations where the provider cannot handle the request

### 2. Provider Adapters

Provider-specific adapters for interpreting responses:

- **EvoMap Adapter**: Handles EvoMap API response interpretation
- **DashScope Adapter**: Handles DashScope API response interpretation

Each adapter implements the `ProviderAdapter` interface and provides consistent classification regardless of the execution path (direct call or subprocess).

### 3. Fault Observation Store

A persistent store for tracking failure observations:

- Uses append-only JSONL format
- Ensures idempotency (same request_id + attempt won't create duplicate records)
- Stores classification, evidence hash, retry timing, and other relevant metadata

### 4. Shared Breaker State

A distributed breaker mechanism that:

- Maintains state across multiple workers
- Uses the task ledger for persistence
- Implements state transitions based on failure patterns
- Respects cooldown periods and retry-after hints
- Allows for probe requests during recovery

## Runtime Behavior

### Process Flow

1. **Request Initiation**: Worker reserves budget and prepares request
2. **Provider Selection**: Selects appropriate provider based on breaker state
3. **Request Execution**: Executes request through the appropriate executor
4. **Response Classification**: Classifies response using provider adapter
5. **State Update**: Updates fault observation store and breaker state
6. **Provider Switching**: If applicable, switches to next available provider
7. **Result Handling**: Processes result or handles failure appropriately

### Failure Handling

#### Confirmed Rejection Handling
- Immediately marks provider as unavailable for specific reason
- Attempts to switch to next available provider
- Respects retry-after timing when available

#### Unknown Effect Handling
- Preserves existing budget reservations
- Does not trigger additional requests
- Maintains state to prevent retries until resolved

#### Budget/Capability Issues
- Properly distinguishes from provider rejection
- Maintains appropriate accounting
- Doesn't incorrectly mark providers as unavailable

### Lease and Budget Management

- Lease checks occur before every request send
- Ownership/fencing verification before success commit
- Budget holds persist across provider switches
- Cumulative budget accounting across all attempts

## Five Invariants Verification

The implementation maintains all five core invariants:

1. **No new budget on provider switch**: Switching providers doesn't create new task budget or clear existing consumption
2. **Unknown usage preserves reservations**: When usage is unknown, reservations remain and are not automatically released
3. **Accurate attempt counting**: External attempt counter covers all actual remote requests
4. **Lease enforcement**: Workers without valid leases cannot submit results
5. **Bounded exit**: When all candidates are unavailable, the system exits within configured bounds

## Testing Requirements

### Unit Tests
- Individual component functionality
- Provider adapter classification accuracy
- Breaker state transitions
- Fault observation storage and retrieval

### Integration Tests
- End-to-end request flow with classification
- Multi-worker shared state consistency
- Provider switching scenarios
- Lease and budget constraint enforcement

### Boundary Tests
- All failure classification types
- Concurrent probe attempts
- Stale lease handling during fallback
- Unknown effect scenarios
- Budget exhaustion cases

## Performance Considerations

- Minimal overhead for successful requests
- Efficient breaker state caching
- Asynchronous-safe observation storage
- Proper cleanup of temporary resources

## Security and Reliability

- No credential exposure in classification results
- Protected against timing attacks through consistent response handling
- Robust error handling to prevent cascading failures
- Isolated failure domains to prevent system-wide impact

## Monitoring and Observability

- Detailed logging of classification decisions
- Metrics for breaker state changes
- Tracking of provider switching frequency
- Audit trail for all budget and lease operations