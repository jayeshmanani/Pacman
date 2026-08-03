UV ?= uv
VENV ?= .venv
PYTHON ?= $(UV) run python
FLAKE8 ?= $(UV) run flake8
MYPY ?= $(UV) run mypy
PYTEST ?= $(UV) run pytest
MAIN ?= pac-man.py
CONFIG ?= config.json

.PHONY: install run debug clean lint lint-strict test check-python-version

install:
	$(UV) venv $(VENV)
	$(UV) pip install flake8 flake8-docstrings mypy pytest

check-python-version:
	@$(PYTHON) -c "import sys; exit(0 if sys.version_info >= (3, 10) else 1)" || (echo "[ERROR] Python 3.10 or higher is required!" && exit 1)

run:
	$(PYTHON) $(MAIN) $(CONFIG)

debug:
	$(PYTHON) -m pdb $(MAIN) $(CONFIG)

clean:
	find . -type d -name "__pycache__" -not -path "./$(VENV)/*" -prune -exec rm -rf {} +
	rm -rf .mypy_cache .pytest_cache
	find . -type f -name "*.py[co]" -not -path "./$(VENV)/*" -delete

lint: check-python-version
	$(FLAKE8) . --exclude=$(VENV)
	$(MYPY) . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict: check-python-version
	$(FLAKE8) . --exclude=$(VENV)
	$(MYPY) . --strict

test: check-python-version
	$(PYTEST) tests


