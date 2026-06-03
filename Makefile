.PHONY: install test docker-test lint typecheck format build clean

install:
	pip install -e ".[dev]"

test:
	pytest

docker-test:
	docker build -f Dockerfile.test -t django-traceid-test .
	docker run --rm django-traceid-test

lint:
	ruff check .

format:
	ruff format .
	ruff check --fix .

typecheck:
	mypy django_traceid

build:
	python -m build

clean:
	rm -rf build dist *.egg-info .pytest_cache .ruff_cache .mypy_cache .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
