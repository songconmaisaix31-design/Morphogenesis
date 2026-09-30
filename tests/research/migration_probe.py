"""Read actual ef77 assets/reports/approval with current B code, without migration."""
from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys
import tempfile


BASELINE_RUNNER = '''
from pathlib import Path
import sys,json
sys.path.insert(0,sys.argv[1])
from contracts.identity import AgentId,AttemptId
from local_assets import LocalAssetStore,Candidate,FileChange,FileExpectation,ValidationPolicy,AssetValidator,AssetPromoter
from local_assets.paths import git
from local_assets.consume import AssetConsumer
from local_assets.models import ConsumptionContext
from local_assets.apply import AssetApplicator
from swarm.models import Signal,Locality
from swarm.task_ledger import TaskLedger
root=Path(sys.argv[2]);target=root/'target';target.mkdir()
git(target,'init','-b','legacy-contract')
(target/'example.py').write_bytes(b'answer = 1\\n')
git(target,'add','example.py')
git(target,'-c','user.name=Legacy Test','-c','user.email=legacy@example.invalid','commit','-m','fixture')
candidate=Candidate(attempt=AttemptId(task_id='legacy',agent=AgentId(role='builder',instance=0),attempt=1),
 base_revision=git(target,'rev-parse','HEAD').decode().strip(),changes=(FileChange(path='example.py',before='answer = 1\\n',after='answer = 2\\n'),),declared_files=1,declared_lines=2)
store=LocalAssetStore(root/'assets')
# Same unchanged official Node helper and installed SDK; no mock/hash fallback.
store.bridge._script=Path(sys.argv[3])
asset_id=store.publish(candidate)
policy=ValidationPolicy(version='legacy-files-v1',expectations=(FileExpectation(path='example.py',content='answer = 2\\n'),))
report=AssetValidator(store,target,policy=policy).validate(asset_id)
assert report.passed,report.reasons
receipt=AssetPromoter(store,policy_version=policy.version).promote(asset_id,report.report_id)
ledger=TaskLedger(root/'tasks.sqlite3','legacy')
ledger.enqueue(Signal(task_id='next',workspace=str(target),scope='.',kind='opportunity'))
lease=ledger.claim('next','consumer',locality=Locality(workspace=str(target),authorized_scopes=('.',)))
consumer=AssetConsumer(store)
context=ConsumptionContext(swarm_id='legacy',task_id='next',worker_id='consumer',fencing_token=lease.token,execution_id='old-adoption',scope='.',input_context='actual legacy reuse')
injected=consumer.inject(asset_id,context)
execution=consumer.execute(injected,attempt=AttemptId(task_id='next',agent=AgentId(role='builder',instance=1),attempt=1),base_revision=candidate.base_revision,path_map={'example.py':'example.py'},preimages={'example.py':'answer = 1\\n'})
child_report=AssetValidator(store,target,policy=policy).validate(execution.candidate_asset_id)
assert child_report.passed,child_report.reasons
AssetPromoter(store,policy_version=policy.version).promote(execution.candidate_asset_id,child_report.report_id)
prepared=AssetApplicator(store,target,policy_version=policy.version).prepare(execution.candidate_asset_id,child_report.report_id)
result={'execution_id':'old-adoption','input_context':context.input_context,'candidate_asset_id':execution.candidate_asset_id,'applied':True,'consumed_asset_ids':[asset_id]}
def apply(owned): prepared.apply(owned)
ledger.submit(lease,'old-result',result,apply=apply)
adoption=consumer.record_adoption('old-adoption','old-result',ledger)
(root/'legacy.json').write_text(json.dumps({'asset_id':asset_id,'candidate_json':candidate.model_dump_json(),'report_id':report.report_id,'receipt':receipt.model_dump(mode='json'),'adoption':adoption.model_dump(mode='json')}),encoding='utf-8')
'''


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline-source", type=Path, required=True)
    args = parser.parse_args()
    b_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(b_root))
    from local_assets import LocalAssetStore, AssetPromoter
    from local_assets.promote import checked_report
    from local_assets.consume import AssetConsumer
    from local_assets.models import ConsumptionContext
    from swarm.task_ledger import TaskLedger
    import json
    helper = b_root / "bridge_node/asset_bridge.mjs"
    assert helper.read_bytes().replace(b"\r\n", b"\n") == (args.baseline_source / "bridge_node/asset_bridge.mjs").read_bytes()
    with tempfile.TemporaryDirectory(prefix="morph-B-ef77-migration-") as temporary:
        root = Path(temporary)
        runner = root / "legacy_runner.py"
        runner.write_text(BASELINE_RUNNER, encoding="utf-8")
        subprocess.run([sys.executable, str(runner), str(args.baseline_source), str(root), str(helper)],
                       check=True, timeout=90)
        old = json.loads((root / "legacy.json").read_bytes())
        assert '"research"' not in old["candidate_json"]
        store = LocalAssetStore(root / "assets")
        candidate, report = checked_report(store, old["asset_id"], old["report_id"], "legacy-files-v1")
        assert candidate.model_dump_json() == old["candidate_json"]
        assert store.publish(candidate) == old["asset_id"]
        assert store.fetch_approved(old["asset_id"]) == candidate
        assert AssetPromoter(store, policy_version="legacy-files-v1").promote(old["asset_id"], old["report_id"]).model_dump(mode="json") == old["receipt"]
        injected = AssetConsumer(store).inject(old["asset_id"], ConsumptionContext(
            swarm_id="legacy", task_id="next", worker_id="consumer", fencing_token=1,
            execution_id="read-existing", scope=".", input_context="legacy-compatible"))
        assert injected.candidate == candidate and report.passed
        adoption = AssetConsumer(store).record_adoption("old-adoption", "old-result", TaskLedger(root / "tasks.sqlite3", "legacy"))
        assert adoption.model_dump(mode="json") == old["adoption"]
        print("contract_local=passed; actual ef77 candidate JSON/address/report/approval/consumption/adoption remains unchanged; no scientific/live claim")


if __name__ == "__main__":
    main()
