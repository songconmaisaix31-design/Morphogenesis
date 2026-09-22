// Terminal-only confirmation. No browser, model, environment or credential access.
const assert = require('node:assert/strict');

function assertTerminal(input) {
  assert(input.isTTY === true && typeof input.setRawMode === 'function',
    'OPERATOR_TTY_REQUIRED: run directly in the operator terminal, not a pipe');
}

function assertAwaitingOffline(records, document) {
  assert.equal(document.mode, 'live', 'OPERATOR_REQUIRES_LIVE');
  assert.equal(document.current.stage, 'awaiting_offline', 'OPERATOR_STAGE_MISMATCH');
  assert.equal(document.current.provenance, 'live', 'OPERATOR_REQUIRES_LIVE');
  assert(Number.isInteger(document.current.sequence), 'OPERATOR_SEQUENCE_REQUIRED');
  assert.equal(records.map(r => r.width).sort((a,b) => a-b).join(','), '1366,1920', 'OPERATOR_TWO_VIEWPORTS_REQUIRED');
  for (const record of records) {
    const observation = record.observations.at(-1);
    assert(observation && observation.mode === record.last, 'OPERATOR_OBSERVATION_REQUIRED');
    assert(observation.mode.includes('等待下线确认'), 'OPERATOR_BROWSER_STAGE_MISMATCH');
    assert.equal(Number(observation.mode.match(/#(\d+)/)?.[1]), document.current.sequence, 'OPERATOR_BROWSER_SEQUENCE_MISMATCH');
    assert.equal(observation.provenance.trim(), '来源：live', 'OPERATOR_BROWSER_NOT_LIVE');
  }
  return document.current.sequence;
}

async function operatorEnter({input, timeoutMs, validate, record, deliver, signal, prompt = () => {}}) {
  let evidence = {source:'operator', stage:'awaiting_offline', status:'checking'};
  try {
    assertTerminal(input);
    assert(Number.isFinite(timeoutMs) && timeoutMs > 0, 'OPERATOR_TIMEOUT');
    const sequence = validate(); // No terminal listener until both views and disk agree.
    evidence = {...evidence, sequence, armedAt:new Date().toISOString(), status:'waiting'};
    record(evidence);
    const at = await new Promise((resolve, reject) => {
      const raw = Boolean(input.isRaw);
      let timer;
      const finish = (error) => {
        clearTimeout(timer);
        input.removeListener('data', onData);
        input.removeListener('end', onEnd);
        input.removeListener('close', onEnd);
        input.removeListener('error', onError);
        signal?.removeEventListener('abort', onCancel);
        input.pause();
        input.setRawMode(raw);
        if (error) reject(Error(error)); else resolve(new Date().toISOString());
      };
      const onEnd = () => finish('OPERATOR_EOF');
      const onError = () => finish('OPERATOR_INPUT_ERROR');
      const onCancel = () => finish('OPERATOR_CANCELLED');
      const onData = chunk => {
        const text = chunk.toString();
        if (/[\x03\x1b]/.test(text)) return onCancel();
        if (/[\x04\x1a]/.test(text)) return onEnd();
        // Never echo, persist or forward arbitrary terminal text (including secrets).
        if (!['\r','\n','\r\n'].includes(text)) return finish('OPERATOR_EXPECTED_SINGLE_ENTER');
        finish();
      };
      if (signal?.aborted) return reject(Error('OPERATOR_CANCELLED'));
      if (input.readableEnded || input.destroyed) return reject(Error('OPERATOR_EOF'));
      input.setRawMode(true);
      // Discard Node-buffered pre-prompt input; only a new key event may confirm.
      while (input.read() !== null) {}
      input.on('data', onData);
      input.once('end', onEnd);
      input.once('close', onEnd);
      input.once('error', onError);
      signal?.addEventListener('abort', onCancel, {once:true});
      timer = setTimeout(() => finish('OPERATOR_TIMEOUT'), timeoutMs);
      prompt();
      input.resume();
    });
    evidence = {...evidence, at, input:'Enter', status:'received'};
    record(evidence); // Persist the actual operator time before any forwarding.
    assert.equal(validate(), evidence.sequence, 'OPERATOR_STAGE_CHANGED');
    if (signal?.aborted) throw Error('OPERATOR_CANCELLED');
    await deliver(); // Exactly one write attempt; an unknown result is never retried.
    evidence = {...evidence, forwardedAt:new Date().toISOString(), status:'forwarded'};
    record(evidence);
    return evidence;
  } catch (error) {
    record({...evidence, failedAt:new Date().toISOString(), status:'failed', failure:String(error)});
    throw error;
  }
}

module.exports = {assertTerminal, assertAwaitingOffline, operatorEnter};
