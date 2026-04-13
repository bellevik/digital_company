from __future__ import annotations

from fastapi.testclient import TestClient

from app.api.dependencies import execution_adapter_dependency
from app.main import app
from app.services.execution import ExecutionResult


class WorkflowExecutionAdapter:
    def run(self, *, prompt: str) -> ExecutionResult:
        return ExecutionResult(
            stdout=(
                '{"summary":"Completed implementation for review.",'
                '"memory_summary":"Implementation complete",'
                '"memory_content":"Ready for human review.",'
                '"follow_up_tasks":[]}'
            ),
            stderr="",
            exit_code=0,
            command=["workflow-executor"],
        )


def _create_completed_task(client: TestClient) -> tuple[dict, dict]:
    app.dependency_overrides[execution_adapter_dependency] = lambda: WorkflowExecutionAdapter()
    agent = client.post("/api/v1/agents", json={"name": "workflow-dev", "role": "developer"}).json()
    task = client.post(
        "/api/v1/tasks",
        json={
            "title": "Prepare reviewable work",
            "description": "Implement and submit for approval.",
            "type": "feature",
            "project_id": "platform",
        },
    ).json()
    work = client.post(f"/api/v1/agents/{agent['id']}/work")
    assert work.status_code == 200
    app.dependency_overrides.pop(execution_adapter_dependency, None)
    return agent, task


def test_submit_for_review_creates_pending_workflow(client: TestClient) -> None:
    _, task = _create_completed_task(client)

    response = client.post(
        f"/api/v1/tasks/{task['id']}/submit-for-review",
        json={"branch_name": "codex/phase4-review", "submission_notes": "Ready for PR review."},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["task_id"] == task["id"]
    assert payload["approval_status"] == "pending_approval"
    assert payload["branch_name"] == "codex/phase4-review"
    assert payload["latest_task_run"] is not None


def test_review_approval_marks_workflow_approved(client: TestClient) -> None:
    _, task = _create_completed_task(client)
    client.post(
        f"/api/v1/tasks/{task['id']}/submit-for-review",
        json={"branch_name": "codex/phase4-review", "submission_notes": "Ready for PR review."},
    )

    response = client.post(
        f"/api/v1/tasks/{task['id']}/review-decisions",
        json={
            "reviewer_name": "CEO",
            "decision": "approved",
            "summary": "Looks good to merge.",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["approval_status"] == "approved"
    assert len(payload["review_decisions"]) == 1
    assert payload["review_decisions"][0]["decision"] == "approved"

    workflow_lookup = client.get(f"/api/v1/workflows/{task['id']}")
    assert workflow_lookup.status_code == 200
    assert workflow_lookup.json()["approval_status"] == "approved"


def test_review_changes_requested_reopens_task(client: TestClient) -> None:
    _, task = _create_completed_task(client)
    client.post(
        f"/api/v1/tasks/{task['id']}/submit-for-review",
        json={"branch_name": "codex/phase4-review", "submission_notes": "Ready for PR review."},
    )

    response = client.post(
        f"/api/v1/tasks/{task['id']}/review-decisions",
        json={
            "reviewer_name": "CEO",
            "decision": "changes_requested",
            "summary": "Address the edge cases before approval.",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["approval_status"] == "changes_requested"

    tasks = client.get("/api/v1/tasks").json()
    reopened = next(item for item in tasks if item["id"] == task["id"])
    assert reopened["status"] == "todo"
    assert reopened["completed_at"] is None
