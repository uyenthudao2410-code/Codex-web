const assert = require('node:assert/strict');
const test = require('node:test');
const unitsRouter = require('../routes/units');
const sharepointService = require('../services/sharepoint');
const logger = require('../logger');

const routeHandler = (method, path) => unitsRouter.stack
    .find(layer => layer.route?.path === path && layer.route.methods[method])
    .route.stack.at(-1).handle;

const createResponse = () => ({
    statusCode: 200,
    body: null,
    status(code) { this.statusCode = code; return this; },
    json(body) { this.body = body; return this; },
});

const restore = (target, key, original) => { target[key] = original; };
const personnelCanonicalId = '11111111-1111-4111-8111-111111111111';

test('representative route rejects ambiguous normalized tax-ID Units without writing', { concurrency: false }, async () => {
    const handler = routeHandler('post', '/representative');
    let writeCalls = 0;
    const originals = {
        getListItem: sharepointService.getListItem,
        getListItems: sharepointService.getListItems,
        getListColumns: sharepointService.getListColumns,
        createListItem: sharepointService.createListItem,
        updateListItem: sharepointService.updateListItem,
        error: logger.error,
    };
    sharepointService.getListItem = async () => ({ CanonicalPersonnelId: personnelCanonicalId, HoTen: 'Representative' });
    sharepointService.getListItems = async () => [
        { id: '91', fields: { CanonicalUnitId: '22222222-2222-4222-8222-222222222222', MaSoThue: '0101234567-001', MaDV: 'DV091' } },
        { id: '92', fields: { CanonicalUnitId: '33333333-3333-4333-8333-333333333333', MaSoThue: '0101234567001', MaDV: 'DV092' } },
    ];
    sharepointService.getListColumns = async () => new Set(['CanonicalUnitId', 'RepresentativeCanonicalPersonnel']);
    sharepointService.createListItem = async () => { writeCalls += 1; };
    sharepointService.updateListItem = async () => { writeCalls += 1; };
    logger.error = () => {};
    try {
        const response = createResponse();
        await handler({ body: { personnelId: '42', canonicalPersonnelId: personnelCanonicalId, representativeType: 'PARTNER_BUSINESS', name: 'Ambiguous unit', maSoThue: '0101234567001' }, user: { email: 'admin@example.test' } }, response);
        assert.equal(response.statusCode, 409);
        assert.equal(response.body.code, 'UNIT_REPRESENTATIVE_TAX_ID_AMBIGUOUS');
        assert.equal(writeCalls, 0);
    } finally {
        restore(sharepointService, 'getListItem', originals.getListItem);
        restore(sharepointService, 'getListItems', originals.getListItems);
        restore(sharepointService, 'getListColumns', originals.getListColumns);
        restore(sharepointService, 'createListItem', originals.createListItem);
        restore(sharepointService, 'updateListItem', originals.updateListItem);
        restore(logger, 'error', originals.error);
    }
});

test('representative route rejects duplicate representative/class relation without MST', { concurrency: false }, async () => {
    const handler = routeHandler('post', '/representative');
    let writeCalls = 0;
    const originals = {
        getListItem: sharepointService.getListItem,
        getListItems: sharepointService.getListItems,
        getListColumns: sharepointService.getListColumns,
        createListItem: sharepointService.createListItem,
        updateListItem: sharepointService.updateListItem,
        error: logger.error,
    };
    sharepointService.getListItem = async () => ({ CanonicalPersonnelId: personnelCanonicalId, HoTen: 'Representative' });
    sharepointService.getListItems = async () => [
        { id: '93', fields: { CanonicalUnitId: '44444444-4444-4444-8444-444444444444', RepresentativeCanonicalPersonnel: personnelCanonicalId, BusinessType: 'Cá nhân/Nhóm nhân công', MaDV: 'DV093' } },
        { id: '94', fields: { CanonicalUnitId: '55555555-5555-4555-8555-555555555555', RepresentativeCanonicalPersonnel: personnelCanonicalId, BusinessType: 'Cá nhân/Nhóm nhân công', MaDV: 'DV094' } },
    ];
    sharepointService.getListColumns = async () => new Set(['CanonicalUnitId', 'RepresentativeCanonicalPersonnel']);
    sharepointService.createListItem = async () => { writeCalls += 1; };
    sharepointService.updateListItem = async () => { writeCalls += 1; };
    logger.error = () => {};
    try {
        const response = createResponse();
        await handler({ body: { personnelId: '42', canonicalPersonnelId: personnelCanonicalId, representativeType: 'CREW', name: 'Ambiguous crew' }, user: { email: 'admin@example.test' } }, response);
        assert.equal(response.statusCode, 409);
        assert.equal(response.body.code, 'UNIT_REPRESENTATIVE_RELATION_AMBIGUOUS');
        assert.equal(writeCalls, 0);
    } finally {
        restore(sharepointService, 'getListItem', originals.getListItem);
        restore(sharepointService, 'getListItems', originals.getListItems);
        restore(sharepointService, 'getListColumns', originals.getListColumns);
        restore(sharepointService, 'createListItem', originals.createListItem);
        restore(sharepointService, 'updateListItem', originals.updateListItem);
        restore(logger, 'error', originals.error);
    }
});

test('generic Unit create rejects ambiguous normalized MST instead of reusing first record', { concurrency: false }, async () => {
    const handler = routeHandler('post', '/');
    let createCalls = 0;
    const originals = {
        getListItems: sharepointService.getListItems,
        createListItem: sharepointService.createListItem,
        error: logger.error,
    };
    sharepointService.getListItems = async () => [
        { id: '81', fields: { CanonicalUnitId: '66666666-6666-4666-8666-666666666666', MaDV: 'DV081', MaSoThue: '0100000081', Name: 'A', UnitType: 'Đối tác' } },
        { id: '82', fields: { CanonicalUnitId: '77777777-7777-4777-8777-777777777777', MaDV: 'DV082', MaSoThue: '0100-000-081', Name: 'B', UnitType: 'Đối tác' } },
    ];
    sharepointService.createListItem = async () => { createCalls += 1; };
    logger.error = () => {};
    try {
        const response = createResponse();
        await handler({ body: { maDV: 'DV099', maSoThue: '0100000081', name: 'Request', unitType: 'Đối tác' }, user: { email: 'admin@example.test' } }, response);
        assert.equal(response.statusCode, 409);
        assert.equal(response.body.code, 'UNIT_TAX_ID_AMBIGUOUS');
        assert.equal(createCalls, 0);
    } finally {
        restore(sharepointService, 'getListItems', originals.getListItems);
        restore(sharepointService, 'createListItem', originals.createListItem);
        restore(logger, 'error', originals.error);
    }
});
