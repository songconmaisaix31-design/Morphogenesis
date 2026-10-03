"""Trusted, bounded Linux diagnostics as DATA; importing never executes probes.

These programs are independent of research candidates. The host compiles/parses
them for offline review, and only an explicitly authorized SDK session runs them.
"""

PAYLOAD = r'''
import ctypes
import errno
import json
import os
from pathlib import Path
import signal
import socket
import struct
import sys
import time

SETTINGS = json.loads(__SETTINGS__)
ROOT = Path("/tmp/morph-research")
CGROUP = Path("/sys/fs/cgroup")

def numbers(name):
    return dict((k, int(v)) for k, v in
                (line.split() for line in (CGROUP / name).read_text().splitlines()))

def limits():
    return {name: (CGROUP / name).read_text().strip() for name in
            ("cpu.max", "memory.max", "memory.swap.max", "pids.max")}

def reap(children):
    for pid in children:
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    for pid in children:
        os.waitpid(pid, 0)

def filesystem():
    access = []
    for path in SETTINGS["canary_paths"]:
        item = {"path": path}
        for mode, label in (("rb", "read"), ("r+b", "write")):
            try:
                with open(path, mode) as f:
                    if label == "write":
                        f.write(b"AT07-UNEXPECTED-WRITE")
                    else:
                        f.read(1)  # Never print contents, even of a fake credential.
                item[label] = "accessible"
            except OSError as error:
                item[label] = error.errno
        access.append(item)
    control = [p for p in ("/var/run/docker.sock", "/run/docker.sock",
                           "/run/containerd/containerd.sock") if Path(p).exists()]
    status = dict(line.split(":", 1) for line in Path("/proc/self/status").read_text().splitlines()
                  if ":" in line)
    try:
        raw = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(3))
        raw.close()
        raw_socket = "allowed"
    except OSError as error:
        raw_socket = error.errno
    libc = ctypes.CDLL(None, use_errno=True)
    unshare = libc.unshare(0x00020000)  # CLONE_NEWNS; no mount or host mutation.
    privilege = {"NoNewPrivs": status.get("NoNewPrivs", "").strip(),
                 "CapEff": status.get("CapEff", "").strip(),
                 "CapBnd": status.get("CapBnd", "").strip(),
                 "raw_socket": raw_socket, "unshare": unshare,
                 "unshare_errno": ctypes.get_errno()}
    ROOT.mkdir(parents=True, exist_ok=True)
    (ROOT / "at07-small.bin").write_bytes(b"AT07-safe-export")
    (ROOT / "at07-large.bin").write_bytes(b"x" * (SETTINGS["artifact_bytes"] + 1))
    outside = Path("/tmp/at07-outside.txt")
    outside.write_bytes(b"AT07-fake-outside-export")
    (ROOT / "at07-link.bin").symlink_to(outside)
    return {"access": access, "control_sockets": control,
            "fake_credential_visible": "AT07_FAKE_CREDENTIAL" in os.environ,
            "privilege": privilege, "limits": limits()}

def network():
    target = SETTINGS["target_ipv4"]
    tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp.settimeout(2)
    try:
        tcp.connect((target, 9000))
        tcp.sendall(b"AT07-DENIED-TCP\n")
        direct = "connected"
    except OSError as error:
        direct = "timeout" if isinstance(error, TimeoutError) else error.errno
    finally:
        tcp.close()
    # Controlled fixture answers this exact .test name positively. The sandbox
    # must receive the egress proxy's NXDOMAIN, never an unavailable-origin pass.
    qname = b"".join(bytes([len(p)]) + p.encode("ascii") for p in
                     "canary.at07.test".split(".")) + b"\0"
    query = struct.pack("!HHHHHH", 1707, 0x0100, 1, 0, 0, 0) + qname + struct.pack("!HH", 1, 1)
    dns = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    dns.settimeout(2)
    try:
        dns.sendto(query, (target, 53))
        answer, _ = dns.recvfrom(512)
        domain = {"id": struct.unpack("!H", answer[:2])[0], "rcode": answer[3] & 15,
                  "answers": struct.unpack("!H", answer[6:8])[0]}
    except OSError as error:
        domain = {"error": type(error).__name__}
    finally:
        dns.close()
    disabled = {n: Path("/proc/sys/net/ipv6/conf/" + n + "/disable_ipv6").read_text().strip()
                for n in ("all", "default", "lo")}
    ipv6 = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    try:
        ipv6.bind(("::1", 0))
        ipv6_bind = "allowed"
    except OSError as error:
        ipv6_bind = error.errno
    finally:
        ipv6.close()
    return {"direct_ipv4": direct, "domain": domain, "ipv6_disabled": disabled,
            "ipv6_bind": ipv6_bind}

def cpu():
    before = numbers("cpu.stat")
    children = []
    started = time.monotonic()
    try:
        for _ in range(2):
            pid = os.fork()
            if pid == 0:
                until = time.monotonic() + 4
                while time.monotonic() < until:
                    sum(range(1000))
                os._exit(0)
            children.append(pid)
        for pid in children:
            os.waitpid(pid, 0)
        children.clear()
    finally:
        reap(children)
    return {"limits": limits(), "before": before, "after": numbers("cpu.stat"),
            "elapsed": time.monotonic() - started, "workers": 2}

def memory():
    before = numbers("memory.events")
    pid = os.fork()
    if pid == 0:
        Path("/proc/self/oom_score_adj").write_text("1000")
        signal.alarm(8)
        blocks = []
        # Finite allocation even if isolation is broken: at most 576 MiB.
        for _ in range((SETTINGS["memory_mib"] + 64) // 8):
            blocks.append(bytearray(b"x") * (8 * 1024 * 1024))
        os._exit(0)
    _, status = os.waitpid(pid, 0)
    return {"limits": limits(), "before": before, "after": numbers("memory.events"),
            "child_status": status, "allocation_ceiling_mib": SETTINGS["memory_mib"] + 64}

def pids():
    before = numbers("pids.events")
    children = []
    failure = None
    try:
        # No unbounded fork bomb; only these exact child PIDs are signalled.
        for _ in range(SETTINGS["process_limit"] + 1):
            try:
                pid = os.fork()
            except OSError as error:
                failure = error.errno
                break
            if pid == 0:
                time.sleep(8)
                os._exit(0)
            children.append(pid)
        after = numbers("pids.events")
        count = len(children)
    finally:
        reap(children)
    return {"limits": limits(), "before": before, "after": after,
            "fork_errno": failure, "children": count}

def timeout():
    # SDK command timeout must terminate this before the completion marker.
    time.sleep(SETTINGS["command_seconds"] + 5)
    (ROOT / "at07-timeout-completed").write_text("unexpected")

if __name__ == "__main__":
    if sys.platform != "linux" or not Path("/.dockerenv").exists():
        raise SystemExit("AT07 requires its explicitly authorized Linux container")
    step = sys.argv[1]
    functions = {"filesystem": filesystem, "network": network, "cpu": cpu,
                 "memory": memory, "pids": pids, "timeout": timeout}
    if step not in functions:
        raise SystemExit("unknown fixed probe")
    if step in {"cpu", "memory", "pids"}:
        effective = limits()
        if effective["pids.max"] != "128" or effective["memory.max"] != "536870912":
            raise SystemExit("resource settings differ; bounded stress refused")
        quota, period = map(int, effective["cpu.max"].split())
        if quota != period:
            raise SystemExit("CPU setting differs; bounded stress refused")
    print(json.dumps(functions[step](), sort_keys=True))
'''
