"""Audit real adapter receipts from MockTransport; no live requests or credentials."""
import json
from pathlib import Path

import httpx
import pytest

from contracts.resolution import Gene, GeneRef
from orchestration.gateway import EVOMAP_MODEL, GatewayExecutor
from tests.integration.audit_rehearsal import gateway_receipt
from tests.t2.test_gateway import KEY, completion, prepared


@pytest.fixture
def receipt(tmp_path: Path):
    config, attempt = prepared(tmp_path)
    gene = Gene(ref=GeneRef(gene_id='first-task'), signals_match=['python'],
                strategy=['Use verified boundary handling'], provenance='mock')
    body = completion(adopted=[gene.ref.gene_id])
    result = GatewayExecutor(tmp_path/'gateway', api_key=KEY, provenance='mock',
                             transport=httpx.MockTransport(lambda _: httpx.Response(200, json=body))).execute(attempt, config, [gene])
    (tmp_path/'config.json').write_text(config.model_dump_json(), encoding='utf-8')
    return tmp_path, result.model_dump(mode='json'), [gene.model_dump(mode='json')]


def test_receipt_audit_is_read_only_and_mock_is_never_live(receipt):
    root, result, genes = receipt
    before = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in root.rglob('*') if p.is_file()}
    report = gateway_receipt(root, result, EVOMAP_MODEL, genes, provenance='mock')
    assert report['http_requests'] == 1 and report['returned_model'] == 'fixture-provider-model'
    assert report['injected_gene_ids'] == report['adopted_gene_ids'] == ['first-task']
    assert before == {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in before}
    with pytest.raises(AssertionError):
        gateway_receipt(root, result, EVOMAP_MODEL, genes)


@pytest.mark.parametrize('corruption', ['usage_missing', 'usage_mismatch', 'model_missing', 'wrong_attempt', 'gene_content', 'applied_source'])
def test_receipt_audit_rejects_disconnected_evidence(receipt, corruption):
    root, result, genes = receipt
    target = root/'gateway'/('request.json' if corruption in ('wrong_attempt', 'gene_content') else 'response.json')
    data = json.loads(target.read_text(encoding='utf-8'))
    if corruption == 'usage_missing':
        del data['body']['usage']
    elif corruption == 'usage_mismatch':
        data['body']['usage']['total_tokens'] += 1
    elif corruption == 'model_missing':
        data['body']['model'] = ''
    elif corruption == 'wrong_attempt':
        data['attempt']['task_id'] = 'unrelated-task'
    elif corruption == 'gene_content':
        payload = json.loads(data['request']['messages'][1]['content'])
        payload['experience'][0]['strategy'] = ['not the real first Gene']
        data['request']['messages'][1]['content'] = json.dumps(payload)
    else:
        config = json.loads((root/'config.json').read_text(encoding='utf-8'))
        (Path(config['workspace'])/'sample.py').write_text('# not the applied proposal\n', encoding='utf-8')
    target.write_text(json.dumps(data), encoding='utf-8')
    with pytest.raises((AssertionError, KeyError)):
        gateway_receipt(root, result, EVOMAP_MODEL, genes, provenance='mock')
