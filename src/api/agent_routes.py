"""FastAPI endpoints for the SADAR AI Agent.

These endpoints expose the professional AI-agent layer implemented in
``src.ai_agent`` without coupling it to the TensorFlow prediction endpoint.
They are safe to use even when the RF classifier model is unavailable.
"""

from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from src.ai_agent import SADARAgent
from src.ai_agent.exceptions import SADARAgentError, ValidationError
from src.ai_agent.threat_analyzer import SignalObservation

router = APIRouter(prefix="/agent", tags=["AI Agent"])


class AgentAskRequest(BaseModel):
    """Question-answer request for the SADAR AI Agent."""

    question: str = Field(..., min_length=2, description="Question about RF signals, threats, or project docs")
    refresh: bool = Field(False, description="Bypass cached answer and regenerate")
    top_k: int = Field(5, ge=1, le=10, description="Number of RAG context chunks to retrieve")


class AgentAskResponse(BaseModel):
    question: str
    answer: str
    sources: list[str]
    used_cache: bool
    used_fallback: bool


class ThreatAnalysisRequest(BaseModel):
    """Threat-analysis request based on classifier output and RF metadata."""

    label: str = Field(..., examples=["Drone", "Normal", "Jamming"])
    confidence: float = Field(..., ge=0.0, le=1.0)
    frequency_mhz: float | None = Field(None, ge=0.0)
    snr_db: float | None = None
    source: str = "SDR"
    location: str = "Unknown"
    metadata: dict[str, Any] = Field(default_factory=dict)


class ThreatAnalysisResponse(BaseModel):
    level: Literal["low", "medium", "high", "critical"]
    score: float
    summary: str
    recommended_actions: list[str]
    timestamp: str
    evidence: dict[str, Any]


class ReportRequest(ThreatAnalysisRequest):
    analyst_notes: str = ""


class ReportResponse(BaseModel):
    markdown: str


class KnowledgeBaseResponse(BaseModel):
    path: str
    chunks: int
    sources: list[str]
    embedding_backend: str
    files_discovered: int = 0
    files_indexed: int = 0
    files_skipped: int = 0
    files_failed: int = 0
    failures: list[str] = Field(default_factory=list)


def _get_agent(request: Request) -> SADARAgent:
    """Return one shared agent instance per FastAPI app."""
    agent = getattr(request.app.state, "sadar_agent", None)
    if agent is None:
        agent = SADARAgent()
        request.app.state.sadar_agent = agent
    return agent


@router.get("/health", summary="Check AI-agent health")
async def agent_health(request: Request) -> dict[str, Any]:
    agent = _get_agent(request)
    status = agent.status()
    return {"status": "ok", "name": status.name, "rag": status.rag, "ollama": status.ollama}


@router.post("/knowledge-base/rebuild", response_model=KnowledgeBaseResponse, summary="Rebuild local RAG index")
async def rebuild_knowledge_base(request: Request, force: bool = True) -> dict[str, Any]:
    agent = _get_agent(request)
    return agent.build_knowledge_base(force=force)


@router.post("/ask", response_model=AgentAskResponse, summary="Ask the SADAR AI Agent")
async def ask_agent(payload: AgentAskRequest, request: Request) -> AgentAskResponse:
    agent = _get_agent(request)
    try:
        result = agent.ask(payload.question, refresh=payload.refresh, top_k=payload.top_k)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except SADARAgentError as exc:
        raise HTTPException(status_code=503, detail="AI-agent query failed") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Unexpected AI-agent error") from exc
    return AgentAskResponse(
        question=result.question,
        answer=result.answer,
        sources=result.sources,
        used_cache=result.used_cache,
        used_fallback=result.used_fallback,
    )


@router.post("/analyze-threat", response_model=ThreatAnalysisResponse, summary="Analyze RF threat level")
async def analyze_threat(payload: ThreatAnalysisRequest, request: Request) -> ThreatAnalysisResponse:
    agent = _get_agent(request)
    try:
        assessment = agent.analyze_threat(SignalObservation(**payload.model_dump()))
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ThreatAnalysisResponse(
        level=assessment.level,
        score=assessment.score,
        summary=assessment.summary,
        recommended_actions=assessment.recommended_actions,
        timestamp=assessment.timestamp,
        evidence=assessment.evidence,
    )


@router.post("/report", response_model=ReportResponse, summary="Generate Markdown incident report")
async def generate_report(payload: ReportRequest, request: Request) -> ReportResponse:
    agent = _get_agent(request)
    observation = payload.model_dump(exclude={"analyst_notes"})
    try:
        markdown = agent.generate_incident_report(observation, analyst_notes=payload.analyst_notes)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ReportResponse(markdown=markdown)
