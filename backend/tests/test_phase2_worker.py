from __future__ import annotations

from fastapi.testclient import TestClient

from app.api.dependencies import execution_adapter_dependency
from app.main import app
from app.services.execution import ExecutionResult


class FakeExecutionAdapter:
    def __init__(self, *, stdout: str, stderr: str = "", exit_code: int = 0):
        self._result = ExecutionResult(
            stdout=stdout,
            stderr=stderr,
            exit_code=exit_code,
            command=["fake-executor"],
        )

    def run(self, *, prompt: str) -> ExecutionResult:
        return self._result


def test_run_agent_once_completes_task_and_creates_follow_ups(client: TestClient) -> None:
    app.dependency_overrides[execution_adapter_dependency] = lambda: FakeExecutionAdapter(
        stdout=(
            '{"summary":"Implemented the first worker pass.",'
            '"memory_summary":"Worker completed feature",'
            '"memory_content":"Feature implementation landed and needs review.",'
            '"follow_up_tasks":[{"title":"Review implementation",'
            '"description":"Perform a focused code review.",'
            '"type":"review","project_id":"platform"}]}'
        )
    )
    agent = client.post("/api/v1/agents", json={"name": "worker-dev", "role": "developer"}).json()
    task = client.post(
        "/api/v1/tasks",
        json={
            "title": "Ship worker runtime",
            "description": "Implement the first worker cycle.",
            "type": "feature",
            "project_id": "platform",
        },
    ).json()

    response = client.post(f"/api/v1/agents/{agent['id']}/work")

    assert response.status_code == 200
    payload = response.json()
    assert payload["outcome"] == "completed"
    assert payload["task_id"] == task["id"]
    assert len(payload["follow_up_task_ids"]) == 1
    assert payload["task_run"]["status"] == "succeeded"
    assert payload["task_run"]["created_follow_up_tasks"] == 1

    task_response = client.get("/api/v1/tasks")
    tasks = task_response.json()
    assert {item["status"] for item in tasks} == {"done", "todo"}

    memory_response = client.get("/api/v1/memory")
    memories = memory_response.json()
    assert len(memories) == 1
    assert memories[0]["summary"] == "Worker completed feature"

    task_runs_response = client.get("/api/v1/task-runs")
    task_runs = task_runs_response.json()
    assert len(task_runs) == 1
    assert task_runs[0]["task_id"] == task["id"]

    app.dependency_overrides.pop(execution_adapter_dependency, None)


def test_run_agent_once_returns_idle_when_queue_has_no_compatible_work(client: TestClient) -> None:
    app.dependency_overrides[execution_adapter_dependency] = lambda: FakeExecutionAdapter(
        stdout='{"summary":"unused","follow_up_tasks":[]}'
    )
    agent = client.post("/api/v1/agents", json={"name": "reviewer-1", "role": "reviewer"}).json()
    client.post(
        "/api/v1/tasks",
        json={
            "title": "Build API",
            "description": "Developer-only work item.",
            "type": "feature",
        },
    )

    response = client.post(f"/api/v1/agents/{agent['id']}/work")

    assert response.status_code == 200
    assert response.json()["outcome"] == "idle"
    assert response.json()["task_run"] is None

    app.dependency_overrides.pop(execution_adapter_dependency, None)


def test_run_agent_once_marks_task_failed_on_executor_error(client: TestClient) -> None:
    app.dependency_overrides[execution_adapter_dependency] = lambda: FakeExecutionAdapter(
        stdout="",
        stderr="codex exec failed",
        exit_code=2,
    )
    agent = client.post("/api/v1/agents", json={"name": "tester-1", "role": "tester"}).json()
    task = client.post(
        "/api/v1/tasks",
        json={
            "title": "Validate release",
            "description": "Testing task that should fail.",
            "type": "review",
        },
    ).json()

    response = client.post(f"/api/v1/agents/{agent['id']}/work")

    assert response.status_code == 200
    payload = response.json()
    assert payload["outcome"] == "failed"
    assert payload["task_id"] == task["id"]
    assert payload["task_run"]["status"] == "failed"
    assert payload["memory_id"] is None

    tasks = client.get("/api/v1/tasks").json()
    assert tasks[0]["status"] == "failed"

    app.dependency_overrides.pop(execution_adapter_dependency, None)
