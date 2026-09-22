const test = require('node:test');
const assert = require('node:assert/strict');
const {PassThrough} = require('node:stream');
const {spawnSync} = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {options} = require('./observe_rehearsal.cjs');
const {assertAwaitingOffline, operatorEnter} = require('./operator_enter.cjs');

// Synthetic terminal and snapshots only; these are not live acceptance evidence.
function fixture() {
  const input = new PassThrough();
  input.isTTY = true;
  input.isRaw = false;
  input.setRawMode = raw => { input.isRaw = raw; };
  const document = {mode:'live',current:{stage:'awaiting_offline',sequence:7,provenance:'live'}};
  const records = [1366,1920].map(width => ({width,last:'真实运行 · 等待下线确认 · #7',
    observations:[{mode:'真实运行 · 等待下线确认 · #7',provenance:'来源：live'}]}));
  const evidence = [];
  const controller = new AbortController();
  let writes = 0;
  const args = {input,timeoutMs:1000,signal:controller.signal,
    validate:() => assertAwaitingOffline(records,document),
    record:row => evidence.push(row),deliver:async() => { writes++; }};
  return {input,document,records,evidence,controller,args,get writes(){return writes;}};
}

test('pure parser keeps defaults, opts in explicitly and rejects ambiguous invocations', () => {
  const base = ['manual','7530','new-evidence'];
  assert.equal(options(base).operator,false);
  assert.equal(options(base).operatorTimeoutMs,120000);
  assert.equal(options([...base,'--operator-enter']).operator,true);
  assert.equal(options([...base,'--operator-enter','--operator-timeout-seconds','30']).operatorTimeoutMs,30000);
  for (const args of [
    ['auto','7530','new-evidence','--operator-enter'],
    [...base,'--operator-timeout-seconds','30'],
    ...['0','-1','1.5','NaN','481'].map(t => [...base,'--operator-enter','--operator-timeout-seconds',t]),
    [...base,'--operator-enter=true'], ['manual','0','out'], ['unknown','7530','out']
  ]) assert.throws(() => options(args));
  const child = spawnSync(process.execPath,['-e',
    "require('./tests/integration/observe_rehearsal.cjs').options(['manual','7530','out','--operator-enter'])"],
    {cwd:path.resolve(__dirname,'../..'),env:{...process.env,MORPH_PLAYWRIGHT:'must-not-load'},encoding:'utf8'});
  assert.equal(child.status,0,child.stderr);
});

test('non-terminal invocation fails before evidence creation, browser loading or demo launch', () => {
  const output = path.join(os.tmpdir(),`morph-operator-preflight-${process.pid}-${Date.now()}`);
  const child = spawnSync(process.execPath,[path.join(__dirname,'observe_rehearsal.cjs'),'manual','7530',output,'--operator-enter'],
    {env:{...process.env,MORPH_PLAYWRIGHT:'must-not-load'},input:'\n',encoding:'utf8'});
  assert.equal(child.status,1);
  assert.match(child.stderr,/OPERATOR_TTY_REQUIRED/);
  assert(!fs.existsSync(output));
});

for (const [name, mutate] of [
  ['one viewport', f => f.records.pop()],
  ['duplicate viewport', f => {f.records[1].width=1366;}],
  ['browser not awaiting', f => {f.records[0].last='repair';}],
  ['stale browser sequence', f => {f.records[1].observations[0].mode=f.records[1].last='等待下线确认 · #6';}],
  ['browser replay', f => {f.records[0].observations[0].provenance='来源：replay';}],
  ['file wrong stage', f => {f.document.current.stage='member_offline';}],
  ['file replay', f => {f.document.mode='replay';}],
  ['file mock', f => {f.document.current.provenance='mock';}],
]) test(`gate never reads input or forwards on ${name}`, async () => {
  const f=fixture(); mutate(f);
  await assert.rejects(operatorEnter(f.args));
  assert.equal(f.input.listenerCount('data'),0);
  assert.equal(f.input.isRaw,false);
  assert.equal(f.writes,0);
  assert.equal(f.evidence.at(-1).status,'failed');
});

test('no automatic Enter, buffered input discarded, one fresh Enter and timestamps retained', async () => {
  const f=fixture();
  f.input.write('\n'); // Pre-prompt buffered key must not arm the effect.
  const pending=operatorEnter(f.args);
  await new Promise(resolve=>setTimeout(resolve,30));
  assert.equal(f.writes,0);
  assert.equal(f.evidence.at(-1).status,'waiting');
  f.input.write('\r');
  const result=await pending;
  f.input.write('\r');
  assert.equal(f.writes,1);
  assert.equal(result.status,'forwarded');
  assert(result.armedAt<=result.at&&result.at<=result.forwardedAt);
  assert.equal(f.input.isRaw,false);
  assert.equal(f.input.listenerCount('data'),0);
  assert.equal(f.input.listenerCount('end'),0);
  assert.equal(f.input.listenerCount('error'),0);
});

for (const [name, trigger, expected] of [
  ['timeout', () => {}, 'OPERATOR_TIMEOUT'],
  ['EOF', f => f.input.end(), 'OPERATOR_EOF'],
  ['Ctrl+D', f => f.input.write('\x04'), 'OPERATOR_EOF'],
  ['Ctrl+Z', f => f.input.write('\x1a'), 'OPERATOR_EOF'],
  ['Ctrl+C', f => f.input.write('\x03'), 'OPERATOR_CANCELLED'],
  ['Escape', f => f.input.write('\x1b'), 'OPERATOR_CANCELLED'],
  ['signal cancellation', f => f.controller.abort(), 'OPERATOR_CANCELLED'],
  ['stream error', f => f.input.emit('error',Error('secret-sentinel')), 'OPERATOR_INPUT_ERROR'],
  ['nonempty input', f => f.input.write('secret-sentinel\r'), 'OPERATOR_EXPECTED_SINGLE_ENTER'],
  ['multiple Enter', f => f.input.write('\r\r'), 'OPERATOR_EXPECTED_SINGLE_ENTER'],
]) test(`${name} fails with durable evidence and no delivery`, async () => {
  const f=fixture();
  const directory=fs.mkdtempSync(path.join(os.tmpdir(),'morph-operator-test-'));
  const target=path.join(directory,'manual-enter.json');
  f.args.record=row=>{f.evidence.push(row);fs.writeFileSync(target,JSON.stringify(row));};
  f.args.timeoutMs=50;
  try {
    const pending=operatorEnter(f.args);
    trigger(f);
    await assert.rejects(pending,new RegExp(expected));
    const persisted=fs.readFileSync(target,'utf8');
    assert.equal(JSON.parse(persisted).status,'failed');
    assert(!persisted.includes('secret-sentinel'));
    assert.equal(f.writes,0);
    assert.equal(f.input.isRaw,false);
    assert.equal(f.input.listenerCount('data'),0);
  } finally {fs.rmSync(directory,{recursive:true});}
});

test('changed runtime stage at Enter prevents forwarding', async () => {
  const f=fixture();
  const pending=operatorEnter(f.args);
  f.document.current.stage='failed';
  f.input.write('\n');
  await assert.rejects(pending,/OPERATOR_STAGE_MISMATCH/);
  assert.equal(f.writes,0);
  assert(f.evidence.at(-1).at);
});

test('unknown forwarding failure is recorded without retry', async () => {
  const f=fixture(); let attempts=0;
  f.args.deliver=async()=>{attempts++;throw Error('OPERATOR_FORWARD_FAILED_NO_RETRY');};
  const pending=operatorEnter(f.args);
  f.input.write('\n');
  await assert.rejects(pending,/NO_RETRY/);
  assert.equal(attempts,1);
  assert.equal(f.evidence.at(-1).status,'failed');
  assert(f.evidence.at(-1).at);
});
