const fs = require('node:fs');
const path = require('node:path');

const root = path.resolve(__dirname, '..');
const lines = (...values) => values.join('\n');

function countOccurrences(text, needle) {
    if (!needle) return 0;
    let count = 0;
    let offset = 0;
    while ((offset = text.indexOf(needle, offset)) !== -1) {
        count += 1;
        offset += needle.length;
    }
    return count;
}

function stageTransform(relativePath, operations) {
    const absolutePath = path.join(root, relativePath);
    const original = fs.readFileSync(absolutePath, 'utf8');
    const eol = original.includes('\r\n') ? '\r\n' : '\n';
    let next = original.replace(/\r\n/gu, '\n');
    for (const [before, after, label] of operations) {
        const occurrences = countOccurrences(next, before);
        if (occurrences !== 1) {
            throw new Error(`${relativePath}:${label}: expected one exact anchor, found ${occurrences}`);
        }
        next = next.replace(before, after);
    }
    return { absolutePath, original, next: eol === '\r\n' ? next.replace(/\n/gu, '\r\n') : next };
}

const migration = stageTransform('backend/migrations/backfill-canonical-master-ids.js', [
    [
        lines(
            "const {",
            "    CANONICAL_MASTER_CONFIG,",
            "    classifyCanonicalMasterRecord",
            "} = require('../utils/canonicalMasterIdentity');"
        ),
        lines(
            "const {",
            "    CANONICAL_MASTER_CONFIG,",
            "    classifyCanonicalMasterRecord",
            "} = require('../utils/canonicalMasterIdentity');",
            "const {",
            "    auditCanonicalMasterRecords,",
            "    assertAuditsReadyForBackfill,",
            "} = require('../utils/canonicalMasterAudit');"
        ),
        'audit-import',
    ],
    [
        lines(
            "        const config = CANONICAL_MASTER_CONFIG[masterType];",
            "        const listId = sharepointService.lists[config.listKey];",
            "        const items = await sharepointService.getListItems(listId);",
            "",
            "        for (const item of items) {"
        ),
        lines(
            "        const config = CANONICAL_MASTER_CONFIG[masterType];",
            "        const listId = sharepointService.lists[config.listKey];",
            "        const items = itemsByMaster.get(masterType) || [];",
            "",
            "        for (const item of items) {"
        ),
        'reuse-audited-items',
    ],
    [
        "    const quarantine = [];",
        lines(
            "    const quarantine = [];",
            "    const audits = [];",
            "    const itemsByMaster = new Map();",
            "",
            "    for (const masterType of masterTypes) {",
            "        const config = CANONICAL_MASTER_CONFIG[masterType];",
            "        const listId = sharepointService.lists[config.listKey];",
            "        const items = await sharepointService.getListItems(listId);",
            "        const audit = auditCanonicalMasterRecords(masterType, items);",
            "        itemsByMaster.set(masterType, items);",
            "        audits.push(audit);",
            "    }",
            "",
            "    const blockingAudits = assertAuditsReadyForBackfill(audits, { apply });"
        ),
        'preflight-audit',
    ],
    [
        "                    { etag: item.eTag }",
        "                    { etag: item.eTag || item['@odata.etag'], requireAllFields: true }",
        'cas-etag',
    ],
    [
        lines("        skipped,", "        quarantine"),
        lines("        skipped,", "        quarantine,", "        audits"),
        'audit-output',
    ],
    [
        "    if (quarantine.length > 0) {",
        "    if (quarantine.length > 0 || blockingAudits.length > 0) {",
        'dry-run-exit-code',
    ],
]);

const units = stageTransform('backend/routes/units.js', [
    [
        lines(
            "const normalizeUnitTaxId = (value) => String(value || '')",
            "    .normalize('NFKC')",
            "    .replace(/\\s+/gu, '')",
            "    .toLowerCase();"
        ),
        lines(
            "const normalizeUnitTaxId = (value) => String(value || '')",
            "    .normalize('NFKC')",
            "    .replace(/[\\s-]+/gu, '')",
            "    .toLowerCase();"
        ),
        'tax-normalizer',
    ],
    [
        "const representativeError = (message, code, status = 400, details = {}) => Object.assign(new Error(message), { code, status, ...details });",
        lines(
            "const representativeError = (message, code, status = 400, details = {}) => Object.assign(new Error(message), { code, status, ...details });",
            "",
            "function uniqueUnitMatch(items, predicate, ambiguityCode) {",
            "    const matches = (items || []).filter(predicate);",
            "    if (matches.length > 1) {",
            "        throw representativeError('Unit identity is ambiguous and requires reconciliation', ambiguityCode, 409);",
            "    }",
            "    return matches[0];",
            "}",
            "",
            "function uniqueUnitByTaxId(items, taxId, ambiguityCode = 'UNIT_TAX_ID_AMBIGUOUS') {",
            "    const normalizedTaxId = normalizeUnitTaxId(taxId);",
            "    if (!normalizedTaxId) return undefined;",
            "    return uniqueUnitMatch(",
            "        items,",
            "        unit => normalizeUnitTaxId(unit?.fields?.MaSoThue) === normalizedTaxId,",
            "        ambiguityCode,",
            "    );",
            "}"
        ),
        'unique-match-helper',
    ],
    [
        lines(
            "                const existing = normalizedTaxId",
            "                    ? existingUnits.find(unit => normalizeRepresentativeTaxId(unit?.fields?.MaSoThue) === normalizedTaxId)",
            "                    : existingUnits.find(unit => (",
            "                        String(unit?.fields?.[representativeStorageField] || '').trim().toLowerCase() === personnel.canonicalPersonnelId",
            "                        && String(unit?.fields?.BusinessType || '').trim() === representativeConfig.businessType",
            "                    ));"
        ),
        lines(
            "                const existing = normalizedTaxId",
            "                    ? uniqueUnitByTaxId(existingUnits, normalizedTaxId, 'UNIT_REPRESENTATIVE_TAX_ID_AMBIGUOUS')",
            "                    : uniqueUnitMatch(",
            "                        existingUnits,",
            "                        unit => (",
            "                            String(unit?.fields?.[representativeStorageField] || '').trim().toLowerCase() === personnel.canonicalPersonnelId",
            "                            && String(unit?.fields?.BusinessType || '').trim() === representativeConfig.businessType",
            "                        ),",
            "                        'UNIT_REPRESENTATIVE_RELATION_AMBIGUOUS',",
            "                    );"
        ),
        'representative-cardinality',
    ],
    [
        lines(
            "                const duplicate = existingUnits.find((unit) => (",
            "                    normalizeUnitTaxId(unit?.fields?.MaSoThue) === normalizeUnitTaxId(sanitized.maSoThue)",
            "                ));"
        ),
        "                const duplicate = uniqueUnitByTaxId(existingUnits, sanitized.maSoThue);",
        'create-cardinality',
    ],
]);

for (const staged of [migration, units]) {
    if (fs.readFileSync(staged.absolutePath, 'utf8') !== staged.original) {
        throw new Error(`${staged.absolutePath}: source changed during guarded transform`);
    }
}
for (const staged of [migration, units]) fs.writeFileSync(staged.absolutePath, staged.next, 'utf8');
console.log('C1-B guarded source transform applied.');
