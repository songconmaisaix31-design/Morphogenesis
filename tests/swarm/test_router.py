import math
import random
import pytest
from swarm.models import Locality, RunLimits, Signal
from swarm.task_ledger import TaskLedger
from swarm.pheromone import PheromoneField
from swarm.router import Router


class FixedRandom(random.Random):
    def choices(self, population, weights=None, *, cum_weights=None, k=1):
        self.weights = weights
        cumulative = 0
        for item, weight in zip(population, weights):
            cumulative += weight
            if cumulative >= .55:
                return [item]
        return [population[-1]]


def setup(tmp_path, now=None):
    now = now or [100.0]
    ledger = TaskLedger(tmp_path/'tasks.db','run',clock=lambda:now[0],limits=RunLimits(max_runtime_seconds=1e12))
    field = PheromoneField(tmp_path/'field.db',ledger=ledger,clock=lambda:now[0])
    a = field.deposit(Signal(task_id='a',workspace=str(tmp_path),scope='a',kind='error_pattern'))
    b = field.deposit(Signal(task_id='b',workspace=str(tmp_path),scope='b',kind='opportunity'))
    return ledger,field,a,b,Locality(workspace=str(tmp_path),authorized_scopes=('.',)),now


def test_history_literally_multiplies_score_changes_next_selection(tmp_path):
    ledger,field,a,b,locality,_ = setup(tmp_path)
    rng=FixedRandom()
    router=Router(field,rng=rng,exploration=0,beta=4)
    assert router.choose('w',locality,{'repair':1.,'innovation':1.}).task_id == 'b'
    for _ in range(30):
        field.reinforce('w','repair',1)
    assert router.choose('w',locality,{'repair':1.,'innovation':1.}).task_id == 'a'
    audit=ledger.audit()[0]['body']
    for s in audit['signals']:
        assert s['score'] == pytest.approx(4*s['w_history']*s['concentration']*s['capability_match']*s['urgency'])
    assert sum(audit['probabilities']) == pytest.approx(1)
    assert router.choose('other',locality,{'repair':1.,'innovation':1.}).task_id == 'b'


def test_scope_dependency_completion_claim_capability_filters(tmp_path):
    ledger,field,a,b,locality,_=setup(tmp_path)
    ledger.enqueue(Signal(task_id='c',workspace=str(tmp_path),scope='c',kind='error_pattern'),dependencies=('a',))
    router=Router(field)
    assert router.choose('w',Locality(workspace=str(tmp_path)),{'repair':1.}) is None
    lease=ledger.claim('a','holder',locality=locality)
    assert router.choose('w',locality,{'repair':1.}) is None
    ledger.submit(lease,'result',{'accepted':True})
    assert router.choose('w',locality,{'repair':1.}).task_id == 'c'
    assert ledger.audit()[0]['body']['filtered']
    assert router.choose('w',Locality(workspace=str(tmp_path),authorized_scopes=('b',)),{'repair':1.}) is None


def test_aging_weighted_exploration_rescues_zero_concentration(tmp_path):
    now=[100.0]
    ledger,field,a,b,locality,_=setup(tmp_path,now)
    now[0]+=1000
    c=field.deposit(Signal(task_id='c',workspace=str(tmp_path),scope='c',kind='opportunity',concentration=0))
    router=Router(field,exploration=1,aging_seconds=100)
    router.choose('w',locality,{'repair':1.,'innovation':1.})
    probs=ledger.audit()[0]['body']['probabilities']
    assert probs == pytest.approx([11/23,11/23,1/23])
    now[0]+=1e9
    assert router.choose('w',locality,{'repair':1.,'innovation':1.}) is not None


def test_softmax_sampling_probabilities_and_invalid_match(tmp_path):
    ledger,field,a,b,locality,_=setup(tmp_path)
    router=Router(field,rng=random.Random(7),exploration=0)
    counts={'a':0,'b':0}
    for _ in range(80):
        counts[router.choose('w',locality,{'repair':1.,'innovation':1.}).task_id]+=1
    assert 20 < counts['a'] < 60
    with pytest.raises(ValueError):
        router.choose('w',locality,{'repair':float('nan')})
    for bad in (-1,float('inf')):
        with pytest.raises(ValueError):
            Router(field,exploration=bad)
