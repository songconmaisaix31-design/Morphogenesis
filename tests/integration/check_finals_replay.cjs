// Read-only historical replay. Never invokes run-demo, an executor, or a gateway.
// MORPH_PYTHON, MORPH_PLAYWRIGHT, MORPH_CHROMIUM must identify installed tools.
// node tests/integration/check_finals_replay.cjs SOURCE_REHEARSAL NEW_OUTPUT [--prepare-only]
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const net = require('node:net');
const crypto = require('node:crypto');
const {spawn} = require('node:child_process');
const assert = require('node:assert/strict');
const {withoutGatewayKey, readGeometry, assertGeometry} = require('./rehearsal_browser.cjs');
const pause = ms => new Promise(resolve => setTimeout(resolve, ms));
const agentName = agent => `${agent.role}#${agent.instance}`;
const write = (file, value) => fs.writeFileSync(file, JSON.stringify(value, null, 2));

function inventory(root) {
  return fs.readdirSync(root, {recursive: true}).sort().flatMap(relative => {
    const file = path.join(root, relative), stat = fs.lstatSync(file, {bigint: true});
    assert(!stat.isSymbolicLink(), `Unexpected source link: ${relative}`);
    return stat.isFile() ? [{relative, bytes: String(stat.size), mtimeNs: String(stat.mtimeNs),
      sha256: crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex')}] : [];
  });
}

async function freePort() {
  const socket = net.createServer();
  await new Promise((resolve, reject) => { socket.once('error', reject); socket.listen(0, '127.0.0.1', resolve); });
  const port = socket.address().port;
  await new Promise(resolve => socket.close(resolve));
  assert(![7526, 7527].includes(port));
  return port;
}

function observe() {
  const get = id => document.getElementById(id);
  const chart = echarts.getInstanceByDom(get('story-pipe-chart'));
  const series = chart?.getOption().series[0];
  const rect = element => {
    const r = element.getBoundingClientRect();
    return {x:r.x,y:r.y,width:r.width,height:r.height,bottom:r.bottom,right:r.right};
  };
  const ledger = document.querySelector('.gene-ledger');
  return {mode:get('rehearsal-mode').textContent, provenance:get('provenance').textContent,
    checkpoint:get('story-checkpoint-rate').textContent, offline:get('story-offline-member').textContent,
    reason:get('story-offline-reason').textContent, genes:get('story-genes').textContent,
    acceptance:Object.fromEntries(['contract_local','interface_live','task_live'].map(id=>[id,get(id).textContent])),
    pipes:series?{data:series.data,links:series.links}:null,
    ids:Object.fromEntries([...document.querySelectorAll('[id]')].map(el=>[el.id,el.textContent])),
    ledger:{rect:rect(ledger),scrollHeight:ledger.scrollHeight,clientHeight:ledger.clientHeight,
      items:[...get('story-genes').children].map(el=>({text:el.textContent,rect:rect(el),className:el.className,
        opacity:getComputedStyle(el).opacity,color:getComputedStyle(el).color}))},
    theme:{background:getComputedStyle(document.body).backgroundColor,color:getComputedStyle(document.body).color}};
}

function assertStage(row, current) {
  assert(row.provenance.includes('replay'));
  assert.equal(row.acceptance.interface_live, 'not_run');
  assert.equal(row.acceptance.task_live, 'not_run');
  assert.equal(row.acceptance.contract_local, current.acceptance.contract_local);
  if (current.checkpoints) assert(row.checkpoint.startsWith(`${current.checkpoints.passed_count}/${current.checkpoints.total}`));
  assertGeometry(row.geometry); // Original implementation and default first-viewport gate, unchanged.
  assert(row.ledger.rect.y >= 0 && row.ledger.rect.bottom < row.geometry.viewportHeight, 'Full ledger outside viewport');
  assert(row.ledger.scrollHeight <= row.ledger.clientHeight + 1, 'Ledger content internally clipped');
  for (const item of row.ledger.items) {
    assert(item.rect.y >= 0 && item.rect.bottom < row.geometry.viewportHeight, 'Gene item outside first viewport');
    assert(item.rect.x >= 0 && item.rect.right <= row.geometry.viewport, 'Gene item horizontally clipped');
  }
  for (const pipe of current.pipes) {
    const edge = row.pipes.links.find(link=>link.source===agentName(pipe.src)&&link.target===agentName(pipe.dst));
    assert(edge, 'Missing real pipe');
    assert(edge.value.includes(pipe.weight.toFixed(2)), 'Pipe weight mismatch');
    assert.equal(edge.active, pipe.active);
    assert.equal(edge.lineStyle.type, pipe.active?'solid':'dashed');
    assert.equal(edge.lineStyle.width, Math.max(2,Math.min(12,1+pipe.weight*4)));
  }
  for (const node of row.pipes.data) {
    const member = current.members.find(member=>agentName(member.agent)===node.name);
    assert(member, 'Topology member absent from real snapshot');
    assert.equal(node.online, member.available);
  }
  const removed = current.members.find(member=>member.available===false);
  if (removed) { assert(row.offline.includes(agentName(removed.agent))); assert(row.reason.includes(removed.reason)); }
}

function assertOriginalStageFacts(rows) {
  assert(rows.some(o=>o.checkpoint.startsWith('0/3')));
  assert(rows.some(o=>o.checkpoint.startsWith('3/3')));
  assert(rows.some(o=>o.pipes?.links.some(edge=>edge.value.includes('1.00'))));
  assert(rows.some(o=>o.pipes?.links.some(edge=>edge.value.includes('1.90')&&edge.lineStyle.width===8.6)));
  assert(rows.some(o=>o.pipes?.links.some(edge=>edge.active===false&&edge.lineStyle.type==='dashed')));
  assert(rows.some(o=>o.pipes?.data.some(node=>node.online===false)));
  assert(rows.at(-1).mode.includes('彩排完成'));
  // The live observer's passed assertion is deliberately inapplicable to replay.
  assert.equal(rows.at(-1).acceptance.task_live, 'not_run');
}

async function main(args = process.argv.slice(2)) {
  assert(args.length===2 || (args.length===3 && args[2]==='--prepare-only'), 'SOURCE_REHEARSAL NEW_OUTPUT [--prepare-only]');
  const source = path.resolve(args[0]), output = path.resolve(args[1]), prepareOnly = args[2]==='--prepare-only';
  const root = path.dirname(source);
  assert.equal(path.basename(source), 'rehearsal.json');
  const relativeOutput = path.relative(root,output);
  assert(relativeOutput.startsWith('..'+path.sep) || path.isAbsolute(relativeOutput), 'Output must be outside original evidence');
  assert(!fs.existsSync(output), 'Use a fresh output directory');
  assert(process.env.MORPH_PYTHON, 'MORPH_PYTHON required');
  fs.mkdirSync(output, {recursive:true});
  const before = inventory(root);
  write(path.join(output,'source-before.json'),before);
  assert.equal(before.length,29,'Expected all 29 original evidence files');
  const document = JSON.parse(fs.readFileSync(source,'utf8'));
  assert.equal(document.mode,'live','Historical source must retain its original provenance');
  assert.deepEqual(document.history.map(s=>s.sequence),Array.from({length:20},(_,i)=>i));
  const workingRoot = fs.mkdtempSync(path.join(os.tmpdir(),'morph-finals-replay-'));
  const working = path.join(workingRoot,'rehearsal.json');
  const setSnapshot = index => {
    write(working+'.tmp',{...document,current:document.history[index],history:document.history.slice(0,index+1)});
    fs.renameSync(working+'.tmp',working);
  };
  setSnapshot(0);
  const port = await freePort(), url = `http://127.0.0.1:${port}`;
  const env = {...withoutGatewayKey(process.env), PYTHONDONTWRITEBYTECODE:'1'};
  const child = spawn(process.env.MORPH_PYTHON,['-u','-m','viz.server','--port',String(port),'--rehearsal',working,'--replay'],
    {cwd:path.resolve(__dirname,'../..'),windowsHide:true,env,stdio:['ignore','pipe','pipe']});
  child.stdout.on('data',chunk=>fs.appendFileSync(path.join(output,'server.stdout.log'),chunk));
  child.stderr.on('data',chunk=>fs.appendFileSync(path.join(output,'server.stderr.log'),chunk));
  let childError = null;
  child.on('error',error=>{childError=String(error);});
  const summary = {scope:prepareOnly?'replay-adapter-preparation':'contract_local/replay-browser',source,output,working,port,
    modelRequests:0,liveObserver:'not_run',snapshots:document.history.length,frames:[],failures:[],startedAt:new Date().toISOString()};
  let browser;
  try {
    let ready = false;
    for(let n=0;n<100;n++) {
      if(childError || child.exitCode!==null) throw Error(childError??`Server exited ${child.exitCode}`);
      try { const response=await fetch(url+'/api/dashboard'); if(response.ok) {ready=true;break;} } catch {}
      await pause(100);
    }
    assert(ready,'Private replay server did not start');
    const pages = [];
    if(!prepareOnly) {
      const {chromium} = require(process.env.MORPH_PLAYWRIGHT);
      browser = await chromium.launch({headless:true,executablePath:process.env.MORPH_CHROMIUM,env});
      summary.browser=browser.version();
      for(const [width,height] of [[1280,720],[1366,768],[1920,1080]]) {
        const page = await browser.newPage({viewport:{width,height}});
        const record = {page,width,height,errors:[],external:[],rows:[]};
        page.on('pageerror',error=>record.errors.push(error.message));
        await page.route('**/*',route=>{
          if(new URL(route.request().url()).origin!==url) {record.external.push(route.request().url());return route.abort();}
          return route.continue();
        });
        await page.goto(url);
        pages.push(record);
      }
    }
    const apiRows=[];
    for(let index=0;index<document.history.length;index++) {
      setSnapshot(index);
      const current=document.history[index];
      const data=await (await fetch(url+'/api/dashboard')).json();
      assert.equal(data.provenance,'replay');
      assert.equal(data.rehearsal.current.sequence,current.sequence);
      assert.equal(data.acceptance.interface_live,'not_run');
      assert.equal(data.acceptance.task_live,'not_run');
      apiRows.push(data);
      for(const record of pages) {
        const {page,width}=record;
        try {
          await page.waitForFunction(seq=>new RegExp(`#${seq}(?:\\D|$)`).test(document.getElementById('rehearsal-mode')?.textContent??''),current.sequence);
          await page.waitForTimeout(650); // At least 300ms, including chart and CSS transitions.
          const row={sequence:current.sequence,stage:current.stage,...await page.evaluate(observe),geometry:await page.evaluate(readGeometry)};
          record.rows.push(row);
          const screenshot=`${width}-${String(current.sequence).padStart(2,'0')}-${current.stage}.png`;
          await page.screenshot({path:path.join(output,screenshot),fullPage:false});
          const keyframe={0:'initial',1:'task-in-progress',6:'member-offline',19:'recovery-completed'}[current.sequence];
          if(keyframe && width!==1366) fs.copyFileSync(path.join(output,screenshot),path.join(output,`${width}-${keyframe}.png`));
          summary.frames.push({width,sequence:current.sequence,stage:current.stage,screenshot});
          assertStage(row,current);
        } catch(error) {summary.failures.push({width,sequence:current.sequence,error:String(error)});}
        write(path.join(output,`${width}.json`),{...record,page:undefined});
      }
    }
    write(path.join(output,'api-replay.json'),apiRows);
    for(const record of pages) {
      try {
        assert.deepEqual(record.rows.map(row=>row.sequence),document.history.map(s=>s.sequence));
        assertOriginalStageFacts(record.rows);
        assert.deepEqual(record.errors,[],'JavaScript errors');
        assert.deepEqual(record.external,[],'External requests');
      } catch(error) {summary.failures.push({width:record.width,error:String(error)});}
    }
  } catch(error) {summary.failures.push({error:String(error)});}
  finally {
    if(browser) await browser.close();
    if(child.exitCode===null && !childError) {
      const exited=new Promise(resolve=>child.once('exit',resolve));
      child.kill(); // Only the exact private server spawned above.
      await exited;
    }
    summary.serverExited=child.exitCode!==null || child.signalCode!==null;
    const after=inventory(root);
    write(path.join(output,'source-after.json'),after);
    summary.sourceUnchanged=JSON.stringify(before)===JSON.stringify(after);
    if(!summary.sourceUnchanged) summary.failures.push({error:'Original evidence changed'});
    summary.endedAt=new Date().toISOString();
    write(path.join(output,'summary.json'),summary);
  }
  console.log(JSON.stringify({scope:summary.scope,snapshots:summary.snapshots,frames:summary.frames.length,
    failures:summary.failures,sourceUnchanged:summary.sourceUnchanged,output}));
  assert.equal(summary.failures.length,0,'Replay acceptance failed; inspect preserved output, do not weaken assertions');
}

module.exports={inventory,assertStage,assertOriginalStageFacts,main};
if(require.main===module) main().catch(error=>{console.error(error);process.exitCode=1;});
