"""Shared data/trace helpers only. Scheduling belongs to each real framework."""
from __future__ import annotations
import asyncio
from dataclasses import asdict, is_dataclass
from importlib.metadata import version
import time
from typing import Callable


class ComparatorAborted(RuntimeError):
    def __init__(self, framework, results, cause_type):
        super().__init__(f'{framework} aborted: {cause_type}; no automatic retry')
        self.framework = framework
        self.results = results
        self.cause_type = cause_type


class AdapterContext:
    def __init__(self, framework, package_version, tasks, executor, *, request_factory,
                 run_id, block_id, seed, concurrency, max_tokens=4096, temperature=0.0,
                 event_sink: Callable | None = None):
        if version(framework) != package_version:
            raise RuntimeError(f'{framework} must be exactly {package_version}')
        if type(concurrency) is not int or not 1 <= concurrency <= 5:
            raise ValueError('Configured concurrency must be 1 through 5')
        if not tasks:
            raise ValueError('A nonempty fixed task inventory is required')
        self.tasks = [{'id': t['id'], 'prompt': t['prompt']} for t in tasks]
        if any(not isinstance(t['id'], str) or not t['id'] or not isinstance(t['prompt'], str) for t in self.tasks):
            raise ValueError('Each task requires a nonempty string id and a string prompt')
        if len({t['id'] for t in self.tasks}) != len(self.tasks):
            raise ValueError('Duplicate task ids')
        self.framework, self.package_version = framework, package_version
        self.executor, self.request_factory = executor, request_factory
        self.run_id, self.block_id, self.seed = run_id, block_id, seed
        self.concurrency, self.max_tokens, self.temperature = concurrency, max_tokens, temperature
        self.event_sink = event_sink
        self.sequence = 0
        self.aborted = False
        self.cause_type = None
        self.active_handlers = set()
        self.active_requests = set()
        self.results = [dict(task_id=t['id'], status='not_run', text=None, usage=None,
                             request_id=None, evidence={}) for t in self.tasks]

    def emit(self, event, index=None, **native):
        self.sequence += 1
        row = dict(schema='swarm.native-adapter-event.v1', event=event,
                   framework=self.framework, framework_version=self.package_version,
                   run_id=self.run_id, block_id=self.block_id, seed=self.seed,
                   monotonic_ns=time.monotonic_ns(), sequence=self.sequence,
                   configured_concurrency=self.concurrency,
                   task_id=self.tasks[index]['id'] if index is not None else None,
                   observation_scope='framework scheduling; NOT HTTP or server computation', **native)
        if self.event_sink is not None:
            self.event_sink(row)

    def abort(self, cause_type):
        self.aborted = True
        self.cause_type = self.cause_type or cause_type

    async def leaf(self, index, **native):
        """One leaf invocation; no loop, pool, retry, HTTP client or key access."""
        if self.aborted:
            return
        handler = asyncio.current_task()
        self.active_handlers.add(handler)
        task = self.tasks[index]
        self.results[index]['status'] = 'running'
        try:
            self.emit('task_start', index, **native)
            request = self.request_factory(run_id=self.run_id, framework=self.framework,
                block_id=self.block_id, seed=self.seed, task_id=task['id'], role='solver',
                attempt=1, prompt=task['prompt'], max_tokens=self.max_tokens,
                temperature=self.temperature)
            # One owned request future inside the framework-invoked leaf. This
            # enables transport cancellation without canceling native queue tasks.
            pending = asyncio.create_task(self.executor.generate(request))
            self.active_requests.add(pending)
            try:
                response = await pending
            finally:
                self.active_requests.discard(pending)
            if is_dataclass(response):
                response = asdict(response)
            elif not isinstance(response, dict):
                response = {name: getattr(response, name) for name in
                            ('text', 'usage', 'status', 'request_id', 'evidence')}
            row = {name: response.get(name) for name in ('text', 'usage', 'status', 'request_id', 'evidence')}
            row['task_id'] = task['id']
            self.results[index] = row
            if row['status'] != 'completed':
                self.abort('noncompleted_model_response')
                await self.cancel_requests()
            self.emit('task_end', index, status=row['status'], **native)
        except asyncio.CancelledError:
            self.results[index]['status'] = 'canceled_unknown'
            self.abort('cancellation')
            self.emit('task_canceled', index, status='canceled_unknown', **native)
            # Return to the native handler so its queue accounting can drain.
        except Exception as error:
            self.results[index]['status'] = 'fatal'
            self.results[index]['evidence'] = {'exception_type': type(error).__name__}
            self.abort(type(error).__name__)
            await self.cancel_requests()
            # Never log repr(error), which may contain a provider response or key.
            self.emit('task_fatal', index, exception_type=type(error).__name__, **native)
        finally:
            self.active_handlers.discard(handler)

    async def cancel_requests(self):
        # Cleanup only, NOT a task scheduler. Shared generate MUST be truly async
        # and hold its account slot until transport finalization (no to_thread).
        requests = [task for task in self.active_requests if not task.done()]
        for task in requests:
            task.cancel()
        if requests:
            await asyncio.gather(*requests, return_exceptions=True)

    def finish(self):
        if self.aborted or any(row['status'] != 'completed' for row in self.results):
            raise ComparatorAborted(self.framework, self.results, self.cause_type or 'incomplete_native_run')
        return self.results
