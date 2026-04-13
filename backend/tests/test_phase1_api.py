from __future__ import annotations

from fastapi.testclient import TestClient


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_and_list_tasks(client: TestClient) -> None:
    create_response = client.post(
        "/api/v1/tasks",
        json={
            "title": "Implement task board",
            "description": "Create the first task API.",
            "type": "feature",
            "project_id": "platform",
        },
    )

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["status"] == "todo"

    list_response = client.get("/api/v1/tasks")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1


def test_task_claim_is_atomic_for_second_agent(client: TestClient) -> None:
    agent_a = client.post("/api/v1/agents", json={"name": "dev-1", "role": "developer"}).json()
    agent_b = client.post("/api/v1/agents", json={"name": "dev-2", "role": "developer"}).json()
    task = client.post(
        "/api/v1/tasks",
        json={
            "title": "Lock a task",
            "description": "Claim should only work once.",
            "type": "feature",
        },
    ).json()

    first_claim = client.post(
        f"/api/v1/tasks/{task['id']}/claim",
        json={"agent_id": agent_a["id"]},
    )
    second_claim = client.post(
        f"/api/v1/tasks/{task['id']}/claim",
        json={"agent_id": agent_b["id"]},
    )

    assert first_claim.status_code == 200
    assert first_claim.json()["status"] == "in_progress"
    assert first_claim.json()["assigned_agent_id"] == agent_a["id"]

    assert second_claim.status_code == 409
    assert second_claim.json()["detail"] == "task_not_available"


def test_memory_endpoint_returns_created_memory(client: TestClient) -> None:
    task = client.post(
        "/api/v1/tasks",
        json={
            "title": "Persist memory",
            "description": "Memory records should be queryable.",
            "type": "research",
        },
    ).json()

    create_response = client.post(
        "/api/v1/memory",
        json={
            "type": "decision",
            "summary": "Use FastAPI",
            "content": "FastAPI keeps the API layer concise.",
            "source_task_id": task["id"],
        },
    )

    assert create_response.status_code == 201

    list_response = client.get("/api/v1/memory")
    assert list_response.status_code == 200
    payload = list_response.json()
    assert len(payload) == 1
    assert payload[0]["summary"] == "Use FastAPI"
