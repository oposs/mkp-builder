# Releasing

This repo ships two things, released **together** from a single version stream:

- **The `mkp-builder` GitHub Action** — consumers pin `oposs/mkp-builder@v2`.
- **The `cmk-oposs-plugin` Claude Code plugin** — the `skills/` tree, versioned by
  `.claude-plugin/plugin.json`.

## The version stream

Git tags (`v2.2.0`, …) with a moving major tag (`@v2`) drive both. A release runs in two
halves, because `main` is protected — see [Why a PR](#why-a-pr) below.

**1. Run the `Release` workflow** (`workflow_dispatch`, bugfix/feature/major). It:

1. computes the next version from the latest tag, and refuses if that tag already exists,
2. rolls the `CHANGES.md` `## [Unreleased]` section into a dated version section,
3. **rewrites `.claude-plugin/plugin.json` to the same version**,
4. pushes a `release/vX.Y.Z` branch and opens a PR.

Nothing is tagged or published yet. Closing the PR cancels the release.

**2. Review the changelog and merge the PR.** That triggers `Publish release`, which
reads the version back out of `plugin.json`, tags it, moves `@vX`, and publishes the
GitHub release with the notes from `CHANGES.md`.

Publishing is idempotent: if the version in `plugin.json` is already tagged it does
nothing. Re-runs, manual dispatches and unrelated pushes to `main` are all harmless.

### Why a PR

`main` is protected by a repository ruleset, and the built-in `GITHUB_TOKEN` **cannot** be
given a bypass — the bypass list accepts users, teams, and GitHub Apps, and the Actions
token is none of those. The alternatives were a GitHub App or a deploy key, i.e. a
credential to store and rotate so a workflow could push a single commit. Landing the
release through a PR instead needs no credential and works with the protection rather
than around it. Tagging is unaffected: the ruleset targets branches, and tags live in a
separate ref namespace.

`plugin.json` remains the single source of truth for the plugin version — Claude Code
resolves `plugin.json → marketplace entry → commit SHA`, and `plugin.json` wins. The
marketplace entry in [`oposs/claude-plugins`](https://github.com/oposs/claude-plugins)
therefore carries **no** `version` field for this plugin (a stale duplicate silently
masks the real one). The workflow keeps `plugin.json` equal to the tag so the two
version lines cannot drift apart.

### Releasing a plugin or skill change

1. Make the change under `skills/` and merge it to `main`.
2. Run the **Release** workflow, then merge the release PR it opens. `plugin.json` is
   bumped for you — there is no hand-written bump commit any more.
3. Users run `/plugin marketplace update` then `/plugin update cmk-oposs-plugin`.

Nothing else is needed here. Claude only re-resolves plugin versions when it re-fetches
the marketplace, so the marketplace repository has to move as well — but that is handled
from the other side: [`oposs/claude-plugins`](https://github.com/oposs/claude-plugins)
runs an hourly **Track plugin versions** workflow that reads this repository's
`plugin.json` and commits when the version changes.

That direction was chosen deliberately. A push from here would need a credential for
another repository (the org restricts fine-grained PATs, leaving a deploy key or a
GitHub App). Polling from the marketplace needs no credential at all, covers every
plugin instead of only those wired up to push, and still catches a version bumped
outside the release workflow.

> **Why the version bump matters.** Claude caches a plugin under its resolved version and
> reads the skill from `~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/`.
> Merging a skill fix without moving the version ships nothing — every Claude keeps
> reading the old cached copy, with no error and no signal that anything is stale. While
> this was a manual step it was missed often enough that an installed copy was found 10
> commits and three merged skill fixes behind `main`. That is why step 3 of the release
> workflow now enforces it.
