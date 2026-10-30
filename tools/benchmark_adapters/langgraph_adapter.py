"""Real LangGraph 1.2.18 StateGraph/Send fan-out and native concurrency limit."""
from __future__ import annotations
import asyncio
import operator
from typing import Annotated, TypedDict
from langgraph.graph import END, START, StateGraph
from langgraph.types import Send
from langsmith import tracing_context
from comparator_contract import AdapterContext, ComparatorAborted


class BatchState(TypedDict):
    indexes: list[int]
    results: Annotated[list[dict], operator.add]


async def run_tasks(tasks, executor, **options):
    context = AdapterContext('langgraph', '1.2.18', tasks, executor, **options)

    def dispatch(state):
        context.emit('graph_send_fanout', native_node_id='__start__', sends=len(state['indexes']))
        return [Send('solve', {'index': index}) for index in state['indexes']]

    async def solve(state):
        index = state['index']
        if context.aborted:
            return {'results': []}
        await context.leaf(index, native_node_id='solve', native_send_index=index)
        return {'results': [context.results[index]]}

    graph = StateGraph(BatchState)
    graph.add_node('solve', solve, retry_policy=None)
    graph.add_conditional_edges(START, dispatch, ['solve'])
    graph.add_edge('solve', END)
    compiled = graph.compile(checkpointer=False)
    context.emit('runtime_start', native_runtime='CompiledStateGraph', native_nodes=['__start__', 'solve', '__end__'])
    execution = None
    try:
        # No LangSmith export or credentials; native graph runtime owns all task
        # fan-out, queuing and max_concurrency. No adapter-side worker pool.
        with tracing_context(enabled=False):
            execution = asyncio.create_task(compiled.ainvoke(
                {'indexes': list(range(len(context.tasks))), 'results': []},
                config={'max_concurrency': context.concurrency, 'recursion_limit': 4, 'callbacks': []}))
            output = await asyncio.shield(execution)
        if len(output['results']) != len(context.tasks):
            context.abort('incomplete_graph_reduction')
    except BaseException as error:
        context.abort('graph_cancellation_or_runtime_failure')
        await context.cancel_requests()
        if execution is not None:
            await asyncio.gather(execution, return_exceptions=True)
        if isinstance(error, asyncio.CancelledError):
            error.results = context.results
        elif isinstance(error, Exception):
            raise ComparatorAborted(context.framework, context.results, type(error).__name__) from None
        raise
    finally:
        context.emit('runtime_closed', native_runtime='CompiledStateGraph',
                     active_adapter_handlers=len(context.active_handlers),
                     transport_cleanup_owned_by_shared_executor=True)
    return context.finish()
