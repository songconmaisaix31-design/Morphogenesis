"""Real AutoGen Core 0.7.5 coordinator/worker message scheduling."""
from __future__ import annotations
import asyncio
from dataclasses import dataclass
from autogen_core import MessageContext, RoutedAgent, SingleThreadedAgentRuntime, TopicId, TypeSubscription, message_handler
from opentelemetry.trace import NoOpTracerProvider
from comparator_contract import AdapterContext, ComparatorAborted


@dataclass
class StartBatch:
    pass


@dataclass
class Work:
    index: int
    slot: int


@dataclass
class Done:
    index: int
    slot: int


async def run_tasks(tasks, executor, **options):
    context = AdapterContext('autogen-core', '0.7.5', tasks, executor, **options)
    finished = asyncio.get_running_loop().create_future()
    runtime = SingleThreadedAgentRuntime(tracer_provider=NoOpTracerProvider(), ignore_unhandled_exceptions=False)

    class Coordinator(RoutedAgent):
        def __init__(self):
            super().__init__('Fixed inventory coordinator; no model invocation')
            self.next_index = 0
            self.completed = 0

        async def dispatch(self, slot):
            if context.aborted or self.next_index == len(context.tasks):
                return
            index = self.next_index
            self.next_index += 1
            context.emit('message_publish_work', index, native_agent_id=str(self.id), worker_slot=slot)
            await self.publish_message(Work(index, slot), TopicId('benchmark_worker', str(slot)))

        @message_handler
        async def on_start(self, message: StartBatch, ctx: MessageContext) -> None:
            for slot in range(min(context.concurrency, len(context.tasks))):
                await self.dispatch(slot)

        @message_handler
        async def on_done(self, message: Done, ctx: MessageContext) -> None:
            self.completed += 1
            context.emit('message_receive_done', message.index, native_agent_id=str(self.id),
                         sender_agent_id=str(ctx.sender), worker_slot=message.slot)
            if context.aborted or self.completed == len(context.tasks):
                if not finished.done():
                    finished.set_result(None)
            else:
                await self.dispatch(message.slot)

    class Worker(RoutedAgent):
        def __init__(self):
            super().__init__('One request per fixed task, via injected model executor')

        @message_handler
        async def on_work(self, message: Work, ctx: MessageContext) -> None:
            if context.aborted:
                return
            await context.leaf(message.index, native_agent_id=str(self.id),
                               sender_agent_id=str(ctx.sender), worker_slot=message.slot)
            await self.publish_message(Done(message.index, message.slot), TopicId('benchmark_coordinator', 'batch'))

    await Coordinator.register(runtime, 'benchmark_coordinator', Coordinator)
    await Worker.register(runtime, 'benchmark_worker', Worker)
    await runtime.add_subscription(TypeSubscription('benchmark_coordinator', 'benchmark_coordinator'))
    await runtime.add_subscription(TypeSubscription('benchmark_worker', 'benchmark_worker'))
    context.emit('runtime_start', native_runtime='SingleThreadedAgentRuntime')
    runtime.start()
    idle = None
    try:
        await runtime.publish_message(StartBatch(), TopicId('benchmark_coordinator', 'batch'))
        # Supervise native runtime failures as well as coordinator completion.
        # This is runtime teardown supervision, not an external model-work pool.
        idle = asyncio.create_task(runtime.stop_when_idle())
        done, _ = await asyncio.wait((finished, idle), return_when=asyncio.FIRST_COMPLETED)
        if idle in done:
            await idle
        if context.aborted:
            await context.cancel_requests()
        await asyncio.shield(idle)
    except BaseException as error:
        context.abort('outer_cancellation_or_runtime_failure')
        await context.cancel_requests()
        if idle is not None:
            await asyncio.gather(idle, return_exceptions=True)
        if isinstance(error, asyncio.CancelledError):
            error.results = context.results
        elif isinstance(error, Exception):
            raise ComparatorAborted(context.framework, context.results, type(error).__name__) from None
        raise
    finally:
        if idle is not None and not idle.done():
            await asyncio.shield(idle)
        await runtime.close()
        context.emit('runtime_closed', native_runtime='SingleThreadedAgentRuntime',
                     active_adapter_handlers=len(context.active_handlers),
                     transport_cleanup_owned_by_shared_executor=True)
    return context.finish()
