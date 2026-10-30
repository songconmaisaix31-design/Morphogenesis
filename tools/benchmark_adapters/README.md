# Native framework comparison adapters

These adapters execute the **real installed** AutoGen Core 0.7.5 and LangGraph
1.2.18 runtimes. They do not execute Pi or SWA, and do not claim integrated SWA
or collaborative-reasoning superiority. The initial parent-controlled pilot is
48 identical GSM8K tasks × 5 concurrency levels × 3 frameworks × 1 repetition:
720 planned one-attempt model leaves. Repeats are a later decision, not automatic.

## Agreed boundary

```python
from swarm.benchmark_model import ModelRequest
from autogen_adapter import run_tasks  # or langgraph_adapter

results = await run_tasks(
    [{"id": task_id, "prompt": exact_shared_prompt}, ...],
    shared_executor,
    request_factory=ModelRequest,
    run_id="pilot", block_id="arm_1", seed=123,
    concurrency=5, max_tokens=4096, temperature=0.0,
    event_sink=parent_owned_safe_event_writer,
)
```

Add this directory to the orchestrator import path. Results retain original task
order with `task_id, text, usage, status, request_id, evidence`. Prompt bytes are
passed unchanged. Extra input fields, including gold answers, are not copied.
No grading, answer repair, retries, credentials, HTTP clients or account limits
are implemented here. `swarm/benchmark_model.py` alone owns the shared account
semaphore, fixed system prompt, transient key, real HTTP request evidence and
transport cancellation. Its async `generate()` must be truly asynchronous, not
a thread wrapper. Native framework settings are not a substitute for that gate.

The same shared gate is used by Morphogenesis and both comparators. One parent
owns execution and admission. Concurrent benchmark processes or other account
traffic cannot be made safe by a per-framework semaphore; do not start them.

## Genuine scheduling

- AutoGen: `SingleThreadedAgentRuntime` delivers typed `StartBatch`, `Work` and
  `Done` messages. A `RoutedAgent` coordinator fills at most c worker slots and
  dispatches the next inventory task on a worker's completion message. The
  runtime, not a common external asyncio pool, executes each worker handler.
- LangGraph: one compiled `StateGraph` emits a `Send("solve", ...)` for each
  inventory index. The actual graph executor queues and executes them under
  `max_concurrency=c`. No node retry policy or graph re-invocation is enabled.
- Shared helper `AdapterContext.leaf` makes exactly one injected request. It has
  no worker loop/pool. Its single owned request future permits canceling HTTP
  work while native message/graph queues drain normally. Framework tasks are
  not replaced by a generic scheduler.

On noncompleted status or exception, admissions stop, owned requests are canceled
and awaited, and the native runtime drains. `ComparatorAborted.results` retains
every task slot, including `not_run` and `canceled_unknown`. External
`CancelledError` also carries `.results`. Parent policy stops the whole pilot
after such an aborted arm; aborted elapsed time is not completed throughput.
Known completed malformed/wrong answers continue unchanged for the parent to
score zero. No canceled response is counted as a wrong completed answer.
HTTP 200 `length`/`content_filter` outcomes likewise remain status `completed`
with untouched `evidence.model_outcome=truncated/filtered`; the parent must score
them FAIL even if partial text contains a numerically correct final marker.

## Native event schema

Events contain `schema, event, framework, framework_version, run_id, block_id,
seed, monotonic_ns, sequence, configured_concurrency, task_id` and native
identity fields (`native_agent_id`, `sender_agent_id`, `worker_slot`, or
`native_node_id`, `native_send_index`). Events include runtime start/close,
AutoGen work publish/done receive, LangGraph Send fan-out, and task start/end/
fatal/canceled. They contain no prompts, response text, headers or credentials.

**These are framework observations, not HTTP concurrency.** Actual request
starts, response boundaries, errors, usage and request IDs come only from the
shared executor. Neither boundary proves provider-internal simultaneous compute.
AutoGen uses a no-op telemetry provider; LangSmith tracing is explicitly off.

## Install and offline validation

Official releases were verified against PyPI JSON, both not yanked:

- https://pypi.org/pypi/autogen-core/0.7.5/json
- https://pypi.org/pypi/langgraph/1.2.18/json

The standalone development `.venv` was isolated from Morphogenesis. The separate
delivery evidence archive's `install-report.json` preserves
the resolved package URLs and SHA256 digests; `dependency-freeze.txt` records the
resolved environment. Install from official PyPI with `requirements.txt` for
the two direct pins, or review the full freeze for exact transitive versions.

```sh
.venv/bin/python -W error -m unittest -v test_adapters.py
```

All tests use a **fake executor**, no key or network/provider calls. Fake delays
are test-only and are never performance evidence. Coverage: 48 one-attempt calls
at each c=1/2/3/4/5 with observed fake peak c; unchanged prompts/no gold; fatal
status/exception; native cancellation with zero active fake requests; malformed
completed responses continue; invalid caps/duplicate IDs rejected before calls.

Official runtime references:

- https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/framework/message-and-communication.html
- https://docs.langchain.com/oss/python/langgraph/graph-api
- https://reference.langchain.com/python/langgraph/types/Send

## Portable source delivery and one shared environment

The owner may copy this small source directory (excluding `.venv`, `__pycache__`
and local build caches) to `tools/benchmark_adapters/` in the Morphogenesis source
package. Modules use no fixed `/scratch` paths. Official dependency license texts
and attribution are included under `licenses/` and `THIRD_PARTY_NOTICES.md`.

From the repository root, use the SAME pinned Python for Morph and both adapters:

```sh
PY=.venv-benchmark/bin/python
export UV_CACHE_DIR="$PWD/.runtime/uv-cache"
uv pip install --python "$PY" --index-url https://pypi.org/simple -r tools/benchmark_adapters/requirements.txt
uv pip check --python "$PY"
PYTHONPATH=. "$PY" tools/benchmark_adapters/validate_adapter_env.py
PYTHONPATH=.:tools/benchmark_adapters "$PY" -W error -m unittest discover -s tools/benchmark_adapters -p test_adapters.py -v
uv pip freeze --python "$PY" > artifacts/comparison-shared-environment-freeze.txt
```

The actual shared environment is uv-created and has no `pip` module; the commands
above intentionally use uv with an explicit writable cache. These are
install/offline commands, not a paid-run command. The parent owns any
live invocation and key input. Never use separate environments to give different
arms different dependency sets. The standalone `.venv` was development validation
only. The same shared candidate has now passed dependency compatibility checking
(103 packages), real ModelRequest/ModelResponse import smoke, and all eight
offline adapter tests with warnings treated as errors. See
`shared-env-offline-smoke.json` and `shared-env-offline-tests.log` in that evidence
archive (not committed runtime artifacts); rerun after
any shared environment change before live execution.
