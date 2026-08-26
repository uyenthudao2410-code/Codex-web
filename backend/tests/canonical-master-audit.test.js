const assert = require('node:assert/strict');
const test = require('node:test');
const {
    auditCanonicalMasterRecords,
    assertAuditsReadyForBackfill,
} = require('../utils/canonicalMasterAudit');

const uuid = {
    one: '11111111-1111-4111-8111-111111111111',
    two: '22222222-2222-4222-8222-222222222222',
};

test('project audit blocks duplicate normalized MaDA before blank canonical backfill', () => {
    const audit = auditCanonicalMasterRecords('projects', [
        { id: '1', eTag: '"1"', fields: { CanonicalProjectId: '', MaDA: 'DA-01' } },
        { id: '2', eTag: '"2"', fields: { CanonicalProjectId: uuid.one, MaDA: ' da-01 ' } },
    ]);
    assert.equal(audit.readyForBackfill, false);
    assert.equal(audit.missingCanonical, 1);
    assert.equal(audit.issues.filter(issue => issue.reason === 'NATURAL_KEY_DUPLICATE').length, 2);
});

test('unit audit blocks duplicate normalized MST', () => {
    const audit = auditCanonicalMasterRecords('units', [
        { id: '3', eTag: '"3"', fields: { CanonicalUnitId: '', MaDV: 'DV003', MaSoThue: '0101-001' } },
        { id: '4', eTag: '"4"', fields: { CanonicalUnitId: uuid.one, MaDV: 'DV004', MaSoThue: '0101001' } },
    ]);
    assert.equal(audit.readyForBackfill, false);
    assert.equal(audit.issues.filter(issue => issue.reason === 'NATURAL_KEY_DUPLICATE').length, 2);
});

test('personnel audit never emits raw CCCD', () => {
    const sensitiveCccd = '001234567890';
    const audit = auditCanonicalMasterRecords('personnel', [
        { id: '5', eTag: '"5"', fields: { CanonicalPersonnelId: '', MaNS: 'STA-005', CCCD: sensitiveCccd } },
    ]);
    assert.equal(audit.readyForBackfill, true);
    assert.deepEqual(audit.assignable, [{ itemId: '5', code: 'STA-005', naturalKeyKind: 'CCCD' }]);
    assert.equal(JSON.stringify(audit).includes(sensitiveCccd), false);
});

test('audit blocks duplicate canonical UUID and missing ETag for an assign candidate', () => {
    const duplicate = auditCanonicalMasterRecords('projects', [
        { id: '6', eTag: '"6"', fields: { CanonicalProjectId: uuid.two, MaDA: 'DA-06' } },
        { id: '7', eTag: '"7"', fields: { CanonicalProjectId: uuid.two, MaDA: 'DA-07' } },
    ]);
    assert.equal(duplicate.readyForBackfill, false);
    assert.equal(duplicate.issues.filter(issue => issue.reason === 'CANONICAL_ID_DUPLICATE').length, 2);

    const missingEtag = auditCanonicalMasterRecords('projects', [
        { id: '8', fields: { CanonicalProjectId: '', MaDA: 'DA-08' } },
    ]);
    assert.equal(missingEtag.readyForBackfill, false);
    assert.ok(missingEtag.issues.some(issue => issue.reason === 'SOURCE_ETAG_REQUIRED'));
});

test('apply guard refuses any non-clean audit while dry-run can report blockers', () => {
    const blockedAudit = auditCanonicalMasterRecords('projects', [
        { id: '9', fields: { CanonicalProjectId: '', MaDA: 'DA-09' } },
    ]);
    assert.equal(assertAuditsReadyForBackfill([blockedAudit], { apply: false }).length, 1);
    assert.throws(
        () => assertAuditsReadyForBackfill([blockedAudit], { apply: true }),
        error => error?.code === 'CANONICAL_MASTER_INTEGRITY_AUDIT_FAILED',
    );
});
