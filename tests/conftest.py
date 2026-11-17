import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import app.database.db as db_mod
import app.orchestration.graph as graph_mod
import app.orchestration.workflow as workflow_mod
from app.database.db import Base, get_db
from app.main import app
from app.services.llm_service import llm_service


TEST_DATABASE_URL = "sqlite:///./test_multi_agent_system.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture()
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db_session, monkeypatch):
    monkeypatch.setattr(db_mod, "SessionLocal", TestingSessionLocal)
    monkeypatch.setattr(graph_mod, "SessionLocal", TestingSessionLocal)
    monkeypatch.setattr(workflow_mod, "SessionLocal", TestingSessionLocal)

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def mock_gemini_llm(monkeypatch):
    def fake_generate_text(prompt: str, system_instruction: str = None, temperature: float = 0.3) -> str:
        sys_lower = (system_instruction or "").lower()
        if "supervisor" in sys_lower or "routing" in sys_lower:
            return '{"task_type": "research", "requires_research": true, "requires_rag": false, "requires_analysis": true, "requires_automation": true, "supervisor_notes": "Mocked supervisor routing."}'
        if "planner" in sys_lower or "roadmap" in sys_lower:
            return '{"plan_summary": "Mocked 3-step roadmap", "subtasks": [{"step": 1, "agent": "Research Agent", "task": "Gather evidence", "priority": "High"}]}'
        if "reviewer" in sys_lower or "quality" in sys_lower:
            return '{"quality_score": 94.0, "quality_explanation": "All facts verified and citations accurate.", "revision_needed": false, "refined_report": "# Verified Enterprise Report\\n\\n## Executive Summary\\nComprehensive verified findings."}'
        return "# Verified Enterprise Report\n\n## Executive Summary\nComprehensive verified findings with citations [1]."

    monkeypatch.setattr(llm_service, "generate_text", fake_generate_text)
    return fake_generate_text