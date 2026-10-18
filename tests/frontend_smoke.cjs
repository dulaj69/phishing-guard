// Logic smoke test with a minimal DOM double; does not replace browser visual QA.
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const elements = new Map();
function el(id) {
  if (!elements.has(id)) elements.set(id, {value: '', checked: false, hidden: true, disabled: false,
    innerHTML: '', textContent: '', addEventListener() {}, querySelectorAll() { return []; }, insertAdjacentHTML() {}});
  return elements.get(id);
}
let requests = [];
const result = {detection: {normalized_text: 'Call 0771234567', tricks_found: [],
  scam_score: .5, label: 'suspicious', model_version: 'test', language: 'en',
  anatomy: {contacts: [{type: 'phone', normalized: '0771234567'}], tactics: [], primary_action: 'call', harm: 2, zero_link: true}},
  verification: {fact_checks: [], explanation: [], risk: {tier: 'Medium', likelihood: 'Medium', harm: 2, matrix_tier: 'Medium', adjustment: 'none'}},
  warning: {show: true, title: 'Check first', level: 'Medium', lines: [], highlights: [],
    language: 'en', intervention: 'verify_first', verification_prompt: 'Check independently', safe_action: null},
  ai_advice: 'scam'};
const context = vm.createContext({console, performance: {now: () => 100}, setInterval() {},
  alert() {throw Error('Unexpected alert');}, document: {getElementById: el, querySelectorAll: () => []},
  fetch: async (path, options) => {requests.push([path, options]); return {ok: true, json: async () => path === '/scenarios' ? [] : result};}});
vm.runInContext(fs.readFileSync('warn/static/app.js', 'utf8'), context);
(async () => {
  el('mode').value = 'demo'; el('condition').value = 'evidence_aware';
  vm.runInContext("openMessage({id: 'custom', custom: true, text: 'Call 0771234567'})", context);
  await new Promise(resolve => setImmediate(resolve));
  assert.match(el('warning').innerHTML, /Check independently/);
  assert.equal(el('actions').hidden, true);
  vm.runInContext("act('call_sms_number')", context);
  assert.equal(vm.runInContext('state.current.finished', context), false);
  el('cannot-check').onclick();
  assert.equal(el('actions').hidden, false);
  vm.runInContext("act('report')", context);
  assert.equal(vm.runInContext('state.current.finished', context), true);
  assert.equal(requests.filter(r => r[0] === '/decision').length, 0); // demo never logs study truth
  assert.equal(JSON.parse(requests.find(r => r[0] === '/analyze')[1].body).study_mode, false);
  console.log('Frontend logic smoke passed: advice gate, reveal, demo isolation.');
})().catch(error => {console.error(error); process.exitCode = 1;});
