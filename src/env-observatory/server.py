"""FastAPI read-only HTTP service for the environment observatory.

Serves the static frontend in this directory plus a small read-only research
JSON API backed by ``swarm/research/service.py``. It never calls propose/claim/
accept/execute/apply — only the read methods (research_package / snapshot /
advisory / context); the single write-shaped entry is the Wayfinder ``POST``
which shells out to the local pi agent (Wayfinder extension).

Start with ``python src/env-observatory/server.py --port 8099`` after running
``seed.py``; point ``OBSERVATORY_HOST_CONFIG`` at the generated host-config.json.
If the HostConfig is missing, the server still starts and the API returns 503
with a clear message instead of crashing.

Read-only safety contract (unchanged from the stdlib predecessor):
- non GET/HEAD (except ``POST /api/wayfinder/ask``) → 405
- GET/HEAD carrying a request body → 413
- every response: nosniff / X-Frame-Options DENY / no-referrer
- no HostConfig → /api/research/* returns 503, static still served
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, PlainTextResponse, Response
from starlette.datastructures import MutableHeaders

from swarm.research.models import HostConfig
from swarm.research.service import build_service

WAYFINDER_TIMEOUT = 180
MAX_QUESTION_CHARS = 2000
MAX_WAYFINDER_BODY = 8192

STATIC_DIR = Path(__file__).resolve().parent
ALLOWED_STATIC = {
    "env-observatory.html", "index.html", "app.js", "data.js", "bg.js",
    "physarum-landing.html",
}
CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript",
}
DEFAULT_PORT = 8099


def load_service() -> tuple[object | None, str | None]:
    path = os.environ.get("OBSERVATORY_HOST_CONFIG")
    if not path:
        return None, "OBSERVATORY_HOST_CONFIG 未设置，请先运行 seed.py 生成 .state/host-config.json"
    config_file = Path(path)
    if not config_file.is_file():
        return None, f"HostConfig 文件不存在：{config_file}（请先运行 seed.py）"
    try:
        config = HostConfig.model_validate_json(config_file.read_text(encoding="utf-8"))
        return build_service(config), None
    except Exception as error:  # noqa: BLE001 - surface the failure on the API, keep serving
        return None, f"HostConfig 加载失败：{type(error).__name__}: {error}"


def _pi_env(env: dict) -> dict:
    """Strip the injected Node shim before spawning pi.

    The desktop session exports NODE_OPTIONS=--require="D:/workbuddy cn/.../genie-
    safe-delete.cjs" --use-system-ca, which patches fs.rmdir. pi removes
    ~/.pi/agent/trust.json.lock on exit, hits the patched call and dies with an
    uncaught error before printing anything --- the Wayfinder POST then sees empty
    stdout (502 wayfinder_empty). Keep --use-system-ca (TLS trust) and drop only
    the --require hook for the child.

    The value is tokenised with shlex, not str.split: the shim path contains a
    space and is quoted, so naive splitting leaves an unterminated quote behind
    and node rejects the whole variable ("invalid value for NODE_OPTIONS").
    """
    options = env.get("NODE_OPTIONS")
    if options:
        try:
            parts = shlex.split(options)
        except ValueError:
            parts = options.split()
        kept = [p for p in parts if not p.startswith("--require")]
        if kept:
            env["NODE_OPTIONS"] = shlex.join(kept)
        else:
            env.pop("NODE_OPTIONS", None)
    return env


def _dashscope_key() -> str | None:
    """DashScope key for the Wayfinder agent: env first, bl config fallback."""
    env_key = os.environ.get("DASHSCOPE_API_KEY")
    if env_key:
        return env_key
    bl_config = Path.home() / ".bailian" / "config.json"
    if bl_config.is_file():
        try:
            data = json.loads(bl_config.read_text(encoding="utf-8"))
            if isinstance(data, dict) and data.get("api_key"):
                return str(data["api_key"])
        except (OSError, ValueError):
            pass
    return None


def run_wayfinder_ask(question: str, host_config: str | None) -> tuple[int, dict]:
    """Invoke the real pi-agent (Wayfinder) once and return its answer.

    pi is an npm global shim (pi.cmd/pi.ps1) on Windows, so it is run through the
    shell with the question embedded as a single quoted argument. The agent loads
    the project ``.pi/extensions/`` (Wayfinder) and the read-only swarm.research
    MCP; the answer is whatever pi prints on stdout.
    """
    key = _dashscope_key()
    if not key:
        return 503, {"error": "no_dashscope_key",
                     "detail": "未配置 DASHSCOPE_API_KEY 或 ~/.bailian/config.json"}
    env = _pi_env(dict(os.environ))
    env["DASHSCOPE_API_KEY"] = key
    if host_config:
        env["WAYFINDER_HOST_CONFIG"] = host_config
    quoted = question.replace("\\", "\\\\").replace('"', '\\"')
    command = 'pi -p "' + quoted + '"'
    try:
        proc = subprocess.run(command, shell=True, cwd=str(ROOT), env=env,
                              capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=WAYFINDER_TIMEOUT)
    except subprocess.TimeoutExpired:
        return 504, {"error": "wayfinder_timeout", "detail": f"pi 超过 {WAYFINDER_TIMEOUT}s 未返回"}
    except FileNotFoundError:
        return 503, {"error": "pi_not_installed",
                     "detail": "pi 未安装（npm i -g @earendil-works/pi-coding-agent）"}
    answer = (proc.stdout or "").strip()
    if not answer:
        detail = (proc.stderr or "").strip()[-500:] or f"pi 退出码 {proc.returncode}"
        return 502, {"error": "wayfinder_empty", "detail": detail}
    return 200, {"answer": answer}


# ---------------------------------------------------------------------------
# Read-only ASGI middleware: method policy (405), body policy (413) and the
# security headers (nosniff / DENY / no-referrer) on every response.
# ---------------------------------------------------------------------------

class ReadOnlyAndSecurityMiddleware:
    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        method = scope.get("method", "GET").upper()
        path = scope.get("path", "")
        if method not in {"GET", "HEAD", "POST"} or (
                method == "POST" and path != "/api/wayfinder/ask"):
            await PlainTextResponse("Read-only endpoint", status_code=405)(
                scope, receive, send)
            return
        if method in {"GET", "HEAD"}:
            headers = {k.decode("latin-1").lower(): v.decode("latin-1")
                       for k, v in scope.get("headers", [])}
            if "transfer-encoding" in headers or headers.get("content-length") not in (None, "0"):
                await PlainTextResponse("Request bodies are not accepted", status_code=413)(
                    scope, receive, send)
                return

        head = method == "HEAD"
        # Starlette does not register HEAD alongside GET here, so a HEAD request is
        # routed as GET internally and only its body payload is stripped.
        routed_scope = dict(scope, method="GET") if head else scope

        async def send_wrapper(message: Any) -> None:
            if message["type"] == "http.response.start":
                mutable = MutableHeaders(scope=message)
                mutable.append("X-Content-Type-Options", "nosniff")
                mutable.append("X-Frame-Options", "DENY")
                mutable.append("Referrer-Policy", "no-referrer")
                await send(message)
            elif head and message["type"] == "http.response.body":
                await send({"type": "http.response.body", "body": b"",
                            "more_body": message.get("more_body", False)})
            else:
                await send(message)

        await self.app(routed_scope, receive, send_wrapper)


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

def create_app(service: object | None = None, *, service_error: str | None = None,
               host_config: str | None = None) -> FastAPI:
    """Build the observatory app. ``service`` may be None (503 degradation)."""
    app = FastAPI(title="env-observatory", docs_url=None, redoc_url=None,
                  openapi_url=None)
    app.add_middleware(ReadOnlyAndSecurityMiddleware)

    def json_response(payload: object, status: int = 200) -> Response:
        body = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")
        return Response(content=body, status_code=status,
                        media_type="application/json; charset=utf-8",
                        headers={"Cache-Control": "no-store"})

    def unavailable() -> Response:
        return json_response({"error": "observatory_service_unavailable",
                              "detail": service_error or "research service not configured"}, 503)

    def resolve_project_id(raw: str | None) -> str:
        if raw:
            return raw
        if service is not None and getattr(service, "config", None) is not None:
            bound = getattr(service.config, "project_id", "")
            if bound:
                return bound
        return "p1"

    # ---- read-only research API -----------------------------------------

    def _read(call: Any) -> Response:
        if service is None:
            return unavailable()
        try:
            return json_response(call())
        except (KeyError, PermissionError) as error:
            return json_response({"error": "not_found_or_forbidden", "detail": str(error)}, 404)
        except ValueError as error:
            return json_response({"error": "invalid_request", "detail": str(error)}, 400)
        except Exception as error:  # noqa: BLE001 - never let a read fault crash the worker
            return json_response({"error": type(error).__name__, "detail": str(error)}, 503)

    @app.get("/api/research/package")
    def api_package(project_id: str | None = None) -> Response:
        return _read(lambda: service.research_package(resolve_project_id(project_id)))

    @app.get("/api/research/snapshot")
    def api_snapshot(project_id: str | None = None) -> Response:
        return _read(lambda: service.research_snapshot(resolve_project_id(project_id)))

    @app.get("/api/research/advisory")
    def api_advisory(project_id: str | None = None) -> Response:
        return _read(lambda: service.research_advisory(resolve_project_id(project_id)))

    @app.get("/api/research/context")
    def api_context(project_id: str | None = None) -> Response:
        return _read(lambda: service.research_context(resolve_project_id(project_id), overview=True))

    @app.get("/api/research/replay/{task_id}")
    def api_replay(task_id: str, project_id: str | None = None) -> Response:
        if not task_id or "/" in task_id:
            return json_response({"error": "invalid_task_id"}, 400)
        return _read(lambda: _replay_slice(service.research_package(resolve_project_id(project_id)), task_id))

    @app.get("/api/research/activity")
    def api_activity(since_seq: int = 0, project_id: str | None = None) -> Response:
        """task_audit increment since ``since_seq`` (drives subscribeActivity polling)."""
        if since_seq < 0:
            return json_response({"error": "invalid_since_seq"}, 400)

        def call() -> dict[str, Any]:
            package = service.research_package(resolve_project_id(project_id))
            audit = package.get("task_audit") or []
            events = sorted((e for e in audit if e.get("sequence", 0) > since_seq),
                            key=lambda e: e.get("sequence", 0))
            latest = max((e.get("sequence", 0) for e in audit), default=since_seq)
            return {"events": events, "latest_seq": latest}

        return _read(call)

    # ---- Wayfinder: the single POST entry (pi Wayfinder) ----------------

    @app.post("/api/wayfinder/ask")
    async def api_wayfinder_ask(request: Request) -> Response:
        length = request.headers.get("Content-Length")
        if length is None or not length.isdigit() or int(length) > MAX_WAYFINDER_BODY:
            return json_response({"error": "invalid_body"}, 413)
        try:
            payload = json.loads((await request.body()).decode("utf-8"))
        except (OSError, ValueError):
            return json_response({"error": "invalid_json"}, 400)
        if not isinstance(payload, dict):
            return json_response({"error": "invalid_json"}, 400)
        question = payload.get("question", "")
        if not isinstance(question, str) or not question.strip():
            return json_response({"error": "missing_question"}, 400)
        if len(question) > MAX_QUESTION_CHARS:
            return json_response({"error": "question_too_long"}, 400)
        status, result = await asyncio.to_thread(run_wayfinder_ask, question.strip(), host_config)
        return json_response(result, status)

    # ---- static frontend --------------------------------------------------

    @app.get("/", include_in_schema=False)
    def static_root() -> Response:
        return _static_file("env-observatory.html")

    @app.get("/{name}", include_in_schema=False)
    def static_named(name: str) -> Response:
        return _static_file(name)

    def _static_file(name: str) -> Response:
        if name not in ALLOWED_STATIC:
            return PlainTextResponse("Not found", status_code=404)
        path = (STATIC_DIR / name).resolve()
        if not path.is_relative_to(STATIC_DIR.resolve()) or not path.is_file():
            return PlainTextResponse("Not found", status_code=404)
        return FileResponse(path, media_type=CONTENT_TYPES.get(path.suffix, "application/octet-stream"),
                            headers={"Cache-Control": "no-store"})

    return app


def _replay_slice(package: dict, task_id: str) -> dict:
    """Slice a research package by task_id, mirroring the frontend §10 semantics."""
    tasks = package.get("tasks") or []
    task = next((t for t in tasks if (t.get("signal") or {}).get("task_id") == task_id), None)
    audit = sorted((e for e in (package.get("task_audit") or []) if e.get("task_id") == task_id),
                   key=lambda e: e.get("sequence", 0))
    executions = [e for e in (package.get("executions") or []) if e.get("task_id") == task_id]
    observations = [n for n in ((package.get("context") or {}).get("notes") or [])
                    if n.get("task_id") == task_id]
    receipts = [r for r in (package.get("adoption_receipts") or [])
                if r.get("adopting_task_id") == task_id
                or (r.get("context") or {}).get("task_id") == task_id]
    return {"task_id": task_id, "task": task, "audit": audit, "executions": executions,
            "observations": observations, "adoption_receipts": receipts}


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve the Morphogenesis environment observatory (read-only).")
    parser.add_argument("--host", default=os.environ.get("OBSERVATORY_HOST", "127.0.0.1"),
                        help="Listen address; defaults to OBSERVATORY_HOST or loopback")
    parser.add_argument("--port", type=int, default=int(os.environ.get("OBSERVATORY_PORT", DEFAULT_PORT)))
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("port must be between 1 and 65535")

    service, service_error = load_service()
    if service_error:
        print(f"[warn] {service_error} —— /api/research/* 将返回 503")

    app = create_app(service, service_error=service_error,
                     host_config=os.environ.get("OBSERVATORY_HOST_CONFIG"))

    import uvicorn
    print(f"环境观测台只读服务: http://{args.host}:{args.port}")
    uvicorn.run(app, host=args.host, port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
