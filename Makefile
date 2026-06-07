# makefile-tier: lib
.DEFAULT_GOAL := help

.PHONY: help install dev test test-cov lint format typecheck docker-test build pre-commit clean

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

typecheck: ## Run mypy type checking
	mypy django_traceid

docker-test: ## Run tests in Docker (CI-compatible)
	docker build -f Dockerfile.test -t django-traceid-test .
	docker run --rm django-traceid-test

build: ## Build wheel distribution package
	python -m build

pre-commit: ## Run all pre-commit checks
	pre-commit run --all-files

clean: ## Remove build artifacts
	rm -rf build dist *.egg-info .pytest_cache .ruff_cache .mypy_cache .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
