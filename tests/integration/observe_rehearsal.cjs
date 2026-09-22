// A single authorized demo invocation with two read-only browser observers.
// No retry: failure preserves logs and stops this process after the current demo exits.
// Usage: node tests/integration/observe_rehearsal.cjs manual|auto PORT OUTPUT_DIR [--executor codex|evomap] [--model MODEL]
// Requires the already installed Playwright and Chromium paths via environment.
const fs = require('node:fs');
const path = require('node:path');
const {spawn} = require('node:child_process');
const assert = require('node:assert/strict');
const {parseArgs} = require('node:util');
const {withoutGatewayKey,readGeometry,assertGeometry}=require('./rehearsal_browser.cjs');

function options(args) {
  const {values,positionals}=parseArgs({args,allowPositionals:true,options:{executor:{type:'string',default:'codex'},model:{type:'string'}}});
  const [mode,portText,outputArg]=positionals;
  assert.equal(positionals.length,3,'mode PORT OUTPUT_DIR required');
  assert(['codex','evomap'].includes(values.executor),'unknown executor');
  const model=values.model??(values.executor==='evomap'?'evomap-gpt-5.6-luna':'gpt-5.6-luna');
  assert(/^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$/.test(model),'invalid model');
  return {mode,portText,outputArg,executor:values.executor,model};
}

async function main(args=process.argv.slice(2)) {
const {mode,portText,outputArg,executor,model}=options(args);
assert(['manual', 'auto'].includes(mode));
assert(/^\d+$/.test(portText));
assert(Number(portText)>0&&Number(portText)<=65535);
const output = path.resolve(outputArg);
assert(!fs.existsSync(output), 'Use a new browser evidence directory; never replace evidence');
fs.mkdirSync(output, {recursive: true});
const url = `http://127.0.0.1:${portText}`;
const pause = ms => new Promise(resolve => setTimeout(resolve, ms));

  // Retain the credential only for the demo child; remove it before loading Playwright.
  const demoEnvironment={...process.env};
  for(const key of Object.keys(process.env)) if(key.toUpperCase()==='MORPH_EVOMAP_API_KEY') delete process.env[key];
  const {chromium}=require(process.env.MORPH_PLAYWRIGHT);
  const browser = await chromium.launch({headless: true, executablePath: process.env.MORPH_CHROMIUM,env:withoutGatewayKey(process.env)});
  const pages = await Promise.all([[1366,768], [1920,1080]].map(async ([width,height]) => {
    const page = await browser.newPage({viewport:{width,height}});
    const record = {page,width,height,last:null,errors:[],responses:[],observations:[]};
    page.on('pageerror', error => record.errors.push(error.message));
    page.on('response', response => record.responses.push({url:response.url(),status:response.status()}));
    await page.route('**/*', route => new URL(route.request().url()).origin === url ? route.continue() : route.abort());
    return record;
  }));
  let stdout = '', exitCode = null, exited = false, entered = false, root = null;
  const startedAt = new Date().toISOString();
  const child = spawn('pwsh', ['-NoProfile','-File','demo/run-demo.ps1','-AuthorizeLive','-Mode',mode,'-Port',portText,'-Executor',executor,'-Model',model,'-TimeoutSeconds','180','-TauSeconds','10','-StageDelay','2'], {windowsHide:true,stdio:['pipe','pipe','pipe'],env:demoEnvironment});
  for(const key of Object.keys(demoEnvironment)) if(key.toUpperCase()==='MORPH_EVOMAP_API_KEY') delete demoEnvironment[key];
  child.stdout.on('data', chunk => {
    stdout += chunk.toString();
    fs.appendFileSync(path.join(output,'demo.stdout.log'),chunk);
    for (const line of stdout.split(/\r?\n/)) {
      try { const value=JSON.parse(line); if(value.root) root=value.root; } catch {}
    }
  });
  child.stderr.on('data', chunk => fs.appendFileSync(path.join(output,'demo.stderr.log'),chunk));
  child.on('exit', code => {exited=true;exitCode=code;});
  child.on('error', () => {exited=true;exitCode=-1;});
  const deadline=Date.now()+480000;
  let failure=null;
  try {
    while(Date.now()<deadline) {
      try { const response=await fetch(url+'/api/dashboard'); if(response.ok) break; } catch {}
      if(exited) throw Error(`Demo exited before viewer readiness: ${exitCode}`);
      await pause(200);
    }
    await Promise.all(pages.map(record=>record.page.goto(url)));
    while(Date.now()<deadline) {
      for(const record of pages) {
        const observation=await record.page.evaluate(()=>{
          const get=id=>document.getElementById(id);
          const chart=echarts.getInstanceByDom(get('story-pipe-chart'));
          const series=chart?.getOption().series[0];
          return {at:new Date().toISOString(),mode:get('rehearsal-mode').textContent,provenance:get('provenance').textContent,
            checkpoint:get('story-checkpoint-rate').textContent,offline:get('story-offline-member').textContent,
            reason:get('story-offline-reason').textContent,genes:get('story-genes').textContent,
            acceptance:Object.fromEntries(['contract_local','interface_live','task_live'].map(id=>[id,get(id).textContent])),
            overflow:document.documentElement.scrollWidth>innerWidth,geneBottom:document.querySelector('.gene-ledger').getBoundingClientRect().bottom,
            pipes:series?{data:series.data,links:series.links}:null};
        });
        if(observation.mode!==record.last) {
          record.last=observation.mode;
          record.observations.push(observation);
          const seq=observation.mode.match(/#(\d+)/)?.[1]??'waiting';
          await record.page.screenshot({path:path.join(output,`${record.width}-${seq}.png`),fullPage:false});
          if(observation.pipes?.data?.length===3) {
            observation.geometry=await record.page.evaluate(readGeometry);
          }
          fs.writeFileSync(path.join(output,`${record.width}.json`),JSON.stringify({...record,page:undefined},null,2));
          console.log(`${record.width}: ${observation.mode}`);
          assert.equal(observation.overflow,false,'horizontal overflow');
          if(observation.geometry) assertGeometry(observation.geometry);
        }
      }
      if(mode==='manual'&&!entered&&pages.every(r=>r.last.includes('等待下线确认'))) {
        // Wait until the runtime reaches its real input(), then deliver Enter through stdin.
        await pause(2300);
        assert(root,'Runtime must identify the new root before manual confirmation');
        assert.equal(JSON.parse(fs.readFileSync(path.join(root,'rehearsal.json'))).current.stage,'awaiting_offline');
        child.stdin.write('\n');entered=true;
        fs.writeFileSync(path.join(output,'manual-enter.json'),JSON.stringify({at:new Date().toISOString(),input:'Enter',stage:'awaiting_offline'}));
      }
      if(exited&&pages.every(r=>/彩排完成|彩排已停止/.test(r.last))) break;
      if(exited&&exitCode!==0) throw Error(`Demo failed: ${exitCode}`);
      await pause(150);
    }
    assert(exited,'Demo has not exited by observation deadline; do not retry');
    assert.equal(exitCode,0,'Demo failed; inspect preserved evidence, do not retry');
    assert(root,'No runtime root printed');
    const document=JSON.parse(fs.readFileSync(path.join(root,'rehearsal.json')));
    assert.equal(document.mode,'live');
    assert.equal(document.current.executor??'codex',executor);
    assert.equal(document.current.model??'gpt-5.6-luna',model);
    if(mode==='manual') assert(entered,'Manual run did not deliver Enter');
    for(const record of pages) {
      const sequences=new Set(record.observations.map(o=>Number(o.mode.match(/#(\d+)/)?.[1])));
      for(const snapshot of document.history) assert(sequences.has(snapshot.sequence),`Missing actual stage ${snapshot.stage} #${snapshot.sequence} at ${record.width}`);
      assert.equal(record.errors.length,0,'browser error');
      assert(record.observations.some(o=>o.checkpoint.startsWith('0/3')));
      assert(record.observations.some(o=>o.checkpoint.startsWith('3/3')));
      assert(record.observations.some(o=>o.pipes?.links.some(edge=>edge.value.includes('1.00'))));
      assert(record.observations.some(o=>o.pipes?.links.some(edge=>edge.value.includes('1.90')&&edge.lineStyle.width===8.6)));
      assert(record.observations.some(o=>o.pipes?.links.some(edge=>edge.active===false&&edge.lineStyle.type==='dashed')));
      assert(record.observations.at(-1).mode.includes('彩排完成'));
      assert.equal(record.observations.at(-1).acceptance.task_live,'passed');
    }
  } catch(error) {failure=String(error);throw error;}
  finally {
    fs.writeFileSync(path.join(output,'summary.json'),JSON.stringify({startedAt,endedAt:new Date().toISOString(),mode,executor,model,root,port:Number(portText),parentPid:child.pid,exitCode,entered,failure,browser:browser.version()},null,2));
    await browser.close();
  }
}
module.exports={options};
if(require.main===module) main().catch(error=>{console.error(error);process.exitCode=1;});
