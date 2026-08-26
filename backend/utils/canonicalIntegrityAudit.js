'use strict';

const { getCanonicalMasterConfig, isCanonicalUuid } = require('./canonicalMasterIdentity');

const NATURAL_KEY_SPECS = Object.freeze({
    personnel: Object.freeze([
        Object.freeze({ name: 'CCCD', fields: Object.freeze(['CCCD', 'SoCCCD', 'CitizenId']), normalize: normalizeDigits }),
        Object.freeze({ name: 'MaNS', fields: Object.freeze(['MaNS', 'EmployeeCode']), normalize: normalizeText })
    ]),
    projects: Object.freeze([
        Object.freeze({ name: 'MaDA', fields: Object.freeze(['MaDA', 'ProjectCode', 'Code']), normalize: normalizeText })
    ]),
    units: Object.freeze([
        Object.freeze({ name: 'MST', fields: Object.freeze(['MST', 'MaSoThue', 'TaxCode']), normalize: normalizeDigits }),
        Object.freeze({ name: 'MaDV', fields: Object.freeze(['MaDV', 'UnitCode', 'Code']), normalize: normalizeText })
    ])
});

const BLOCK_REASONS = Object.freeze({
    CANONICAL_ID_INVALID: 'CANONICAL_ID_INVALID',
    CANONICAL_ID_DUPLICATE: 'CANONICAL_ID_DUPLICATE',
    NATURAL_KEY_DUPLICATE: 'NATURAL_KEY_DUPLICATE',
    NATURAL_KEY_REQUIRED: 'NATURAL_KEY_REQUIRED',
    SOURCE_ETAG_REQUIRED: 'SOURCE_ETAG_REQUIRED',
    SOURCE_ITEM_ID_REQUIRED: 'SOURCE_ITEM_ID_REQUIRED'
});

function normalizeText(value) {
    return String(value ?? '').trim().toUpperCase();
}

function normalizeDigits(value) {
    return String(value ?? '').replace(/\D/gu, '');
}

function getFields(item) {
    return item?.fields && typeof item.fields === 'object' ? item.fields : (item || {});
}

function sourceRecordIdFor(item) {
    const fields = getFields(item);
    const value = item?.id ?? fields.Id ?? fields.ID;
    const normalized = String(value ?? '').trim();
    return normalized || null;
}

function sourceEtagFor(item) {
    const value = item?.eTag ?? item?.['@odata.etag'] ?? item?._etag;
    const normalized = String(value ?? '').trim();
    return normalized || null;
}

function firstFieldValue(fields, names) {
    for (const name of names) {
        if (fields?.[name] !== undefined && fields?.[name] !== null && String(fields[name]).trim() !== '') return fields[name];
    }
    return null;
}

function collectNaturalKeys(masterType, item) {
    const specs = NATURAL_KEY_SPECS[masterType];
    if (!specs) throw new Error(`Unsupported canonical master type: ${masterType}`);
    const fields = getFields(item);
    return specs.flatMap((spec) => {
        const rawValue = firstFieldValue(fields, spec.fields);
        if (rawValue === null) return [];
        const normalized = spec.normalize(rawValue);
        return normalized ? [{ name: spec.name, normalized }] : [];
    });
}

function auditCanonicalMasterIntegrity(masterType, items) {
    if (!Array.isArray(items)) throw new Error('items must be an array');
    const config = getCanonicalMasterConfig(masterType);
    if (!NATURAL_KEY_SPECS[masterType]) throw new Error(`Unsupported canonical master type: ${masterType}`);

    const records = items.map((item) => {
        const fields = getFields(item);
        return {
            sourceRecordId: sourceRecordIdFor(item),
            sourceEtag: sourceEtagFor(item),
            canonicalRaw: String(fields?.[config.sharePointField] ?? '').trim(),
            naturalKeys: collectNaturalKeys(masterType, item)
        };
    });

    const canonicalCounts = new Map();
    const naturalKeyCounts = new Map();
    for (const record of records) {
        if (record.canonicalRaw && isCanonicalUuid(record.canonicalRaw)) {
            const key = record.canonicalRaw.toLowerCase();
            canonicalCounts.set(key, (canonicalCounts.get(key) ?? 0) + 1);
        }
        for (const naturalKey of record.naturalKeys) {
            const key = `${naturalKey.name}:${naturalKey.normalized}`;
            naturalKeyCounts.set(key, (naturalKeyCounts.get(key) ?? 0) + 1);
        }
    }

    const blockers = [];
    const assignmentCandidates = [];
    let validCanonicalCount = 0;
    let missingCanonicalCount = 0;
    const addBlocker = (record, reason, extra = {}) => blockers.push({ masterType, sourceRecordId: record.sourceRecordId, reason, ...extra });

    for (const record of records) {
        if (!record.sourceRecordId) {
            addBlocker(record, BLOCK_REASONS.SOURCE_ITEM_ID_REQUIRED);
            continue;
        }
        if (record.canonicalRaw) {
            if (!isCanonicalUuid(record.canonicalRaw)) {
                addBlocker(record, BLOCK_REASONS.CANONICAL_ID_INVALID);
                continue;
            }
            validCanonicalCount += 1;
            if ((canonicalCounts.get(record.canonicalRaw.toLowerCase()) ?? 0) > 1) addBlocker(record, BLOCK_REASONS.CANONICAL_ID_DUPLICATE);
        } else {
            missingCanonicalCount += 1;
            if (record.naturalKeys.length === 0) addBlocker(record, BLOCK_REASONS.NATURAL_KEY_REQUIRED);
            if (!record.sourceEtag) addBlocker(record, BLOCK_REASONS.SOURCE_ETAG_REQUIRED);
        }
        for (const naturalKey of record.naturalKeys) {
            const key = `${naturalKey.name}:${naturalKey.normalized}`;
            if ((naturalKeyCounts.get(key) ?? 0) > 1) addBlocker(record, BLOCK_REASONS.NATURAL_KEY_DUPLICATE, { keyName: naturalKey.name });
        }
        if (!record.canonicalRaw && record.naturalKeys.length > 0 && record.sourceEtag
            && !blockers.some((blocker) => blocker.sourceRecordId === record.sourceRecordId)) {
            assignmentCandidates.push({ sourceRecordId: record.sourceRecordId, sourceEtag: record.sourceEtag });
        }
    }

    const blockerReasonCounts = blockers.reduce((counts, blocker) => {
        counts[blocker.reason] = (counts[blocker.reason] ?? 0) + 1;
        return counts;
    }, {});

    return {
        masterType,
        processed: records.length,
        validCanonicalCount,
        missingCanonicalCount,
        assignmentCandidateCount: assignmentCandidates.length,
        assignmentCandidates,
        blockerCount: blockers.length,
        blockerReasonCounts,
        blockers,
        readyForAssignment: blockers.length === 0
    };
}

module.exports = { BLOCK_REASONS, NATURAL_KEY_SPECS, auditCanonicalMasterIntegrity };
