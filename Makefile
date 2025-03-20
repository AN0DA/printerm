.PHONY: lint mypy test

all: lint mypy test

lint:
	uv run ruff format printerm/ test/ \
	&& uv run ruff check --fix --show-fixes printerm/ test/ \
	&& uv run bandit -c pyproject.toml -r printerm/

mypy:
	uv run mypy printerm/ test/

test:
	uv run pytest --cov --cov-report term-missing:skip-covered
