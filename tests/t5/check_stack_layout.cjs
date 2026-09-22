// T5 Stack-layout acceptance: replay viewer at 1366x768 / 1920x1080 / 390x844.
// Checks sidebar navigation, dark/light toggle persistence, no horizontal
// overflow, and captures real Chromium screenshots. Read-only against the page.
// Usage: MORPH_PLAYWRIGHT=... MORPH_CHROMIUM=... node tests/t5/check_stack_layout.cjs URL OUTPUT_DIR
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const { chromium } = require(process.env.MORPH_PLAYWRIGHT);
const [url, output] = process.argv.slice(2);
assert(url && output, 'URL OUTPUT_DIR required');
fs.mkdirSync(output, { recursive: true });

(async () => {
  const browser = await chromium.launch({ headless: true, executablePath: process.env.MORPH_CHROMIUM });
  const results = [];
  try {
    for (const [width, height] of [[1366, 768], [1920, 1080], [390, 844]]) {
      const page = await browser.newPage({ viewport: { width, height } });
      await page.goto(url);
      await page.waitForFunction(() => document.querySelector('#provenance').textContent.includes('replay'));
      await page.waitForTimeout(1400);
      const state = await page.evaluate(() => ({
        viewport: innerWidth,
        overflow: document.documentElement.scrollWidth > innerWidth,
        menuLinks: [...document.querySelectorAll('#main-menu a')].map((a) => a.getAttribute('href')),
        scheme: document.documentElement.dataset.scheme,
        stored: localStorage.getItem('StackColorScheme'),
        badge: document.querySelector('#provenance').textContent,
        mode: document.querySelector('#rehearsal-mode').textContent,
        states: ['contract_local', 'interface_live', 'task_live'].map((id) => document.getElementById(id).textContent),
        attribution: document.querySelector('.site-footer .powerby').textContent,
      }));
      assert.equal(state.overflow, false, `horizontal overflow at ${width}`);
      assert(state.menuLinks.includes('#rehearsal-board') && state.menuLinks.includes('#acceptance-widget'), 'sidebar nav missing anchors');
      assert(state.attribution.includes('Hugo Theme Stack'), 'theme attribution missing');
      await page.screenshot({ path: path.join(output, `stack-${width}-light.png`) });

      // Toggle to the dark scheme; it must flip data-scheme and persist.
      if (width === 390) {
        await page.click('#toggle-menu');
        await page.waitForSelector('#main-menu.show');
      }
      await page.click('#dark-mode-toggle');
      await page.waitForFunction(() => document.documentElement.dataset.scheme === 'dark');
      await page.waitForTimeout(1200);
      const dark = await page.evaluate(() => ({
        scheme: document.documentElement.dataset.scheme,
        stored: localStorage.getItem('StackColorScheme'),
        overflow: document.documentElement.scrollWidth > innerWidth,
      }));
      assert.equal(dark.stored, 'dark', 'StackColorScheme not persisted');
      assert.equal(dark.overflow, false, `horizontal overflow in dark at ${width}`);
      await page.screenshot({ path: path.join(output, `stack-${width}-dark.png`) });
      results.push({ width, height, ...state, dark });

      // Narrow-screen navigation: the acceptance widget must be genuinely
      // reachable — clicking the menu anchor scrolls it into the viewport and
      // closes the menu. Keyboard: Enter on the hamburger opens (and reports
      // aria-expanded), Escape closes.
      if (width === 390) {
        if (!(await page.evaluate(() => document.querySelector('#main-menu').classList.contains('show')))) {
          await page.click('#toggle-menu');
        }
        await page.waitForSelector('#main-menu.show');
        await page.click('#main-menu a[href="#acceptance-widget"]');
        await page.waitForTimeout(600);
        const nav = await page.evaluate(() => {
          const rect = document.querySelector('#acceptance-widget').getBoundingClientRect();
          return {
            targetVisible: rect.top < innerHeight && rect.bottom > 0,
            menuOpen: document.querySelector('#main-menu').classList.contains('show'),
            statesText: document.querySelector('#acceptance-widget').textContent,
          };
        });
        assert.equal(nav.targetVisible, true, 'acceptance widget not visible after menu anchor click');
        assert.equal(nav.menuOpen, false, 'menu stayed open over the anchor target');
        assert(nav.statesText.includes('task_live'), 'acceptance states unreachable on phone');
        await page.focus('#toggle-menu');
        await page.keyboard.press('Enter');
        await page.waitForSelector('#main-menu.show');
        assert.equal(await page.getAttribute('#toggle-menu', 'aria-expanded'), 'true', 'aria-expanded not set');
        assert.equal(await page.getAttribute('#toggle-menu', 'aria-controls'), 'main-menu', 'aria-controls missing');
        await page.keyboard.press('Escape');
        await page.waitForFunction(() => !document.querySelector('#main-menu').classList.contains('show'));
        assert.equal(await page.getAttribute('#toggle-menu', 'aria-expanded'), 'false', 'aria-expanded not cleared');
        results.at(-1).mobileNav = { anchorVisible: true, keyboard: true };
      }
      await page.close();
    }
  } finally { await browser.close(); }
  fs.writeFileSync(path.join(output, 'stack-layout.json'), JSON.stringify(results, null, 2));
  console.log(JSON.stringify(results.map((r) => ({ width: r.width, overflow: r.overflow, scheme: r.scheme, dark: r.dark.scheme }))));
})().catch((error) => { console.error(error); process.exitCode = 1; });
