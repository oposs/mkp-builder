# Releasing

This repo ships one thing: the **`mkp-builder` GitHub Action**. Consumers pin
`oposs/mkp-builder@v2`.

(The `cmk-oposs-plugin` Claude Code skill used to be released from here too. It now lives
in [`oposs/cmk-oposs-plugin`](https://github.com/oposs/cmk-oposs-plugin) with its own
version stream, because one number could not honestly describe both.)

The release workflows come from the `oposs/repo-infra` standard and are not edited here.
What is specific to this repository lives in `.github/repo-infra.json`:

- `moving_major_tag: true` — publishing moves the floating `v2` tag as well as creating
  the exact `v2.Y.Z` one. Every consumer pins the floating tag, so this is the setting
  that decides whether a release reaches anyone.
- `version_files: []` — an action is tag-versioned. There is no file carrying the
  version, so `CHANGES.md` and the tags are the whole version stream.

## The version stream

`main` is protected, so a release lands in two halves.

**1. Run the `Create release PR` workflow** (Actions → Create release PR → Run workflow →
bugfix / feature / major). It:

1. refuses unless every check on the current `main` commit is green,
2. computes the next version from the tags and refuses if it already exists,
3. rolls the `CHANGES.md` `[Unreleased]` section into a dated version section,
4. pushes a `release/vX.Y.Z` branch and opens a pull request.

Nothing is tagged or published yet. Closing the pull request cancels the release.

**2. Review the changelog and merge.** That triggers the publish workflow, which reads
the version back out of `CHANGES.md`, tags it, moves `v2`, and publishes the GitHub
release with the notes from that section.

`CHANGES.md` is the single source of truth for the version. The first `##` heading
carrying a semver is the newest release; `## [Unreleased]` has no digits and is skipped.

Use `### New`, never `### Added`. The roller matches literally on `### New`, and the
wrong heading loses the section from the release notes without failing anything.

## Why a pull request

`main` is protected by a repository ruleset, and the built-in `GITHUB_TOKEN` **cannot**
be given a bypass — the bypass list accepts users, teams and GitHub Apps, and the Actions
token is none of those. Landing the release through a pull request needs no stored
credential and works with the protection rather than around it. Tagging is unaffected:
the ruleset targets branches, and tags live in a separate ref namespace.

A pull request opened by `GITHUB_TOKEN` does not start its `pull_request` workflow runs
automatically — they are created in an **approval-required** state, and anyone with write
access starts them with **Approve workflows to run**. That click is deliberate; the
alternative is a credential to create, store and rotate.

## Releasing an action change

1. Make the change to `action.yml` or `mkp-builder.py`, add a `CHANGES.md` entry under
   `## [Unreleased]`, and merge to `main`.
2. Run the **Create release PR** workflow, then merge the release PR it opens.

Consumers pinning `@v2` pick it up as soon as the major tag moves. Nothing else is needed.

## Testing the action

`ci.yml`'s `action-test` job calls `.github/workflows/action-test.yml`, which is this
repository's own file — the standard fixes the path and the trigger and nothing else.
It must stay `on: [workflow_call]`; adding `push` or `pull_request` beside it makes every
run happen twice.

`ci.yml`'s other job, `action-manifest`, fails when a workflow passes an input `action.yml`
does not declare, or omits one it marks required. GitHub only warns about the first and
does not enforce the second, so both used to pass silently here.
