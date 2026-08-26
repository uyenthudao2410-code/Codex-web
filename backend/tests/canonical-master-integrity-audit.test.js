const assert = require('node:assert/strict');
const test = require('node:test');
const {
    auditCanonicalMasterRecords,
    assertAuditsReadyForBackfill,
} = require('../utils/canonicalMasterIntegrityAudit');

const UUID_ONE = '11111111-1111-4111-8111-111111111111';
const UUID_TWO = '22222222-2222-4222-8222-222222222222';

test('blocks duplicate Project MaDA and normalized Unit MST', () => {
    const projectAudit = auditCanonicalMasterRecords('projects', [
        { id: '1', eTag: '"1"', fields: { CanonicalProjectId: '', MaDA: 'DA-01' } },
        { id: '2', eTag: '"2"', fields: { CanonicalProjectId: UUID_ONE, MaDA: ' da-01 ' } },
    ]);
    assert.equal(projectAudit.readyForBackfill, false);
    assert.equal(projectAudit.issues.filter(issue => issue.reason === 'NATURAL_KEY_DUPLICATE').length, 2);

    const unitAudit = auditCanonicalMasterRecords('units', [
        { id: '3', eTag: '"3"', fields: { CanonicalUnitId: '', MaDV: 'DV003', MaSoThue: '0101-001' } },
        { id: '4', eTag: '"4"', fields: { CanonicalUnitId: UUID_ONE, MaDV: 'DV004', MaSoThue: '0101001' } },
    ]);
    assert.equal(unitAudit.readyForBackfill, false);
    assert.equal(unitAudit.issues.filter(issue => issue.reason === 'NATURAL_KEY_DUPLICATE').length, 2);
});

test('never emits raw CCCD and requires ETag for blank-canonical assignment', () => {
    const rawCccd = '001234567890';
    const cleanAudit = auditCanonicalMasterRecords('personnel', [
        { id: '5', eTag: '"5"', fields: { CanonicalPersonnelId: '', MaNS: 'STA-005', CCCD: rawCccd } },
    ]);
    assert.equal(cleanAudit.readyForBackfill, true);
    assert.deepEqual(cleanAudit.assignable, [{ itemId: '5', code: 'STA-005', naturalKeyKind: 'CCCD' }]);
    assert.equal(JSON.stringify(cleanAudit).includes(rawCccd), false);

    const missingEtag = auditCanonicalMasterRecords('projects', [
        { id: '8', fields: { CanonicalProjectId: '', MaDA: 'DA-08' } },
    ]);
    assert.equal(missingEtag.readyForBackfill, false);
    assert.ok(missingEtag.issues.some(issue => issue.reason === 'SOURCE_ETAG_REQUIRED'));
});

test('blocks duplicate canonical UUID and apply guard fails closed', () => {
    const duplicateAudit = auditCanonicalMasterRecords('projects', [
        { id: '6', eTag: '"6"', fields: { CanonicalProjectId: UUID_TWO, MaDA: 'DA-06' } },
        { id: '7', eTag: '"7"', fields: { CanonicalProjectId: UUID_TWO, MaDA: 'DA-07' } },
    ]);
    assert.equal(duplicateAudit.issues.filter(issue => issue.reason === 'CANONICAL_ID_DUPLICATE').length, 2);
    assert.equal(assertAuditsReadyForBackfill([duplicateAudit], { apply: false }).length, 1);
    assert.throws(
        () => assertAuditsReadyForBackfill([duplicateAudit], { apply: true }),
        error => error?.code === 'CANONICAL_MASTER_INTEGRITY_AUDIT_FAILED',
    );
});
