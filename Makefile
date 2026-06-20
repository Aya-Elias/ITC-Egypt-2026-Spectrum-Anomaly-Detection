.PHONY: install install-dev test test-core test-ml lint format security run-api run-dashboard

PYTHON ?= python
PIP ?= $(PYTHON) -m pip

install:
	$(PIP) install -r requirements.txt

install-dev:
	$(PIP) install -r requirements-dev.txt

test:
	$(PYTHON) -m pytest -q

test-core:
	$(PYTHON) -m pytest -q -m "not ml"

test-ml:
	$(PYTHON) -m pytest -q -m ml

lint:
	$(PYTHON) -m ruff check --select E9,F63,F7,F82 src tests

format:
	$(PYTHON) -m ruff format src tests

security:
	$(PYTHON) -m bandit -q -r src

run-api:
	$(PYTHON) -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

run-dashboard:
	$(PYTHON) -m streamlit run src/dashboard/app.py
