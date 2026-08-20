# Releasing

This repo ships one thing: the **`mkp-builder` GitHub Action**. Consumers pin
`oposs/mkp-builder@v2`.

(The `cmk-oposs-plugin` Claude Code skill used to be released from here too. It now lives
in [`oposs/cmk-oposs-plugin`](https://github.com/oposs/cmk-oposs-plugin) with its own
version stream, because one number could not honestly describe both.)

## The version stream

Git tags (`v2.2.0`, …) with a moving major tag (`@v2`). A release runs in two halves,
because `main` is protected — see [Why a PR](#why-a-pr) below.

**1. Run the `Create release PR` workflow** (`workflow_dispatch`, bugfix/feature/major). It:

1. computes the next version from the latest tag, and refuses if that tag already exists,
2. rolls the `CHANGES.md` `## [Unreleased]` section into a dated version section,
3. pushes a `release/vX.Y.Z` branch and opens a PR.

Nothing is tagged or published yet. Closing the PR cancels the release.

**2. Review the changelog and merge the PR.** That triggers `Release publisher`, which
reads the version back out of `CHANGES.md`, tags it, moves `@vX`, and publishes the GitHub
release with the notes from that section.

`CHANGES.md` is the single source of truth for the version. The first `##` heading carrying
a semver is the newest release; `## [Unreleased]` has no digits and is skipped, so a
changelog with nothing released matches nothing and the publisher fails rather than tagging
something arbitrary.

`Release publisher` has **no manual trigger, by design** — publishing should be a
consequence of merging a release PR, never something anyone starts by hand. With `main`
protected against direct pushes, that leaves exactly one route to a release. If a run
fails, re-run it from the Actions UI; the version comes from the repository rather than
from run inputs, so a re-run does exactly what the original attempt would have.

Publishing is idempotent: if the newest version in `CHANGES.md` is already tagged it does
nothing. That matters more now than it used to, because the publisher triggers on any push
to `main` that touches `CHANGES.md` — including an ordinary PR that only adds an
`[Unreleased]` entry. Such a push resolves to the already-tagged newest release and stops.

### Why a PR

`main` is protected by a repository ruleset, and the built-in `GITHUB_TOKEN` **cannot** be
given a bypass — the bypass list accepts users, teams, and GitHub Apps, and the Actions
token is none of those. The alternatives were a GitHub App or a deploy key, i.e. a
credential to store and rotate so a workflow could push a single commit. Landing the
release through a PR instead needs no credential and works with the protection rather
than around it. Tagging is unaffected: the ruleset targets branches, and tags live in a
separate ref namespace.

### Releasing an action change

1. Make the change to `action.yml` or `mkp-builder.py`, add a `CHANGES.md` entry under
   `## [Unreleased]`, and merge to `main`.
2. Run the **Create release PR** workflow, then merge the release PR it opens.

Consumers pinning `@v2` pick it up as soon as the major tag moves. Nothing else is needed.
