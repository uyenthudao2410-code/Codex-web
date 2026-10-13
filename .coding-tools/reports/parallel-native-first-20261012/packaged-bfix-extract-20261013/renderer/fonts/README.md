# Bundled webfont provenance

These six WOFF2 files are unchanged copies of the Google Fonts distributor
artifacts pinned by URL, size and SHA-256 in [provenance.json](provenance.json).
An HTTPS revalidation on 2026-09-05 compared every downloaded artifact with its
existing local file using byte equality as well as SHA-256. The files were not
replaced, converted, renamed internally, or subset again in this repository.

This is a current exact-artifact verification, **not** a reconstruction of the
original local acquisition time. That time is unknown. Google Fonts' internal
build/subsetting parameters are also not recorded here; the receipt identifies
the actual versioned distribution artifacts instead of asserting a reproducible
upstream build. The `v24`/`v12` URL segments are distributor versions, not the
embedded OpenType version numbers.

Local OpenType metadata was read using FontTools 4.60.1 with Node's Brotli
decompressor. JetBrains Mono declares `Version 2.211`, weight axis 100–800;
Plus Jakarta Sans declares `Version 2.071;gftools[0.9.30]`, weight axis 200–800.
Their embedded copyright and OFL URL agree with the upstream projects. The
matching official CSS selects normal-style Vietnamese, Latin Extended and
Latin subsets; the exact CSS request and user agent are in the manifest.

## Notices and license

- JetBrains Mono: Copyright 2020 The JetBrains Mono Project Authors.
  Upstream: [JetBrains/JetBrainsMono](https://github.com/JetBrains/JetBrainsMono).
  Distributed license: [JetBrainsMono-OFL.txt](JetBrainsMono-OFL.txt).
- Plus Jakarta Sans: Copyright 2020 The Plus Jakarta Sans Project Authors.
  Upstream: [tokotype/PlusJakartaSans](https://github.com/tokotype/PlusJakartaSans).
  Distributed license: [PlusJakartaSans-OFL.txt](PlusJakartaSans-OFL.txt).

Both font families remain under SIL Open Font License 1.1, not the application's
license. The copied OFL files retain the full copyright, conditions and
disclaimer. Only line endings/trailing horizontal whitespace were normalized;
the manifest records both upstream and distributed-text hashes. The pinned
upstream OFL headers do not declare Reserved Font Names. No endorsement by the
font authors is claimed.

`package.json` includes `renderer/**/*` and `THIRD_PARTY_NOTICES.md`, so the font
binaries, manifest and these notices are in the same package input set. This is
source/package-input coverage, not proof that an installer was built or tested.

Run the offline integrity and integration checks from the repository root:

```text
node --test tests/font-provenance.test.js tests/token-dashboard.test.js
```

Before accepting replacement font bytes, fetch the exact proposed official
artifact, compare its bytes/hash, inspect its metadata/license, and update the
manifest and notices together. A changed manifest alone is not new upstream
verification. Do not change a hash merely to make a test pass.
