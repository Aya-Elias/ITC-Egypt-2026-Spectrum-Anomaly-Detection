#!/usr/bin/env bash
set -euo pipefail
python -m compileall -q src tests
python -m pytest -q -m "not ml" "$@"
