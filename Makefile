SYSTEM_PYTHON ?= python3
VENV ?= .venv
PYTHON ?= $(VENV)/bin/python
PIP ?= $(PYTHON) -m pip
FLAKE8 ?= $(VENV)/bin/flake8
MYPY ?= $(VENV)/bin/mypy
MAIN ?= pac-man.py
CONFIG ?= config.json

.PHONY: install run debug clean lint lint-strict test

install:
	$(SYSTEM_PYTHON) -m venv $(VENV)
	$(PIP) install flake8 mypy pytest

run:
	$(PYTHON) $(MAIN) $(CONFIG)

debug:
	$(PYTHON) -m pdb $(MAIN) $(CONFIG)

clean:
	find . -type d -name "__pycache__" -not -path "./$(VENV)/*" -prune -exec rm -rf {} +
	rm -rf .mypy_cache .pytest_cache
	find . -type f -name "*.py[co]" -not -path "./$(VENV)/*" -delete

lint:
	$(FLAKE8) . --exclude=$(VENV)
	$(MYPY) . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	$(FLAKE8) . --exclude=$(VENV)
	$(MYPY) . --strict

test:
	$(PYTHON) -m pytest tests
