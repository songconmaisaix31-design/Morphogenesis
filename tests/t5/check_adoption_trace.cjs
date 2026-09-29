// Real same-origin replay first; synthetic browser responses are separate mock
// boundary probes, not runtime/adoption evidence. No remote requests are allowed.
// MORPH_PLAYWRIGHT=... MORPH_CHROMIUM=... node this-file URL NEW_OUTPUT_DIR
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require(process.env.MORPH_PLAYWRIGHT);
const { withoutGatewayKey } = require('../integration/rehearsal_browser.cjs');
const [base, output] = process.argv.slice(2);
assert(base && output && !fs.existsSync(output), 'URL and fresh output directory required');
assert(['127.0.0.1', 'localhost', '[::1]'].includes(new URL(base).hostname), 'local viewer required');
fs.mkdirSync(output, { recursive: true });
const checks = [], pageErrors = [], forbiddenRequests = [];
function check(name, condition) {
  assert(condition, name);
  checks.push(name);
  console.log(`PASS ${name}`);
}
const fields = row => row.locator('dl').evaluate(dl => Object.fromEntries(
  [...dl.children].map(div => [div.querySelector('dt').textContent, div.querySelector('dd').textContent])
));

(async () => {
  const response = await fetch(`${base}/api/dashboard`);
  assert.equal(response.status, 200);
  const dashboard = await response.json();
  assert.equal(dashboard.provenance, 'replay');
  assert.equal(dashboard.acceptance.interface_live, 'not_run');
  assert.equal(dashboard.acceptance.task_live, 'not_run');
  assert(dashboard.rehearsal.original_run_uri, 'replay needs original evidence URI');
  assert(dashboard.adoptions.length > 0, 'real replay must include an adoption');
  fs.writeFileSync(path.join(output, 'dashboard.json'), JSON.stringify(dashboard, null, 2));
  const browser = await chromium.launch({ headless: true, executablePath: process.env.MORPH_CHROMIUM, env: withoutGatewayKey(process.env) });
  let probePage;
  let override;
  let offline = false;
  async function pageFor(width, height) {
    const page = await browser.newPage({ viewport: { width, height }, reducedMotion: 'reduce' });
    page.on('pageerror', error => pageErrors.push(error.message));
    await page.route('**/*', route => {
      const request = route.request(), url = new URL(request.url());
      if (url.origin !== new URL(base).origin || request.method() !== 'GET') {
        forbiddenRequests.push({ url: request.url(), method: request.method() });
        return route.abort();
      }
      // Existing EvoMap is outside this acceptance; do not invoke upstream GETs.
      if (url.pathname.startsWith('/api/evomap')) return route.fulfill({ status: 200, contentType: 'application/json', body: '{}' });
      if (page === probePage && url.pathname === '/api/dashboard') {
        if (offline) return route.abort('failed');
        if (override) return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(override) });
      }
      return route.continue();
    });
    return page;
  }
  try {
    for (const [width, height] of [[1366, 768], [1920, 1080], [375, 812]]) {
      const page = await pageFor(width, height);
      await page.goto(`${base}/#/workspace`);
      await page.waitForFunction(() => document.getElementById('provenance')?.textContent === '来源：replay');
      await page.getByRole('tab', { name: 'Gene 池', exact: true }).click();
      const rows = page.locator('.backend-adoption');
      check(`${width} replay records match API count`, await rows.count() === dashboard.adoptions.length);
      for (const [index, use] of dashboard.adoptions.entries()) {
        const row = rows.nth(index);
        const summary = row.locator('summary');
        await summary.focus();
        await page.keyboard.press('Enter');
        check(`${width} record ${index} opens by keyboard`, await row.evaluate(el => el.open));
        const actual = await fields(row);
        assert.deepEqual(actual, {
          '运行': use.run_id, '任务': use.attempt.task_id,
          '成员': `${use.attempt.agent.role}#${use.attempt.agent.instance}`,
          '尝试': String(use.attempt.attempt), 'Gene': use.ref.gene_id, '版本': String(use.ref.version),
          '资产': use.ref.asset_id ?? '未知', '采用时间（UTC）': new Date(use.used_at * 1000).toISOString(), '来源': 'replay',
        });
        check(`${width} record ${index} every displayed field equals API`, true);
        check(`${width} source visible when collapsed or expanded`, (await summary.textContent()).includes('replay'));
        check(`${width} focus indicator visible`, await summary.evaluate(el => getComputedStyle(el).outlineStyle !== 'none'));
        check(`${width} semantic time equals API`, await row.locator('time').getAttribute('datetime') === new Date(use.used_at * 1000).toISOString());
        await row.locator('dd').last().scrollIntoViewIfNeeded();
        check(`${width} last detail remains reachable by scrolling`, await row.locator('dd').last().evaluate(el => {
          const bounds = el.getBoundingClientRect(), frame = document.querySelector('.backend-content-scroll').getBoundingClientRect();
          return bounds.top >= frame.top && bounds.bottom <= frame.bottom;
        }));
      }
      check(`${width} document and panel have no horizontal overflow`, await page.evaluate(() => {
        const panel = document.querySelector('.backend-content-scroll');
        return document.documentElement.scrollWidth <= innerWidth && panel.scrollWidth <= panel.clientWidth + 1;
      }));
      check(`${width} existing live acceptance remains not_run`, await page.locator('#task_live').textContent() === 'not_run'
        && await page.locator('#interface_live').textContent() === 'not_run');
      await page.screenshot({ path: path.join(output, `adoptions-${width}.png`) });
      const first = rows.first();
      await first.locator('summary').focus();
      await page.keyboard.press('Space');
      check(`${width} record closes by keyboard`, !(await first.evaluate(el => el.open)));
      await page.close();
    }

    // These inputs exercise presentation boundaries only, visibly labelled mock.
    // No generated or altered records are ever served as live or replay evidence.
    probePage = await pageFor(375, 812);
    const firstUse = structuredClone(dashboard.adoptions[0]);
    firstUse.provenance = 'mock';
    firstUse.used_at = 0;
    firstUse.attempt.agent.instance = 0;
    firstUse.attempt.attempt = 0;
    const secondUse = structuredClone(firstUse);
    secondUse.attempt.attempt = 1;
    const thirdUse = structuredClone(firstUse);
    thirdUse.attempt.task_id = 'mock-other-task';
    override = {
      provenance: 'mock', acceptance: { contract_local: 'not_run', interface_live: 'not_run', task_live: 'not_run' },
      events: [], genes: [], adoptions: [firstUse, secondUse, thirdUse], metrics: [], result: null,
      rehearsal: null, source_label: '浏览器 mock 采用边界探针', notes: [], hub_status: '待发布',
    };
    await probePage.goto(`${base}/#/workspace`);
    await probePage.waitForFunction(() => document.getElementById('provenance')?.textContent === '来源：mock');
    await probePage.getByRole('tab', { name: 'Gene 池', exact: true }).click();
    const probeRows = probePage.locator('.backend-adoption');
    check('mock same Gene and member keep multiple attempts/tasks', await probeRows.count() === 3);
    const probeFacts = [];
    for (let i = 0; i < 3; i++) {
      await probeRows.nth(i).locator('summary').click();
      probeFacts.push(await fields(probeRows.nth(i)));
    }
    check('mock attempt zero and one stay distinct', probeFacts[0]['尝试'] === '0' && probeFacts[1]['尝试'] === '1');
    check('mock different task is not merged', probeFacts[2]['任务'] === 'mock-other-task' && probeFacts[0]['任务'] !== probeFacts[2]['任务']);
    check('mock member zero and epoch zero remain known', probeFacts[0]['成员'].endsWith('#0') && probeFacts[0]['采用时间（UTC）'] === '1970-01-01T00:00:00.000Z');
    check('mock probes never promoted to live', probeFacts.every(row => row['来源'] === 'mock') && await probePage.locator('#task_live').textContent() === 'not_run');

    // Incomplete input is deliberately not a valid UseRecord. This is a UI
    // resilience probe, not evidence that the backend accepts broken contracts.
    override.adoptions = [{ run_id: null, attempt: { agent: { role: null, instance: null }, attempt: null }, ref: {}, used_at: null }];
    await probePage.waitForFunction(() => document.querySelectorAll('.backend-adoption').length === 1
      && document.querySelector('.backend-adoption summary')?.textContent.includes('未知'));
    await probeRows.first().locator('summary').click();
    const unknown = await fields(probeRows.first());
    check('missing identity/version/source/time stay unknown without defaults', Object.entries(unknown).every(([label, value]) => value === (label === '成员' ? '未知#未知' : '未知')));
    check('null time does not render epoch', await probeRows.first().locator('time').count() === 0);

    // Restore the real response before testing existing stale-data behaviour.
    override = undefined;
    await probePage.waitForFunction(() => document.getElementById('provenance')?.textContent === '来源：replay');
    const beforeFailure = await probeRows.allTextContents();
    offline = true;
    await probePage.waitForFunction(() => document.getElementById('connection-state')?.textContent.includes('连接失败'));
    check('connection failure keeps exact last real adoption records', JSON.stringify(await probeRows.allTextContents()) === JSON.stringify(beforeFailure));
    check('connection failure explicitly marks stale data', /上次|旧/.test(await probePage.locator('#connection-state').textContent()));
    offline = false;
    await probePage.waitForFunction(() => document.getElementById('connection-state')?.textContent === '');
    check('real replay recovers without changing provenance', await probePage.locator('#provenance').textContent() === '来源：replay');

    override = { ...structuredClone(dashboard), provenance: 'mock', rehearsal: null, result: null,
      acceptance: { contract_local: 'not_run', interface_live: 'not_run', task_live: 'not_run' },
      source_label: '浏览器 mock 注入边界探针', adoptions: [],
      genes: dashboard.genes.map(gene => ({ ...gene, provenance: 'mock', injected_count: 5, use_count: 0 })),
    };
    await probePage.waitForFunction(() => document.querySelector('.backend-adoptions')?.textContent.includes('暂无采用记录'));
    check('injected genes without UseRecord never create adoption rows', await probeRows.count() === 0);
    delete override.adoptions;
    await probePage.waitForFunction(() => document.querySelector('.backend-adoptions')?.textContent.includes('采用记录未提供'));
    check('missing adoption list differs from an empty list', await probeRows.count() === 0);
    check('zero browser page errors', pageErrors.length === 0);
    check('only same-origin GET requests', forbiddenRequests.length === 0);
  } finally {
    fs.writeFileSync(path.join(output, 'summary.json'), JSON.stringify({
      checks, pageErrors, forbiddenRequests, replay_source: dashboard.rehearsal.original_run_uri,
      scope: 'local real replay plus labelled mock and incomplete-input browser probes; no task_live claim',
    }, null, 2));
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
