import json

from local_assets.research import scientific_plan


def test_scientific_comparison_excludes_role_local_path_and_keeps_full_content():
    original = {"plan_id": "case-v1", "role": "author",
                "code": {"local_path": "/author/code.py", "sha256": "1" * 64, "name": "code.py"},
                "data": {"local_path": "/author/data", "sha256": "2" * 64, "name": "data"},
                "environment": {"image": "python@sha256:" + "3" * 64},
                "criteria": {"version": "v1", "tolerance": 1e-9}, "parameters": ["original"], "seed": 0}
    reproduction = json.loads(json.dumps(original))
    reproduction["role"] = "replication"
    reproduction["code"]["local_path"] = "/peer/code.py"
    reproduction["data"]["local_path"] = "/peer/data"
    assert scientific_plan(json.dumps(original)) == scientific_plan(json.dumps(reproduction))
    for key, changed in (("seed", 1), ("parameters", ["reverse"]),
                         ("criteria", {"version": "v2", "tolerance": 1e-9}),
                         ("code", {"sha256": "4" * 64, "name": "code.py"}),
                         ("environment", {"image": "another-image"})):
        variant = {**reproduction, key: changed}
        assert scientific_plan(json.dumps(original)) != scientific_plan(json.dumps(variant))
