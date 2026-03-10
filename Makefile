# Environment variables
PYTHON := python
VENV := .venv

# Command parameters with defaults
TEST_ARGS ?=
LINT_ARGS ?=
PYTHON_ARGS ?=

# Makefile targets
.PHONY: \
	help \
	setup \
	install \
	install-dev \
	package \
	clean \
	python \
	test \
	test-all \
	test-unit \
	test-integration \
	lint \
	type-check \
	check-lazy-ignores

# Help text
HELP_TEXT := "Makefile targets:\n\
setup        - create a virtualenv and install dev dependencies\n\
install      - install runtime dependencies into active venv\n\
install-dev  - install development runtime dependencies into active venv\n\
package      - build a wheel distribution into dist/\n\
package-install - install a built wheel into the active venv\n\
clean        - remove venv and build artifacts\n\
test         - run full pytest suite (alias for test-all)\n\
test-all     - run all tests (unit + integration + slow)\n\
test-unit    - run only fast unit tests\n\
test-integration - run integration tests\n\
python	     - run an interactive Python shell in venv\n\
lint         - run ruff linter on source and tests\n\
type-check   - run mypy type checking on source and tests\n\
check-lazy-ignores - checks for lint errors that were ignored\n\

## Targets

help:
	@echo $(HELP_TEXT)

setup:
	@echo "Creating virtualenv .venv and installing dev dependencies..."
	uv venv
	uv pip install -e .[dev]

install-dev:
	@echo "Install development package into current venv."
	uv pip install -e ".[dev]"

install:
	@echo "Install runtime package into current venv."
	uv pip install -e .

package:
	@echo "Building wheel (.whl) into dist/..."
	uv build --wheel

package-install:
	@echo "Installing built wheel into current venv..."
	uv pip install dist/*.whl

clean:
	@echo "Cleaning build artifacts, caches, and temporary files..."
	rm -rf dist/ build/ *.egg-info .pytest_cache/ .ruff_cache/ .mypy_cache/
	rm -rf src/*.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete
	find . -type f -name '*.pyo' -delete
	find . -type f -name '*.log' -delete
	rm -f db.sqlite3 db.sqlite3-journal

python:
	@echo "Starting interactive Python shell in venv..."
	uv run python $(PYTHON_ARGS)

test:
	@echo "Running full test suite with pytest..."
	uv run pytest -q $(TEST_ARGS) -n auto --tb=short

test-all:
	@echo "Running all tests (unit + integration + slow)..."
	uv run pytest -q $(TEST_ARGS) -n auto --tb=short

test-unit:
	@echo "Running unit tests only..."
	uv run pytest -q -m unit $(TEST_ARGS) -n auto --tb=short

test-integration:
	@echo "Running integration tests..."
	uv run pytest -q -m integration $(TEST_ARGS) -n auto --tb=short

lint:
	@echo "Running ruff linter..."
	uv run ruff check $(LINT_ARGS) src/ tests/

type-check:
	@echo "Running mypy type checker..."
	uv run mypy src/ tests/

check-lazy-ignores:
	@echo "Checking for lint errors that were ignored..."
	rg "#noqa|C901|# type:"
