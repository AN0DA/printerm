.PHONY: lint mypy test test-all test-coverage clean help

# Default target
all: lint mypy test

# Code quality checks
lint:
	uv run ruff format printerm/ test/ \
	&& uv run ruff check --fix --show-fixes printerm/ test/ \
	&& uv run bandit -c pyproject.toml -r printerm/

mypy:
	uv run mypy printerm/ test/

# Testing targets
test:
	uv run pytest --cov --cov-report term-missing:skip-covered

test-ci:
	uv run pytest --cov --cov-report term-missing:skip-covered -m "not gui"

# Cleanup
clean:
	rm -rf test_reports/
	rm -rf .coverage
	rm -rf .pytest_cache/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

# Help
help:
	@echo "Available targets:"
	@echo "  all           - Run linting, type checking, and tests"
	@echo "  lint          - Run code formatting and linting"
	@echo "  mypy          - Run type checking"
	@echo "  test          - Run all tests with coverage"
	@echo "  test-ci       - Run CI tests (excluding GUI tests)"
	@echo "  clean         - Remove test artifacts"
	@echo "  help          - Show this help"
