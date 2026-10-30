"""OFFLINE FAKE EXECUTOR TESTS ONLY: not paid calls or performance evidence."""
import asyncio
from dataclasses import dataclass
import unittest
import autogen_adapter
import langgraph_adapter
from comparator_contract import ComparatorAborted


@dataclass
class FakeRequest:
    run_id: str
    framework: str
    block_id: str
    seed: int
    task_id: str
    prompt: str
    max_tokens: int
    temperature: float
    role: str = 'solver'
    attempt: int = 1


class FakeExecutor:
    def __init__(self, *, fail=None, block=False, expected_active=1, fatal_status=False, malformed=False):
        self.calls, self.active, self.peak = [], 0, 0
        self.fail, self.block = fail, block
        self.started = asyncio.Event()
        self.expected_active = expected_active
        self.fatal_status, self.malformed = fatal_status, malformed

    async def generate(self, request):
        self.calls.append(request)
        self.active += 1
        self.peak = max(self.peak, self.active)
        if self.active >= self.expected_active:
            self.started.set()
        try:
            if self.fail == request.task_id:
                raise RuntimeError('offline injected failure')
            if self.fatal_status and request.task_id == 't0':
                return dict(text=None, usage=None, status='fatal', request_id='fake_429',
                            evidence={'kind': 'offline_fake_not_benchmark', 'http_status': 429})
            if self.block:
                await asyncio.Event().wait()
            else:
                # Test-only yielding delay: never used by a real benchmark.
                await asyncio.sleep(0.002)
            return dict(text='malformed answer' if self.malformed else '#### 7', usage={'input_tokens': 10, 'output_tokens': 3},
                        status='completed', request_id='fake_' + request.task_id,
                        evidence={'kind': 'offline_fake_not_benchmark'})
        finally:
            self.active -= 1


class NativeAdapterTests(unittest.IsolatedAsyncioTestCase):
    def options(self, c, events):
        return dict(request_factory=FakeRequest, run_id='offline', block_id='b1', seed=123,
                    concurrency=c, max_tokens=4096, temperature=0.0, event_sink=events.append)

    def tasks(self, n=48):
        return [dict(id=f't{i}', prompt=f'exact public question {i}\nReturn final #### answer.',
                     gold='must never enter framework task or model request') for i in range(n)]

    async def test_native_scheduling_one_call_per_task_all_levels(self):
        for adapter in (autogen_adapter, langgraph_adapter):
            for c in (1, 2, 3, 4, 5):
                with self.subTest(adapter=adapter.__name__, concurrency=c):
                    fake, events = FakeExecutor(), []
                    tasks = self.tasks()
                    rows = await asyncio.wait_for(adapter.run_tasks(tasks, fake, **self.options(c, events)), 10)
                    self.assertEqual(len(fake.calls), 48)
                    self.assertEqual(len({call.task_id for call in fake.calls}), 48)
                    self.assertEqual(fake.peak, c)
                    self.assertEqual(fake.active, 0)
                    self.assertEqual([row['task_id'] for row in rows], [task['id'] for task in tasks])
                    by_id = {task['id']: task for task in tasks}
                    for call in fake.calls:
                        self.assertEqual(call.prompt, by_id[call.task_id]['prompt'])
                        self.assertEqual((call.attempt, call.role, call.max_tokens, call.temperature), (1, 'solver', 4096, 0.0))
                        self.assertFalse(hasattr(call, 'gold'))
                    self.assertEqual(sum(e['event'] == 'task_start' for e in events), 48)
                    self.assertEqual(sum(e['event'] == 'task_end' for e in events), 48)
                    self.assertEqual(events[-1]['event'], 'runtime_closed')
                    self.assertEqual(events[-1]['active_adapter_handlers'], 0)
                    self.assertTrue(all('prompt' not in event and 'text' not in event for event in events))

    async def test_exception_is_one_attempt_aborted_denominator_retained(self):
        for adapter in (autogen_adapter, langgraph_adapter):
            with self.subTest(adapter=adapter.__name__):
                fake, events = FakeExecutor(fail='t0'), []
                with self.assertRaises(ComparatorAborted) as caught:
                    await asyncio.wait_for(adapter.run_tasks(self.tasks(), fake, **self.options(5, events)), 5)
                self.assertEqual(len(caught.exception.results), 48)
                self.assertEqual(sum(call.task_id == 't0' for call in fake.calls), 1)
                self.assertLessEqual(len(fake.calls), 5)
                self.assertEqual(fake.active, 0)

    async def test_cancellation_drains_native_fake_requests(self):
        for adapter in (autogen_adapter, langgraph_adapter):
            with self.subTest(adapter=adapter.__name__):
                fake, events = FakeExecutor(block=True, expected_active=5), []
                task = asyncio.create_task(adapter.run_tasks(self.tasks(), fake, **self.options(5, events)))
                await asyncio.wait_for(fake.started.wait(), 5)
                task.cancel()
                with self.assertRaises(asyncio.CancelledError) as caught:
                    await asyncio.wait_for(task, 5)
                self.assertEqual(len(caught.exception.results), 48)
                self.assertEqual(fake.active, 0)
                self.assertEqual(len(fake.calls), 5)
                self.assertEqual(events[-1]['event'], 'runtime_closed')

    async def test_fatal_response_cancels_and_preserves_unknown_usage(self):
        for adapter in (autogen_adapter, langgraph_adapter):
            fake = FakeExecutor(fatal_status=True)
            with self.assertRaises(ComparatorAborted) as caught:
                await adapter.run_tasks(self.tasks(), fake, **self.options(5, []))
            self.assertEqual(len(caught.exception.results), 48)
            self.assertEqual(caught.exception.results[0]['status'], 'fatal')
            self.assertIsNone(caught.exception.results[0]['usage'])
            self.assertEqual(fake.active, 0)
            self.assertLessEqual(len(fake.calls), 5)
            self.assertTrue(any(row['status'] == 'not_run' for row in caught.exception.results))

    async def test_known_completed_malformed_answer_does_not_abort(self):
        for adapter in (autogen_adapter, langgraph_adapter):
            fake = FakeExecutor(malformed=True)
            rows = await adapter.run_tasks(self.tasks(), fake, **self.options(5, []))
            self.assertEqual(len(rows), 48)
            self.assertEqual(len(fake.calls), 48)
            self.assertTrue(all(row['text'] == 'malformed answer' and row['status'] == 'completed' for row in rows))

    async def test_known_truncated_and_filtered_outcomes_preserved_for_grader(self):
        class KnownTerminalExecutor(FakeExecutor):
            async def generate(self, request):
                row = await super().generate(request)
                row['evidence']['model_outcome'] = 'truncated' if int(request.task_id[1:]) % 2 == 0 else 'filtered'
                row['evidence']['finish_reason'] = 'length' if row['evidence']['model_outcome'] == 'truncated' else 'content_filter'
                row['text'] = '#### 7' if row['evidence']['model_outcome'] == 'truncated' else None
                return row
        for adapter in (autogen_adapter, langgraph_adapter):
            fake = KnownTerminalExecutor()
            rows = await adapter.run_tasks(self.tasks(), fake, **self.options(5, []))
            self.assertEqual(len(fake.calls), 48)
            self.assertTrue(all(row['status'] == 'completed' for row in rows))
            self.assertEqual(rows[0]['evidence']['model_outcome'], 'truncated')
            self.assertEqual(rows[0]['text'], '#### 7')
            self.assertEqual(rows[1]['evidence']['model_outcome'], 'filtered')
            self.assertIsNone(rows[1]['text'])

    async def test_invalid_levels_and_duplicate_ids_fail_before_calls(self):
        for adapter in (autogen_adapter, langgraph_adapter):
            for c in (0, 6, 8):
                fake = FakeExecutor()
                with self.assertRaises(ValueError):
                    await adapter.run_tasks(self.tasks(), fake, **self.options(c, []))
                self.assertEqual(fake.calls, [])
            fake = FakeExecutor()
            with self.assertRaises(ValueError):
                await adapter.run_tasks([{'id': 'same', 'prompt': 'a'}, {'id': 'same', 'prompt': 'b'}], fake, **self.options(1, []))
            self.assertEqual(fake.calls, [])

    async def test_native_dispatch_failure_preserves_aborted_inventory(self):
        def broken_sink(row):
            if row['event'] in ('message_publish_work', 'graph_send_fanout'):
                raise OSError('offline evidence sink failure')
        for adapter in (autogen_adapter, langgraph_adapter):
            fake = FakeExecutor()
            options = self.options(5, [])
            options['event_sink'] = broken_sink
            with self.assertRaises(ComparatorAborted) as caught:
                await asyncio.wait_for(adapter.run_tasks(self.tasks(), fake, **options), 5)
            self.assertEqual(len(caught.exception.results), 48)
            self.assertTrue(all(row['status'] == 'not_run' for row in caught.exception.results))
            self.assertEqual(fake.calls, [])


if __name__ == '__main__':
    unittest.main()
