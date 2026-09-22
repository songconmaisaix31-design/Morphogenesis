// Exercise installed official helpers and schema. No local hashing implementation.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const Ajv = require('ajv');
const addFormats = require('ajv-formats');

(async () => {
  const sdk = await import('@evomap/gep-sdk');
  const ajv = new Ajv({ allErrors: true, strict: false, allowUnionTypes: true });
  addFormats(ajv);
  const schema = JSON.parse(fs.readFileSync(require.resolve('@evomap/gep-sdk/schemas/gene.schema.json'), 'utf8'));
  const validate = ajv.compile(schema);
  const asset = {
    type: 'Gene', schema_version: sdk.SCHEMA_VERSION, id: 'local_contract_probe',
    category: 'repair', signals_match: ['boundary_case'],
    strategy: ['Check the documented boundary cases'],
    constraints: { max_files: 1, forbidden_paths: ['.git'] },
    validation: ['independent fixed exercise cases'],
  };
  asset.asset_id = sdk.computeAssetId(asset);
  assert.equal(validate(asset), true, JSON.stringify(validate.errors));
  assert.equal(sdk.verifyAssetId(asset), true);
  assert.equal(sdk.verifyAssetId({ ...asset, strategy: ['tampered'] }), false);
  assert.equal(validate({ ...asset, category: 'invalid' }), false);
  assert.equal(sdk.canonicalize({ b: 2, a: 1 }), '{"a":1,"b":2}');
  console.log(JSON.stringify({ scope: 'contract_local', schema_version: sdk.SCHEMA_VERSION,
    schema_valid: true, asset_id_verified: true, tampering_rejected: true, published: false }));
})().catch((error) => { console.error(error); process.exitCode = 1; });
