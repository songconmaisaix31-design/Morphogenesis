const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '../../src/env-observatory');

function dataLayer(fetch, protocol = 'http:') {
  let polls = 0;
  const context = { window: { location: { protocol, search: '' }, fetch }, URLSearchParams,
    setInterval() { polls++; }, clearInterval() {} };
  vm.runInNewContext(fs.readFileSync(path.join(root, 'data.js'), 'utf8'), context);
  return { api: context.window.EnvData, polls: () => polls };
}

test('HTTP 503 stays empty and never starts example activity', async () => {
  const { api, polls } = dataLayer(async () => ({ ok: false, status: 503 }));
  const [pkg, snap, replay] = await Promise.all([api.fetchPackage(), api.fetchSnapshot(), api.fetchReplay('T-11')]);
  assert.equal(pkg.source, 'unconnected');
  assert.equal(pkg.tasks.length, 0);
  assert.equal(pkg.task_audit.length, 0);
  assert.equal(pkg.project_id, null);
  assert.equal(snap.branches.length, 0);
  assert.equal(replay.task, null);
  assert.match(replay.error, /503/);
  api.subscribeActivity(() => assert.fail('fabricated event'))();
  assert.equal(polls(), 0);
});

test('file opening and network rejection stay unconnected', async () => {
  for (const protocol of ['file:', 'http:']) {
    const { api } = dataLayer(async () => { throw Error('offline'); }, protocol);
    const pkg = await api.fetchPackage();
    assert.equal(pkg.source, 'unconnected');
    assert.equal(pkg.tasks.length, 0);
  }
});

test('HTTP transport does not promote mock provenance or pin project p1', async () => {
  const urls = [];
  const pkg = { project_id: 'actual-project', task_audit: [], tasks: [{ provenance: 'mock', cost: null }] };
  const { api } = dataLayer(async url => {
    urls.push(url); return { ok: true, json: async () => structuredClone(pkg) };
  });
  const result = await api.fetchPackage();
  assert.equal(result.source, 'backend');
  assert.equal(result.tasks[0].provenance, 'mock');
  assert.equal(result.tasks[0].cost, null);
  assert.equal(urls[0], '/api/research/package');
});

test('a failed refresh clears previous research facts and replay cannot masquerade as fresh', async () => {
  let fail = false;
  const { api } = dataLayer(async () => ({ ok: !fail, status: 503,
    json: async () => ({ tasks: [{ task_id: 'old' }], task_audit: [] }) }));
  assert.equal((await api.fetchPackage()).tasks.length, 1);
  fail = true;
  assert.equal((await api.fetchPackage()).tasks.length, 0);
  assert.equal((await api.fetchReplay('old')).audit.length, 0);
});

function swarmLayer() {
  const html = fs.readFileSync(path.join(root, 'env-observatory.html'), 'utf8');
  const start = html.indexOf('  var SWARM_HEARTBEAT_S');
  const end = html.indexOf('  /* ---------------- 视图标题', start);
  const elements = {};
  const context = { Date, T: x => x, $: id => elements[id] ||= { textContent: '', innerHTML: '' } };
  vm.createContext(context);
  vm.runInContext(html.slice(start, end), context);
  return { context, elements };
}

test('unbound and failed swarm counters are unknown, not zero', () => {
  const { context: c, elements: e } = swarmLayer();
  c.renderSwarmStats({ health: 'missing', workers: [], tasks: [] });
  for (const id of ['swAlive', 'swTotal', 'swStopped', 'swLeased', 'swTasks']) assert.equal(e[id].textContent, 'unknown');
  c.SWARM_STATE.error = 'HTTP 503';
  c.renderSwarmStats({ health: 'ok', workers: [], tasks: [], sources: { ledger: { state: 'ok' } } });
  assert.equal(e.swTasks.textContent, 'unknown');
});

test('replay, missing heartbeats, and unknown worker states never imply online', () => {
  const { context: c } = swarmLayer();
  const now = Date.now() / 1000;
  assert.equal(c.swPeerClass({ state: 'unknown', updated_at: now }, now), 'is-unknown');
  assert.equal(c.swPeerClass({ state: 'running' }, now), 'is-unknown');
  c.SWARM_STATE.data = { replay: true };
  assert.equal(c.swPeerClass({ state: 'running', updated_at: now }, now), 'is-unknown');
});

test('lease, budget nulls, and hostile identifiers remain literal backend facts', () => {
  const { context: c, elements: e } = swarmLayer();
  c.renderSwarmTasksBudget({ tasks: [{ task_id: '<img src=x onerror=alert(1)>', status: 'claimed',
    lease_state: 'expired', owner: null, token: 7, expires_at: null }],
    budget: { breaker: null, reservations: [{ task_id: 'T', worker_id: 'W', state: 'unknown',
      reserved_usd: 0.5, tokens: null, cost: null }] }, sources: { budget: { state: 'ok' } } });
  assert.match(e.swTasksBody.innerHTML, /claimed \/ expired/);
  assert.match(e.swTasksBody.innerHTML, /&lt;img/);
  assert.doesNotMatch(e.swTasksBody.innerHTML, /<img/);
  assert.match(e.swBudgetBody.innerHTML, /0.5 \/ unknown/);
  assert.match(e.swBudgetBody.innerHTML, /<td>unknown<\/td>/);
});

test('all inline JavaScript parses without a build transform', () => {
  const html = fs.readFileSync(path.join(root, 'env-observatory.html'), 'utf8');
  for (const [, script] of html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)) new vm.Script(script);
});

test('historical display context is explicit and cannot promote aggregate acceptance', () => {
  const { context: c, elements: e } = swarmLayer();
  const data = { replay: true, health: 'partial', acceptance: { provenance: 'replay',
    contract_local: 'not_run', interface_live: 'not_run', task_live: 'not_run' },
    display_context: { source: 'operator_configuration', run_status: 'ended',
      scope_label: '局部代码缺陷 <sample>', scope_reference: 'arguments.json / code_defects' },
    worker_audit: [{ task_id: 'one', task_live: 'passed', provenance: 'live' }] };
  const original = JSON.stringify(data);
  c.renderSwarmSource(data);
  assert.match(e.swObservation.innerHTML, /历史观察/);
  assert.match(e.swObservation.innerHTML, /运行已结束/);
  assert.match(e.swObservation.innerHTML, /只读展示配置/);
  assert.match(e.swObservation.innerHTML, /局部代码缺陷 &lt;sample&gt;/);
  assert.match(e.swObservation.innerHTML, /arguments.json/);
  assert.match(e.swAcceptanceBar.innerHTML, /整体场景/);
  assert.match(e.swAcceptanceBar.innerHTML, /task_live.*not_run/);
  assert.doesNotMatch(e.swAcceptanceBar.innerHTML, /passed/);
  assert.equal(JSON.stringify(data), original);
});

test('unconfigured paths and live audit never imply scope or ended execution', () => {
  const { context: c, elements: e } = swarmLayer();
  c.renderSwarmSource({ replay: true, state_directory: '/formal-v1/clamp/state',
    worker_audit: [{ provenance: 'live', task_live: 'passed' }] });
  assert.match(e.swObservation.innerHTML, /范围未声明/);
  assert.match(e.swObservation.innerHTML, /结束状态未知/);
  assert.doesNotMatch(e.swObservation.innerHTML, /clamp|运行已结束/);
  c.renderSwarmSource({ replay: false });
  assert.doesNotMatch(e.swObservation.innerHTML, /历史观察|运行已结束/);
});
