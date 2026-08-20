# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### New

### Changed

### Fixed

## 2.3.0 - 2026-08-20
### New
- The skill now ships a test harness. A plugin repo can run pytest against the real Checkmk API, pulled from Checkmk and pinned to the version the plugin targets, instead of against hand-written stubs.

## 2.2.2 - 2026-08-17
### Changed
- Renamed the release workflows for what they actually do: `Release` →
  **Create release PR** (`create-release-pr.yml`) and `Publish release` →
  **Release publisher** (`release-publisher.yml`). Since 2.2.1 split the release in two,
  the old names read like two ways to do the same thing, when only one is ever the right
  button to press.
- **Release publisher** no longer has a `workflow_dispatch` trigger. Publishing should be
  a consequence of merging a release PR, not something anyone can start from a dropdown;
  with `main` protected against direct pushes, merging a PR that changes `plugin.json` is
  now the only route to a release. This costs no recovery: a failed run is re-run from the
  Actions UI regardless of trigger, and because the version is read from `plugin.json`
  rather than from run inputs, a re-run is faithful to the original attempt.

## 2.2.1 - 2026-08-17
### New
- Ship the release/CI workflows as copyable skill artifacts under
  `skills/checkmk-plugin/assets/` (`release.yml`, `validate.yml`,
  `CHANGES.md.template`) so plugin repos bootstrap CI with a `cp`, and the skill
  docs stay light instead of inlining ~250 lines of YAML.

### Changed
- Document the `workflow_dispatch` + `CHANGES.md` release pipeline as the
  recommended default in the checkmk-plugin skill (SKILL.md and
  `references/mkp-builder.md`); keep the minimal tag-push workflow as a short
  alternative. Reference the bundled artifacts instead of inlining them.
- Bump GitHub Actions in the shipped templates to current majors:
  `actions/checkout` v4→v7, `actions/upload-artifact` v4→v7,
  `actions/download-artifact` v4→v8, `softprops/action-gh-release` v2→v3
  (`oposs/mkp-builder` stays `@v2`).
- Commit `.claude-plugin/plugin.json` (previously gitignored) so the plugin owns its
  own version as the single source of truth (`0.2.0`); the marketplace entry no longer
  carries a `version`. See `RELEASING.md` for the plugin release process.
- The release now runs in two halves. **Release** prepares a `release/vX.Y.Z` branch that
  rolls `CHANGES.md` and syncs `.claude-plugin/plugin.json`, and opens a PR;
  **Publish release** tags, moves `@vX` and publishes once that PR is merged. `main` is
  protected by a ruleset, and the built-in `GITHUB_TOKEN` cannot be granted a bypass —
  the bypass list takes users, teams and GitHub Apps, not the Actions token. Rather than
  introduce an App or a deploy key just to push one commit, the release now lands through
  a PR like any other change. Tagging is unaffected, since the ruleset targets branches
  and tags are a separate ref namespace. The changelog roll and version bump are now
  reviewable before they ship, and nothing is tagged until the PR is merged, so closing
  it cancels the release.
- The release syncs `.claude-plugin/plugin.json` to the release version, so the Claude
  plugin version and the git tag can no longer drift. It fails if the manifest is missing
  or the rewrite does not take, rather than shipping a release no Claude would ever see.
  Publishing reads the version back out of that file, which makes it idempotent: if the
  version is already tagged the workflow does nothing, so re-runs and stray pushes to
  `main` are harmless.
- Nudging the marketplace after a release is no longer this repository's job. Claude only
  re-resolves plugin versions when it re-fetches the marketplace, so the marketplace has
  to move too — previously a manual step with nothing to enforce it. `oposs/claude-plugins`
  now runs an hourly workflow that reads this repo's `plugin.json` and commits when the
  version changes. Pulling rather than pushing needs no cross-repo credential (the org
  restricts fine-grained PATs), covers every plugin rather than only those wired up to
  push, and catches versions bumped outside the release workflow. See `RELEASING.md`.
- Bring the Claude plugin version in sync with the repository's release tags:
  `0.2.1` → `2.2.0` (the current tag). The two version lines had drifted apart because
  only the git tag was automated, so every skill fix needed a hand-written bump commit
  that trailed the fix by a separate PR.

### Fixed
- Skill changes could ship without reaching anyone. Claude caches a plugin under its
  resolved version, so merging a skill fix had no effect until `plugin.json` was bumped
  by hand — a step with nothing to enforce it and no signal when it was missed. The
  installed copy on a developer machine was found 10 commits behind `main`, missing
  three merged skill fixes.
- Correct special-agent secret handling in the checkmk-plugin skill
  (`references/12-special-agents.md`): a bare `Secret` reaches the agent as an
  inline `<pw_id>:<pw_store_file>` reference that `replace_passwords()` does not
  resolve (it only rewrites the legacy `--pwstore=...` argv form), so the old
  guidance sent the literal reference and every request failed with `401`.
  Document passing a bare `Secret` (no `.unsafe()`, nothing leaks into `ps`) and
  resolving it in the agent with `password_store.lookup()`. Plugin `0.2.0`→`0.2.1`.

## 2.2.0 - 2026-03-02
### New
- Add notification plugin support to mkp-builder (collects from `local/share/check_mk/notifications/`, creates `notifications.tar`)
- Add Claude Code plugin with Checkmk 2.3.x plugin development skill (`skills/checkmk-plugin/`)
- Install via OPOSS marketplace: `/plugin marketplace add oposs/claude-plugins` then `/plugin install cmk-oposs-plugin@oposs-plugins`

### Changed
- Move plugin development guide from `cmk-plugin-guide/` into `skills/checkmk-plugin/references/`
- Update README with Claude Code plugin install instructions

## 2.1.0 - 2025-11-19
### New
- Add notification plugin support to mkp-builder (collects from `local/share/check_mk/notifications/`, creates `notifications.tar`)
- Add notification plugin development guide (14-notifications.md) covering Discord/webhook examples, environment variables, testing

## 2.0.3 - 2025-11-14
### New
- refactored plugin guide with added snmp plugin info
- added renaming information to plugin guide
- added special_agent informtion to plugin guide

### Changed
- change all CheckMk strings to Checkmk

## 2.0.2 - 2025-08-07
### Fixed
- Fix lib.tar creation to properly handle both `check_mk/` and `python3/cmk/` directory structures with consistent MKP-compatible archive paths
- Add conflict detection when both `local/lib/check_mk/` and `local/lib/python3/cmk/` exist as directories

## 2.0.1 - 2025-08-07
### Changed
- Update README.md examples to use v2.0.0 and document breaking changes from v1.x

### Fixed
- Fix deprecated GitHub Actions ::set-output command usage to use new GITHUB_OUTPUT environment file format

## 2.0.0 - 2025-08-07
### New
- Add support for INI configuration format with `.mkp-builder.ini` files
- Add multiline description support in configuration files
- Add `__pycache__` directory filtering to exclude Python cache files from packages

### Changed
- **BREAKING**: Configuration file format changed from `.mkp-builderrc` (key=value) to `.mkp-builder.ini` (INI format with `[package]` section)
- **BREAKING**: Command line arguments renamed for clarity:
  - `--cmk-min` → `--version-min-required`
  - `--cmk-packaged` → `--version-packaged`
- **BREAKING**: GitHub Action inputs renamed:
  - `cmk-min-version` → `version-min-required`
  - `cmk-packaged-version` → `version-packaged`
- Internal configuration keys now match info file structure (e.g., `version.min_required`, `version.packaged`)
- Improved JSON formatting in `info.json` with proper indentation
- Enhanced Python dict formatting in `info` file using `pprint` module with 80-character line width

### Fixed
- Package files now properly exclude `__pycache__` directories and their contents

## 1.0.1 - 2025-08-06
### New
- Add full support for `VERSION_USABLE_UNTIL` including a command line argument, a GHA input and documentation.

## 1.0.0 - 2025-08-06
### New
- Initial release of Checkmk MKP Builder Action


