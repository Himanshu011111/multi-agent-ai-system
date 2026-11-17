def test_end_to_end_multi_agent_workflow(client, mock_gemini_llm):
    # 1. Create a research task
    create_res = client.post(
        "/api/tasks/create",
        json={
            "title": "Enterprise Agentic AI Evaluation",
            "description": "Analyze multi-agent orchestration benchmarks and generate a verified report.",
            "task_type": "research",
        },
    )
    assert create_res.status_code == 200
    task_id = create_res.json()["id"]

    # 2. Execute the 7-agent LangGraph workflow
    exec_res = client.post(
        f"/api/tasks/{task_id}/execute",
        json={"human_approved": False},
    )
    assert exec_res.status_code == 200
    result = exec_res.json()
    assert result["status"] == "completed"
    assert result["quality_score"] >= 80.0
    assert len(result["reports"]) >= 1

    # 3. Verify report download endpoint
    report_id = result["reports"][0]["id"]
    dl_res = client.get(f"/api/reports/download/{report_id}")
    assert dl_res.status_code == 200
    assert len(dl_res.content) > 100


def test_human_in_the_loop_approval_gate(client, mock_gemini_llm):
    # Sensitive keyword ("email") should pause workflow in 'needs_approval' state
    create_res = client.post(
        "/api/tasks/create",
        json={
            "title": "Send Compliance Audit Email",
            "description": "Compile security audit findings and send email notification to leadership.",
            "task_type": "complex_automation",
        },
    )
    task_id = create_res.json()["id"]

    exec_res = client.post(
        f"/api/tasks/{task_id}/execute",
        json={"human_approved": False},
    )
    assert exec_res.status_code == 200
    assert exec_res.json()["status"] == "needs_approval"

    # Approve task and verify completion
    approve_res = client.post(f"/api/tasks/{task_id}/approve")
    assert approve_res.status_code == 200
    assert approve_res.json()["status"] == "completed"