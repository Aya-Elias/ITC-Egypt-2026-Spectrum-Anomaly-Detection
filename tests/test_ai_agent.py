from pathlib import Path
import sqlite3

import pytest
from fastapi.testclient import TestClient

from src.ai_agent import AgentConfig, SADARAgent
from src.ai_agent.embedding_model import EmbeddingConfig, EmbeddingModel
from src.ai_agent.exceptions import ConfigurationError, ValidationError
from src.ai_agent.feedback_loop import FeedbackLoop
from src.ai_agent.llm_handler import LLMHandler
from src.ai_agent.rag_retriever import RAGRetriever
from src.ai_agent.response_cache import ResponseCache
from src.ai_agent.threat_analyzer import SignalObservation, ThreatAnalyzer
from src.ai_agent.tools.db_query_tool import run_readonly_query
from src.ai_agent.vector_store import JsonVectorStore
from src.api.main import app


def test_config_validates_bad_timeout(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("OLLAMA_TIMEOUT", "bad")
    with pytest.raises(ConfigurationError):
        AgentConfig()


def test_threat_analyzer_scores_jamming_high():
    assessment = ThreatAnalyzer().assess(
        SignalObservation(label="Jamming", confidence=0.92, frequency_mhz=2450, snr_db=24)
    )
    assert assessment.level == "critical"
    assert assessment.score > 0.85
    assert assessment.recommended_actions
    assert assessment.to_dict()["level"] == "critical"


def test_threat_analyzer_rejects_bad_confidence():
    with pytest.raises(ValidationError):
        ThreatAnalyzer().assess(SignalObservation(label="Drone", confidence=1.2))


def test_threat_analyzer_limits_metadata():
    config = AgentConfig(max_metadata_items=1)
    analyzer = ThreatAnalyzer(config=config)
    with pytest.raises(ValidationError):
        analyzer.assess(SignalObservation(label="Drone", confidence=0.8, metadata={"a": 1, "b": 2}))


def test_vector_store_search_roundtrip(tmp_path: Path):
    store = JsonVectorStore(
        tmp_path / "index.json",
        embedding_model=EmbeddingModel(EmbeddingConfig(dimension=64, use_sentence_transformers=False)),
    )
    store.add_texts(["Drone RF signal near 2.4 GHz", "Normal FM broadcast"], source="manual.md")
    results = store.search("drone signal", top_k=1)
    assert len(results) == 1
    assert "Drone" in results[0].chunk.text


def test_vector_store_recovers_from_corrupt_index(tmp_path: Path):
    index = tmp_path / "index.json"
    index.write_text("not-json", encoding="utf-8")
    store = JsonVectorStore(index)
    assert store.chunks == []


def test_response_cache_recovers_from_corrupt_json(tmp_path: Path):
    cache_path = tmp_path / "responses.json"
    cache_path.write_text("not-json", encoding="utf-8")
    cache = ResponseCache(path=cache_path)
    assert cache.get("anything") is None


def test_rag_indexes_temp_documents(tmp_path: Path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "manual.md").write_text("Drone detection guidance.\n\nVerify spectrum evidence.", encoding="utf-8")
    config = AgentConfig(
        external_docs_dir=docs,
        cache_dir=tmp_path,
        index_path=tmp_path / "rag.json",
        response_cache_path=tmp_path / "cache.json",
        feedback_path=tmp_path / "feedback.jsonl",
    )
    retriever = RAGRetriever(agent_config=config)
    stats = retriever.build_index(force=True)
    assert stats["files_indexed"] == 1
    assert stats["chunks"] >= 1
    assert retriever.retrieve("drone guidance")


def test_llm_fallback_when_client_fails():
    class FailingClient:
        def generate(self, **_: object) -> str:
            raise RuntimeError("offline")

    response = LLMHandler(client=FailingClient()).generate("hello")  # type: ignore[arg-type]
    assert response.used_fallback is True
    assert "offline" in response.content


def test_agent_report_generation_works(tmp_path: Path):
    config = AgentConfig(
        cache_dir=tmp_path,
        index_path=tmp_path / "rag.json",
        response_cache_path=tmp_path / "cache.json",
        feedback_path=tmp_path / "feedback.jsonl",
    )
    agent = SADARAgent(config=config)
    report = agent.generate_incident_report({"label": "Drone", "confidence": 0.88, "location": "Test range"})
    assert "SADAR RF Threat Assessment Report" in report
    assert "Drone" in report


def test_feedback_rejects_invalid_rating(tmp_path: Path):
    loop = FeedbackLoop(path=tmp_path / "feedback.jsonl")
    with pytest.raises(ValidationError):
        loop.record("q", "a", rating="bad")  # type: ignore[arg-type]


def test_db_query_tool_allows_bounded_select(tmp_path: Path):
    db = tmp_path / "events.db"
    conn = sqlite3.connect(db)
    conn.execute("create table events(id integer, label text)")
    conn.execute("insert into events values(1, 'Drone')")
    conn.commit()
    conn.close()

    rows = run_readonly_query(db, "select * from events", limit=10)
    assert rows == [{"id": 1, "label": "Drone"}]


def test_db_query_tool_rejects_unsafe_sql(tmp_path: Path):
    db = tmp_path / "events.db"
    sqlite3.connect(db).close()
    with pytest.raises(ValidationError):
        run_readonly_query(db, "select * from events; drop table events")


def test_fastapi_agent_endpoints():
    client = TestClient(app)
    health = client.get("/api/v1/agent/health")
    assert health.status_code == 200
    assert "rag" in health.json()

    threat = client.post(
        "/api/v1/agent/analyze-threat",
        json={"label": "Jamming", "confidence": 0.92, "frequency_mhz": 2450, "snr_db": 24},
    )
    assert threat.status_code == 200
    assert threat.json()["level"] == "critical"

    report = client.post("/api/v1/agent/report", json={"label": "Drone", "confidence": 0.8})
    assert report.status_code == 200
    assert "SADAR RF Threat Assessment Report" in report.json()["markdown"]


def test_fastapi_agent_ask_uses_fallback():
    client = TestClient(app)
    response = client.post("/api/v1/agent/ask", json={"question": "What is jamming?", "refresh": True})
    assert response.status_code == 200
    assert "answer" in response.json()
