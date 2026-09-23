// Browser acceptance for the immersive intro and read-only workspace.
// Usage: MORPH_PLAYWRIGHT=... MORPH_CHROMIUM=... node this-file URL OUTPUT_DIR
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require(process.env.MORPH_PLAYWRIGHT);

const [base, output] = process.argv.slice(2);
assert(base && output && !fs.existsSync(output), 'URL and a new output directory required');
fs.mkdirSync(output, { recursive: true });

(async () => {
  const browser = await chromium.launch({ executablePath: process.env.MORPH_CHROMIUM, headless: true });
  const errors = [];
  const consoleErrors = [];
  const failures = [];
  const check = (name, actual) => { assert(actual, name); console.log(`PASS ${name}`); };
  const makePage = async (width, height, reducedMotion = 'no-preference') => {
    const page = await browser.newPage({ viewport: { width, height }, reducedMotion });
    page.on('pageerror', (error) => errors.push(error.message));
    page.on('console', (message) => { if (message.type() === 'error') consoleErrors.push({ text: message.text(), location: message.location() }); });
    page.on('response', (response) => {
      if (response.status() >= 400 && !response.url().includes('/api/evomap')) failures.push(`${response.status()} ${response.url()}`);
    });
    await page.route('**/*', (route) => {
      if (new URL(route.request().url()).origin !== new URL(base).origin) {
        failures.push(`external ${route.request().url()}`);
        return route.abort();
      }
      return route.continue();
    });
    await page.route('**/api/evomap*', (route) => route.fulfill({ status: 404, contentType: 'application/json', body: '{}' }));
    return page;
  };
  try {
    const page = await makePage(1366, 768);
    await page.goto(`${base}/#/physarum`, { waitUntil: 'domcontentloaded' });
    await page.waitForSelector('canvas.physarum-canvas', { timeout: 20000 });
    check('small bilingual Physarum caption', await page.locator('.morph-hero').innerText().then((text) => text.includes('黏菌') && text.includes('PHYSARUM')));
    check('no early workspace CTA', !(await page.locator('.story-enter').isVisible()));
    await page.screenshot({ path: path.join(output, '01-physarum-1366.png') });
    await page.waitForTimeout(5700);
    check('concept growth scene and caption', await page.locator('.growth-intro').getAttribute('data-concept-animation') === 'true' && await page.locator('.growth-intro').innerText().then((text) => text.includes('自生长') && text.includes('AGENT SWARM') && text.includes('概念动画')));
    await page.screenshot({ path: path.join(output, '02-growth-1366.png') });
    await page.waitForTimeout(2300);
    check('large bilingual product title', await page.locator('.story-product.is-visible h1').innerText().then((text) => text.includes('形态发生') && text.includes('MORPHOGENESIS')));
    await page.screenshot({ path: path.join(output, '03-product-1366.png') });
    await page.waitForSelector('.story-enter.is-visible:not([disabled])', { timeout: 3000 });
    check('CTA is readable as soon as it is enabled', await page.locator('.story-enter').evaluate((el) => {
      const style = getComputedStyle(el);
      return style.opacity === '1' && style.color === 'rgb(245, 213, 71)' && el.getBoundingClientRect().height >= 44;
    }));
    await page.keyboard.press('Tab');
    check('CTA is keyboard focusable', await page.evaluate(() => document.activeElement?.classList.contains('story-enter')));
    await page.locator('.story-enter').hover();
    await page.waitForTimeout(300);
    check('CTA hover has a visible background', await page.locator('.story-enter').evaluate((el) => getComputedStyle(el).backgroundColor !== 'rgba(0, 0, 0, 0)'));
    await page.waitForTimeout(1800); // capture the settled CTA, not its fade-in frame
    await page.screenshot({ path: path.join(output, '04-enter-1366.png') });
    await page.locator('.story-enter').click();
    await page.waitForFunction(() => document.body.dataset.view === 'workspace');
    check('CTA opens workspace hash', new URL(page.url()).hash === '#/workspace');
    await page.waitForFunction(() => document.querySelector('#provenance')?.textContent?.includes('mock'), null, { timeout: 15000 });
    await page.waitForTimeout(500); // the workspace crossfade settles
    check('mock provenance and three acceptance states retained', await page.locator('#contract_local, #interface_live, #task_live').count() === 3);
    check('real topology has honest empty state', await page.locator('.swarm-badge').count() === 1);
    await page.screenshot({ path: path.join(output, '05-workspace-1366.png') });
    const workspaceOverflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth);
    check('desktop has no horizontal overflow', !workspaceOverflow);
    const wide = await makePage(1920, 1080);
    await wide.goto(`${base}/#/workspace`, { waitUntil: 'domcontentloaded' });
    await wide.waitForSelector('.backend-main');
    await wide.screenshot({ path: path.join(output, '06-workspace-1920.png') });
    check('workspace deep link', await wide.evaluate(() => document.body.dataset.view === 'workspace'));
    const phone = await makePage(375, 812, 'reduce');
    await phone.goto(`${base}/#/physarum`, { waitUntil: 'domcontentloaded' });
    await phone.waitForSelector('.story-enter.is-visible:not([disabled])');
    await phone.screenshot({ path: path.join(output, '07-intro-375-reduced.png') });
    check('reduced motion exposes CTA immediately', await phone.locator('.story-product.is-visible').count() === 1);
    check('phone intro no horizontal overflow', await phone.evaluate(() => document.documentElement.scrollWidth === innerWidth));
    await phone.locator('.story-enter').click();
    await phone.waitForFunction(() => document.body.dataset.view === 'workspace');
    await phone.screenshot({ path: path.join(output, '08-workspace-375.png') });
    check('phone workspace no horizontal overflow', await phone.evaluate(() => document.documentElement.scrollWidth === innerWidth));
    const alias = await makePage(1366, 768);
    await alias.goto(`${base}/#/swarm`, { waitUntil: 'domcontentloaded' });
    check('legacy swarm hash opens workspace', await alias.evaluate(() => document.body.dataset.view === 'workspace'));
    check('no uncaught browser errors', errors.length === 0);
    check('no unexpected browser console errors',
      consoleErrors.every(({ text, location }) => /404 \(Not Found\)/.test(text) && location.url.includes('/api/evomap')));
    check('no unexpected HTTP failures', failures.length === 0);
    console.log(`PASS screenshots ${output}`);
  } finally {
    await browser.close();
  }
})().catch((error) => { console.error(error); process.exitCode = 1; });
