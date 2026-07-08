# Releasing

This repo ships two things with **independent** version streams:

## 1. The `mkp-builder` GitHub Action

Versioned by git tags (`v2.2.0`, …) with a moving major tag (`@v2`). Cut a release by
running the **Release** workflow (`workflow_dispatch`, bugfix/feature/major). It rolls
`CHANGES.md`, tags, and moves `@v2`. Consumers pin `oposs/mkp-builder@v2`.

## 2. The `cmk-oposs-plugin` Claude Code plugin

The plugin's version lives **only** in `.claude-plugin/plugin.json` (`version`). It is the
single source of truth — Claude Code resolves a plugin's version as
`plugin.json → marketplace entry → commit SHA`, and `plugin.json` wins. The marketplace
entry in [`oposs/claude-plugins`](https://github.com/oposs/claude-plugins) therefore carries
**no** `version` field for this plugin (avoid setting it in two places — a stale duplicate
silently masks the real one).

### Releasing a plugin change

1. Make the plugin/skill change under `skills/`.
2. **Bump `version` in `.claude-plugin/plugin.json`** in the same change. Pushing new commits
   without bumping does nothing — Claude caches the resolved version and keeps the old copy.
3. Push to `main`.
4. **Push a change to the marketplace repo** (`oposs/claude-plugins`) as well — Claude
   re-resolves plugin versions when it re-fetches the marketplace, so the marketplace clone
   has to move for the bump to be noticed. A one-line edit (e.g. a note in that repo) is
   enough. *(This can be automated from CI later with a PAT that can push to the marketplace
   repo; not wired up yet.)*
5. Users run `/plugin marketplace update` then `/plugin update cmk-oposs-plugin`.
