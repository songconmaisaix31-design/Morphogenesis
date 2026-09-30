"""Contract-local tests: upstream behaviors, exact argv, unknown-preserving events."""

import json
from pathlib import Path
import subprocess
import sys
import shutil

import pytest

from contracts.identity import AgentId
from orchestration.native_agents.events import parse_event
from orchestration.native_agents.launch import build_launch, write_mcp_config
from orchestration.native_agents.models import LaunchRequest, McpStdio, ResearchBootstrap
from orchestration.native_agents.registry import REGISTRY, child_environment, resolve_executable
from orchestration.native_agents.upstream_contracts import is_print_headless, recognize_process


@pytest.mark.parametrize(("tokens", "headless"), [
    (["claude", "--print", "hello"], True),
    (["claude", "-p", "hello"], True),
    (["claude", "--output-format=json", "hello"], True),
    (["claude", "--output-format", "stream-json", "hello"], True),
    (["claude", "--resume", "abc123"], False),
    (["claude", "--", "--print"], False),
    (["claude", "--output-format=text"], False),
    (["claude", "--output-format"], False),
])
def test_upstream_print_mode_port(tokens: list[str], headless: bool) -> None:
    # Adapted from upstream agent-process-recognition.test.ts print-mode cases;
    # the terminator behavior is directly in print-mode-headless-command.ts.
    assert is_print_headless(tokens) is headless


def test_python_port_against_unchanged_upstream_typescript() -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node required to execute original TypeScript module")
    version = subprocess.run([node, "--version"], capture_output=True, text=True, check=True).stdout
    parts = tuple(int(part) for part in version.strip().lstrip("v").split("."))
    if parts < (22, 6, 0):
        pytest.skip("Node >=22.6 required for built-in TypeScript stripping")
    cases = [["claude", *args] for args in [[], ["--print"], ["-p", "hello"], ["--", "--print"],
             ["--output-format", "stream-json"], ["--output-format=JSON"], ["--output-format=text"],
             ["--resume", "abc123"], ["--output-format"], ["--print=true"], ["--", "--output-format=json"]]]
    harness = Path(__file__).parent / "upstream/check_print_mode.mjs"
    result = subprocess.run([node, "--experimental-strip-types", str(harness)], input=json.dumps(cases),
                             capture_output=True, text=True, encoding="utf-8", shell=False, check=True)
    assert json.loads(result.stdout) == [is_print_headless(case) for case in cases]


@pytest.mark.parametrize(("name", "runtime"), [
    ("codex-aarch64-ap", "codex"),
    (r"C:\Users\dev\AppData\Roaming\npm\claude.exe", "claude"),
    ("/usr/local/bin/claude", "claude"), ("powershell.exe", None),
    ("openclaude", None), ("cmd.exe", None), ("node", None), (None, None),
])
def test_upstream_process_basename_port(name: str | None, runtime: str | None) -> None:
    assert recognize_process(name) == runtime


def npm_shim(tmp_path: Path, runtime: str, entry: str) -> Path:
    spec = REGISTRY[runtime]
    root = tmp_path / "space & ` dollar $ HOME"
    root.mkdir(exist_ok=True)
    shim = root / (runtime + ".ps1")
    shim.write_text("this shell content must never be executed", encoding="utf-8")
    package = root / "node_modules" / spec.npm_package
    (package / "bin").mkdir(parents=True)
    (package / entry).write_text("placeholder", encoding="utf-8")
    (package / "package.json").write_text(json.dumps({"name": spec.npm_package, "bin": {runtime: entry}}))
    return shim


def test_windows_npm_native_entry_from_actual_manifest(tmp_path: Path) -> None:
    shim = npm_shim(tmp_path, "claude", "bin/claude.exe")
    command = resolve_executable(REGISTRY["claude"], platform="win32", executable=str(shim))
    assert command == (str((shim.parent / "node_modules/@anthropic-ai/claude-code/bin/claude.exe").resolve()),)
    assert not any(part.lower() in {"cmd", "powershell", "-command", "/c"} for part in command)


def test_windows_npm_js_entry_requires_native_node(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    shim = npm_shim(tmp_path, "codex", "bin/codex.js")
    monkeypatch.setattr("orchestration.native_agents.registry.shutil.which", lambda name: "C:/node/node.exe")
    command = resolve_executable(REGISTRY["codex"], platform="win32", executable=str(shim))
    assert command == ("C:/node/node.exe", str((shim.parent / "node_modules/@openai/codex/bin/codex.js").resolve()))


def test_windows_npm_entry_escape_is_rejected(tmp_path: Path) -> None:
    shim = npm_shim(tmp_path, "claude", "bin/claude.exe")
    package = shim.parent / "node_modules/@anthropic-ai/claude-code"
    (package / "package.json").write_text(json.dumps({"name": REGISTRY["claude"].npm_package,
                                                      "bin": {"claude": "../../../../../escaped.exe"}}))
    with pytest.raises((ValueError, FileNotFoundError)):
        resolve_executable(REGISTRY["claude"], platform="win32", executable=str(shim))


def test_linux_and_wsl_resolve_local_executable_without_shell(tmp_path: Path) -> None:
    cli = tmp_path / "codex"
    cli.touch()
    assert resolve_executable(REGISTRY["codex"], platform="linux", executable=str(cli)) == (str(cli),)
    assert resolve_executable(REGISTRY["codex"], platform="wsl", executable=str(cli)) == (str(cli),)


SESSION = "4b30d7cc-bb1d-4ffc-a3bd-813d9c2523ad"


@pytest.mark.parametrize("runtime", ["codex", "claude"])
@pytest.mark.parametrize("mode", ["headless", "interactive"])
@pytest.mark.parametrize("resume", [False, True])
def test_native_launch_prompt_transport_and_resume(tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
                                                  runtime: str, mode: str, resume: bool) -> None:
    monkeypatch.setattr("orchestration.native_agents.launch.resolve_executable", lambda spec: (spec.executable,))
    prompt = "--print\n科学 $HOME `touch x` $(echo x); & \"quoted\""
    config_path = tmp_path / "host.json"
    config_path.write_text(json.dumps({"workspace": str(tmp_path), "worker_id": "native-author", "swarm_id": "research-demo",
                                      "agent": {"role": "builder", "instance": 0}}))
    request = LaunchRequest(runtime=runtime, workspace=tmp_path, prompt=prompt, mode=mode,
                            session_id=SESSION if resume else None,
                            mcp=McpStdio(command=sys.executable, args=("-m", "swarm.research", "--config", str(config_path))))
    plan = build_launch(request, claude_mcp_path=tmp_path / "mcp.json")
    assert not any(arg in {"--last", "--ephemeral", "--ignore-user-config", "--bare",
                          "--dangerously-skip-permissions", "--dangerously-bypass-approvals-and-sandbox"} for arg in plan.argv)
    if mode == "headless":
        assert plan.stdin_text == prompt
        assert prompt not in plan.argv
    else:
        assert plan.stdin_text is None
        assert plan.argv[-2:] == ("--", prompt)
    if resume:
        assert plan.argv.count(SESSION) == 1
        assert ("resume" if runtime == "codex" else "--resume") in plan.argv
    if runtime == "codex":
        assert any("mcp_servers.morph_research.command=" in token for token in plan.argv)
        assert plan.mcp_config is None
    else:
        assert plan.mcp_config["mcpServers"]["morph_research"]["command"] == sys.executable
    # Paths may legitimately include the workspace parent named 'orca'. Runtime
    # dependency is determined by the executable, not substrings of data arguments.
    assert plan.argv[0] == runtime
    assert not any(token in {"orca", "orca-dev", "orca-ide", "cmd", "powershell", "/c"} for token in plan.argv)
    assert plan.host_binding.agent == AgentId(role="builder", instance=0)
    assert plan.host_binding.worker_id == "native-author"


def test_mcp_write_is_exclusive_and_preserves_existing_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("orchestration.native_agents.launch.resolve_executable", lambda spec: (spec.executable,))
    path = tmp_path / "mcp.json"
    plan = build_launch(LaunchRequest(runtime="claude", workspace=tmp_path, prompt="discover",
                        mcp=McpStdio(command=sys.executable)), claude_mcp_path=path)
    write_mcp_config(plan, path)
    content = path.read_bytes()
    with pytest.raises(FileExistsError):
        write_mcp_config(plan, path)
    assert path.read_bytes() == content


@pytest.mark.parametrize("env", [{"HOME": "copied"}, {"CODEX_HOME": "copied"}, {"ORCA_TOKEN": "bad"}])
def test_mcp_cannot_replace_native_auth_or_dispatch_authority(env: dict[str, str]) -> None:
    with pytest.raises(ValueError):
        McpStdio(command=sys.executable, env=env)


def test_child_inherits_auth_locations_without_orca_capability(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CODEX_HOME", "original-user-location")
    monkeypatch.setenv("ORCA_DISPATCH_CAPABILITY", "must-not-inherit")
    environment = child_environment()
    assert environment["CODEX_HOME"] == "original-user-location"
    assert "ORCA_DISPATCH_CAPABILITY" not in environment


@pytest.mark.parametrize("line", ["not json", "null", "[]", "3", '{"type":"future.event","nested":{"x":0}}'])
@pytest.mark.parametrize("runtime", ["codex", "claude"])
def test_unknown_event_preserved_without_invented_usage(line: str, runtime: str) -> None:
    event, = parse_event(runtime, line)
    assert event.kind == "unknown"
    assert event.usage.tokens is None and event.usage.cost_usd is None
    assert event.terminal is None


@pytest.mark.parametrize("usage", [{}, {"input_tokens": None, "output_tokens": 0},
                                     {"input_tokens": True, "output_tokens": 2},
                                     {"input_tokens": -1, "output_tokens": 2}])
def test_invalid_or_missing_usage_is_unknown(usage: dict[str, object]) -> None:
    event, = parse_event("codex", json.dumps({"type": "turn.completed", "usage": usage}))
    assert event.usage.tokens is None


def test_codex_zero_is_known_and_cached_input_not_double_counted() -> None:
    event, = parse_event("codex", '{"type":"turn.completed","usage":{"input_tokens":0,"output_tokens":0,"cached_input_tokens":10}}')
    assert event.usage.tokens == 0
    assert event.usage.cost_usd is None


def test_codex_real_mcp_shape_retains_tool_and_session_events() -> None:
    event, = parse_event("codex", '{"type":"item.started","item":{"id":"item_3","type":"mcp_tool_call","server":"morph_research","tool":"discover"}}')
    assert (event.kind, event.tool_name, event.tool_id) == ("tool", "discover", "item_3")
    event, = parse_event("codex", json.dumps({"type": "thread.started", "thread_id": SESSION}))
    assert event.session_id == SESSION


def test_claude_tool_and_result_shapes() -> None:
    events = parse_event("claude", json.dumps({"type": "assistant", "session_id": SESSION, "message": {
        "content": [{"type": "tool_use", "id": "a", "name": "mcp__morph_research__discover"},
                    {"type": "tool_use", "id": "b", "name": "Bash"}]}}))
    assert [event.tool_id for event in events] == ["a", "b"]
    result, = parse_event("claude", json.dumps({"type": "result", "subtype": "success", "is_error": False,
        "session_id": SESSION, "total_cost_usd": 0, "usage": {"input_tokens": 3, "output_tokens": 2,
         "cache_creation_input_tokens": 4, "cache_read_input_tokens": 5}}))
    assert result.terminal == "completed" and result.usage.tokens == 14 and result.usage.cost_usd == 0
    unknown, = parse_event("claude", '{"type":"result","subtype":"success"}')
    assert unknown.terminal is None and unknown.usage.tokens is None


@pytest.mark.parametrize("runtime", ["codex", "claude"])
@pytest.mark.parametrize("tool_name", ["claim_task", "lease_task"])
def test_canonical_attempt_parsed_from_mcp_result_without_new_identity(runtime: str, tool_name: str) -> None:
    attempt = {"task_id": "science-1", "agent": {"role": "builder", "instance": 0}, "attempt": 2}
    lease = {"task_id": "science-1", "worker_id": "native-author", "attempt_id": attempt}
    if runtime == "codex":
        raw = {"type": "item.completed", "item": {"id": "t1", "type": "mcp_tool_call", "server": "morph_research", "tool": tool_name,
                "arguments": {"action": "claim", "task_id": "science-1"},
                "result": {"structured_content": {"result": lease}}}}
    else:
        raw = {"type": "user", "session_id": SESSION, "message": {"content": [
            {"type": "tool_result", "tool_use_id": "t1", "content": [{"type": "text", "text": json.dumps(lease)}]}]}}
    event, = parse_event(runtime, json.dumps(raw))
    assert event.kind == "tool_result" and event.tool_id == "t1"
    assert event.reported_attempt.model_dump() == attempt
    assert event.raw == raw


def test_old_lease_result_does_not_invent_attempt_id() -> None:
    event, = parse_event("codex", '{"type":"item.completed","item":{"id":"t1","type":"mcp_tool_call","result":{"structured_content":{"task_id":"science-1","worker_id":"native-author"}}}}')
    assert event.reported_attempt is None


def test_research_config_workspace_mismatch_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("orchestration.native_agents.launch.resolve_executable", lambda spec: (spec.executable,))
    config = tmp_path / "host.json"
    config.write_text(json.dumps({"workspace": str(tmp_path / "other"), "worker_id": "native-author", "swarm_id": "s",
                                  "agent": {"role": "builder", "instance": 0}}))
    with pytest.raises(ValueError, match="workspace differs"):
        build_launch(LaunchRequest(runtime="codex", workspace=tmp_path, prompt="discover",
                     mcp=McpStdio(command=sys.executable, args=("-m", "swarm.research", "--config", str(config)))))


def test_bootstrap_guides_discovery_without_assignment() -> None:
    prompt = ResearchBootstrap(space="cpu-research", agent=AgentId(role="builder", instance=0),
                               objective="compare methods", tool_names=("discover", "claim", "renew")).prompt()
    assert "choose and claim work yourself" in prompt and "Role: builder" in prompt
    assert "unknown exit, usage and cost remain unknown" in prompt


def test_shell_metacharacters_are_literal_real_subprocess_argv(tmp_path: Path) -> None:
    value = '科学 $HOME `bad` $(bad); & " quote \\ newline\n--print'
    completed = subprocess.run([sys.executable, "-c", "import json,sys;print(json.dumps(sys.argv[1:]))", value],
                               capture_output=True, text=True, encoding="utf-8", shell=False, check=True)
    assert json.loads(completed.stdout) == [value]
    assert list(tmp_path.iterdir()) == []
