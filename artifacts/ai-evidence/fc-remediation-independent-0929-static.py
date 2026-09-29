"""Read-only comparison of existing test ASTs and the retained B failure log."""
import ast
import collections
import json
from pathlib import Path
import re
import subprocess
import sys

BASE = "3a34ecafe5f48b1a5a7c94c9e063797427817cab"


def git(*args):
    return subprocess.check_output(["git", *args])


def functions(blob):
    result = {}
    def walk(node, prefix=""):
        for item in getattr(node, "body", []):
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                name = prefix + item.name
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name.startswith("test_"):
                    result[name] = item
                walk(item, name + ".")
    walk(ast.parse(blob))
    return result


def assertions(node):
    return [ast.dump(item, include_attributes=False) for item in ast.walk(node) if isinstance(item, ast.Assert)]


def inspect(ref):
    files = git("ls-tree", "-r", "--name-only", BASE, "tests").decode().splitlines()
    changed, absent, assertion_changes, decorator_changes = [], [], [], []
    count = total_assertions = 0
    for path in files:
        if not path.endswith(".py"):
            continue
        before = git("show", BASE + ":" + path)
        after = git("show", ref + ":" + path)
        old, new = functions(before), functions(after)
        count += len(old)
        total_assertions += sum(len(assertions(node)) for node in old.values())
        for name, node in old.items():
            if name not in new:
                absent.append(path + ":" + name)
                continue
            replacement = new[name]
            if ast.dump(node) != ast.dump(replacement):
                changed.append(path + ":" + name)
            if assertions(node) != assertions(replacement):
                assertion_changes.append(path + ":" + name)
            if [ast.dump(x) for x in node.decorator_list] != [ast.dump(x) for x in replacement.decorator_list]:
                decorator_changes.append(path + ":" + name)
    return dict(ref=ref, original_test_functions=count, original_assertions=total_assertions,
                missing=absent, changed_functions=changed, assertion_changes=assertion_changes,
                decorator_changes=decorator_changes,
                changed_test_paths=git("diff", "--name-only", BASE, ref, "tests").decode().splitlines())


if __name__ == "__main__":
    results = [inspect(ref) for ref in sys.argv[1:]]
    log = Path("../morph-fc-breaker-fix-0929/.runtime/full.log").read_text(encoding="utf-8-sig")
    failures = [line for line in log.splitlines() if line.startswith(("FAILED ", "ERROR tests/"))]
    blocks = re.split(r"(?m)^_+ .* _+\s*$", log)
    tracebacks = [block for block in blocks if re.search(r"(?m)^E\s+", block)]
    results.append(dict(b_full_summary=log.splitlines()[-1], terminal_cases=len(failures),
        by_file=dict(collections.Counter(line.split("::")[0] for line in failures)),
        traceback_blocks=len(tracebacks),
        temp_guard_blocks=sum("requires a dedicated directory under the OS temp root" in b or
                              "requires a new private root under OS TEMP" in b for b in tracebacks),
        terminal_exception_lines=[line for line in log.splitlines()
                                  if re.match(r"^E\s+(?:\w*Error|\w*Exception):", line)]))
    print(json.dumps(results, indent=2))
    assert all(not row[key] for row in results[:-1]
               for key in ("missing", "assertion_changes", "decorator_changes"))
