"""Controlled, content-free TCP/DNS fixture. Run ONLY in its owned container."""

import json
import os
from pathlib import Path
import selectors
import socket
import struct
import time


def main() -> None:
    if not Path("/.dockerenv").exists() or os.environ.get("AT07_FAKE_CREDENTIAL") != "AT07-SYNTHETIC-NOT-A-SECRET":
        raise SystemExit("owned AT07 target container required")
    tcp = socket.socket()
    tcp.bind(("0.0.0.0", 9000))
    tcp.listen(4)
    dns = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    dns.bind(("0.0.0.0", 9053))
    selector = selectors.DefaultSelector()
    selector.register(tcp, selectors.EVENT_READ)
    selector.register(dns, selectors.EVENT_READ)
    counts = {"denied_tcp_hits": 0, "dns_queries": 0}
    deadline = time.monotonic() + 600
    try:
        while time.monotonic() < deadline:
            for key, _ in selector.select(timeout=1):
                if key.fileobj is tcp:
                    client, _ = tcp.accept()
                    with client:
                        client.settimeout(1)
                        request = client.recv(64)
                        if request.startswith(b"AT07-DENIED"):
                            counts["denied_tcp_hits"] += 1
                        body = {**counts, "canary_exists": Path("/at07-host-canary/credentials").is_file(),
                                "fake_credential_present": "AT07_FAKE_CREDENTIAL" in os.environ}
                        client.sendall(json.dumps(body).encode() + b"\n")
                else:
                    query, address = dns.recvfrom(512)
                    # One fixed name/type only; never forward DNS to an upstream.
                    question = b"\x06canary\x04at07\x04test\0\0\x01\0\x01"
                    if len(query) != 12 + len(question) or query[12:] != question:
                        continue
                    counts["dns_queries"] += 1
                    answer = (query[:2] + struct.pack("!HHHHH", 0x8180, 1, 1, 0, 0) + question
                              + b"\xc0\x0c" + struct.pack("!HHIH", 1, 1, 1, 4) + socket.inet_aton("127.0.0.1"))
                    dns.sendto(answer, address)
    finally:
        selector.close()
        tcp.close()
        dns.close()


if __name__ == "__main__":
    main()
