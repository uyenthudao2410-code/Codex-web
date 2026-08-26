const { createHash } = require('node:crypto');
const { getCanonicalMasterConfig, isCanonicalUuid } = require('./canonicalMasterIdentity');

const normalizeText = value => String(value ?? '').normalize('NFKC').trim();
const shortHash = value => createHash('sha256').update(value).digest('hex').slice(0, 16);

function naturalKeyFor(masterType, fields = {}) {
    if (masterType === 'personnel') {
        const value = normalizeText(fields.CCCD || fields.CMND).replace(/[\s-]+/gu, '');
        return value ? { kind: 'CCCD', value } : null;
    }
    if (masterType === 'projects') {
        const value = normalizeText(fields.MaDA).toUpperCase();
        return value ? { kind: 'MADA', value } : null;
    }
    if (masterType === 'units') {
        const taxId = normalizeText(fields.MaSoThue).replace(/[\s-]+/gu, '');
        if (taxId) return { kind: 'MST', value: taxId };
        const representative = normalizeText(
            fields.RepresentativeCanonicalPersonnel || fields.RepresentativeCanonicalPersonnelId
        ).toLowerCase();
        const businessType = normalizeText(fields.BusinessType).toUpperCase();
        return representative && businessType
            ? { kind: 'REPRESENTATIVE_CLASS', value: `${representative}:${businessType}` }
            : null;
    }
    throw new Error(`Unsupported canonical master type: ${masterType}`);
}

function safeCode(masterType, fields) {
    const value = masterType === 'personnel'
        ? fields.MaNS
        : masterType === 'projects'
            ? fields.MaDA
            : fields.MaDV;
    return normalizeText(value) || null;
}

function auditCanonicalMasterRecords(masterType, items) {
    if (!Array.isArray(items)) throw new Error('items must be an array');
    const config = getCanonicalMasterConfig(masterType);
    const rows = [];
    const issues = [];
    const canonicalGroups = new Map();
    const naturalKeyGroups = new Map();

    for (const item of items) {
        const fields = item?.fields && typeof item.fields === 'object' ? item.fields : (item || {});
        const itemId = normalizeText(item?.id ?? fields.Id ?? fields.ID);
        const code = safeCode(masterType, fields);
        const canonicalId = normalizeText(fields[config.sharePointField]).toLowerCase();
        const missingCanonical = !canonicalId;
        const naturalKey = naturalKeyFor(masterType, fields);
        const naturalKeyFingerprint = naturalKey
            ? shortHash(`${naturalKey.kind}:${naturalKey.value}`)
            : null;
        const naturalKeyRef = naturalKey ? `${naturalKey.kind}:${naturalKeyFingerprint}` : null;
        const etag = normalizeText(item?.eTag ?? item?.['@odata.etag']);

        rows.push({
            itemId: itemId || null,
            code,
            missingCanonical,
            naturalKeyKind: naturalKey?.kind || null,
        });

        if (!itemId) issues.push({ itemId: null, code, reason: 'SOURCE_ITEM_ID_REQUIRED' });

        if (canonicalId) {
            if (!isCanonicalUuid(canonicalId)) {
                issues.push({ itemId: itemId || null, code, reason: 'CANONICAL_ID_INVALID' });
            } else {
                canonicalGroups.set(canonicalId, [...(canonicalGroups.get(canonicalId) || []), itemId || null]);
            }
        }

        if (naturalKeyRef) {
            naturalKeyGroups.set(naturalKeyRef, [...(naturalKeyGroups.get(naturalKeyRef) || []), itemId || null]);
        } else if (missingCanonical) {
            issues.push({ itemId: itemId || null, code, reason: 'NATURAL_KEY_REQUIRED' });
        }

        if (missingCanonical && !etag) {
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

    const blockedItemIds = new Set(issues.map(issue => issue.itemId).filter(Boolean));
    const assignable = rows
        .filter(row => row.missingCanonical && row.itemId && !blockedItemIds.has(row.itemId))
        .map(row => ({ itemId: row.itemId, code: row.code, naturalKeyKind: row.naturalKeyKind }));

    issues.sort((left, right) => (
        String(left.itemId || '').localeCompare(String(right.itemId || ''))
        || left.reason.localeCompare(right.reason)
    ));

    return {
        masterType,
        total: rows.length,
        missingCanonical: rows.filter(row => row.missingCanonical).length,
        assignable,
        issueCount: issues.length,
        readyForBackfill: issues.length === 0,
        issues,
    };
}

function assertAuditsReadyForBackfill(audits, { apply = false } = {}) {
    if (!Array.isArray(audits)) throw new Error('audits must be an array');
    const blockers = audits.filter(audit => audit?.readyForBackfill !== true);
    if (apply && blockers.length > 0) {
        const error = new Error('CANONICAL_MASTER_INTEGRITY_AUDIT_FAILED');
        error.code = 'CANONICAL_MASTER_INTEGRITY_AUDIT_FAILED';
        error.blockers = blockers.map(audit => ({
            masterType: audit.masterType,
            issueCount: audit.issueCount,
        }));
        throw error;
    }
    return blockers;
}

module.exports = {
    auditCanonicalMasterRecords,
    assertAuditsReadyForBackfill,
};
