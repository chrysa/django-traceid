# TESTING — django-traceid

## How to run (FACT — `Makefile`, `pyproject.toml`)

The chrysa convention is to run everything through `make` / containers, never linters or
pytest directly on the host (`CLAUDE.md`).

```bash
make install     # pip install -e ".[dev]"  (+ pre-commit)
make test        # pytest
make test-cov    # pytest with coverage (term + xml)
make docker-test # build Dockerfile.test and run tests in-container (CI-equivalent)
make lint        # ruff check .
make typecheck   # mypy in Docker (Dockerfile.typecheck)
make ci          # lint + typecheck + test
```

`pytest` config (`pyproject.toml [tool.pytest.ini_options]`): `DJANGO_SETTINGS_MODULE =
tests.settings`, `addopts` include `--cov=django_traceid --cov-report=term-missing
--cov-fail-under=85`. So the suite **fails under 85% coverage** (FACT).

## Suite shape (FACT — `tests/`)

33 test functions across 5 files:

| File | Tests | Focus |
| --- | --- | --- |
| `tests/test_middleware.py` | 13 | HTTP extraction/generation, response header echo, validation, sync/async, streaming, Sentry tagging |
| `tests/test_context.py` | 6 | `ContextVar` bind/reset, `trace_context`, generator format |
| `tests/test_rq.py` | 6 | enqueue-with-trace, `trace_aware` restore/strip, manual restore |
| `tests/test_conf.py` | 5 | defaults, override, import-string resolution, `setting_changed` reload |
| `tests/test_filters.py` | 3 | record enrichment, empty-string outside context, custom attr name |

Support files: `tests/settings.py` (test Django settings), `tests/urls.py` (test URLconf),
`tests/__init__.py`.

## Coverage evidence (INFERENCE)

`.coverage`, `coverage.xml`, and a `.benchmarks/` dir are present in the tree — coverage is
generated and (per `pyproject.toml`) rewritten to repo-relative paths for SonarCloud mapping.
Latest coverage numbers are not asserted here beyond the 85% gate. **UNKNOWN**: current exact
coverage percentage (not re-run during documentation).

## Gaps / not covered by the in-repo suite (INFERENCE)

- Celery and MQTT/Redis propagation are documented behaviours of `rq.py` but the suite exercises
  the RQ-like/duck-typed path only; real Celery/broker integration is not tested here.
- Async streaming reset is described as "left to the default reset"; the streaming test focuses
  on the sync path (see `ARCHITECTURE.md §4`).

## Verification commands used to write this doc

- `grep -rn "def test_" tests/` → 33 functions (counts per file above).
