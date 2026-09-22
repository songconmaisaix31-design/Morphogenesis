// Finals UI acceptance: replay viewer at 1280x720 / 1920x1080 / 390x844.
// Verifies provenance/mode markers, three giant numbers, topology geometry
// (no clipped/overlapping labels), Gene ledger inside the first viewport, no
// horizontal overflow, event feed truthfulness shape, and reduced-motion.
// Usage: MORPH_PLAYWRIGHT=... MORPH_CHROMIUM=... node tests/t5/check_finals_layout.cjs URL OUTPUT_DIR
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const { chromium } = require(process.env.MORPH_PLAYWRIGHT);
const [url, output] = process.argv.slice(2);
assert(url && output, 'URL OUTPUT_DIR required');
fs.mkdirSync(output, { recursive: true });

const readGeometry = () => {
  const chart = echarts.getInstanceByDom(document.getElementById('story-pipe-chart'));
  const display = chart.getZr().storage.getDisplayList();
  const bounds = (element) => {
    const r = element.getBoundingRect().clone();
    r.applyTransform(element.getComputedTransform());
    return { type: element.type, text: element.style.text, x: r.x, y: r.y, width: r.width, height: r.height };
  };
  return {
    width: chart.getWidth(), height: chart.getHeight(),
    overflow: document.documentElement.scrollWidth > innerWidth,
    geneBottom: document.querySelector('.gene-ledger').getBoundingClientRect().bottom,
    labels: display.filter((e) => e.type === 'tspan').map(bounds),
    nodes: display.filter((e) => e.type === 'path').map(bounds),
  };
};

const assertGeometry = (row, viewportHeight) => {
  assert(!row.overflow, 'horizontal overflow');
  assert(row.geneBottom < viewportHeight, `Gene ledger outside first viewport: ${row.geneBottom}`);
  assert.equal(row.labels.length, 3, 'expected 3 labels');
  assert.equal(row.nodes.length, 3, 'expected 3 nodes');
  for (const item of [...row.labels, ...row.nodes]) {
    assert(item.x >= 0 && item.y >= 0 && item.x + item.width <= row.width && item.y + item.height <= row.height, `clipped ${item.text ?? 'node'}`);
  }
  for (let i = 0; i < row.labels.length; i++) for (let j = i + 1; j < row.labels.length; j++) {
    const a = row.labels[i], b = row.labels[j];
    assert(a.x + a.width <= b.x || b.x + b.width <= a.x || a.y + a.height <= b.y || b.y + b.height <= a.y, 'overlapping labels');
  }
  for (const node of row.nodes) for (const label of row.labels) {
    assert.equal(node.width, node.height, 'expected circle symbol');
    const cx = node.x + node.width / 2, cy = node.y + node.height / 2;
    const dx = cx - Math.max(label.x, Math.min(cx, label.x + label.width));
    const dy = cy - Math.max(label.y, Math.min(cy, label.y + label.height));
    assert(dx * dx + dy * dy >= (node.width / 2) ** 2, `label over circle: ${label.text}`);
  }
};

(async () => {
  const browser = await chromium.launch({ headless: true, executablePath: process.env.MORPH_CHROMIUM });
  const results = [];
  try {
    for (const [width, height] of [[1280, 720], [1920, 1080], [390, 844]]) {
      const page = await browser.newPage({ viewport: { width, height } });
      await page.goto(url);
      await page.waitForFunction(() => document.querySelector('#provenance').textContent.includes('replay'));
      await page.waitForTimeout(1400);
      const state = await page.evaluate(() => ({
        viewport: innerWidth,
        overflow: document.documentElement.scrollWidth > innerWidth,
        badge: document.querySelector('#provenance').textContent,
        mode: document.querySelector('#rehearsal-mode').textContent,
        checkpoint: document.querySelector('#story-checkpoint-rate').textContent,
        tokens: document.querySelector('#metric-tokens').textContent,
        geneCount: document.querySelector('#story-gene-count').textContent,
        members: document.querySelector('#header-members').textContent,
        round: document.querySelector('#header-round').textContent,
        states: ['contract_local', 'interface_live', 'task_live'].map((id) => document.getElementById(id).textContent),
        events: document.querySelectorAll('#event-feed .event-row').length,
        latestAccent: getComputedStyle(document.querySelector('#event-feed .event-row .event-stage')).color,
        genes: document.querySelector('#story-genes').textContent,
      }));
      assert.equal(state.overflow, false, `horizontal overflow at ${width}`);
      assert(/#\d+/.test(state.mode), 'mode missing #seq');
      assert(state.checkpoint.startsWith('3/3'), 'checkpoint rate missing');
      assert.equal(state.tokens, '1226', 'current task tokens should come from the recovery task usage');
      assert.equal(state.geneCount, '0', 'both genes archived in the final snapshot');
      assert.equal(state.members, '4/5', 'online member count (builder#0 offline in this snapshot)');
      assert.equal(state.round, '2 · 恢复', 'task round must not be the snapshot sequence');
      assert(state.events >= 19, 'event feed missing stage history');
      assert(state.genes.includes('已归档'), 'archived gene state missing');
      const geometry = await page.evaluate(readGeometry);
      if (width !== 390) assertGeometry(geometry, height);
      await page.screenshot({ path: path.join(output, `finals-${width}.png`) });
      results.push({ width, height, state: { ...state, genes: undefined }, geometry: { geneBottom: geometry.geneBottom, labels: geometry.labels.length } });
      await page.close();
    }
    // reduced-motion must disable the pass pulse animation path.
    const page = await browser.newPage({ viewport: { width: 1280, height: 720 }, reducedMotion: 'reduce' });
    await page.goto(url);
    await page.waitForFunction(() => document.querySelector('#provenance').textContent.includes('replay'));
    await page.waitForTimeout(800);
    const reduced = await page.evaluate(() => document.querySelector('.morph-board.checkpoint-pulse') === null);
    assert.equal(reduced, true, 'pulse must not run under reduced motion');
    await page.close();

    // Big-number fade: steady 1s polling never animates; a real value change
    // fades exactly once; an identical value does not; reduced-motion never.
    const anim = await browser.newPage({ viewport: { width: 1280, height: 720 } });
    await anim.goto(url);
    await anim.waitForFunction(() => document.querySelector('#provenance').textContent.includes('replay'));
    const animResult = await anim.evaluate(async () => {
      const el = document.getElementById('metric-tokens');
      let starts = 0;
      el.addEventListener('animationstart', () => { starts += 1; });
      const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
      await sleep(2300);                     // steady polling window
      const steady = starts;
      setBigNumber('metric-tokens', '999');  // real change
      await sleep(120);
      const onChange = starts;
      await sleep(1200);                     // next poll restores the real 1226
      const restored = el.textContent;
      const afterRestore = starts;
      setBigNumber('metric-tokens', '1226'); // identical value
      await sleep(500);
      return { steady, onChange, restored, afterRestore, sameValue: starts };
    });
    assert.equal(animResult.steady, 0, 'steady polling must not flash the number');
    assert(animResult.onChange >= 1, 'a real change must fade once');
    assert.equal(animResult.restored, '1226', 'displayed value must follow real data');
    assert(animResult.afterRestore >= animResult.onChange, 'poll-driven change may fade');
    assert.equal(animResult.sameValue, animResult.afterRestore, 'identical value must not re-flash');
    await anim.close();

    const rm = await browser.newPage({ viewport: { width: 1280, height: 720 }, reducedMotion: 'reduce' });
    await rm.goto(url);
    await rm.waitForFunction(() => document.querySelector('#provenance').textContent.includes('replay'));
    const rmResult = await rm.evaluate(async () => {
      const el = document.getElementById('metric-tokens');
      let starts = 0;
      el.addEventListener('animationstart', () => { starts += 1; });
      setBigNumber('metric-tokens', '999');
      await new Promise((r) => setTimeout(r, 500));
      return { starts, flagged: el.classList.contains('num-changed') };
    });
    assert.equal(rmResult.starts, 0, 'no fade under reduced motion');
    assert.equal(rmResult.flagged, false, 'num-changed class must not be set under reduced motion');
    await rm.close();
  } finally { await browser.close(); }
  fs.writeFileSync(path.join(output, 'finals-layout.json'), JSON.stringify(results, null, 2));
  console.log(JSON.stringify(results.map((r) => ({ width: r.width, overflow: r.state.overflow, geneBottom: Math.round(r.geometry.geneBottom), checkpoint: r.state.checkpoint, tokens: r.state.tokens }))));
})().catch((error) => { console.error(error); process.exitCode = 1; });
