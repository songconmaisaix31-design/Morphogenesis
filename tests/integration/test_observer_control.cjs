// Execute the actual observer control flow with local fake browser/child boundaries.
// No server, browser binary, PowerShell launcher or model request is executed.
const test = require('node:test');
const assert = require('node:assert/strict');
const {EventEmitter} = require('node:events');
const {PassThrough} = require('node:stream');
const {createRequire} = require('node:module');
const vm = require('node:vm');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');

for (const reason of ['timeout','EOF','cancel','changed-stage','operator-success','legacy-success']) {
  test(`observer control flow: ${reason} (local fixture only)`, async () => {
    const success=reason.endsWith('success');
    const legacy=reason==='legacy-success';
    const directory = fs.mkdtempSync(path.join(os.tmpdir(),'morph-observer-test-'));
    const root = path.join(directory,'runtime');
    const output = path.join(directory,'evidence');
    fs.mkdirSync(root);
    const rehearsal = {mode:'live',current:{stage:'awaiting_offline',sequence:7,provenance:'live'},
      history:[{stage:'awaiting_offline',sequence:7}]};
    fs.writeFileSync(path.join(root,'rehearsal.json'),JSON.stringify(rehearsal));
    const fakeProcess = new EventEmitter();
    fakeProcess.env = {MORPH_PLAYWRIGHT:'fake-playwright',MORPH_CHROMIUM:'fake-chromium',MORPH_EVOMAP_API_KEY:'local-secret-sentinel'};
    fakeProcess.stdin = new PassThrough();
    fakeProcess.stdin.isTTY = true;
    fakeProcess.stdin.setRawMode = value => {fakeProcess.stdin.isRaw=value;};
    const child = new EventEmitter();
    child.pid = 12345;
    child.stdout = new PassThrough();
    child.stderr = new PassThrough();
    child.stdin = new PassThrough();
    let bytes = 0, launches = 0, browserClosed = false, pageCount = 0;
    child.stdin.on('data', chunk => {
      bytes+=chunk.length;
      if(success) {
        assert.equal(chunk.toString(),'\n');
        rehearsal.current.stage='completed';rehearsal.current.sequence=8;
        rehearsal.history.push({stage:'completed',sequence:8});
        fs.writeFileSync(path.join(root,'rehearsal.json'),JSON.stringify(rehearsal));
        setImmediate(()=>child.emit('exit',0));
      }
    });
    child.stdin.on('finish', () => child.emit('exit',1));
    const browser = {version:()=>'fixture-browser',close:async()=>{browserClosed=true;},
      newPage:async()=>{
        pageCount++;
        return {on:()=>{},route:async()=>{},goto:async()=>{},
          evaluate:async()=>({at:new Date().toISOString(),
            mode:rehearsal.current.stage==='completed'?'真实运行 · 彩排完成 · #8':'真实运行 · 等待下线确认 · #7',
            checkpoint:rehearsal.current.stage==='completed'?'3/3':'0/3',acceptance:{task_live:'passed'},
            provenance:'来源：live',overflow:false,pipes:{data:[],links:[{value:'1.00'},
              {value:'1.90',lineStyle:{width:8.6}},{value:'inactive',active:false,lineStyle:{type:'dashed'}}]}}),
          screenshot:async({path:target})=>fs.writeFileSync(target,'fixture-screenshot')};
      }};
    const filename = path.join(__dirname,'observe_rehearsal.cjs');
    const realRequire = createRequire(filename);
    const module = {exports:{}};
    const context = {module,process:fakeProcess,AbortController,setTimeout,clearTimeout,
      fetch:async()=>({ok:true}),
      console:{log:message=>{
        if (!message.includes('请在本终端')) return;
        setImmediate(()=>{
          if (reason==='EOF') fakeProcess.stdin.end();
          if (reason==='cancel') fakeProcess.emit('SIGINT');
          if (reason==='operator-success') fakeProcess.stdin.write('\r');
          if (reason==='changed-stage') {
            rehearsal.current.stage='failed';
            fs.writeFileSync(path.join(root,'rehearsal.json'),JSON.stringify(rehearsal));
            fakeProcess.stdin.write('\r');
          }
        });
      }},
      require:name=>{
        if (name==='node:child_process') return {spawn:(command,args,config)=>{
          launches++;
          assert.equal(command,'pwsh');
          assert(!JSON.stringify(args).includes('local-secret-sentinel'));
          assert.equal(config.env.MORPH_EVOMAP_API_KEY,'local-secret-sentinel');
          setImmediate(()=>child.stdout.write(JSON.stringify({root})+'\n'));
          return child;
        }};
        if (name==='fake-playwright') {
          assert(!Object.keys(fakeProcess.env).includes('MORPH_EVOMAP_API_KEY'));
          return {chromium:{launch:async config=>{
            assert(!Object.keys(config.env).includes('MORPH_EVOMAP_API_KEY'));
            return browser;
          }}};
        }
        return realRequire(name);
      }};
    // Make stdout root available before the observer's first page observation.
    browser.newPage = ((original)=>async(...args)=>{
      const page = await original(...args);
      page.goto=async()=>{await new Promise(resolve=>setImmediate(resolve));};
      return page;
    })(browser.newPage);
    try {
      vm.runInNewContext(fs.readFileSync(filename,'utf8'),context,{filename});
      const run=module.exports.main(['manual','7530',output,...(legacy?[]:['--operator-enter','--operator-timeout-seconds','1'])]);
      if(success) await run;
      else await assert.rejects(run,
        new RegExp({timeout:'OPERATOR_TIMEOUT',EOF:'OPERATOR_EOF',cancel:'OPERATOR_CANCELLED','changed-stage':'OPERATOR_STAGE_MISMATCH'}[reason]));
      await new Promise(resolve=>setImmediate(resolve));
      assert.equal(launches,1);
      assert.equal(pageCount,2);
      assert.equal(bytes,success?1:0);
      assert.equal(child.stdin.writableEnded,!success);
      assert.equal(browserClosed,true);
      assert.equal(Boolean(fakeProcess.stdin.isRaw),false);
      assert.equal(fakeProcess.listenerCount('SIGINT'),0);
      const summary=JSON.parse(fs.readFileSync(path.join(output,'summary.json')));
      assert.equal(summary.confirmation,legacy?undefined:'operator');
      assert.equal(summary.entered,success);
      assert.equal(Boolean(summary.failure),!success);
      const receipt=JSON.parse(fs.readFileSync(path.join(output,'manual-enter.json')));
      if(legacy) assert.deepEqual(Object.keys(receipt).sort(),['at','input','stage']);
      else assert.equal(receipt.status,success?'forwarded':'failed');
      assert(fs.existsSync(path.join(output,'demo.stdout.log')));
      for(const name of fs.readdirSync(output)) assert(!fs.readFileSync(path.join(output,name),'utf8').includes('local-secret-sentinel'));
    } finally {fs.rmSync(directory,{recursive:true});}
  });
}
