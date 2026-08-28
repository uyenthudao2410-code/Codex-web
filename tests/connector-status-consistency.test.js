const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

function connectorPresentation() {
  const source = fs.readFileSync(path.resolve(__dirname, '..', 'renderer', 'app.js'), 'utf8');
  const start = source.indexOf('function connectorContractPresentation');
  const end = source.indexOf('// The backend is the authority', start);
  assert.ok(start >= 0 && end > start);
  const context = vm.createContext({});
  vm.runInContext(source.slice(start, end), context, { filename: 'renderer/app-connector-presentation.js' });
  return context.connectorContractPresentation;
}

test('Command Center refuses green acknowledged state while acknowledgement is still pending', () => {
  const present = connectorPresentation();
  const contradictory = present({
    connectorContractState: 'CURRENT_ACKNOWLEDGED',
    connectorRefreshRequired: false,
    connectorAcknowledgementPending: true
  });
  assert.equal(contradictory.state, 'UNAVAILABLE');
  assert.equal(contradictory.notice, true);
  assert.match(contradictory.message, /mâu thuẫn/);

  const converged = present({
    connectorContractState: 'CURRENT_ACKNOWLEDGED',
    connectorRefreshRequired: false,
    connectorAcknowledgementPending: false
  });
  assert.equal(converged.state, 'CURRENT_ACKNOWLEDGED');
  assert.equal(converged.notice, false);
});
