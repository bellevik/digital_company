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
- `GET /api/v1/memory`
- `POST /api/v1/memory`

## Phase Workflow

- Implement one phase at a time
- Verify before approval
- Commit and push only after approval

The detailed delivery breakdown lives in [`docs/implementation-plan.md`](/Users/bellevik/git/codex/digital_company/docs/implementation-plan.md).
