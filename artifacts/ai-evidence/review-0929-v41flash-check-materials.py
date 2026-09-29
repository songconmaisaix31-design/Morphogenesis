"""Verify allowed material paths, preserved evidence, input and absent-response status."""
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
BASE = "403909204c8b589d33943298e1cde0a2094bb15e"
SHA = "c552250c0d07f5f70f09eb0a5ab3c322195e34ec"
PREFIX = "artifacts/ai-evidence/review-0929-v41flash-"
APPEND = ["TASKS.md", "docs/FC_HUMAN_REVIEW_0929.md", "docs/FC_REMEDIATION_0929.md",
          "artifacts/ai-evidence/fc-remediation-governance-0929-report.md"]


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=True).stdout


def main():
    changed = set(git("diff", "--name-only", BASE).decode().splitlines())
    changed.update(git("ls-files", "--others", "--exclude-standard").decode().splitlines())
    assert changed
    assert all(path in APPEND or path == "docs/FC_RELEASE_PLAN_0929.md" or path.startswith(PREFIX) for path in changed), changed
    prefixes = []
    for path in APPEND:
        old = git("show", f"{BASE}:{path}")
        current = (ROOT / path).read_bytes()
        # Git has canonical LF while Windows checkouts may have CRLF. No other
        # normalization is permitted. Entire old material includes signature slots.
        assert current.replace(b"\r\n", b"\n").startswith(old.replace(b"\r\n", b"\n")), path
        prefixes.append({"path": path, "old_git_blob_bytes": len(old), "result": "PASS", "comparison": "full prefix; only Git checkout CRLF/LF normalized"})
    legacy = git("ls-files", "artifacts/ai-evidence/review-0929-formal-v2-*").decode().splitlines()
    assert len(legacy) == 11
    for path in legacy:
        assert git("diff", BASE, "--", path) == b"", path
    packet = json.loads((OUT / "review-0929-v41flash-input.json").read_text(encoding="utf-8"))
    check = json.loads((OUT / "review-0929-v41flash-input-check.json").read_text(encoding="utf-8"))
    assert packet["candidate"] == SHA and len(packet["content"].encode()) == check["bytes"]
    assert check["reused_v2_data_body_exact"] and len(check["inherited_numbered_excerpts"]) == 22
    old_packet = json.loads((OUT / "review-0929-formal-v2-input.json").read_text(encoding="utf-8-sig"))
    old_body = old_packet["content"][old_packet["content"].index("## Original FC changed paths"):]
    assert packet["content"].count(old_body) == 1
    for item in check["diff_checks"]:
        diff = git("diff", "--no-ext-diff", "--no-color", item["from"], item["to"], "--", "swarm/", "orchestration/").decode()
        assert packet["content"].count(diff) == 1
    preflight = json.loads((OUT / "review-0929-v41flash-preflight.json").read_text(encoding="utf-8-sig"))
    assert preflight["resolved_catalog"]["model"] == "deepseek-flash"
    assert all(not item["present"] for item in preflight["credential_environment_presence"])
    assert all(not item["exists"] for item in preflight["native_config_file_presence"])
    assert preflight["request_count"] == 0 and preflight["submitted"] is False
    assert all(preflight[key] is None for key in ("returned_model", "usage", "cost", "review_exit_code"))
    assert preflight["invocation_policy"]["max_wall_time_ms"] == 600000
    assert preflight["invocation_policy"]["automatic_retry"] is False
    result = json.loads((OUT / "review-0929-v41flash-verification.json").read_text(encoding="utf-8"))
    assert result["exit_code"] == 2 and result["status"] == "NOT_RUN_NO_RESPONSE"
    assert len(result["missing_dimensions"]) == 37 and result["results"] == []
    control = json.loads((OUT / "review-0929-v41flash-legacy-control.json").read_text(encoding="utf-8"))
    assert control["exit_code"] == 1
    assert [x["verification"] for x in control["results"]] == ["PASS", "PASS", "INVALID", "INVALID", "NOT_RUN", "NOT_RUN", "NOT_RUN", "NOT_RUN"]
    assert not (OUT / "review-0929-v41flash-raw.txt").exists()
    links = []
    for relative in sorted(changed):
        if not relative.endswith(".md"):
            continue
        path = ROOT / relative
        text = path.read_text(encoding="utf-8-sig")
        if relative in APPEND:
            old = git("show", f"{BASE}:{relative}").decode()
            text = text[len(old):]
        for target in re.findall(r"\]\(([^)]+)\)", text):
            if "://" in target or target.startswith("#"):
                continue
            candidate = (path.parent / target.split("#", 1)[0]).resolve()
            # This check's own output is written below.
            assert candidate.exists() or candidate == OUT / "review-0929-v41flash-final-check.json", target
            links.append({"from": relative, "target": target})
    desktop = Path("C:/Users/DW/Desktop/Morphogenesis_今日开发与验收_2026-09-29.md")
    desktop_before = ROOT / ".runtime/fc-v41flash/desktop-before.bin"
    assert desktop.read_bytes().startswith(desktop_before.read_bytes())
    source = ROOT.parent / "morph-fc-candidate-0929"
    assert git("-C", str(source), "rev-parse", "HEAD").decode().strip() == SHA
    assert git("-C", str(source), "status", "--porcelain") == b""
    git("diff", "--check")
    payload = {"base": BASE, "candidate": SHA, "status": "PASS_MATERIALS_ONLY", "exit_code": 0,
               "changed_paths": sorted(changed), "old_document_prefixes": prefixes,
               "unchanged_old_v2_files": legacy, "human_slots": "unchanged in preserved entire old human-review document",
               "input_bytes": check["bytes"], "required_coverage": 37,
               "new_review": "NOT_RUN_NO_RESPONSE; exit 2", "legacy_control": "2 PASS / 2 INVALID; exit 1",
               "request_count": 0, "usage": None, "cost": None,
               "desktop_previous_bytes_preserved": len(desktop_before.read_bytes()),
               "source_candidate_clean": True, "source_tests_six_gates_and_D_rerun": False,
               "local_links_checked": len(links), "links": links,
               "meaning": "material correctness only; FC-E OPEN, H1/H3 unsigned, FC BLOCKED"}
    (OUT / "review-0929-v41flash-final-check.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": payload["status"], "exit_code": 0, "paths": len(changed), "links": len(links)}))


if __name__ == "__main__":
    main()
