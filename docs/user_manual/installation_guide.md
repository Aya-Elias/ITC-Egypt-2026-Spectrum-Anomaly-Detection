# Installation Guide

## Recommended Python

Use Python 3.10, 3.11, or 3.12. TensorFlow is not supported on Python 3.14.

## Core API/demo setup

```bash
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\\Scripts\\activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m uvicorn src.api.main:app --reload
```

## Full ML runtime

```bash
python -m pip install -r requirements-ml.txt
python -m pytest -q -m ml
```
