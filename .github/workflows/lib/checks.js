// repo-infra: workflow-lib v1
'use strict';

// Everything that reported on the commit, whatever workflow produced it. The
// previous version polled listWorkflowRuns for a hardcoded 'test.yml', which
// saw one workflow and broke whenever a repo named its CI something else.
const PASSING = new Set(['success', 'neutral', 'skipped']);

async function checkState(github, { owner, repo, ref }, opts = {}) {
  const all = await github.paginate(github.rest.checks.listForRef, {
    owner, repo, ref, per_page: 100,
  });

  // A job that waits for the checks on its own commit is itself one of those
  // checks, so without this the caller waits for the job doing the waiting.
  // Ids are the Actions job ids: a check run's id and its job id are the same
  // number, so listJobsForWorkflowRun(context.runId) yields exactly this set.
  const ignore = new Set(opts.ignoreCheckRunIds || []);
  const runs = all.filter((r) => !ignore.has(r.id));

  const pending = runs.filter((r) => r.status !== 'completed');
  const failed = runs.filter(
    (r) => r.status === 'completed' && !PASSING.has(r.conclusion),
  );

  return {
    total: runs.length,
    pending,
    failed,
    // Zero checks is not success. Releasing a commit that nothing tested is
    // exactly the state this guard exists to prevent.
    ok: runs.length > 0 && pending.length === 0 && failed.length === 0,
  };
}

async function waitForChecks(github, params, opts = {}) {
  const intervalMs = opts.intervalMs ?? 15000;
  const timeoutMs = opts.timeoutMs ?? 15 * 60 * 1000;
  const sleep = opts.sleep ?? ((ms) => new Promise((r) => { setTimeout(r, ms); }));
  const now = opts.now ?? (() => Date.now());

  const started = now();
  for (;;) {
    const state = await checkState(github, params, opts);
    if (state.failed.length > 0) return state;
    if (state.pending.length === 0) return state;
    if (now() - started >= timeoutMs) return { ...state, timedOut: true };
    await sleep(intervalMs);
  }
}

module.exports = { checkState, waitForChecks };
