'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const source = fs.readFileSync(path.join(__dirname, '..', 'renderer/work-hub.js'), 'utf8');
function section(start, end) {
  const from = source.indexOf(start), to = source.indexOf(end, from);
  assert.ok(from >= 0 && to > from, `Missing UI fragment: ${start}`);
  return source.slice(from, to);
}
function deferred() {
  let resolve;
  const promise = new Promise((done) => { resolve = done; });
  return { promise, resolve };
}
function node(text = '') {
  return {
    text, children: [],
    append(...children) { this.children.push(...children); },
    replaceChildren(...children) { this.children = children; },
    addEventListener() {},
    get textContent() { return this.text + this.children.map((child) => child.textContent).join(''); },
  };
}
function fixture() {
  let workspace = 'E:/alpha';
  const replies = [], boxes = new Map();
  for (const selector of ['#whTaskBoard', '#whWorkerList', '#whTargetList']) boxes.set(selector, node());
  const request = () => { const reply = deferred(); replies.push(reply); return reply.promise; };
  const context = vm.createContext({
    ui: { requests: {}, gen: 0, taskPayload: null },
    currentProject: () => workspace,
    $: (selector) => boxes.get(selector),
    el: (_tag, _className, text) => node(text),
    smallButton: (text) => node(text),
    unwrap: (value) => value,
    window: { mcpAssistant: { taskHistory: request, orchestration: request, listControlPlaneWorkspaces: request } },
  });
  vm.runInContext(section('  function requestScope(', '  function saveCurrentDraft('), context);
  vm.runInContext(section('  async function renderTaskBoard(', '  function renderIntegrations('), context);
  return { context, replies, boxes, switchProject() { workspace = 'E:/beta'; context.ui.gen += 1; } };
}

const cases = [
  ['renderTaskBoard', '#whTaskBoard', (label) => [{ objective: label, status: 'done' }]],
  ['renderWorkers', '#whWorkerList', (label) => ({ clients: [{ client_id: label, online: true }] })],
  ['renderTargets', '#whTargetList', (label) => [{ name: label, path: '/workspace' }]],
];

for (const [method, selector, payload] of cases) {
  for (const switchProject of [false, true]) {
    test(`${method} ignores a stale response after ${switchProject ? 'changing project' : 'a newer refresh'}`, async () => {
      const f = fixture();
      const oldRender = f.context[method]();
      if (switchProject) f.switchProject();
      const latestRender = f.context[method]();
      f.replies[1].resolve(payload('latest-result'));
      await latestRender;
      assert.match(f.boxes.get(selector).textContent, /latest-result/);
      if (switchProject && method === 'renderTargets') assert.match(f.boxes.get(selector).textContent, /E:\/beta/);
      const accepted = f.boxes.get(selector).textContent;
      f.replies[0].resolve(payload('stale-result'));
      await oldRender;
      assert.equal(f.boxes.get(selector).textContent, accepted);
      assert.doesNotMatch(f.boxes.get(selector).textContent, /stale-result/);
    });
  }
}
