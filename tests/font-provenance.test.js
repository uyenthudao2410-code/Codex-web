const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');

const root = path.resolve(__dirname, '..');
const fontsRoot = path.join(root, 'renderer', 'fonts');
const read = (relative) => fs.readFileSync(path.join(root, relative), 'utf8');
const provenance = JSON.parse(read('renderer/fonts/provenance.json'));
const sha256 = (bytes) => crypto.createHash('sha256').update(bytes).digest('hex');

test('every bundled WOFF2 matches its exact distributor artifact receipt', () => {
  assert.equal(provenance.schema_version, 1);
  assert.equal(provenance.status, 'VERIFIED_EXACT_DISTRIBUTOR_ARTIFACTS');
  assert.equal(provenance.original_local_acquisition_at, null);
  assert.equal(provenance.files.length, 6);
  assert.deepEqual(
    fs.readdirSync(fontsRoot).filter((file) => file.endsWith('.woff2')).sort(),
    provenance.files.map((entry) => entry.file).sort()
  );
  for (const entry of provenance.files) {
    assert.equal(path.basename(entry.file), entry.file);
    const family = provenance.families[entry.family];
    assert.ok(family, entry.family);
    const source = new URL(entry.source_url);
    assert.equal(source.protocol, 'https:');
    assert.equal(source.hostname, 'fonts.gstatic.com');
    assert.ok(source.pathname.startsWith(family.distributor_path));
    assert.match(entry.sha256, /^[a-f0-9]{64}$/);
    const bytes = fs.readFileSync(path.join(fontsRoot, entry.file));
    assert.equal(bytes.subarray(0, 4).toString('ascii'), 'wOF2');
    assert.equal(bytes.length, entry.bytes, entry.file);
    assert.equal(sha256(bytes), entry.sha256, entry.file);
  }
});

test('CSS declares the actual bundled variable-font weight axes and all six sources', () => {
  const css = read('renderer/fonts.css');
  const faces = [...css.matchAll(/@font-face\s*\{([^}]+)\}/g)].map((match) => match[1]);
  assert.equal(faces.length, provenance.files.length);
  assert.deepEqual(provenance.families['JetBrains Mono'].weight_axis, { min: 100, default: 400, max: 800 });
  assert.deepEqual(provenance.families['Plus Jakarta Sans'].weight_axis, { min: 200, default: 400, max: 800 });
  for (const entry of provenance.files) {
    const matching = faces.filter((face) => face.includes(`./fonts/${entry.file}`));
    assert.equal(matching.length, 1, entry.file);
    assert.ok(matching[0].includes(`font-family: '${entry.family}';`));
    const axis = provenance.families[entry.family].weight_axis;
    assert.ok(matching[0].includes(`font-weight: ${axis.min} ${axis.max};`));
    assert.match(matching[0], /font-style:\s*normal;/);
    assert.match(matching[0], /font-display:\s*swap;/);
  }
});

test('full font licenses and attribution travel with the package input set', () => {
  const notice = read('THIRD_PARTY_NOTICES.md');
  const buildFiles = JSON.parse(read('package.json')).build.files;
  assert.ok(buildFiles.includes('renderer/**/*'));
  assert.ok(buildFiles.includes('THIRD_PARTY_NOTICES.md'));
  assert.equal(provenance.license, 'OFL-1.1');
  assert.ok(notice.includes('renderer/fonts/provenance.json'));
  for (const [name, family] of Object.entries(provenance.families)) {
    const license = fs.readFileSync(path.join(fontsRoot, family.license_file));
    assert.equal(sha256(license), family.license_file_sha256, family.license_file);
    assert.ok(license.toString('utf8').startsWith(family.copyright));
    assert.match(license.toString('utf8'), /SIL OPEN FONT LICENSE Version 1\.1 - 26 February 2007/);
    assert.match(license.toString('utf8'), /PERMISSION & CONDITIONS/);
    assert.match(license.toString('utf8'), /TERMINATION/);
    assert.match(license.toString('utf8'), /DISCLAIMER/);
    assert.match(family.license_source_url, /githubusercontent\.com\/[^/]+\/[^/]+\/[a-f0-9]{40}\/OFL\.txt$/);
    assert.ok(notice.includes(name));
    assert.ok(notice.includes(`renderer/fonts/${family.license_file}`));
  }
});
