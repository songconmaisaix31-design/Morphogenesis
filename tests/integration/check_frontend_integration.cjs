// Whole-page integration acceptance for the merged frontend tracks (P+T+S+E).
// Real Chromium against a local viz.server serving the mock fixture (page is
// labelled mock). EvoMap panel queries hit the server-side read-only Hub loop
// (public endpoints, already authorized); the browser itself must stay
// same-origin — any non-local request is aborted and counted.
// Usage: MORPH_PLAYWRIGHT=... MORPH_CHROMIUM=... node tests/integration/check_frontend_integration.cjs URL OUTPUT_DIR
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const { withoutGatewayKey } = require('./rehearsal_browser.cjs');
for (const key of Object.keys(process.env)) if (key.toUpperCase() === 'MORPH_EVOMAP_API_KEY') delete process.env[key];
const { chromium } = require(process.env.MORPH_PLAYWRIGHT);
const [url, output] = process.argv.slice(2);
assert(url && output && !fs.existsSync(output), 'usage: URL NEW_OUTPUT_DIR');
fs.mkdirSync(output, { recursive: true });

const results = [];
function record(name, ok, detail = '') {
  results.push({ name, ok, detail });
  console.log(`${ok ? 'PASS' : 'FAIL'} ${name}${detail ? ` — ${detail}` : ''}`);
}

(async () => {
  const browser = await chromium.launch({ headless: true, executablePath: process.env.MORPH_CHROMIUM, env: withoutGatewayKey(process.env) });
  try {
    const page = await browser.newPage({ viewport: { width: 1366, height: 768 } });
    const errors = [], external = [];
    let dashboardReads = 0, evomapReads = 0;
    page.on('pageerror', (error) => errors.push(error.message));
    await page.route('**/*', (route) => {
      const request = new URL(route.request().url());
      if (request.origin !== url) { external.push(request.href); return route.abort(); }
      if (request.pathname === '/api/dashboard') dashboardReads++;
      if (request.pathname === '/api/evomap') evomapReads++;
      return route.continue();
    });

    // 1. Load: hero is the only big word, physarum view active, CRT veil on.
    await page.goto(url, { waitUntil: 'domcontentloaded' });
    await page.waitForSelector('.morph-hero-title', { timeout: 20000 });
    const title = await page.textContent('.morph-hero-title');
    record('hero title MORPHOGENESIS', title.trim() === 'MORPHOGENESIS', title.trim());
    const titleCount = await page.locator('.morph-hero-title').count();
    record('single hero title', titleCount === 1, `count=${titleCount}`);
    const view0 = await page.evaluate(() => document.body.dataset.view);
    record('default view physarum', view0 === 'physarum', view0);
    await page.waitForSelector('.crt-overlay', { timeout: 10000 });
    const crtStyle = await page.evaluate(() => {
      const el = document.querySelector('.crt-overlay');
      const cs = getComputedStyle(el);
      return { pointerEvents: cs.pointerEvents, opacity: Number(cs.opacity) };
    });
    record('CRT overlay pointer-events none, opacity 0.03-0.05',
      crtStyle.pointerEvents === 'none' && crtStyle.opacity >= 0.03 && crtStyle.opacity <= 0.05,
      JSON.stringify(crtStyle));

    // 2. Physarum field: real WebGL canvas or honestly labelled fallback;
    //    pointer moves over the title area and the field raise no errors.
    await page.waitForTimeout(1500); // let the P-track module load and start
    const fieldKind = await page.evaluate(() => ({
      canvas: Boolean(document.querySelector('canvas.physarum-canvas')),
      fallback: Boolean(document.querySelector('.physarum-fallback')),
      heroNote: Boolean(document.querySelector('.morph-hero-note')),
    }));
    record('physarum canvas present (no fallback note)', fieldKind.canvas && !fieldKind.heroNote, JSON.stringify(fieldKind));
    const heroBox = await page.locator('.morph-hero').boundingBox();
    for (const [fx, fy] of [[0.5, 0.5], [0.5, 0.35], [0.3, 0.6], [0.7, 0.4], [0.5, 0.8]]) {
      await page.mouse.move(heroBox.x + heroBox.width * fx, heroBox.y + heroBox.height * fy, { steps: 6 });
      await page.waitForTimeout(120);
    }
    record('pointermove over title-covered field, no pageerror so far', errors.length === 0, errors.join(' | '));
    await page.screenshot({ path: path.join(output, '01-physarum-hero.png') });

    // 3. Switch to AGENT SWARM via the hero marker (first screen hides the
    //    header by design; the two hero markers are the normal-state switch).
    const heroSwitchVisible = await page.locator('.morph-hero-markers .morph-marker:text-is("AGENT SWARM")').isVisible();
    record('hero AGENT SWARM marker visible on first screen', heroSwitchVisible);
    await page.click('.morph-hero-markers .morph-marker:text-is("AGENT SWARM")');
    await page.waitForFunction(() => document.body.dataset.view === 'swarm', null, { timeout: 10000 });
    const navVisible = await page.locator('.morph-nav .morph-marker:text-is("PHYSARUM")').isVisible();
    record('header nav visible in swarm view', navVisible);
    await page.waitForFunction(() => document.getElementById('provenance')?.textContent !== '加载中', null, { timeout: 15000 });
    const provenance = await page.textContent('#provenance');
    record('dashboard provenance rendered (mock fixture)', /mock/i.test(provenance), provenance.trim());
    const moduleState = await page.evaluate(() => document.body.dataset.swarmModule);
    record('swarm module loaded (T track wired)', moduleState === 'loaded', moduleState);
    await page.waitForSelector('section[aria-label="Agent Swarm 拓扑"]', { timeout: 10000 });
    // mock fixture has no rehearsal snapshot: the honest empty state with a
    // provenance badge is the correct render — no fabricated nodes/edges.
    const topoState = await page.evaluate(() => ({
      badge: document.querySelector('.swarm-badge')?.textContent ?? '',
      stateMsg: document.querySelector('.swarm-state')?.textContent ?? '',
      nodes: document.querySelectorAll('.swarm-svg .swarm-node, .swarm-svg g[class*="node"]').length,
    }));
    record('topology honest state with provenance badge', Boolean(topoState.badge), JSON.stringify(topoState).slice(0, 160));
    const acceptance = await page.evaluate(() => ({
      contract: document.getElementById('contract_local')?.textContent,
      source: document.getElementById('source-label')?.textContent,
    }));
    record('acceptance strip + source label present', Boolean(acceptance.contract && acceptance.source), JSON.stringify(acceptance).slice(0, 160));
    await page.screenshot({ path: path.join(output, '02-swarm-topology.png') });

    // 4. EvoMap panel: one automatic load on first entry, then two distinct
    //    manual queries; real Hub data with explicit source/state labels.
    await page.waitForSelector('.morph-evomap-state', { timeout: 60000 });
    await page.waitForFunction(() => {
      const chip = document.querySelector('.morph-evomap-state');
      return chip && /live|cache|stale|error/.test(chip.textContent);
    }, null, { timeout: 60000 });
    const autoState = await page.textContent('.morph-evomap-state');
    record('evomap auto-load on first swarm entry', /live|cache/.test(autoState), autoState.trim());
    const hubLine = await page.textContent('.morph-evomap-body .morph-evomap-line');
    record('hub source line (public, key boolean only)', /evomap\.ai/.test(hubLine) && /API key 未配置/.test(hubLine), hubLine.trim().slice(0, 120));
    const catCount = await page.locator('.morph-evomap-cats .morph-evomap-cat').count();
    record('community categories real counts visible', catCount > 0, `chips=${catCount}`);
    const boundaryCount = await page.locator('.morph-evomap-boundaries li').count();
    record('boundary declarations listed', boundaryCount >= 5, `count=${boundaryCount}`);
    const poolLine = await page.evaluate(() => {
      const lines = [...document.querySelectorAll('.morph-evomap-section .morph-evomap-line')].map((el) => el.textContent);
      return lines.find((line) => line.includes('本地 Gene 池') || line.includes('未配置')) ?? '';
    });
    record('local pool honestly unconfigured', /未配置/.test(poolLine), poolLine.slice(0, 80));

    const doSearch = async (q, type, limit) => {
      await page.fill('.morph-evomap-form input[type="search"]', q);
      await page.selectOption('.morph-evomap-form select[aria-label="资产类型"]', type);
      await page.selectOption('.morph-evomap-form select[aria-label="条数上限"]', String(limit));
      await page.click('.morph-evomap-form button[type="submit"]');
      await page.waitForFunction(
        ([eq, et]) => {
          const line = [...document.querySelectorAll('.morph-evomap-section .morph-evomap-line')]
            .map((el) => el.textContent).find((t) => t.includes('查询 q='));
          if (!line || !line.includes(`q=“${eq}”`)) return false;
          if (et && !line.includes(`type=${et}`)) return false;
          const chip = document.querySelector('.morph-evomap-state');
          return chip && /live|cache|stale|error/.test(chip.textContent)
            && ![...document.querySelectorAll('.morph-evomap-line')].some((el) => el.textContent === '正在读取 EvoMap 状态…');
        },
        [q, type], { timeout: 60000 },
      );
      return page.evaluate(() => ({
        chip: document.querySelector('.morph-evomap-state')?.textContent ?? '',
        queryLine: [...document.querySelectorAll('.morph-evomap-section .morph-evomap-line')]
          .map((el) => el.textContent).find((t) => t.includes('查询 q=')) ?? '',
        assets: document.querySelectorAll('.morph-evomap-asset').length,
        assetIds: [...document.querySelectorAll('.morph-evomap-id')].slice(0, 3).map((el) => el.getAttribute('title') ?? ''),
      }));
    };
    const search1 = await doSearch('optimize', '', '5');
    record('manual query q=optimize limit=5 returns real assets', /live|cache/.test(search1.chip) && search1.assets > 0 && search1.assetIds.every((id) => id.startsWith('sha256:')), JSON.stringify({ chip: search1.chip, assets: search1.assets }));
    const search2 = await doSearch('repair', 'Capsule', '5');
    record('manual query type=Capsule echo + state', /live|cache/.test(search2.chip) && search2.queryLine.includes('type=Capsule'), JSON.stringify({ chip: search2.chip, assets: search2.assets, line: search2.queryLine.slice(0, 80) }));
    await page.screenshot({ path: path.join(output, '03-evomap-explorer.png'), fullPage: false });
    // EvoMap panel must not leak into the topology zone.
    const crossCheck = await page.evaluate(() => ({
      evomapInsideTopology: Boolean(document.querySelector('.morph-topology .morph-evomap')),
      topoBadgeStill: document.querySelector('.swarm-badge')?.textContent ?? '',
    }));
    record('evomap data never enters topology panel', !crossCheck.evomapInsideTopology && Boolean(crossCheck.topoBadgeStill), JSON.stringify(crossCheck).slice(0, 120));

    // 5. Repeated switching: hero marker (physarum side) + nav marker (swarm
    //    side) x5, then keyboard 1/2; DOM stays single.
    for (let i = 0; i < 5; i++) {
      await page.click('.morph-nav .morph-marker:text-is("PHYSARUM")');
      await page.waitForFunction(() => document.body.dataset.view === 'physarum', null, { timeout: 5000 });
      await page.click('.morph-hero-markers .morph-marker:text-is("AGENT SWARM")');
      await page.waitForFunction(() => document.body.dataset.view === 'swarm', null, { timeout: 5000 });
    }
    await page.keyboard.press('1');
    await page.waitForFunction(() => document.body.dataset.view === 'physarum', null, { timeout: 5000 });
    await page.keyboard.press('2');
    await page.waitForFunction(() => document.body.dataset.view === 'swarm', null, { timeout: 5000 });
    const dupes = await page.evaluate(() => {
      const seen = new Map();
      for (const el of document.querySelectorAll('[id]')) seen.set(el.id, (seen.get(el.id) ?? 0) + 1);
      return [...seen.entries()].filter(([, n]) => n > 1).map(([id]) => id);
    });
    record('5x marker switch + keyboard 1/2, no duplicate ids', dupes.length === 0, dupes.join(','));
    record('no pageerror after whole flow', errors.length === 0, errors.slice(0, 3).join(' | '));

    // 6. CRT toggle persists via localStorage.
    await page.click('.morph-crt-toggle');
    const crtOff = await page.evaluate(() => ({ overlay: Boolean(document.querySelector('.crt-overlay')), stored: localStorage.getItem('morph-crt') }));
    record('CRT toggle off removes overlay + persists', !crtOff.overlay && crtOff.stored === 'off', JSON.stringify(crtOff));
    await page.click('.morph-crt-toggle');
    await page.waitForSelector('.crt-overlay', { timeout: 5000 });
    record('CRT toggle back on', true);

    // 7. Reduced motion: static fallback field, static CRT, switching intact.
    const reduced = await browser.newPage({ viewport: { width: 1366, height: 768 }, reducedMotion: 'reduce' });
    const reducedErrors = [];
    reduced.on('pageerror', (error) => reducedErrors.push(error.message));
    await reduced.goto(url, { waitUntil: 'domcontentloaded' });
    await reduced.waitForSelector('.morph-hero-title', { timeout: 20000 });
    await reduced.waitForTimeout(1200);
    const reducedState = await reduced.evaluate(() => ({
      fallback: Boolean(document.querySelector('.physarum-fallback')),
      canvas: Boolean(document.querySelector('canvas.physarum-canvas')),
      crtStatic: document.querySelector('.crt-overlay')?.classList.contains('is-static') ?? false,
    }));
    record('reduced motion: static fallback, no canvas, static CRT', reducedState.fallback && !reducedState.canvas && reducedState.crtStatic, JSON.stringify(reducedState));
    await reduced.click('.morph-hero-markers .morph-marker:text-is("AGENT SWARM")');
    await reduced.waitForFunction(() => document.body.dataset.view === 'swarm', null, { timeout: 5000 });
    record('reduced motion: switch works, no pageerror', reducedErrors.length === 0, reducedErrors.slice(0, 2).join(' | '));
    await reduced.screenshot({ path: path.join(output, '04-reduced-motion.png') });
    await reduced.close();

    record('browser stayed same-origin (server-side Hub only)', external.length === 0, external.slice(0, 3).join(' | '));
    await page.screenshot({ path: path.join(output, '05-final-swarm.png') });
    await page.close();

    const summary = {
      url, when: new Date().toISOString(),
      viewport: '1366x768', dashboardReads, evomapReads, externalRequests: external,
      pageerrors: errors, results,
      passed: results.filter((r) => r.ok).length, failed: results.filter((r) => !r.ok).length,
    };
    fs.writeFileSync(path.join(output, 'summary.json'), JSON.stringify(summary, null, 2));
    console.log(`\n${summary.passed} passed, ${summary.failed} failed; evidence in ${output}`);
    if (summary.failed) process.exitCode = 1;
  } finally {
    await browser.close();
  }
})().catch((error) => {
  console.error('acceptance aborted:', error);
  process.exitCode = 1;
});
