// No model execution: display every snapshot from an explicitly MOCK fixture.
// URL FIXTURE_JSON NEW_WORKING_JSON NEW_OUTPUT_DIR; viewer reads NEW_WORKING_JSON.
const fs=require('node:fs');
const path=require('node:path');
const assert=require('node:assert/strict');
const {withoutGatewayKey,readGeometry,assertGeometry}=require('./rehearsal_browser.cjs');
for(const key of Object.keys(process.env)) if(key.toUpperCase()==='MORPH_EVOMAP_API_KEY') delete process.env[key];
const {chromium}=require(process.env.MORPH_PLAYWRIGHT);
const [url,fixture,working,output]=process.argv.slice(2);
assert(url&&fixture&&working&&output);
const original=fs.readFileSync(fixture),mtime=fs.statSync(fixture).mtimeMs;
const document=JSON.parse(original);
assert.equal(document.mode,'mock','Preflight never reclassifies live evidence');
assert(!fs.existsSync(working)&&!fs.existsSync(output));
fs.mkdirSync(path.dirname(working),{recursive:true});
fs.mkdirSync(output,{recursive:true});

(async()=>{
  const browser=await chromium.launch({headless:true,executablePath:process.env.MORPH_CHROMIUM,env:withoutGatewayKey(process.env)});
  const rows=[];
  try {
    const pages=await Promise.all([[1366,768],[1920,1080]].map(async([width,height])=>{
      const page=await browser.newPage({viewport:{width,height}});
      await page.route('**/*',route=>new URL(route.request().url()).origin===url?route.continue():route.abort());
      await page.goto(url);
      return {page,width};
    }));
    for(let i=0;i<document.history.length;i++) {
      const current=document.history[i];
      const next={...document,current,history:document.history.slice(0,i+1)};
      fs.writeFileSync(working+'.tmp',JSON.stringify(next));fs.renameSync(working+'.tmp',working);
      for(const {page,width} of pages) {
        await page.waitForFunction(sequence=>document.getElementById('rehearsal-mode').textContent.endsWith(`#${sequence}`),current.sequence);
        assert((await page.locator('#provenance').textContent()).includes('mock'));
        assert.equal(await page.locator('#task_live').textContent(),'not_run');
        const geometry=await page.evaluate(readGeometry);
        rows.push({sequence:current.sequence,stage:current.stage,...geometry});
        await page.screenshot({path:path.join(output,`${width}-${current.sequence}.png`)});
        fs.writeFileSync(path.join(output,'geometry.json'),JSON.stringify(rows,null,2));
        assertGeometry(geometry);
      }
    }
  } finally {await browser.close();}
  assert(original.equals(fs.readFileSync(fixture))&&mtime===fs.statSync(fixture).mtimeMs);
  console.log(JSON.stringify({provenance:'mock',model_requests:0,frames:rows.length,stages:document.history.map(s=>s.stage),original_unchanged:true}));
})().catch(error=>{console.error(error);process.exitCode=1;});
