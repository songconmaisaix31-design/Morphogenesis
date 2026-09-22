const test=require('node:test');
const assert=require('node:assert/strict');
const {spawnSync}=require('node:child_process');
const {withoutGatewayKey}=require('./rehearsal_browser.cjs');
const {options}=require('./observe_rehearsal.cjs');

test('legacy CLI and explicit gateway preserve executor-specific model selection',()=>{
  const legacy=options(['manual','7526','new-evidence']);
  assert.equal(legacy.executor,'codex');assert.equal(legacy.model,'gpt-5.6-luna');
  assert.equal(options(['auto','7526','new-evidence','--executor','evomap']).model,'evomap-gpt-5.6-luna');
  assert.equal(options(['auto','7526','new-evidence','--executor','evomap','--model','explicit']).model,'explicit');
  assert.throws(()=>options(['auto','7526','new-evidence','--executor','unknown']));
});

test('actual child receives no sentinel under the browser environment policy',()=>{
  const parent={...withoutGatewayKey(process.env),MORPH_EVOMAP_API_KEY:'local-sentinel-not-a-credential',morph_evomap_api_key:'case-sentinel'};
  const child=spawnSync(process.execPath,['-e',"process.exit(Object.keys(process.env).some(k=>k.toUpperCase()==='MORPH_EVOMAP_API_KEY')?1:0)"],{env:withoutGatewayKey(parent),encoding:'utf8'});
  assert.equal(child.status,0,child.stderr);
  assert.equal(parent.MORPH_EVOMAP_API_KEY,'local-sentinel-not-a-credential');
});
