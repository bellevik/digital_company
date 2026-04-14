# Digital Company

Digital Company is a local-first autonomous AI software organization scaffold. It is being built in approval-gated phases from the Codex blueprint in [`/Users/bellevik/Downloads/full_codex_blueprint.md`](/Users/bellevik/Downloads/full_codex_blueprint.md).

## Current Scope

Phase 0 establishes the project foundation:

- FastAPI backend scaffold
- React frontend scaffold
- Postgres + pgvector local stack
- Docker Compose orchestration
- Base documentation and environment templates

Phase 1 adds the first working backend domain:

- SQLAlchemy models for tasks, agents, memories, embeddings, and task events
- Alembic migration for the initial Postgres + pgvector schema
- Atomic task claim endpoint so only one agent can acquire a task
- API endpoints for task, agent, and memory creation/listing
- Backend tests for the initial workflow

Phase 2 adds the first worker runtime:

- Role-based prompt templates for the agent system
- Task run records capturing prompt, stdout, stderr, exit code, and follow-up count
- Operator-triggered worker cycle endpoint for running one agent against the queue
- Codex CLI execution adapter boundary with a mock adapter option for local development and tests
- Automatic task completion, task-result memory creation, and follow-up task generation

Phase 3 upgrades the memory system:

- Deterministic embeddings generated for every memory record
- Search API with `keyword`, `vector`, and `hybrid` retrieval strategies
- Retrieval scoring returned to the operator for visibility
- Worker prompts now use retrieved memory context instead of recency-only selection

Phase 4 adds the approval workflow:

- Dedicated workflow record per task tied to the latest task run
- Human review submission with branch tracking and submission notes
- Review decisions with `approved` or `changes_requested`
- Operator workflow visibility endpoints
- Automatic task reopening when changes are requested

Phase 5 delivers the operator UI:

- Live task board grouped by status
- Task detail view with activity feed, task runs, and workflow summary
- Agent console for creation and single-cycle execution
- Task creation form
- Memory search console with retrieval scoring
- Approval controls for review submission and decisions

## Repository Layout

- `backend/`: FastAPI service
- `frontend/`: React + Vite operator UI
- `docs/`: implementation notes and delivery plan

## Local Development

1. Copy `.env.example` to `.env` if you need to override defaults.
2. Start the stack:

```bash
docker compose up --build
```

Or use:

```bash
make dev
```

Expected local services:

- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`
- Postgres: `localhost:5432`

## Backend Commands

Run the initial migration:

```bash
docker compose run --rm backend alembic upgrade head
```

Run the backend tests:

```bash
docker compose run --rm backend pytest
```

Current Phase 1 API surface:

- `GET /api/v1/health`
- `GET /api/v1/meta`
- `GET /api/v1/tasks`
- `POST /api/v1/tasks`
- `PATCH /api/v1/tasks/{task_id}`
- `POST /api/v1/tasks/{task_id}/claim`
- `GET /api/v1/tasks/{task_id}/events`
- `GET /api/v1/agents`
- `POST /api/v1/agents`
- `POST /api/v1/agents/{agent_id}/work`
- `GET /api/v1/memory`
- `POST /api/v1/memory`
- `GET /api/v1/memory/search`
- `GET /api/v1/task-runs`
- `GET /api/v1/workflows`
- `GET /api/v1/workflows/{task_id}`
- `POST /api/v1/tasks/{task_id}/submit-for-review`
- `POST /api/v1/tasks/{task_id}/review-decisions`

## Worker Runtime

The Phase 2 worker runtime executes a single agent cycle through:

1. Selecting the next compatible `todo` task for the agent role
2. Claiming it atomically
3. Building a role-specific prompt with recent memory context
4. Running the configured execution adapter
5. Persisting the execution record in `task_runs`
6. Marking the task `done` or `failed`
7. Writing a `task_result` memory and optional follow-up tasks

By default the worker uses the Codex CLI:

- `CODEX_EXECUTION_BACKEND=codex_cli`
- `CODEX_CLI_COMMAND=codex`

For local dry runs without Codex installed you can switch to:

- `CODEX_EXECUTION_BACKEND=mock`

## Memory Retrieval

Every stored memory now gets an embedding record. The retrieval API supports:

- `keyword`: term overlap scoring
- `vector`: deterministic embedding similarity
- `hybrid`: weighted combination of keyword and vector scores

Example:

```bash
curl "http://localhost:8000/api/v1/memory/search?query=atomic%20task%20locking&strategy=hybrid"
```

## Approval Workflow

The Phase 4 approval flow is:

1. Execute a task through the worker runtime
2. Submit that task for review with a branch name
3. Inspect workflow state through the workflow endpoints
4. Record a human review decision

If a reviewer requests changes, the task is reopened to `todo` so it can re-enter the queue.

## Operator UI

The frontend at `http://localhost:5173` now provides the main operator surface:

- Create tasks and agents
- Run agents against the queue
- Inspect task runs and activity
- Search memory and inspect retrieval scores
- Submit work for review and record review decisions

## Phase Workflow

- Implement one phase at a time
- Verify before approval
- Commit and push only after approval

The detailed delivery breakdown lives in [`docs/implementation-plan.md`](/Users/bellevik/git/codex/digital_company/docs/implementation-plan.md).
