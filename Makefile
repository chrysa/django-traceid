# makefile-tier: lib
.DEFAULT_GOAL := help

MATRIX_PYTHON ?= 3.13 3.14
MATRIX_DJANGO ?= 5.2 6.0

.PHONY: help install dev test test-cov lint format typecheck docker-test docker-test-matrix build pre-commit clean

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*##' $(MAKEFILE_LIST) | \
		awk 'BEGIN{FS=":.*##"}{printf "  %-20s %s\n", $$1, $$2}'

install: ## Install dev dependencies
	pip install -e ".[dev]"

dev: install ## Alias for install (no separate dev server)

test: ## Run unit tests
	pytest

test-cov: ## Run tests with coverage
	pytest --cov=django_traceid --cov-report=term-missing --cov-report=xml

lint: ## Run ruff linter
	ruff check .

format: ## Auto-format code
	ruff format .
	ruff check --fix .

typecheck: ## Run mypy type checking (Docker)
	docker build -f Dockerfile.typecheck -t django-traceid-typecheck .
	docker run --rm django-traceid-typecheck

docker-test: ## Run tests in Docker (CI-compatible)
	@# Pre-create coverage.xml as a file so the bind-mount maps file->file
	@# (Docker auto-creates a *directory* for a missing bind source, which
	@# then makes coverage's open(path,"w") fail). No -t is allocated, so this
	@# also runs in CI / non-interactive contexts.
	@rm -rf coverage.xml
	@touch coverage.xml
	docker build -f Dockerfile.test -t django-traceid-test .
	docker run --rm -v "$(PWD)/coverage.xml:/app/coverage.xml" django-traceid-test

docker-test-matrix: ## Run tests in Docker across Python x Django (override MATRIX_PYTHON / MATRIX_DJANGO)
	@fail=0; for py in $(MATRIX_PYTHON); do for dj in $(MATRIX_DJANGO); do \
		echo "=== Python $$py / Django $$dj ==="; \
		rm -rf coverage.xml; touch coverage.xml; \
		docker build -q -f Dockerfile.test --build-arg PYTHON_VERSION=$$py --build-arg DJANGO_VERSION=$$dj -t django-traceid-test:$$py-$$dj . >/dev/null \
		&& docker run --rm -v "$(PWD)/coverage.xml:/app/coverage.xml" django-traceid-test:$$py-$$dj || fail=1; \
	done; done; exit $$fail

build: ## Build wheel distribution package
	python -m build

pre-commit: ## Run all pre-commit checks
	pre-commit run --all-files

clean: ## Remove build artifacts
	rm -rf build dist *.egg-info .pytest_cache .ruff_cache .mypy_cache .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +

.PHONY: ci
ci: lint typecheck test  ## CI: run all checks (lint + typecheck + test)
