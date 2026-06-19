# AGENTS.md — target

Guidance for AI coding agents working in this repository. Human contributors: see `CLAUDE.md`
and `CONTRIBUTING.md`.

## Conventions

- Language: English for all code, comments, docs, and config.
- Commits: Conventional Commits (`feat`, `fix`, `chore`, `docs`, `refactor`, `test`, `ci`).
- Branches: `feature/`, `bugfix/`, `chore/`, `hotfix/`, `release/`; default branch `develop`.
- One PR per issue, scoped tight; every PR references an issue (`Closes/Fixes/Refs #N`).
- Squash merge only; never force-push shared branches.

## Standards

This repo follows the chrysa transverse standards imported in `CLAUDE.md`
(`@.chrysa/STANDARDS.md`). Key gates: test coverage >= 85%, 0 lint warnings, mypy clean,
SonarCloud rating A. Max function 50 lines, max file 500 lines.

## Before you commit

- Run `make lint` and `make test`; both must pass.
- Keep changes minimal and scoped to the referenced issue.
- Never commit secrets or a real `.env` (use `.env.example`).
- Regenerate the changelog only via `make changelog` (git-cliff), never by hand.

## Safe editing

- Read `CLAUDE.md` and any `primer.md` at session start for current state and conventions.
- Prefer small, reviewable diffs over large rewrites.
- When unsure about blast radius, inspect callers before editing shared symbols.
