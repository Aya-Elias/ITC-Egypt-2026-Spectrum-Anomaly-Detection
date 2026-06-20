#!/usr/bin/env bash
set -euo pipefail
curl -fsSL https://ollama.com/install.sh | sh
ollama pull "${OLLAMA_MODEL:-llama3}"
