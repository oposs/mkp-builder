# Releasing

This repo ships two things, released **together** from a single version stream:

- **The `mkp-builder` GitHub Action** — consumers pin `oposs/mkp-builder@v2`.
- **The `cmk-oposs-plugin` Claude Code plugin** — the `skills/` tree, versioned by
  `.claude-plugin/plugin.json`.

## The version stream

Git tags (`v2.2.0`, …) with a moving major tag (`@v2`) drive both. Cut a release by
running the **Release** workflow (`workflow_dispatch`, bugfix/feature/major). It:

1. computes the next version from the latest tag,
2. rolls the `CHANGES.md` `## [Unreleased]` section into a dated version section,
3. **rewrites `.claude-plugin/plugin.json` to the same version**,
4. commits `CHANGES.md` + `plugin.json`, tags, and moves `@v2`.

`plugin.json` remains the single source of truth for the plugin version — Claude Code
resolves `plugin.json → marketplace entry → commit SHA`, and `plugin.json` wins. The
marketplace entry in [`oposs/claude-plugins`](https://github.com/oposs/claude-plugins)
therefore carries **no** `version` field for this plugin (a stale duplicate silently
masks the real one). The workflow keeps `plugin.json` equal to the tag so the two
version lines cannot drift apart.

### Releasing a plugin or skill change

1. Make the change under `skills/` and merge it to `main`.
2. Run the **Release** workflow. It bumps `plugin.json` for you — there is no
   hand-written bump commit any more.
3. **Push a change to the marketplace repo** (`oposs/claude-plugins`). Claude only
   re-resolves plugin versions when it re-fetches the marketplace, so the marketplace
   clone has to move for the new version to be noticed. A one-line edit is enough.
   *(Still manual — could be automated from CI with a PAT that can push there.)*
4. Users run `/plugin marketplace update` then `/plugin update cmk-oposs-plugin`.

> **Why the version bump matters.** Claude caches a plugin under its resolved version and
> reads the skill from `~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/`.
> Merging a skill fix without moving the version ships nothing — every Claude keeps
> reading the old cached copy, with no error and no signal that anything is stale. While
> this was a manual step it was missed often enough that an installed copy was found 10
> commits and three merged skill fixes behind `main`. That is why step 3 of the release
> workflow now enforces it.
