'use strict';

const assert = require('node:assert/strict');
const test = require('node:test');
const { auditCanonicalMasterIntegrity, BLOCK_REASONS } = require('../utils/canonicalIntegrityAudit');

const UUID_A = '11111111-1111-4111-8111-111111111111';
const UUID_B = '22222222-2222-4222-8222-222222222222';

function item(id, fields, eTag = `\"${id}\"`) { return { id: String(id), eTag, fields }; }

test('Personnel audit keeps raw CCCD out of output and allows an ETag-protected blank canonical candidate', () => {
    const rawCccd = '012345678901';
    const result = auditCanonicalMasterIntegrity('personnel', [item(1, { CanonicalPersonnelId: '', CCCD: rawCccd, MaNS: 'NS001' })]);
    assert.equal(result.assignmentCandidateCount, 1);
    assert.equal(result.blockerCount, 0);
    assert.equal(result.readyForAssignment, true);
    assert.equal(JSON.stringify(result).includes(rawCccd), false);
});

test('Project audit blocks duplicate canonical IDs', () => {
    const result = auditCanonicalMasterIntegrity('projects', [
        item(1, { CanonicalProjectId: UUID_A, MaDA: 'DA001' }),
        item(2, { CanonicalProjectId: UUID_A, MaDA: 'DA002' })
    ]);
    assert.equal(result.readyForAssignment, false);
    assert.equal(result.blockerReasonCounts[BLOCK_REASONS.CANONICAL_ID_DUPLICATE], 2);
});

test('Unit audit blocks duplicate normalized MST without emitting the MST value', () => {
    const rawMst = '0101-234-567';
    const result = auditCanonicalMasterIntegrity('units', [
        item(1, { CanonicalUnitId: UUID_A, MST: rawMst, MaDV: 'DV001' }),
        item(2, { CanonicalUnitId: UUID_B, MST: '0101234567', MaDV: 'DV002' })
    ]);
    assert.equal(result.readyForAssignment, false);
    assert.equal(result.blockerReasonCounts[BLOCK_REASONS.NATURAL_KEY_DUPLICATE], 2);
    assert.equal(JSON.stringify(result).includes(rawMst), false);
    assert.equal(result.blockers.every((blocker) => blocker.keyName === 'MST'), true);
});

test('Blank canonical assignment requires ETag and a natural key', () => {
    const result = auditCanonicalMasterIntegrity('projects', [
        item(1, { CanonicalProjectId: '', MaDA: 'DA001' }, null),
        item(2, { CanonicalProjectId: '' }, null)
    ]);
    assert.equal(result.assignmentCandidateCount, 0);
    assert.equal(result.blockerReasonCounts[BLOCK_REASONS.SOURCE_ETAG_REQUIRED], 2);
    assert.equal(result.blockerReasonCounts[BLOCK_REASONS.NATURAL_KEY_REQUIRED], 1);
});

test('Valid unique canonical masters are audit-clean', () => {
    const result = auditCanonicalMasterIntegrity('projects', [
        item(1, { CanonicalProjectId: UUID_A, MaDA: 'DA001' }),
        item(2, { CanonicalProjectId: UUID_B, MaDA: 'DA002' })
    ]);
    assert.equal(result.validCanonicalCount, 2);
    assert.equal(result.missingCanonicalCount, 0);
    assert.equal(result.blockerCount, 0);
    assert.equal(result.readyForAssignment, true);
});
