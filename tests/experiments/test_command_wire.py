"""Official SDK HTTP request boundary; no sandbox or command is executed."""

from datetime import timedelta
from importlib.metadata import version
import json
import shlex
from unittest.mock import Mock

import httpx
import pytest
from opensandbox.config import ConnectionConfigSync
from opensandbox.exceptions import InvalidArgumentException, SandboxApiException
from opensandbox.models.execd import RunCommandOpts
from opensandbox.models.sandboxes import SandboxEndpoint
from opensandbox.sync.adapters.command_adapter import CommandsAdapterSync
from opensandbox.transport import RetryPolicy

from orchestration.experiments.backend import OpenSandboxSession


# Exact argv used by the failed interface-i-0930-bc4-01 cgroup probe.
CGROUP_ARGV = ["python3", "-c", (
    "from pathlib import Path;import json;"
    "print(json.dumps({n:Path('/sys/fs/cgroup/'+n).read_text().strip() "
    "for n in ['cpu.max','memory.max']}))")]
LITERAL_ARGV = ["python3", "-c", "import sys;print(sys.argv[1:])",
                "a b", "$HOME", "x'y", "", "a; echo unexpected", "$(id)", "a\nb"]
REQUIRED_MESSAGE = ("invalid request, validation error Key: 'RunCommandRequest.Command' "
                    "Error:Field validation for 'Command' failed on the 'required' tag")


@pytest.fixture
def command_http_boundary():
    assert version("opensandbox") == "1.1.0"
    requests = []

    def capture(request):
        payload = json.loads(request.read())
        requests.append((request.method, request.url.path, payload))
        # The actual pinned execd v1.1.0 source requires Command, not Argv.
        # This models only that published HTTP validation boundary, not a runtime.
        if not isinstance(payload.get("command"), str) or not payload["command"]:
            return httpx.Response(400, json={"code": "INVALID_REQUEST_BODY", "message": REQUIRED_MESSAGE},
                                  headers={"x-request-id": "contract-only"}, request=request)
        events = b'data: {"type":"init","text":"wire-command","timestamp":1}\n\n'
        if not payload.get("background", False):
            events += b'data: {"type":"execution_complete","timestamp":2,"execution_time":1}\n\n'
        return httpx.Response(200, headers={"content-type": "text/event-stream"},
                              content=events, request=request)

    config = ConnectionConfigSync(transport=httpx.MockTransport(capture),
                                  retry_policy=RetryPolicy.disabled(), disable_metrics=True)
    adapter = CommandsAdapterSync(config, SandboxEndpoint(endpoint="localhost:44772"))
    try:
        yield adapter, requests
    finally:
        # The production SandboxSync owns this transport; this test creates only an adapter.
        adapter._httpx_client.close()


@pytest.mark.parametrize("background", [False, True])
def test_official_110_list_reproduces_pinned_execd_command_required(command_http_boundary, background):
    adapter, requests = command_http_boundary
    with pytest.raises(SandboxApiException, match="RunCommandRequest.Command") as caught:
        adapter.run(CGROUP_ARGV, opts=RunCommandOpts(background=background,
                    timeout=timedelta(seconds=10), working_directory="/tmp/morph-research"))
    assert caught.value.status_code == 400
    assert caught.value.error.code == "INVALID_REQUEST_BODY"
    assert len(requests) == 1  # Transport retry remains disabled.
    method, path, body = requests[0]
    assert method == "POST" and path == "/command"
    assert body["argv"] == CGROUP_ARGV and "command" not in body
    assert body["timeout"] == 10000 and body["cwd"] == "/tmp/morph-research"
    assert body.get("background", False) is background


@pytest.mark.parametrize("background", [False, True])
@pytest.mark.parametrize("argv", [CGROUP_ARGV, LITERAL_ARGV], ids=["original-cgroup", "literal-arguments"])
def test_session_sends_compatible_command_without_argument_loss(command_http_boundary, argv, background):
    adapter, requests = command_http_boundary
    sandbox = Mock(id="wire-owned", commands=adapter)
    session = OpenSandboxSession(sandbox, owned=True)
    operation = session.start if background else session.run
    result = operation(argv, 10, "/tmp/morph-research")
    assert len(requests) == 1
    method, path, body = requests[0]
    assert method == "POST" and path == "/command"
    assert isinstance(body["command"], str) and "argv" not in body
    # POSIX lexical parsing must preserve every literal token, including shell syntax.
    assert shlex.split(body["command"]) == argv
    assert body["timeout"] == 10000 and body["cwd"] == "/tmp/morph-research"
    assert body.get("background", False) is background
    assert result.id == "wire-command" and session.command_ids == {"wire-command"}
    assert result.exit_code is (None if background else 0)
    sandbox.kill.assert_not_called()


@pytest.mark.parametrize("argv", [[], [""], ["echo", "a\0b"], ["echo", None]])
def test_invalid_argv_is_rejected_before_official_http_request(command_http_boundary, argv):
    adapter, requests = command_http_boundary
    session = OpenSandboxSession(Mock(id="wire-owned", commands=adapter), owned=True)
    with pytest.raises(InvalidArgumentException):
        session.run(argv, 10, "/tmp/morph-research")
    assert requests == [] and session.command_ids == set()
