---
name: release-changelog
description: "Turn commits/PRs merged since the last git tag into a changelog entry for this PyPI-published library."
disable-model-invocation: true
---

# Release Changelog

User-invoked only — a release note is a deliberate action, not something to
draft automatically after a random change.

## Steps

1. Find the last tag and list what's new since it:
   ```bash
   last_tag=$(git tag --sort=-version:refname | head -1)
   git log "${last_tag}"..HEAD --oneline --no-merges
   ```
2. Group by Conventional Commit type (`feat`, `fix`, `chore`, `docs`, `refactor`,
   `test`, `ci`, `perf`) into changelog sections: `Added`, `Fixed`, `Changed`,
   `Removed` — map `feat` → Added, `fix`/`perf` → Fixed, `refactor`/`chore` →
   Changed, drop `docs`/`ci`/`test` from the visible changelog.
3. For each entry, keep the commit's own summary line — don't paraphrase or
   invent detail not in the commit message or its linked PR.
4. Present the drafted section to the user for confirmation before writing
   anything to `CHANGELOG.md` — do not commit or tag automatically; the
   `release.yml` workflow (GitVersion) handles the actual tag on push to `main`.

## Done means

A reviewed changelog section, grouped and attributed to real commits since
`last_tag`, ready for the user to paste into `CHANGELOG.md`.
