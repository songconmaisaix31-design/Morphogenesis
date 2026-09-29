// Existing OpenAI SDK 6.40.0 (Apache-2.0), reused from installed dsh 0.1.5-rc.3.
// One request only. No agent loop, tools, retry, alternate provider, or credential fallback.
const fs = require('node:fs');
const path = require('node:path');
const { createRequire } = require('node:module');
const localRequire = createRequire('C:/Users/DW/AppData/Roaming/npm/node_modules/@deepseek-ai/dsh/package.json');
const OpenAI = localRequire('openai');
const YAML = localRequire('yaml');
const root = __dirname;
const prefix = path.join(root, 'review-0929-formal-v2');
const candidate = 'c552250c0d07f5f70f09eb0a5ab3c322195e34ec';
const original = 'C:/Users/DW/orca/workspaces/Morphogenesis/decentralized-swarm/.runtime/fc-auth';
const patch = YAML.parse(fs.readFileSync(path.join(original, 'dsh-dashscope.patch.yml'), 'utf8'), { logLevel: 'silent' });
const provider = patch.find(x => x.id === 'llm-pi-ai').config.providers['dashscope-fc'];
const selected = patch.find(x => x.id === 'agent-default-model').config;
if (selected.provider !== 'dashscope-fc' || selected.model !== 'deepseek-r1' ||
    provider.baseURL !== 'https://dashscope.aliyuncs.com/compatible-mode/v1' ||
    provider.retryPolicy.maxRetries !== 0 || !provider.models.some(x => x.id === 'deepseek-r1' && x.maxTokens === 16384)) {
  throw new Error('Original provider/model boundary changed; no request');
}
const input = fs.readFileSync(prefix + '-input.md', 'utf8');
const inputBytes = Buffer.byteLength(input);
if (!input.includes(candidate) || inputBytes > 95000) throw new Error('Wrong candidate or input exceeds 95000 UTF-8 bytes');
const metadata = {
  candidate, configured_model: selected.model, provider: selected.provider,
  original_profile: 'headless', execution: 'installed SDK single chat completion; no dsh tool loop',
  sdk: 'openai@6.40.0', max_retries: 0, max_output_tokens: 16384,
  input_bytes: inputBytes, input_token_count: 'unknown; not locally tokenized',
  provider_context: 131072, provider_max_input_tokens: 98304,
  capacity_source: 'https://help.aliyun.com/en/model-studio/deepseek-r1',
  cost: 'unknown', usage: 'not_collected', submitted: false,
};
if (process.argv[2] !== '--send-after-six-gates') {
  console.log(JSON.stringify({ ...metadata, mode: 'prepare_only; credential unread; no request' }));
  process.exit(0);
}
// Must be invoked only after coordinator's explicit six-green notification.
// Exclusive evidence creation prevents accidentally repeating this authorized request.
fs.writeFileSync(prefix + '-call.json', JSON.stringify(metadata, null, 2) + '\n', { flag: 'wx' });
const key = fs.readFileSync(path.join(original, 'private', 'dashscope-api-key'), 'utf8').trim();
let fetchCalls = 0;
const client = new OpenAI({
  apiKey: key, baseURL: provider.baseURL, maxRetries: 0, timeout: 600000,
  fetch: async (url, options) => {
    if (++fetchCalls !== 1 || String(url) !== provider.baseURL + '/chat/completions') {
      throw new Error('Single-request boundary rejected');
    }
    metadata.submitted = true;
    metadata.submitted_at = new Date().toISOString();
    fs.writeFileSync(prefix + '-call.json', JSON.stringify(metadata, null, 2) + '\n');
    return fetch(url, { ...options, redirect: 'error' });
  },
});
(async () => {
  try {
    const response = await client.chat.completions.create({
      model: selected.model, max_tokens: 16384, stream: false,
      messages: [{ role: 'user', content: input }],
    });
    // No request headers or credentials are serialized; provider response is preserved.
    fs.writeFileSync(prefix + '-response.json', JSON.stringify(response, null, 2) + '\n', { flag: 'wx' });
    const message = response.choices?.[0]?.message;
    fs.writeFileSync(prefix + '-raw.txt', message?.content ?? '', { flag: 'wx' });
    Object.assign(metadata, {
      result: 'response_received', returned_model: response.model ?? 'unknown',
      response_id: response.id ?? 'unknown', finish_reason: response.choices?.[0]?.finish_reason ?? 'unknown',
      usage: response.usage ?? 'unknown', fetch_calls: fetchCalls, completed_at: new Date().toISOString(),
    });
    if (response.model !== selected.model || !message?.content || response.choices?.[0]?.finish_reason !== 'stop') {
      metadata.review_status = 'INCOMPLETE_OR_MODEL_MISMATCH';
      process.exitCode = 2;
    } else metadata.review_status = 'RECEIVED_NOT_ACCEPTED; requires v2 mechanical and semantic checks';
  } catch (error) {
    Object.assign(metadata, {
      result: 'ERROR_STOP_NO_RETRY', error_type: error?.name ?? 'unknown',
      http_status: Number.isInteger(error?.status) ? error.status : 'unknown',
      effect: 'unknown', usage: 'unknown', fetch_calls: fetchCalls, completed_at: new Date().toISOString(),
    });
    // Do not serialize arbitrary error objects/messages which may carry sensitive context.
    process.exitCode = 1;
  } finally {
    fs.writeFileSync(prefix + '-call.json', JSON.stringify(metadata, null, 2) + '\n');
    console.log(JSON.stringify(metadata));
  }
})();
