from __future__ import annotations

from fastapi.testclient import TestClient


def test_seed_demo_populates_empty_system(client: TestClient) -> None:
    response = client.post("/api/v1/operations/seed-demo")

    assert response.status_code == 200
    payload = response.json()
    assert payload["created_agents"] >= 1
    assert payload["created_tasks"] >= 1
    assert payload["created_memories"] >= 1

    summary = client.get("/api/v1/operations/summary")
    assert summary.status_code == 200
    summary_payload = summary.json()
    assert summary_payload["agents_total"] >= 1
    assert summary_payload["tasks_total"] >= 1
    assert summary_payload["memories_total"] >= 1


def test_manual_self_improvement_run_creates_follow_up_tasks(client: TestClient) -> None:
    client.post("/api/v1/tasks", json={
        "title": "Broken worker run",
        "description": "Something failed and needs attention.",
        "type": "ops",
        "project_id": "platform",
    })
    tasks = client.get("/api/v1/tasks").json()
    target_task = tasks[0]
    client.patch(
        f"/api/v1/tasks/{target_task['id']}",
        json={"status": "failed"},
    )

    response = client.post("/api/v1/operations/self-improvement/run")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "succeeded"
    assert payload["created_task_count"] >= 1
    assert payload["proposed_branch_name"].startswith("codex/self-improvement")

    runs = client.get("/api/v1/operations/self-improvement/runs")
    assert runs.status_code == 200
    assert len(runs.json()) == 1

    all_tasks = client.get("/api/v1/tasks").json()
    assert any(task["title"] == "Investigate failed task executions" for task in all_tasks)
