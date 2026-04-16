from __future__ import annotations

from fastapi.testclient import TestClient


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_and_list_projects(client: TestClient, projects_root) -> None:
    create_response = client.post(
        "/api/v1/projects",
        json={
            "id": "platform",
            "name": "Platform",
            "description": "Shared platform work.",
        },
    )

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["id"] == "platform"
    assert created["name"] == "Platform"
    assert (projects_root / "platform").is_dir()

    list_response = client.get("/api/v1/projects")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1


def test_delete_project_removes_empty_workspace(client: TestClient, projects_root) -> None:
    client.post(
        "/api/v1/projects",
        json={
            "id": "platform",
            "name": "Platform",
            "description": "Shared platform work.",
        },
    )

    delete_response = client.delete("/api/v1/projects/platform")

    assert delete_response.status_code == 204
    assert client.get("/api/v1/projects").json() == []
    assert not (projects_root / "platform").exists()


def test_delete_project_rejects_projects_with_tasks(client: TestClient) -> None:
    client.post(
        "/api/v1/projects",
        json={"id": "platform", "name": "Platform", "description": "Shared platform work."},
    )
    client.post(
        "/api/v1/tasks",
        json={
            "title": "Implement task board",
            "description": "Create the first task API.",
            "type": "feature",
            "project_id": "platform",
        },
    )

    delete_response = client.delete("/api/v1/projects/platform")

    assert delete_response.status_code == 409
    assert delete_response.json()["detail"] == "project_has_tasks"


def test_create_and_list_tasks(client: TestClient, projects_root) -> None:
    client.post(
        "/api/v1/projects",
        json={"id": "platform", "name": "Platform", "description": "Shared platform work."},
    )
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
    assert (projects_root / "platform").is_dir()
    assert (projects_root / "platform" / ".gitkeep").is_file()

    list_response = client.get("/api/v1/tasks")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1


def test_create_task_rejects_unsafe_project_id(client: TestClient) -> None:
    response = client.post(
        "/api/v1/tasks",
        json={
            "title": "Bad path",
            "description": "Should not allow traversal.",
            "type": "feature",
            "project_id": "../outside",
        },
    )

    assert response.status_code == 422
    assert "project_id must use only letters, numbers, dots, underscores, or hyphens" in response.json()["detail"]


def test_create_task_requires_existing_project(client: TestClient) -> None:
    response = client.post(
        "/api/v1/tasks",
        json={
            "title": "Unknown project",
            "description": "Tasks must target an existing project.",
            "type": "feature",
            "project_id": "missing-project",
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "project_not_found"


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


def test_retry_failed_task_returns_it_to_queue(client: TestClient) -> None:
    task = client.post(
        "/api/v1/tasks",
        json={
            "title": "Retry me",
            "description": "Failed work should be queueable again.",
            "type": "feature",
        },
    ).json()
    client.patch(f"/api/v1/tasks/{task['id']}", json={"status": "failed"})

    retry_response = client.post(f"/api/v1/tasks/{task['id']}/retry")

    assert retry_response.status_code == 200
    payload = retry_response.json()
    assert payload["status"] == "todo"
    assert payload["completed_at"] is None
    assert payload["assigned_agent_id"] is None

    events = client.get(f"/api/v1/tasks/{task['id']}/events").json()
    assert any(event["payload"].get("action") == "retry_requested" for event in events)


def test_delete_task_removes_task_history_and_detaches_memory(client: TestClient) -> None:
    task = client.post(
        "/api/v1/tasks",
        json={
            "title": "Remove me",
            "description": "Deleted work should leave no task records.",
            "type": "research",
        },
    ).json()
    memory = client.post(
        "/api/v1/memory",
        json={
            "type": "decision",
            "summary": "Keep memory",
            "content": "Memory survives task deletion.",
            "source_task_id": task["id"],
        },
    ).json()

    delete_response = client.delete(f"/api/v1/tasks/{task['id']}")

    assert delete_response.status_code == 200
    assert delete_response.json() == {"status": "deleted"}
    assert all(item["id"] != task["id"] for item in client.get("/api/v1/tasks").json())
    assert client.get(f"/api/v1/tasks/{task['id']}/events").json() == []

    memories = client.get("/api/v1/memory").json()
    detached_memory = next(item for item in memories if item["id"] == memory["id"])
    assert detached_memory["source_task_id"] is None


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
