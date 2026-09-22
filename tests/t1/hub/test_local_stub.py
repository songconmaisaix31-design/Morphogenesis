"""Real loopback HTTP transport, deliberately mock assets and mock Hub behavior."""

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from threading import Thread

from hub_client import HubClient, HubConfig, PublicationRecord, PublishApproval


def test_hello_publish_fetch_loopback(publication: Path, record: PublicationRecord) -> None:
    requests: list[dict[str, object]] = []
    stored_assets: list[object] = []

    class Stub(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: object) -> None:
            pass

        def do_POST(self) -> None:
            nonlocal stored_assets
            message = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            requests.append(message)
            if self.path == "/a2a/hello":
                body = {"status": "acknowledged", "your_node_id": message["sender_id"], "node_secret": "loopback-fixture-secret"}
            elif self.headers.get("Authorization") != "Bearer loopback-fixture-secret":
                self.send_error(401)
                return
            elif self.path == "/a2a/publish":
                stored_assets = message["payload"]["assets"]
                body = {"status": "candidate"}
            elif self.path == "/a2a/fetch":
                body = {"assets": stored_assets}
            else:
                self.send_error(404)
                return
            encoded = json.dumps({"payload": body}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

    server = HTTPServer(("127.0.0.1", 0), Stub)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    origin = f"http://127.0.0.1:{server.server_port}"
    client = HubClient(HubConfig(base_url=origin))
    try:
        assert client.hello(env_fingerprint={"runtime": "contract-fixture"}).state == "acknowledged"
        approval = PublishApproval(
            approved_by="local-contract-test", payload_json=record.payload_json,
            provenance=record.provenance, sender_id=client.config.sender_id, hub_url=origin,
        )
        published = client.publish(publication, approval=approval)
        fetched = client.fetch(signals=["fixture_error"])
        assert published.state == "candidate"
        assert fetched.state == "discovered"
        assert fetched.assets == json.loads(record.payload_json)["assets"]
        assert fetched.acceptance.provenance == "mock"
        assert fetched.acceptance.interface_live == fetched.acceptance.task_live == "not_run"
        assert [m["message_type"] for m in requests] == ["hello", "publish", "fetch"]
    finally:
        client.close()
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
