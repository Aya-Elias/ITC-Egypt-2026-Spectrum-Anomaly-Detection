"""LLM orchestration layer for SADAR."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .config import AgentConfig, PROMPTS_DIR
from .ollama_client import OllamaClient


@dataclass(slots=True)
class LLMResponse:
    content: str
    provider: str
    model: str
    used_fallback: bool = False


class LLMHandler:
    """Generates professional responses with Ollama and safe fallbacks."""

    def __init__(
        self,
        client: OllamaClient | None = None,
        model: str | None = None,
        config: AgentConfig | None = None,
    ) -> None:
        self.config = config or AgentConfig()
        self.client = client or OllamaClient(agent_config=self.config)
        self.model = model or self.config.ollama_model

    def generate(self, prompt: str, system: str | None = None, temperature: float = 0.2) -> LLMResponse:
        """Generate a response, returning a structured fallback when the LLM is unavailable."""
        try:
            text = self.client.generate(prompt=prompt, system=system, model=self.model, temperature=temperature)
            if text:
                return LLMResponse(text, provider="ollama", model=self.model)
        except Exception as exc:
            return LLMResponse(
                self._fallback_response(reason=str(exc)),
                provider="fallback",
                model="none",
                used_fallback=True,
            )
        return LLMResponse(
            self._fallback_response(reason="empty model response"),
            provider="fallback",
            model="none",
            used_fallback=True,
        )

    def answer_with_context(self, question: str, context: str, style: str = "professional") -> LLMResponse:
        system = load_prompt("qa_system.txt", prompts_dir=self.config.prompts_dir)
        prompt = (
            "Use the local SADAR reference context to answer accurately.\n"
            f"Style: {style}.\n\n"
            f"Context:\n{context}\n\n"
            f"Question:\n{question}\n\n"
            "Answer with clear bullets, mention uncertainty, and cite source names when available."
        )
        return self.generate(prompt, system=system)

    def _fallback_response(self, reason: str) -> str:
        return (
            "The local Ollama model is currently unavailable, so this is a safe fallback response.\n\n"
            f"Reason: {reason}\n\n"
            "What still works: retrieval/indexing, RF threat analysis, incident report generation, "
            "response caching, and feedback capture.\n\n"
            "To enable generative answers: start Ollama and pull the configured model."
        )


def load_prompt(name: str, prompts_dir: str | Path | None = None) -> str:
    directory = Path(prompts_dir) if prompts_dir else PROMPTS_DIR
    path = directory / name
    if path.exists():
        return path.read_text(encoding="utf-8", errors="ignore").strip()
    return "You are SADAR, a professional RF spectrum anomaly detection assistant."
