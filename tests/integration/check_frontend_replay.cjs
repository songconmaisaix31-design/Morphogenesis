// Replay + no-data acceptance for the integrated frontend, complementing
// check_frontend_integration.cjs (mock fixture). Every topology/task/event
// assertion is compared against the live /api/dashboard JSON of the same
// server — never hardcoded screen text alone.
// Modes:
//   replay  — server runs --rehearsal <real evidence> --replay; page must be
//             labelled 回放视图, nodes/edges/ghost/results derive from the
//             snapshot, replay never poses as task_live.
//   nodata  — server runs with no input source; page must honestly show
//             未加载导出 / empty topology with zero fabricated nodes.
// Usage: MORPH_PLAYWRIGHT=... MORPH_CHROMIUM=... node tests/integration/check_frontend_replay.cjs URL OUTPUT_DIR replay|nodata
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const assert = require('node:assert/strict');
const { withoutGatewayKey } = require('./rehearsal_browser.cjs');
for (const key of Object.keys(process.env)) if (key.toUpperCase() === 'MORPH_EVOMAP_API_KEY') delete process.env[key];
const { chromium } = require(process.env.MORPH_PLAYWRIGHT);
const [url, output, mode] = process.argv.slice(2);
assert(url && output && ['replay', 'nodata'].includes(mode) && !fs.existsSync(output), 'usage: URL NEW_OUTPUT_DIR replay|nodata');
fs.mkdirSync(output, { recursive: true });

const results = [];
function record(name, ok, detail = '') {
  results.push({ name, ok, detail });
  console.log(`${ok ? 'PASS' : 'FAIL'} ${name}${detail ? ` — ${detail}` : ''}`);
}
const agentKey = (agent) =>
  agent && typeof agent === 'object' ? `${agent.role ?? 'unknown'}#${agent.instance ?? '?'}` : String(agent ?? 'unknown');

function fetchJson(u) {
  return new Promise((resolve, reject) => {
    http.get(u, (res) => {
      const chunks = [];
      res.on('data', (c) => chunks.push(c));
      res.on('end', () => {
        try { assert.equal(res.statusCode, 200); resolve(JSON.parse(Buffer.concat(chunks).toString('utf-8'))); }
        catch (error) { reject(error); }
      });
    }).on('error', reject);
  });
}

(async () => {
  const dashboard = await fetchJson(`${url}/api/dashboard`);
  fs.writeFileSync(path.join(output, 'dashboard.json'), JSON.stringify(dashboard, null, 2));
  const browser = await chromium.launch({ headless: true, executablePath: process.env.MORPH_CHROMIUM, env: withoutGatewayKey(process.env) });
  try {
    const page = await browser.newPage({ viewport: { width: 1366, height: 768 } });
    const errors = [], external = [], consoleErrors = [], requests = [], httpFailures = [];
    page.on('pageerror', (error) => errors.push(error.message));
    page.on('console', message => {
      if (message.type() === 'error') consoleErrors.push({ text: message.text(), url: message.location().url });
    });
    // Observe the real server only: no browser routes, response injection or retries.
    page.on('request', request => {
      requests.push({ url: request.url(), method: request.method() });
      if (new URL(request.url()).origin !== new URL(url).origin) external.push(request.url());
    });
    page.on('response', response => {
      if (response.status() >= 400) httpFailures.push({ url: response.url(), status: response.status() });
    });
    const evomapResponse = page.waitForResponse(response => new URL(response.url()).pathname === '/api/evomap', { timeout: 60000 });
    await page.goto(`${url}/#/workspace`, { waitUntil: 'domcontentloaded' });
    await page.waitForSelector('.backend-main', { timeout: 20000 });
    await page.waitForFunction(() => document.getElementById('provenance')?.textContent !== '加载中', null, { timeout: 15000 });

    // Provenance labelling must match the server's own fields.
    const header = await page.evaluate(() => ({
      provenance: document.getElementById('provenance')?.textContent ?? '',
      sourceLabel: document.getElementById('source-label')?.textContent ?? '',
      rehearsalMode: document.getElementById('rehearsal-mode')?.textContent ?? '',
    }));
    // empty_dashboard deliberately exposes its source_label (未加载导出) in
    // place of the raw `live` provenance: there is no loaded live snapshot to
    // claim. Replay and populated sources continue to show provenance verbatim.
    const expectedHeaderProvenance = mode === 'nodata' ? dashboard.source_label : `来源：${dashboard.provenance}`;
    record('header provenance/source state matches server semantics', header.provenance === expectedHeaderProvenance,
      `${header.provenance} vs ${expectedHeaderProvenance}`);
    record('header source_label matches server', header.sourceLabel === dashboard.source_label, header.sourceLabel);

    await page.getByRole('tab', { name: '蜂群拓扑', exact: true }).click();
    await page.waitForFunction(() => document.body.dataset.view === 'workspace', null, { timeout: 10000 });
    await page.waitForSelector('section[aria-label="Agent Swarm 拓扑"]', { timeout: 10000 });

    const current = dashboard.rehearsal?.current ?? null;
    if (mode === 'replay') {
      assert(current, 'replay mode requires rehearsal.current');
      const expectedKeys = [...new Set([
        ...(current.members ?? []).map((m) => agentKey(m.agent)),
        ...(current.pipes ?? []).flatMap((p) => [agentKey(p.src), agentKey(p.dst)]),
      ])].sort();
      const expectedEdges = (current.pipes ?? []).map((p) => ({
        key: `${agentKey(p.src)}→${agentKey(p.dst)}`, active: p.active !== false, weight: p.weight ?? null,
      }));
      const removed = current.routing?.removed_member ? agentKey(current.routing.removed_member) : null;
      const rerouted = current.routing?.selected_attempt?.agent ? agentKey(current.routing.selected_attempt.agent) : null;

      record('replay label: badge 回放视图 + 只读', /回放视图/.test(header.rehearsalMode) && /原始证据只读/.test(header.rehearsalMode), header.rehearsalMode);
      record('replay acceptance never claims task_live', (dashboard.acceptance?.task_live ?? 'not_run') !== 'passed', JSON.stringify(dashboard.acceptance));
      record('real API replay and all three acceptance states', dashboard.provenance === 'replay'
        && dashboard.acceptance.contract_local === 'passed' && dashboard.acceptance.interface_live === 'not_run'
        && dashboard.acceptance.task_live === 'not_run', JSON.stringify(dashboard.acceptance));

      await page.waitForSelector('.swarm-svg .swarm-node-label', { timeout: 10000 });
      const topo = await page.evaluate(() => ({
        badge: document.querySelector('.swarm-badge')?.textContent ?? '',
        stage: document.querySelector('.swarm-hud-stage')?.textContent ?? '',
        task: document.querySelector('.swarm-hud-dim')?.textContent ?? '',
        nodeLabels: [...document.querySelectorAll('.swarm-svg .swarm-node-label')].map((el) => el.textContent).sort(),
        edgePaths: [...document.querySelectorAll('.swarm-svg path')].map((el) => el.getAttribute('class') ?? ''),
        ghostLine: document.querySelector('.swarm-ghost-line')?.textContent ?? '',
        ghostClass: document.querySelector('.swarm-ghost-line')?.getAttribute('class') ?? '',
      }));
      record('topology badge 回放视图 · 只读', /回放视图/.test(topo.badge) && /只读/.test(topo.badge), topo.badge);
      record('node identities == /api/dashboard members+pipes', JSON.stringify(topo.nodeLabels) === JSON.stringify(expectedKeys), `dom=${topo.nodeLabels} api=${expectedKeys}`);
      record('edge count == pipes', topo.edgePaths.length === expectedEdges.length, `${topo.edgePaths.length} vs ${expectedEdges.length}`);
      const activeDom = topo.edgePaths.filter((cls) => cls.includes('swarm-edge-active')).length;
      const activeApi = expectedEdges.filter((e) => e.active).length;
      record('active edge count matches pipes.active', activeDom === activeApi, `dom=${activeDom} api=${activeApi}`);
      record('stage/sequence/task from snapshot', topo.stage.includes(`#${current.sequence}`) && topo.task === current.task_id, `${topo.stage} | ${topo.task}`);
      if (removed) {
        const ghostOk = topo.ghostLine.includes(removed) && (!rerouted || topo.ghostLine.includes(rerouted));
        record(`ghost banner names removed ${removed} and reroute ${rerouted}`, ghostOk, topo.ghostLine.slice(0, 120));
        const recoverySucceeded = (current.results ?? []).some((r) => r.status === 'succeeded' && agentKey(r.attempt?.agent) === rerouted);
        if (recoverySucceeded) {
          record('literal recovered phrase only for real success', topo.ghostLine.includes('Ghost 已离开，任务重路由') && topo.ghostClass.includes('swarm-ghost-recovered'), topo.ghostClass);
        }
      }
      // Node detail: click the removed member's <g> (label text is inside the
      // SVG and does not itself receive the click), detail aside must quote real facts.
      const targetKey = removed ?? expectedKeys[0];
      await page.locator(`.swarm-svg g.swarm-node:has(.swarm-node-label:text-is("${targetKey}"))`).dispatchEvent('click');
      await page.waitForSelector('.swarm-detail:not(.swarm-detail-hint)', { timeout: 5000 });
      const detail = await page.textContent('.swarm-detail');
      const resultsForKey = (current.results ?? []).filter((r) => agentKey(r.attempt?.agent) === targetKey);
      record('node detail shows real facts', detail.includes(targetKey) && (resultsForKey.length === 0 || /任务结果|结果/.test(detail)), detail.slice(0, 100).replace(/\s+/g, ' '));
      await page.click('.swarm-detail-close');

      // Event feed renders rehearsal.history stage rows; compare with the wire.
      const feed = await page.evaluate(() => ({
        rows: document.querySelectorAll('#event-feed .event-row').length,
        firstRow: document.querySelector('#event-feed .event-row')?.textContent ?? '',
        text: document.getElementById('event-feed')?.textContent ?? '',
      }));
      const apiHistory = (dashboard.rehearsal?.history ?? []).length;
      const latestSeq = Math.max(...(dashboard.rehearsal?.history ?? [{ sequence: -1 }]).map((h) => h.sequence ?? -1));
      record('event feed rows == rehearsal.history, latest first',
        feed.rows === apiHistory && (apiHistory === 0 ? /尚无阶段快照/.test(feed.text) : feed.firstRow.includes(`#${latestSeq}`)),
        `dom_rows=${feed.rows} api_history=${apiHistory} first="${feed.firstRow.slice(0, 40)}"`);

      // Big numbers + checkpoint list vs snapshot facts.
      const boards = await page.evaluate(() => ({
        rate: document.getElementById('story-checkpoint-rate')?.textContent ?? '',
        checks: [...document.querySelectorAll('#story-checkpoints li')].map((el) => el.textContent),
        tokens: document.getElementById('metric-tokens')?.textContent ?? '',
        geneCount: document.getElementById('story-gene-count')?.textContent ?? '',
        offlineMember: document.getElementById('story-offline-member')?.textContent ?? '',
        offlineReason: document.getElementById('story-offline-reason')?.textContent ?? '',
      }));
      const cps = current.checkpoints ?? null;
      if (cps) {
        record('checkpoint big number == passed/total·ratio', boards.rate.startsWith(`${cps.passed_count}/${cps.total}`) && boards.rate.includes(`${Math.round(cps.ratio * 100)}%`), boards.rate);
        const expectChecks = (cps.checks ?? []).map((c) => `${c.name}：${c.passed === true ? '通过' : c.passed === false ? '失败' : '待判定'}`);
        record('checkpoint list == snapshot checks', JSON.stringify(boards.checks) === JSON.stringify(expectChecks), boards.checks.join(' | '));
      }
      const tokenValues = (current.results ?? []).map((r) => r?.usage?.tokens).filter((t) => Number.isFinite(t));
      record('tokens big number from real result usage', tokenValues.length === 0 ? boards.tokens === '未知' : tokenValues.includes(Number(boards.tokens)), `dom=${boards.tokens} api=${tokenValues}`);
      const curGenes = current.genes ?? [];
      const activeGenes = curGenes.filter((g) => g.archived_at === null || g.archived_at === undefined).length;
      record('gene count == active genes in snapshot', boards.geneCount === String(curGenes.length ? activeGenes : '未知'), `dom=${boards.geneCount} api=${activeGenes}/${curGenes.length}`);
      const ledger = await page.evaluate(() => ({
        cards: document.querySelectorAll('#story-genes .gene-fact').length,
        states: [...document.querySelectorAll('#story-genes .gene-state')].map((el) => el.textContent),
        archived: [...document.querySelectorAll('#story-genes .gene-fact')].filter((el) => el.textContent.includes('已归档')).length,
      }));
      const apiArchived = curGenes.filter((g) => g.archived_at !== null && g.archived_at !== undefined).length;
      record('gene ledger cards == snapshot genes, archived count matches',
        ledger.cards === curGenes.length && ledger.archived === apiArchived,
        `dom=${ledger.cards}/${ledger.archived} api=${curGenes.length}/${apiArchived} states=${ledger.states}`);
      const pipeRows = await page.evaluate(() => [...document.querySelectorAll('#story-pipes .pipe-row')].map((el) => ({
        active: el.className.includes('pipe-active'), text: el.textContent,
      })));
      record('pipe list rows == pipes with weights', pipeRows.length === expectedEdges.length
        && pipeRows.every((row, i) => row.active === expectedEdges[i].active
          && (expectedEdges[i].weight === null || row.text.includes(`权重 ${Number(expectedEdges[i].weight).toFixed(2)}`))),
        pipeRows.map((r) => r.text.slice(0, 60)).join(' || '));
      if (removed) {
        record('offline card names removed member + reason + reroute',
          boards.offlineMember.includes(removed) && boards.offlineReason.includes(rerouted ?? ''),
          `${boards.offlineMember} | ${boards.offlineReason.slice(0, 60)}`);
      }

      // Click through every node; each detail aside must quote that key.
      let detailOk = true;
      const detailNotes = [];
      for (const key of expectedKeys) {
        await page.locator(`.swarm-svg g.swarm-node:has(.swarm-node-label:text-is("${key}"))`).dispatchEvent('click');
        await page.waitForSelector('.swarm-detail:not(.swarm-detail-hint)', { timeout: 5000 });
        const text = await page.textContent('.swarm-detail');
        if (!text.includes(key)) { detailOk = false; detailNotes.push(key); }
      }
      record('all node details quote their own key', detailOk, detailNotes.join(','));
      await page.screenshot({ path: path.join(output, 'replay-swarm.png'), fullPage: true });
    } else {
      // nodata: empty_dashboard (provenance live, source_label 未加载导出)
      record('source_label explicitly 未加载导出', dashboard.source_label.includes('未加载导出') && header.sourceLabel.includes('未加载导出'), header.sourceLabel);
      record('no rehearsal snapshot on the wire', current === null, `current=${current}`);
      const emptyTopo = await page.evaluate(() => ({
        badge: document.querySelector('.swarm-badge')?.textContent ?? '',
        dim: document.querySelector('.swarm-hud-dim')?.textContent ?? '',
        message: document.querySelector('.swarm-state')?.textContent ?? '',
        nodes: document.querySelectorAll('.swarm-svg .swarm-node-label').length,
        edges: document.querySelectorAll('.swarm-svg path').length,
      }));
      record('topology empty state explicit, zero fabricated nodes/edges',
        /空态/.test(emptyTopo.dim) && /未加载彩排快照/.test(emptyTopo.message) && emptyTopo.nodes === 0 && emptyTopo.edges === 0,
        JSON.stringify(emptyTopo));
      const states = await page.evaluate(() => ({
        contract: document.getElementById('contract_local')?.textContent,
        iface: document.getElementById('interface_live')?.textContent,
        task: document.getElementById('task_live')?.textContent,
        mode: document.getElementById('rehearsal-mode')?.textContent,
      }));
      record('acceptance all not_run, mode says no snapshot',
        states.contract === 'not_run' && states.iface === 'not_run' && states.task === 'not_run' && /尚未加载彩排快照|未加载/.test(states.mode),
        JSON.stringify(states));
      // Misleading-check: the raw badge text pair a user actually reads.
      record('no surface claims live results without data',
        !/passed/.test(states.contract + states.iface + states.task) && !/通过率.*\d/.test(await page.textContent('#story-checkpoint-rate') ?? ''),
        `badge=${header.provenance} label=${header.sourceLabel}`);
      await page.screenshot({ path: path.join(output, 'nodata-swarm.png'), fullPage: true });
    }

    const evomapWire = await evomapResponse;
    const evomap = await evomapWire.json();
    fs.writeFileSync(path.join(output, 'evomap.json'), JSON.stringify(evomap, null, 2));
    await page.waitForFunction(() => document.querySelector('.morph-evomap-form button[type=submit]')?.disabled === false);
    const screenshots = [];
    for (const [width, height] of [[1366, 768], [1920, 1080], [375, 812]]) {
      await page.setViewportSize({ width, height });
      const shot = async name => {
        const file = `${mode}-${width}-${name}.png`;
        await page.screenshot({ path: path.join(output, file) }); screenshots.push(file);
      };
      await page.getByRole('tab', { name: '当前任务', exact: true }).click();
      await page.evaluate(() => document.fonts.ready);
      record(`${width} local Inter font loaded`, await page.evaluate(() => [...document.fonts].some(font => font.family === 'Inter Variable' && font.status === 'loaded')));
      record(`${width} task and provenance from real API`, await page.locator('#provenance').innerText() === expectedHeaderProvenance
        && (!current || (await page.locator('.backend-breadcrumb-task').innerText()) === current.task_id));
      await shot('task');
      await page.getByRole('button', { name: '验收详情', exact: true }).click();
      for (const state of ['contract_local', 'interface_live', 'task_live']) {
        record(`${width} visible ${state} equals API`, await page.locator(`#${state}`).isVisible()
          && await page.locator(`#${state}`).innerText() === dashboard.acceptance[state]);
      }
      await shot('details');
      await page.keyboard.press('Escape');
      await page.getByRole('tab', { name: '蜂群拓扑', exact: true }).click();
      if (await page.locator('.swarm-detail-close').isVisible()) await page.locator('.swarm-detail-close').click();
      await shot('topology');
      if (current?.members.length) {
        await page.locator('.swarm-member-list button').first().click();
        await page.locator('.swarm-detail').evaluate(el => el.scrollIntoView({ block: 'center', behavior: 'instant' }));
        record(`${width} member detail visible in content viewport`, await page.locator('.swarm-detail').evaluate(el => {
          const r = el.getBoundingClientRect(), frame = document.querySelector('.backend-content-scroll').getBoundingClientRect();
          return r.top >= frame.top && r.bottom <= frame.bottom;
        }));
        await shot('member');
        await page.locator('.swarm-detail-close').click();
      }
      for (const [tab, panel, name] of [['Gene 池', 'genes', 'genes'], ['证据与指标', 'evidence', 'evidence'], ['EvoMap 只读', 'evomap', 'evomap']]) {
        await page.getByRole('tab', { name: tab, exact: true }).click();
        await page.waitForTimeout(250); // let the chart resize to its newly visible panel
        record(`${width} ${name} view actually visible`, await page.locator(`#backend-${panel}`).isVisible()
          && await page.locator('[role=tabpanel]:visible').count() === 1);
        if (name === 'evomap') {
          const text = await page.locator('#backend-evomap').innerText();
          for (const key of ['community_search', 'community_categories', 'local_pool']) {
            if (evomap[key]) record(`${width} EvoMap ${key} state matches real response`, text.includes(evomap[key].state));
          }
        }
        record(`${width} ${name} no horizontal overflow`, await page.evaluate(() => document.documentElement.scrollWidth === innerWidth));
        await shot(name);
      }
    }
    record('only read-only browser requests', requests.every(request => request.method === 'GET'));
    record('no unexpected HTTP failures', httpFailures.every(response => new URL(response.url).pathname.startsWith('/api/evomap')), JSON.stringify(httpFailures));
    record('no unexpected console errors', consoleErrors.every(error => error.url.includes('/api/evomap') && /Failed to load resource/.test(error.text)), JSON.stringify(consoleErrors));
    record('no pageerror', errors.length === 0, errors.slice(0, 3).join(' | '));
    record('browser stayed same-origin', external.length === 0, external.slice(0, 3).join(' | '));

    const summary = {
      url, mode, when: new Date().toISOString(),
      provenance: dashboard.provenance, source_label: dashboard.source_label,
      pageerrors: errors, externalRequests: external, consoleErrors, httpFailures, requests, screenshots, results,
      passed: results.filter((r) => r.ok).length, failed: results.filter((r) => !r.ok).length,
    };
    fs.writeFileSync(path.join(output, `summary-${mode}.json`), JSON.stringify(summary, null, 2));
    console.log(`\n${summary.passed} passed, ${summary.failed} failed; evidence in ${output}`);
    if (summary.failed) process.exitCode = 1;
  } finally {
    await browser.close();
  }
})().catch((error) => {
  console.error('acceptance aborted:', error);
  process.exitCode = 1;
});
