PYTHON ?= python3
PIP ?= $(PYTHON) -m pip
MAIN ?= pac-man.py
CONFIG ?= config.json

.PHONY: install run debug clean lint lint-strict

install:
	@if [ -f requirements.txt ]; then $(PIP) install -r requirements.txt; else echo "requirements.txt not found; nothing to install yet."; fi

run:
	$(PYTHON) $(MAIN) $(CONFIG)

debug:
	$(PYTHON) -m pdb $(MAIN) $(CONFIG)

clean:
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	rm -rf .mypy_cache .pytest_cache
	find . -type f -name "*.py[co]" -delete

lint:
	flake8 .
	mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	flake8 .
	mypy . --strict
