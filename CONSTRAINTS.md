# CONSTRAINTS — django-traceid

Tags: [HARD] enforced by code/tooling · [SOFT] convention/intent · [ENV] environment.

## Runtime / compatibility
- [HARD] Python **3.12+**. `requires-python` floor is intentional; `rq.py:trace_aware` uses PEP
  695 generic syntax (`def trace_aware[F: ...]`) that does not parse before 3.12.
  Evidence: `pyproject.toml`, `README.md`.
- [SOFT] Django **4.2+** supported (LTS floor); only long-standing Django APIs used, so it likely
  runs on older Django too. Evidence: `README.md`.
- [HARD] Runtime dependency is **Django only**. `rq`/`sentry-sdk` must be host-provided; the
  library never imports them at top level. Evidence: `pyproject.toml`, `rq.py`, `middleware.py`.

## Quality gates
- [HARD] Test coverage must be **>= 85%** (`--cov-fail-under=85`). Evidence: `pyproject.toml`.
- [HARD] `mypy --strict` clean; typed distribution (`py.typed`). Evidence: `CLAUDE.md`, classifiers.
- [HARD] Lint via `ruff` (chrysa shared rule set). Evidence: `pyproject.toml`, `Makefile`.
- [SOFT] Lint/typecheck run in **pre-commit**, not in the CI test job (CI runs tests + Sonar).
  Evidence: `.github/workflows/ci.yml` header note.

## Container / dev-loop policy (chrysa standard)
- [SOFT] All checks run via `make` or `pre-commit` only — never invoke linters/tests directly on
  the host. Evidence: `CLAUDE.md`.
- [HARD] Tests and typecheck have container recipes (`Dockerfile.test`, `Dockerfile.typecheck`);
  `make docker-test` is the CI-equivalent path. Evidence: `Makefile`.

## Behavioural invariants (from code)
- [HARD] Incoming id reused only if it matches `[A-Za-z0-9_.-]+` and is within
  `INCOMING_MAX_LENGTH`. Evidence: `middleware.py`.
- [HARD] `TraceIdFilter` never drops a record (always returns `True`) and emits `""` outside a
  request. Evidence: `filters.py`.
- [HARD] `trace_context(None)` / `restore_trace_context(falsy)` are no-ops. Evidence: `context.py`, `rq.py`.

## Governance / naming (contradiction — see REVIEW.md)
- [SOFT] Branch model & default branch are stated inconsistently across `CLAUDE.md`
  (`main`, `feat/fix/chore/docs`) and `AGENTS.md` (`develop`, `feature/bugfix/...`). Resolve
  before relying on either for automation.
