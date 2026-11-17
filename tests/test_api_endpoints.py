import io


def test_health_and_root_endpoints(client):
    root_res = client.get("/")
    assert root_res.status_code == 200
    assert root_res.json()["status"] == "online"

    health_res = client.get("/health")
    assert health_res.status_code == 200
    body = health_res.json()
    assert body["status"] == "healthy"
    assert "llm_model" in body
    assert "embedding_model" in body


def test_task_creation_and_listing(client):
    create_payload = {
        "title": "Test Quantum Computing Architecture",
        "description": "Research fault-tolerant quantum error correction algorithms.",
        "task_type": "research",
    }
    res = client.post("/api/tasks/create", json=create_payload)
    assert res.status_code == 200
    task_data = res.json()
    assert task_data["title"] == create_payload["title"]
    assert task_data["status"] == "pending"

    list_res = client.get("/api/tasks/")
    assert list_res.status_code == 200
    assert any(t["id"] == task_data["id"] for t in list_res.json())

    stats_res = client.get("/api/tasks/summary/stats")
    assert stats_res.status_code == 200
    assert stats_res.json()["total_tasks"] >= 1


def test_agents_live_status_registry(client):
    res = client.get("/api/agents/status")
    assert res.status_code == 200
    agents = res.json()["agents"]
    assert len(agents) == 7
    agent_names = {a["name"] for a in agents}
    assert "Supervisor Agent" in agent_names
    assert "Reviewer / QA Agent" in agent_names


def test_document_upload_validation(client):
    # Unsupported file extension (.exe) must be rejected with HTTP 400
    bad_file = io.BytesIO(b"malicious binary content")
    res = client.post(
        "/api/documents/upload",
        files={"file": ("malware.exe", bad_file, "application/octet-stream")},
    )
    assert res.status_code == 400
    assert "Unsupported file format" in res.json()["detail"]

    # Valid .txt document must succeed
    good_file = io.BytesIO(b"LangGraph enables cyclic stateful multi-agent orchestration.")
    ok_res = client.post(
        "/api/documents/upload",
        files={"file": ("architecture_notes.txt", good_file, "text/plain")},
    )
    assert ok_res.status_code == 200
    assert ok_res.json()["filename"] == "architecture_notes.txt"