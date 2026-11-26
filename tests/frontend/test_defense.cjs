const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const { resolve } = require('node:path');
const { test } = require('node:test');
const vm = require('node:vm');

const componentSource = readFileSync(resolve(__dirname, '../../gui/js/defense.js'), 'utf8');

test('submitAnswer sends the active turn index and advances to the returned turn', async () => {
  const calls = [];
  const app = {
    async api(path, options) {
      const body = JSON.parse(options.body);
      calls.push({ path, method: options.method, body });
      return { id: 'defense-1', current_turn_index: body.turn_index + 1 };
    },
    toast() {},
    async refreshActiveProject() {},
  };
  const component = vm.runInNewContext(`${componentSource}\ndefenseComponent()`, {
    Alpine: { store: () => app },
  });
  component.activeSession = { id: 'defense-1', current_turn_index: 0 };

  component.studentAnswer = ' Primera respuesta ';
  await component.submitAnswer();
  component.studentAnswer = 'Segunda respuesta';
  await component.submitAnswer();

  assert.deepEqual(calls, [
    { path: '/api/defense/sessions/defense-1/reply', method: 'POST',
      body: { turn_index: 0, student_answer: 'Primera respuesta' } },
    { path: '/api/defense/sessions/defense-1/reply', method: 'POST',
      body: { turn_index: 1, student_answer: 'Segunda respuesta' } },
  ]);
  assert.equal(component.activeSession.current_turn_index, 2);
  assert.equal(component.studentAnswer, '');
});
