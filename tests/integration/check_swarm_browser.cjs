const fs = require('node:fs');
const http = require('node:http');
const os = require('node:os');
const path = require('node:path');

const playwrightPath = process.env.MORPH_PLAYWRIGHT;
const chromiumPath = process.env.MORPH_CHROMIUM;
if (!playwrightPath || !chromiumPath) throw new Error('MORPH_PLAYWRIGHT and MORPH_CHROMIUM are required');
const { chromium } = require(playwrightPath);

const root = path.resolve(__dirname, '..', '..', 'viz', 'static');
const screenshots = path.join(os.tmpdir(), 'morph-swarm-viz-browser');
fs.mkdirSync(screenshots, { recursive: true });

const emptyDashboard = {
  schema: 'morph.dashboard/1', provenance: 'mock', source_label: '未加载导出',
  acceptance: { contract_local: 'not_run', interface_live: 'not_run', task_live: 'not_run' },
  rehearsal: null, notes: [],
};
const workers = Array.from({ length: 16 }, (_, index) => ({ worker_id: `worker-${String(index + 1).padStart(2, '0')}`, state: index % 3 ? 'idle' : 'done' }));
const tasks = Array.from({ length: 96 }, (_, index) => ({
  task_id: `task-${String(index + 1).padStart(3, '0')}`, capability: `capability-${(index % 4) + 1}`,
  lease_state: index % 5 ? 'completed' : 'leased', status: index % 5 ? 'completed' : 'claimed',
  owner: workers[index % workers.length].worker_id, dependencies: index ? [`task-${String(index).padStart(3, '0')}`] : [], attempts: 1,
}));
const richSwarm = {
  schema: 'morph.swarm.readonly/1', observed_at: 1790208000, readonly: true, health: 'ok',
  hub_status: '待发布（未配置 Hub 沙箱）',
  acceptance: { provenance: 'replay', contract_local: 'not_run', interface_live: 'not_run', task_live: 'not_run' },
  sources: { ledger: { state: 'ok' }, field: { state: 'ok' }, validation: { state: 'ok' } },
  workers, tasks,
  routes: workers.map((worker, index) => ({ worker_id: worker.worker_id, pipe_key: `capability-${(index % 4) + 1}`, weight: 1, decayed_weight: 0.82, samples: 3 })),
  signals: [{ signal_id: 'signal-1', task_id: 'task-002', concentration: 1, decayed_concentration: 0.74 }],
  budget: { reservations: [{ reservation_id: 'r1', task_id: 'task-002', state: 'unknown_cost_allowed', reserved_usd: 0.01, tokens: 420, usage_metering: 'verified', cost: 'unknown' }] },
  audit: [{ sequence: 1, event: 'task_claimed', task_id: 'task-002' }],
  worker_audit: [{ worker_id: 'worker-01', task_id: 'task-001', provenance: 'live' }],
  assets: [{ execution_id: 'e1', asset_id: 'sha256:source', candidate_asset_id: 'sha256:candidate', worker_id: 'worker-01', task_id: 'task-001', result_id: 'result-1' }],
  promotions: [], boundaries: [],
};
const missingSwarm = { ...richSwarm, health: 'missing', acceptance: { ...richSwarm.acceptance, provenance: 'unverified' }, workers: [], tasks: [], routes: [], signals: [], audit: [], worker_audit: [], assets: [], notes: ['当前没有可读取的蜂群状态。'] };
let swarmMode = 'rich';

const mime = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8', '.woff2': 'font/woff2' };
const server = http.createServer((request, response) => {
  const pathname = new URL(request.url, 'http://127.0.0.1').pathname;
  if (pathname === '/api/dashboard') return json(response, 200, emptyDashboard);
  if (pathname === '/api/evomap') return json(response, 200, {
    schema: 'morph.evomap.readonly/1', generated_at: 1790208000,
    hub: { status: 'pending' },
    community_search: { state: 'missing', source: 'none', error: null, genes: [], notes: [] },
    community_categories: { state: 'missing', source: 'none', error: null, categories: [], notes: [] },
    local_pool: { state: 'missing', source: 'none', error: null, genes: [], notes: [] }, boundaries: [],
  });
  if (pathname === '/favicon.ico') { response.writeHead(204); response.end(); return; }
  if (pathname === '/vendor/echarts.min.js') {
    response.writeHead(200, { 'Content-Type': 'text/javascript; charset=utf-8' });
    response.end('window.echarts={init:()=>({setOption(){},resize(){},dispose(){}}),getInstanceByDom:()=>null};'); return;
  }
  if (pathname === '/api/swarm') {
    if (swarmMode === 'error') return json(response, 503, { notes: ['蜂群只读观察暂时失败，请稍后重试。'] });
    return json(response, 200, swarmMode === 'missing' ? missingSwarm : richSwarm);
  }
  const relative = pathname === '/' ? 'index.html' : pathname.slice(1);
  const file = path.resolve(root, relative);
  if (!file.startsWith(root) || !fs.existsSync(file) || !fs.statSync(file).isFile()) {
    response.writeHead(404); response.end(); return;
  }
  response.writeHead(200, { 'Content-Type': mime[path.extname(file)] || 'application/octet-stream' });
  fs.createReadStream(file).pipe(response);
});
function json(response, status, value) {
  const body = Buffer.from(JSON.stringify(value));
  response.writeHead(status, { 'Content-Type': 'application/json', 'Content-Length': body.length, 'Cache-Control': 'no-store' });
  response.end(body);
}

(async () => {
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
  const base = `http://127.0.0.1:${server.address().port}/#/swarm`;
  const browser = await chromium.launch({ executablePath: chromiumPath, headless: true });
  try {
    for (const width of [1366, 1920, 375]) {
      swarmMode = 'rich';
      const page = await browser.newPage({ viewport: { width, height: width === 375 ? 812 : 900 }, reducedMotion: 'reduce' });
      const errors = [];
      page.on('console', (message) => { if (message.type() === 'error') errors.push(`${message.text()} @ ${message.location().url}`); });
      page.on('response', (response) => { if (response.status() >= 400) errors.push(`HTTP ${response.status()} ${response.url()}`); });
      page.on('pageerror', (error) => errors.push(error.message));
      await page.goto(base, { waitUntil: 'networkidle' });
      await page.getByText('GHOST IN THE SWARM').waitFor();
      await page.getByText('历史回放').first().waitFor();
      await page.getByText('采用谱系（1）').waitFor();
      await page.getByText('16 worker · 96 task').waitFor();
      await page.getByText(/显示 \d+ \/ 118 实体/).waitFor();
      await page.getByText('用量已确认 420 tokens').waitFor();
      await page.getByText('费用未知（本轮允许继续）').waitFor();
      if (await page.getByText('未发生 / 未加载').count()) throw new Error('legacy rehearsal heading overwrote swarm heading');
      if (await page.getByText('没有中心 planner 节点').count()) throw new Error('planner disclaimer leaked into product copy');
      if (await page.getByText(/涌现或收敛/).count()) throw new Error('engineering disclaimer leaked into product copy');
      const workerNode = page.getByRole('button', { name: 'worker worker-01' });
      await workerNode.focus(); await page.keyboard.press('Enter');
      await page.getByText('worker-01', { exact: true }).last().waitFor();
      await page.keyboard.press('Escape');
      if (await page.getByRole('button', { name: '关闭拓扑实体详情' }).count()) throw new Error('Escape did not clear topology selection');
      for (const kind of ['worker', 'capability', 'task', 'asset']) {
        if (!await page.locator(`.swarm-node-${kind}`).count()) throw new Error(`${width}px ${kind} node is unreachable`);
      }
      await page.getByRole('button', { name: '下一组' }).click();
      await page.getByText('第 2 / 12 组').waitFor();
      await page.getByRole('button', { name: 'task task-009' }).waitFor();
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
      if (overflow > 1) throw new Error(`${width}px horizontal overflow: ${overflow}`);
      if (errors.length) throw new Error(`${width}px console errors: ${errors.join(' | ')}`);
      await page.screenshot({ path: path.join(screenshots, `swarm-${width}.png`), fullPage: true });
      if (width === 1366) {
        swarmMode = 'error';
        await page.getByText('陈旧快照 · 更新失败').waitFor({ timeout: 4000 });
         await page.getByRole('button', { name: 'task task-009' }).waitFor();
         swarmMode = 'rich';
         await page.getByText('陈旧快照 · 更新失败').waitFor({ state: 'detached', timeout: 4000 });
         await page.getByText('只读快照').waitFor();
      }
      await page.close();
    }
    swarmMode = 'missing';
    const page = await browser.newPage({ viewport: { width: 1366, height: 900 } });
    await page.goto(base, { waitUntil: 'networkidle' });
    await page.getByLabel('去中心化蜂群').getByText('状态源缺失').waitFor();
    if (await page.getByText('规划器').count()) throw new Error('missing state rendered planner copy');
    await page.screenshot({ path: path.join(screenshots, 'swarm-missing.png'), fullPage: true });
    await page.close();
    swarmMode = 'error';
    const errorPage = await browser.newPage({ viewport: { width: 1366, height: 900 } });
    await errorPage.goto(base, { waitUntil: 'networkidle' });
    await errorPage.getByLabel('去中心化蜂群').getByText('观察失败', { exact: true }).waitFor();
    await errorPage.getByText(/蜂群只读观察暂时失败，请稍后重试。/).last().waitFor();
    await errorPage.screenshot({ path: path.join(screenshots, 'swarm-error.png'), fullPage: true });
    await errorPage.close();
    console.log(JSON.stringify({ ok: true, screenshots }));
  } finally {
    await browser.close();
    await new Promise((resolve) => server.close(resolve));
  }
})().catch((error) => { console.error(error); process.exitCode = 1; });
