// repo-infra: workflow-lib v1
'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const checks = require('./checks.js');

const PARAMS = { owner: 'oposs', repo: 'repo-infra', ref: 'abc123' };

// A fake Octokit whose paginate returns successive fixtures, one per call.
function fakeGithub(pages) {
  let call = 0;
  return {
    rest: { checks: { listForRef: 'listForRef' } },
    paginate: async () => {
      const page = pages[Math.min(call, pages.length - 1)];
      call += 1;
      return page;
    },
    calls: () => call,
  };
}

const ok = (name) => ({ name, status: 'completed', conclusion: 'success' });
const bad = (name) => ({ name, status: 'completed', conclusion: 'failure' });
const running = (name) => ({ name, status: 'in_progress', conclusion: null });
const skipped = (name) => ({ name, status: 'completed', conclusion: 'skipped' });

test('all checks green is ok', async () => {
  const state = await checks.checkState(fakeGithub([[ok('CI'), ok('Changelog')]]), PARAMS);
  assert.equal(state.ok, true);
  assert.equal(state.total, 2);
});

test('a failure is not ok and is named', async () => {
  const state = await checks.checkState(fakeGithub([[ok('CI'), bad('Changelog')]]), PARAMS);
  assert.equal(state.ok, false);
  assert.deepEqual(state.failed.map((c) => c.name), ['Changelog']);
});

test('a running check is not ok and is named', async () => {
  const state = await checks.checkState(fakeGithub([[ok('CI'), running('Slow')]]), PARAMS);
  assert.equal(state.ok, false);
  assert.deepEqual(state.pending.map((c) => c.name), ['Slow']);
});

test('a skipped check does not count as a failure', async () => {
  const state = await checks.checkState(fakeGithub([[ok('CI'), skipped('Optional')]]), PARAMS);
  assert.equal(state.ok, true);
});

test('no checks at all is not ok', async () => {
  // The dangerous case: releasing a commit nothing ever tested.
  const state = await checks.checkState(fakeGithub([[]]), PARAMS);
  assert.equal(state.ok, false);
  assert.equal(state.total, 0);
});

test('waitForChecks returns as soon as something fails', async () => {
  const github = fakeGithub([[bad('CI')]]);
  const state = await checks.waitForChecks(github, PARAMS, {
    sleep: async () => { throw new Error('should not have slept'); },
  });
  assert.equal(state.ok, false);
  assert.equal(github.calls(), 1);
});

test('waitForChecks polls until pending clears', async () => {
  const github = fakeGithub([
    [running('CI')],
    [running('CI')],
    [ok('CI')],
  ]);
  let slept = 0;
  const state = await checks.waitForChecks(github, PARAMS, {
    sleep: async () => { slept += 1; },
  });
  assert.equal(state.ok, true);
  assert.equal(slept, 2);
});

test('waitForChecks gives up after the timeout', async () => {
  const github = fakeGithub([[running('CI')]]);
  let clock = 0;
  const state = await checks.waitForChecks(github, PARAMS, {
    intervalMs: 1000,
    timeoutMs: 3000,
    now: () => clock,
    sleep: async (ms) => { clock += ms; },
  });
  assert.equal(state.timedOut, true);
  assert.equal(state.ok, false);
});

// --- self-exclusion -------------------------------------------------------
// A job that waits for the checks on its own commit is itself one of those
// checks. Without this, the release guard waits for the job doing the waiting.

const withId = (id, name, status, conclusion) => ({
  id, name, status, conclusion,
});

test('checkState ignores the check runs it is told to ignore', async () => {
  const github = fakeGithub([[
    withId(1, 'CI', 'completed', 'success'),
    withId(2, 'Prepare the release pull request', 'in_progress', null),
  ]]);
  const state = await checks.checkState(github, PARAMS, { ignoreCheckRunIds: [2] });
  assert.equal(state.total, 1);
  assert.deepEqual(state.pending.map((c) => c.name), []);
  assert.equal(state.ok, true);
});

test('waitForChecks does not wait for its own job', async () => {
  // The deadlock this prevents: the guard polled until its 15 minute timeout
  // and reported "Still running: Prepare the release pull request".
  const github = fakeGithub([[
    withId(1, 'CI', 'completed', 'success'),
    withId(2, 'Prepare the release pull request', 'in_progress', null),
  ]]);
  const state = await checks.waitForChecks(github, PARAMS, {
    ignoreCheckRunIds: [2],
    sleep: async () => { throw new Error('should not have slept'); },
  });
  assert.equal(state.ok, true);
  assert.equal(github.calls(), 1);
});

test('a commit whose only check is the ignored job counts as no checks', async () => {
  // Refusing here is the point: nothing else tested this commit.
  const github = fakeGithub([[
    withId(2, 'Prepare the release pull request', 'in_progress', null),
  ]]);
  const state = await checks.checkState(github, PARAMS, { ignoreCheckRunIds: [2] });
  assert.equal(state.total, 0);
  assert.equal(state.ok, false);
});
