import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { pathToFileURL } from 'node:url';

const file = process.argv[2];
const compiled = process.argv[3];
if (!file || !compiled) throw new Error('Pass generated WSGI JSON and esbuild adapter JS path');
const actual = JSON.parse(readFileSync(file, 'utf8'));
const { adaptInvestigation, adaptShortlist, formatExactUsd, EvidenceBridgeError } =
  await import(pathToFileURL(compiled).href);

function copy(value) { return structuredClone(value); }
function rejects(code, mutate) {
  const response = copy(actual.supported);
  mutate(response);
  assert.throws(
    () => adaptInvestigation(response),
    e => e instanceof EvidenceBridgeError && e.code === code,
    'Expected rejection code: ' + code,
  );
}

const good = adaptInvestigation(actual.supported);
const weak = adaptInvestigation(actual.insufficient);
const list = adaptShortlist(actual.shortlist);

assert.equal(good.contractVersion, 'p3-draft-v0.3');
assert.equal(good.status, 'supported_neighbourhood');
assert.equal(good.selectedCount, 3);
assert.equal(good.comparables.length, 3);
assert.equal(good.askingPriceText, '$500,000.00');
assert.equal(good.comparables[0].exactPriceUsd, '525000.00');
assert.equal(good.comparables[0].priceText, '$525,000.00');
assert.equal(formatExactUsd('9007199254740993.07'), '$9,007,199,254,740,993.07');
assert.equal(good.valuation, null);
assert.equal(good.buildingIdentityVerified, false);
assert.deepEqual(good.location, { available: false, reason: 'no_verified_map_feature_contract' });
assert.ok(good.sourceSnapshotIds.includes('sale-snap'));

assert.equal(weak.status, 'insufficient_data');
assert.equal(weak.selectedCount, 0);
assert.deepEqual(weak.comparables, []);
assert.equal(weak.location.available, false);
assert.equal(weak.valuation, null);

assert.equal(list.maxEntries, 3);
assert.equal(list.entries.length, 2);
assert.deepEqual(list.entries.map(e => e.investigation.status),
  ['supported_neighbourhood', 'insufficient_data']);
assert.deepEqual(list.entries.map(e => e.noteText), ['Review source', 'No evidence']);
assert.deepEqual(list.entries.map(e => e.investigationId),
  list.entries.map(e => e.investigation.investigationId));

// No client-side borrowing of fake diagram coordinates or reassignment of match policy.
for (const view of [good, weak, ...list.entries.map(e => e.investigation)]) {
  assert.equal(view.location.available, false);
  assert.equal('diagramPoint' in view, false);
  assert.equal('coordinates' in view, false);
  assert.equal('sale_price' in view, false);
}

rejects('unsupported_contract', r => { r.contract_version = 'p3-draft-v9'; });
rejects('unexpected_valuation', r => { r.valuation = 515000; });
rejects('non_fixture_source', r => { r.data_build.source_kind = 'actual_publisher'; });
rejects('comparable_count_mismatch', r => { r.selected_count = 1; });
rejects('invalid_sale_money', r => { r.comparables[0].sale_price_usd = '525000.1'; });
rejects('legacy_float_price', r => { r.comparables[0].sale_price = 525000.0; });
rejects('invalid_subject_pin', r => { r.subject.pin = 'not-a-real-pin'; });
rejects('unknown_status', r => { r.status = 'valuation_ready'; });
rejects('missing_source_snapshots', r => { r.data_build.source_snapshot_ids = null; });
rejects('duplicate_sale_identity', r => {
  r.comparables[1].pin = r.comparables[0].pin;
  r.comparables[1].document = r.comparables[0].document;
  r.comparables[1].sale_date = r.comparables[0].sale_date;
});
rejects('unverified_address_identity', r => {
  r.subject.address_id = 'fictional-1';
  r.subject.identity_scope = 'building_verified';
});
assert.throws(() => adaptShortlist({
  ...actual.shortlist,
  entries: [actual.shortlist.entries[0], actual.shortlist.entries[0]],
}), e => e instanceof EvidenceBridgeError && e.code === 'duplicate_members');
assert.throws(() => adaptShortlist({
  ...actual.shortlist,
  entries: [{
    ...actual.shortlist.entries[0], note_text: 'a'.repeat(801),
  }],
}), e => e instanceof EvidenceBridgeError && e.code === 'invalid_note');

rejects('invalid_sale_chronology',r=>{r.comparables[0].age_days=0;});
rejects('invalid_area_difference',r=>{r.comparables[0].size_difference_pct=26;});
rejects('invalid_neighbourhood_evidence',r=>{r.comparables[0].same_neighborhood='yes';});
console.log('PASS: actual WSGI P3/P6 responses, exact cents, unsupported states, 13 tamper guards, geometry unavailable');
