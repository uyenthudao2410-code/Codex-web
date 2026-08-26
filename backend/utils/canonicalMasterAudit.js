const { createHash } = require('node:crypto');
const { getCanonicalMasterConfig, isCanonicalUuid } = require('./canonicalMasterIdentity');

function normalizedText(value) {
    return String(value ?? '').normalize('NFKC').trim();
}

function canonicalMasterNaturalKey(masterType, fields = {}) {
    if (masterType === 'personnel') {
        const cccd = normalizedText(fields.CCCD || fields.CMND).replace(/[\s-]+/gu, '');
        return cccd ? { kind: 'CCCD', value: cccd } : null;
    }
    if (masterType === 'projects') {
        const maDA = normalizedText(fields.MaDA).toUpperCase();
        return maDA ? { kind: 'MADA', value: maDA } : null;
    }
    if (masterType === 'units') {
        const taxId = normalizedText(fields.MaSoThue).replace(/[\s-]+/gu, '');
        if (taxId) return { kind: 'MST', value: taxId };
        const representative = normalizedText(
            fields.RepresentativeCanonicalPersonnel || fields.RepresentativeCanonicalPersonnelId
        ).toLowerCase();
        const businessType = normalizedText(fields.BusinessType).toUpperCase();
        return representative && businessType
            ? { kind: 'REPRESENTATIVE_CLASS', value: `${representative}:${businessType}` }
            : null;
    }
    throw new Error(`Unsupported canonical master type: ${masterType}`);
}

function shortHash(value) {
    return createHash('sha256').update(value).digest('hex').slice(0, 16);
}

function sourceFields(item) {
    return item?.fields && typeof item.fields === 'object' ? item.fields : (item || {});
}

function sourceItemId(item, fields) {
    return normalizedText(item?.id ?? fields.Id ?? fields.ID);
}

function sourceEtag(item) {
    return normalizedText(item?.eTag ?? item?.['@odata.etag']);
}

function safeCode(masterType, fields) {
    const value = masterType === 'personnel'
        ? fields.MaNS
        : masterType === 'projects'
            ? fields.MaDA
            : fields.MaDV;
    return normalizedText(value) || null;
}

function auditCanonicalMasterRecords(masterType, items) {
    if (!Array.isArray(items)) throw new Error('items must be an array');
    const config = getCanonicalMasterConfig(masterType);
    const records = [];
    const issues = [];
    const canonicalGroups = new Map();
    const naturalKeyGroups = new Map();

    for (const item of items) {
        const fields = sourceFields(item);
        const itemId = sourceItemId(item, fields);
        const code = safeCode(masterType, fields);
        const canonicalValue = normalizedText(fields[config.sharePointField]).toLowerCase();
        const missingCanonical = !canonicalValue;
        const naturalKey = canonicalMasterNaturalKey(masterType, fields);
        const naturalKeyFingerprint = naturalKey ? shortHash(`${naturalKey.kind}:${naturalKey.value}`) : null;
        const naturalKeyRef = naturalKey ? `${naturalKey.kind}:${naturalKeyFingerprint}` : null;
        const etagPresent = Boolean(sourceEtag(item));

        records.push({
            itemId: itemId || null,
            code,
            missingCanonical,
            naturalKeyKind: naturalKey?.kind || null,
            naturalKeyFingerprint,
            etagPresent,
        });

        if (!itemId) issues.push({ itemId: null, code, reason: 'SOURCE_ITEM_ID_REQUIRED' });
        if (canonicalValue) {
            if (!isCanonicalUuid(canonicalValue)) {
                issues.push({ itemId: itemId || null, code, reason: 'CANONICAL_ID_INVALID' });
            } else {
                const rows = canonicalGroups.get(canonicalValue) || [];
                rows.push(itemId || null);
                canonicalGroups.set(canonicalValue, rows);
            }
        }
        if (naturalKeyRef) {
            const rows = naturalKeyGroups.get(naturalKeyRef) || [];
            rows.push(itemId || null);
            naturalKeyGroups.set(naturalKeyRef, rows);
        } else if (missingCanonical) {
            issues.push({ itemId: itemId || null, code, reason: 'NATURAL_KEY_REQUIRED' });
        }
        if (missingCanonical && !etagPresent) {
            issues.push({ itemId: itemId || null, code, reason: 'SOURCE_ETAG_REQUIRED' });
        }
    }

    for (const [canonicalId, itemIds] of canonicalGroups) {
        if (itemIds.length <= 1) continue;
        const canonicalFingerprint = shortHash(`CANONICAL:${canonicalId}`);
        itemIds.forEach(itemId => issues.push({
            itemId,
            code: null,
            reason: 'CANONICAL_ID_DUPLICATE',
            canonicalFingerprint,
        }));
    }
    for (const [naturalKeyRef, itemIds] of naturalKeyGroups) {
        if (itemIds.length <= 1) continue;
        const [naturalKeyKind, naturalKeyFingerprint] = naturalKeyRef.split(':');
        itemIds.forEach(itemId => issues.push({
            itemId,
            code: null,
            reason: 'NATURAL_KEY_DUPLICATE',
            naturalKeyKind,
            naturalKeyFingerprint,
        }));
    }

    const issueItemIds = new Set(issues.map(issue => issue.itemId).filter(Boolean));
    const assignable = records
        .filter(record => record.missingCanonical && record.itemId && !issueItemIds.has(record.itemId))
        .map(record => ({ itemId: record.itemId, code: record.code, naturalKeyKind: record.naturalKeyKind }));
    const sortedIssues = issues.sort((left, right) => (
        String(left.itemId || '').localeCompare(String(right.itemId || ''))
        || left.reason.localeCompare(right.reason)
    ));

    return {
        masterType,
        total: records.length,
        missingCanonical: records.filter(record => record.missingCanonical).length,
        assignable,
        issueCount: sortedIssues.length,
        readyForBackfill: sortedIssues.length === 0,
        issues: sortedIssues,
    };
}

function assertAuditsReadyForBackfill(audits, { apply = false } = {}) {
    if (!Array.isArray(audits)) throw new Error('audits must be an array');
    const blocking = audits.filter(audit => audit?.readyForBackfill !== true);
    if (apply && blocking.length > 0) {
        const error = new Error('CANONICAL_MASTER_INTEGRITY_AUDIT_FAILED');
        error.code = 'CANONICAL_MASTER_INTEGRITY_AUDIT_FAILED';
        error.blockers = blocking.map(audit => ({ masterType: audit.masterType, issueCount: audit.issueCount }));
        throw error;
    }
    return blocking;
}

module.exports = {
    auditCanonicalMasterRecords,
    assertAuditsReadyForBackfill,
    canonicalMasterNaturalKey,
};
