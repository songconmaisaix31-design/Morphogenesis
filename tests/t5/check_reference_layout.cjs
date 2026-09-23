// Browser checks for the user-snapshot adaptation. Requires the existing
// mock viewer, Playwright and Chromium. Optional final argument is a dashboard
// captured through the existing replay adapter, never live task evidence.
// node this-file URL NEW_OUTPUT_DIR [REPLAY_DASHBOARD_JSON]
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require(process.env.MORPH_PLAYWRIGHT);
const [base, output, replayPath] = process.argv.slice(2);
assert(base && output && !fs.existsSync(output), 'URL and a fresh output directory required');
fs.mkdirSync(output, { recursive: true });

(async () => {
  const browser = await chromium.launch({ executablePath: process.env.MORPH_CHROMIUM, headless: true });
  const checks = [], errors = [], consoleErrors = [], badRequests = [], requests = [];
  const check = (name, value) => { assert(value, name); checks.push(name); console.log(`PASS ${name}`); };
  const pageFor = async (width, height, reducedMotion = 'reduce') => {
    const page = await browser.newPage({ viewport: { width, height }, reducedMotion });
    page.on('pageerror', error => errors.push(error.message));
    page.on('console', msg => { if (msg.type() === 'error') consoleErrors.push({ text: msg.text(), url: msg.location().url }); });
    await page.route('**/*', route => {
      const req = route.request(); requests.push({ url: req.url(), method: req.method() });
      if (new URL(req.url()).origin !== new URL(base).origin || req.method() !== 'GET') {
        badRequests.push(req.url()); return route.abort();
      }
      return route.continue();
    });
    await page.route('**/api/evomap*', route => route.fulfill({ status: 404, contentType: 'application/json', body: '{}' }));
    return page;
  };
  try {
    for (const [width, height] of [[1366, 768], [1920, 1080], [375, 812]]) {
      const page = await pageFor(width, height);
      await page.goto(`${base}/#/workspace`);
      await page.waitForFunction(() => document.querySelector('#provenance')?.textContent.includes('mock'));
      await page.evaluate(() => document.fonts.ready);
      check(`${width} Inter loaded`, await page.evaluate(() => [...document.fonts].some(font => font.family === 'Inter Variable' && font.status === 'loaded')));
      check(`${width} no invented members`, await page.locator('.swarm-node').count() === 0);
      check(`${width} compact truthful topology empty state`, await page.locator('.swarm-shell').evaluate(el => el.getBoundingClientRect().height < 150 && el.textContent.includes('空态')));
      check(`${width} actual exported Gene bodies shown`, await page.locator('#story-genes').innerText().then(text => text.includes('review-first') && text.includes('生命周期未提供')));
      check(`${width} Envelope feed labels its mock source`, await page.locator('#event-feed').innerText().then(text => text.includes('Envelope') && text.includes('mock') && text.includes('builder#0')));
      check(`${width} unknown tokens and lifecycle count preserved`, await page.locator('#metric-tokens').innerText() === '未知' && await page.locator('#story-gene-count').innerText() === '未知');
      check(`${width} acceptance does not upgrade`, await page.locator('#interface_live').innerText() === 'not_run' && await page.locator('#task_live').innerText() === 'not_run');
      check(`${width} no horizontal overflow`, await page.evaluate(() => document.documentElement.scrollWidth === innerWidth));
      check(`${width} unique data IDs`, await page.evaluate(() => { const ids = [...document.querySelectorAll('[id]')].map(el => el.id); return new Set(ids).size === ids.length; }));
      check(`${width} context text remains readable`, await page.locator('.backend-context .state-row span').first().evaluate(el => parseFloat(getComputedStyle(el).fontSize) >= 12));
      check(`${width} empty state is a flat document row`, await page.locator('.swarm-shell').evaluate(el => getComputedStyle(el).borderRadius === '0px' && getComputedStyle(el).backgroundColor === 'rgba(0, 0, 0, 0)'));
      await page.screenshot({ path: path.join(output, `workspace-${width}.png`) });
      await page.screenshot({ path: path.join(output, `workspace-${width}-full.png`), fullPage: true });
      await page.getByRole('button', { name: 'EvoMap 只读', exact: false }).click();
      check(`${width} navigation changes active section`, await page.locator('.backend-nav-group button[aria-current]').innerText().then(text => text.includes('EvoMap')));
      await page.screenshot({ path: path.join(output, `evomap-${width}.png`) });
      await page.locator('.backend-return').click();
      await page.waitForSelector('.story-enter.is-visible');
      check(`${width} reduced motion keeps explicit entry`, await page.evaluate(() => document.body.dataset.view === 'physarum'));
      check(`${width} old caption does not overlap title`, await page.locator('.growth-intro__caption').evaluate(el => getComputedStyle(el).visibility === 'hidden'));
      check(`${width} title fits 10 percent insets`, await page.locator('.story-product h1').evaluate(el => { const r = el.getBoundingClientRect(); return r.left >= innerWidth * .099 && r.right <= innerWidth * .901; }));
      if (width === 1366) check('English title respects reference h1 multiplier', await page.locator('.story-product [lang=en]').evaluate(el => parseFloat(getComputedStyle(el).fontSize) >= 76 && parseFloat(getComputedStyle(el).fontSize) <= 92));
      await page.screenshot({ path: path.join(output, `intro-${width}-reduced.png`) });
      await page.keyboard.press('Tab'); // switch from pointer to keyboard modality
      await page.locator('.story-enter').focus();
      check(`${width} visible keyboard outline`, await page.locator('.story-enter').evaluate(el => getComputedStyle(el).outlineStyle !== 'none'));
      await page.keyboard.press('Enter');
      await page.waitForFunction(() => document.body.dataset.view === 'workspace');
      check(`${width} hidden growth pauses`, await page.locator('.growth-intro').getAttribute('data-active') === 'false');
      await page.route('**/api/dashboard', route => route.fulfill({ status: 503, body: 'unavailable' }));
      await page.waitForFunction(() => document.querySelector('#connection-state')?.textContent.includes('保留上次快照'));
      check(`${width} failure preserves exported facts`, await page.locator('#story-genes').innerText().then(text => text.includes('review-first')));
      await page.screenshot({ path: path.join(output, `stale-${width}.png`) });
      await page.close();
    }

    const intro = await pageFor(1366, 768, 'no-preference');
    await intro.goto(`${base}/#/physarum`);
    await intro.waitForSelector('.growth-intro.is-active');
    await intro.waitForTimeout(400);
    // Contract test of the Page Visibility handler; synthetic hidden state is
    // explicitly scoped here, distinct from physical tab/OS acceptance.
    await intro.evaluate(() => { Object.defineProperty(document, 'hidden', { configurable: true, value: true }); document.dispatchEvent(new Event('visibilitychange')); });
    await intro.waitForTimeout(200);
    check('visibility handler pauses CSS growth', await intro.locator('.growth-intro__branch').first().evaluate(el => getComputedStyle(el).animationPlayState === 'paused'));
    await intro.waitForTimeout(4800);
    check('visibility handler pauses phase clock', await intro.locator('.story-product.is-visible').count() === 0);
    await intro.evaluate(() => { delete document.hidden; document.dispatchEvent(new Event('visibilitychange')); });
    await intro.waitForSelector('.story-enter.is-visible', { timeout: 10000 });
    check('resume still awaits explicit entry', await intro.evaluate(() => document.body.dataset.view === 'physarum'));
    await intro.locator('.story-enter').click();
    await intro.locator('.backend-return').click();
    await intro.waitForSelector('.growth-intro.is-active');
    check('return restarts branch growth', await intro.locator('.growth-intro__branch').last().evaluate(el => parseFloat(getComputedStyle(el).strokeDashoffset) > .9));
    await intro.close();

    if (replayPath) {
      const replay = JSON.parse(fs.readFileSync(replayPath, 'utf8'));
      assert.equal(replay.provenance, 'replay');
      assert.equal(replay.acceptance.task_live, 'not_run');
      for (const [width, height] of [[1366, 768], [1920, 1080], [375, 812]]) {
        const page = await pageFor(width, height);
        await page.route('**/api/dashboard', route => route.fulfill({ contentType: 'application/json', body: JSON.stringify(replay) }));
        await page.goto(`${base}/#/swarm`);
        await page.waitForSelector('.swarm-node');
        check(`${width} replay nodes from actual snapshot`, await page.locator('.swarm-node').count() >= replay.rehearsal.current.members.length);
        check(`${width} replay provenance remains downgraded`, await page.locator('#provenance').innerText().then(text => text.includes('replay')) && await page.locator('#task_live').innerText() === 'not_run');
        await page.locator('.swarm-frame').focus(); await page.keyboard.press('ArrowRight');
        check(`${width} keyboard selects a real member`, await page.locator('.swarm-node-picked').count() === 1);
        await page.keyboard.press('Escape');
        check(`${width} Escape clears member selection`, await page.locator('.swarm-node-picked').count() === 0);
        await page.locator('.swarm-member-list button').first().click();
        check(`${width} readable member control selects actual detail`, await page.locator('.swarm-node-picked').count() === 1 && await page.locator('.swarm-member-list button[aria-pressed=true]').count() === 1);
        await page.screenshot({ path: path.join(output, `replay-${width}-member.png`) });
        await page.locator('.swarm-detail-close').click();
        check(`${width} replay no horizontal overflow`, await page.evaluate(() => document.documentElement.scrollWidth === innerWidth));
        await page.evaluate(() => window.scrollTo(0, 0));
        await page.screenshot({ path: path.join(output, `replay-${width}.png`) });
        await page.screenshot({ path: path.join(output, `replay-${width}-full.png`), fullPage: true });
        await page.close();
      }
    }
    check('no uncaught browser errors', errors.length === 0);
    check('only expected missing EvoMap and injected 503 console errors', consoleErrors.every(item => /404 \(Not Found\)/.test(item.text) && item.url.includes('/api/evomap') || /503 \(Service Unavailable\)/.test(item.text) && item.url.includes('/api/dashboard')));
    check('only same-origin GET requests', badRequests.length === 0);
  } finally {
    fs.writeFileSync(path.join(output, 'result.json'), JSON.stringify({ checks, errors, consoleErrors, badRequests, requests }, null, 2));
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
