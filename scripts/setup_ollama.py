"""Check Ollama connectivity for the SADAR agent."""

from __future__ import annotations

import os

import requests


def main() -> None:
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    response = requests.get(f"{base_url}/api/tags", timeout=5)
    response.raise_for_status()
    models = [m.get("name") for m in response.json().get("models", [])]
    print(f"Ollama reachable at {base_url}. Models: {models or 'none installed'}")


if __name__ == "__main__":
    main()
