// Read-only replay plus explicitly injected empty/error UI fixtures. No model calls.
// Usage: node tests/integration/check_stack_behavior.cjs URL NEW_OUTPUT_DIR
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const {withoutGatewayKey, readGeometry, assertGeometry} = require('./rehearsal_browser.cjs');
for (const key of Object.keys(process.env)) if (key.toUpperCase() === 'MORPH_EVOMAP_API_KEY') delete process.env[key];
const {chromium} = require(process.env.MORPH_PLAYWRIGHT);
const [url, output] = process.argv.slice(2);
assert(url && output && !fs.existsSync(output));
fs.mkdirSync(output, {recursive: true});

(async () => {
  const browser = await chromium.launch({headless: true, executablePath: process.env.MORPH_CHROMIUM, env: withoutGatewayKey(process.env)});
  const results = [];
  try {
    for (const [width, height] of [[1366,768], [1920,1080], [390,844]]) {
      const page = await browser.newPage({viewport: {width, height}, colorScheme: 'light'});
      const errors = [], external = [];
      let fixture = null, apiReads = 0;
      page.on('pageerror', error => errors.push(error.message));
      await page.route('**/*', route => {
        const request = new URL(route.request().url());
        if (request.origin !== url) { external.push(request.href); return route.abort(); }
        if (request.pathname === '/api/dashboard') {
          apiReads++;
          if (fixture === 'error') return route.fulfill({status: 503, body: 'local test fixture'});
          if (fixture === 'empty') return route.fulfill({json: {provenance: 'mock', source_label: 'Explicit empty integration fixture', hub_status: '待发布', acceptance: {}, genes: [], adoptions: [], events: [], metrics: [], notes: ['contract_local empty fixture'], rehearsal: null}});
        }
        return route.continue();
      });
      await page.goto(url);
      await page.waitForFunction(() => document.querySelector('#provenance').textContent.includes('replay'));
      await page.waitForTimeout(1400);
      const acceptance = await page.locator('.states strong').allTextContents();
      assert.deepEqual(acceptance, ['passed', 'not_run', 'not_run']);
      assert(apiReads >= 2, 'dashboard did not refresh');
      const geometry = await page.evaluate(readGeometry);
      assertGeometry(geometry, {geneInFirstViewport: width !== 390});
      assert(!geometry.overflow);
      for (const anchor of ['#rehearsal-board', '#acceptance-widget', '#legacy-dashboard', '#run-notes']) {
        if (width === 390) { await page.locator('#toggle-menu').scrollIntoViewIfNeeded(); await page.click('#toggle-menu'); }
        await page.click(`#main-menu a[href="${anchor}"]`);
        await page.waitForTimeout(400);
        assert(await page.locator(anchor).evaluate(el => {
          const r = el.getBoundingClientRect(); return r.top < innerHeight && r.bottom > 0 && r.width > 0;
        }), `unreachable ${anchor} at ${width}`);
      }
      if (width === 390) { await page.locator('#toggle-menu').scrollIntoViewIfNeeded(); await page.click('#toggle-menu'); }
      await page.click('#dark-mode-toggle');
      await page.reload();
      await page.waitForFunction(() => document.querySelector('#provenance').textContent.includes('replay'));
      assert.equal(await page.getAttribute('html', 'data-scheme'), 'dark');
      assert.equal(await page.evaluate(() => localStorage.getItem('StackColorScheme')), 'dark');
      await page.screenshot({path: path.join(output, `persisted-${width}-dark.png`)});
      if (width === 390) {
        await page.locator('.gene-ledger').scrollIntoViewIfNeeded();
        assert(await page.locator('#story-genes').isVisible());
        assert.equal(await page.locator('.gene-fact').count(), 2);
        await page.screenshot({path: path.join(output, 'phone-gene-detail.png')});
        await page.evaluate(() => scrollTo(0, 0));
      }
      fixture = 'error';
      await page.waitForFunction(() => document.querySelector('#provenance').textContent === '数据不可用');
      assert.deepEqual(await page.locator('.states strong').allTextContents(), ['not_run', 'not_run', 'not_run']);
      assert((await page.locator('#notes').textContent()).includes('HTTP 503'));
      assert(!(await page.locator('#story-checkpoint-rate').textContent()).includes('3/3'));
      await page.screenshot({path: path.join(output, `error-${width}.png`)});
      fixture = 'empty';
      await page.waitForFunction(() => document.querySelector('#provenance').textContent.includes('mock'));
      assert.deepEqual(await page.locator('.states strong').allTextContents(), ['not_run', 'not_run', 'not_run']);
      for (const id of ['gene-empty', 'message-empty', 'metric-empty']) assert(await page.locator(`#${id}`).isVisible());
      assert(!(await page.locator('#story-checkpoint-rate').textContent()).includes('3/3'));
      await page.screenshot({path: path.join(output, `empty-${width}.png`)});
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
      fixture = null;
      await page.waitForFunction(() => document.querySelector('#provenance').textContent.includes('replay'));
      assert.deepEqual(await page.locator('.states strong').allTextContents(), acceptance);
      assert.deepEqual(errors, []);
      assert.deepEqual(external, []);
      results.push({width, height, apiReads, acceptance, geometry, anchors: 4, themeReload: true, emptyErrorReset: true, recovered: true, errors, external});
      await page.close();
    }
  } finally {
    fs.writeFileSync(path.join(output, 'behavior.json'), JSON.stringify(results, null, 2));
    await browser.close();
  }
  console.log(JSON.stringify({scope: 'contract_local/replay', modelRequests: 0, results}));
})().catch(error => {console.error(error); process.exitCode = 1;});
