// Thin transport adapter; algorithms and schemas belong to @evomap/gep-sdk.
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import Ajv from 'ajv';
import addFormats from 'ajv-formats';
import { SCHEMA_VERSION, canonicalize, computeAssetId, verifyAssetId } from '@evomap/gep-sdk';

const require = createRequire(import.meta.url);
const ajv = new Ajv({ allErrors: true, allowUnionTypes: true });
addFormats(ajv);
const validators = new Map([
  ['Gene', 'gene'], ['Capsule', 'capsule'], ['EvolutionEvent', 'evolution-event'],
].map(([type, name]) => [type, ajv.compile(JSON.parse(readFileSync(
  require.resolve(`@evomap/gep-sdk/schemas/${name}.schema.json`), 'utf8',
)))]));

function validateAsset(asset) {
  const validator = validators.get(asset?.type);
  if (!validator) throw new Error('unsupported_asset_type');
  const schemaValid = validator(asset);
  const idValid = verifyAssetId(asset);
  return {
    valid: schemaValid && idValid,
    schema_valid: schemaValid,
    asset_id_valid: idValid,
    schema_version: SCHEMA_VERSION,
    // Never echo submitted values or validation params (which can contain data).
    errors: (validator.errors || []).map(({ instancePath, keyword }) => ({
      path: instancePath, keyword,
    })),
  };
}

async function main() {
  const chunks = [];
  let size = 0;
  for await (const chunk of process.stdin) {
    size += chunk.length;
    if (size > 2 * 1024 * 1024) throw new Error('request_too_large');
    chunks.push(chunk);
  }
  let request;
  try {
    request = JSON.parse(Buffer.concat(chunks).toString('utf8'));
  } catch {
    throw new Error('invalid_json');
  }
  if (SCHEMA_VERSION !== '1.14.0') throw new Error('sdk_version_mismatch');
  if (!request || typeof request !== 'object' || Array.isArray(request)) {
    throw new Error('invalid_request');
  }
  let result;
  switch (request.operation) {
    case 'canonicalize': result = canonicalize(request.value); break;
    case 'computeAssetId': result = computeAssetId(request.value); break;
    case 'verifyAssetId': result = verifyAssetId(request.value); break;
    case 'validateAsset': result = validateAsset(request.value); break;
    default: throw new Error('unsupported_operation');
  }
  process.stdout.write(JSON.stringify({ ok: true, result }) + '\n');
}

main().catch((error) => {
  const known = new Set([
    'unsupported_asset_type', 'request_too_large', 'invalid_json',
    'sdk_version_mismatch', 'invalid_request', 'unsupported_operation',
  ]);
  process.stdout.write(JSON.stringify({
    ok: false, error: known.has(error.message) ? error.message : 'sdk_error',
  }) + '\n');
  process.exitCode = 1;
});
