#!/usr/bin/env python3
"""Offline discovery/import/contract validation in the SAME Python as Morph."""
import asyncio
import importlib.metadata
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
if (HERE.parent.parent / 'swarm' / 'benchmark_model.py').is_file():
    sys.path.insert(0, str(HERE.parent.parent))

from swarm.benchmark_model import ModelRequest, ModelResponse
import autogen_adapter
import langgraph_adapter


class OfflineExecutor:
    def __init__(self):
        self.calls = 0

    async def generate(self, request):
        assert isinstance(request, ModelRequest)
        assert request.attempt == 1 and request.max_tokens == 4096
        self.calls += 1
        await asyncio.sleep(0)  # cooperative yield only; no benchmark timing
        return ModelResponse(text='#### 7', usage=None, status='completed',
                             request_id=None, evidence={'kind': 'offline_fake'})


async def main():
    output = {'scope': 'offline import and contract smoke, NOT benchmark results',
              'python_executable': sys.executable, 'model_api_calls': 0, 'frameworks': {}}
    for module, package, expected in ((autogen_adapter, 'autogen-core', '0.7.5'),
                                      (langgraph_adapter, 'langgraph', '1.2.18')):
        installed = importlib.metadata.version(package)
        assert installed == expected
        executor, events = OfflineExecutor(), []
        rows = await module.run_tasks([{'id': f'fake{i}', 'prompt': f'Offline fake problem {i}'} for i in range(5)],
            executor, request_factory=ModelRequest, run_id='offline', block_id='b1', seed=20261030,
            concurrency=5, max_tokens=4096, temperature=0, event_sink=events.append)
        assert len(rows) == executor.calls == 5
        assert events[-1]['active_adapter_handlers'] == 0
        output['frameworks'][package] = {'version': installed, 'module': Path(module.__file__).name,
            'fake_calls': executor.calls, 'native_events': len(events), 'active_after': 0}
    print(json.dumps(output, indent=2))


if __name__ == '__main__':
    asyncio.run(main())
