# Digital Company

Digital Company is a local-first autonomous AI software organization scaffold. It is being built in approval-gated phases from the Codex blueprint in [`/Users/bellevik/Downloads/full_codex_blueprint.md`](/Users/bellevik/Downloads/full_codex_blueprint.md).

## Current Scope

Phase 0 establishes the project foundation:

- FastAPI backend scaffold
- React frontend scaffold
- Postgres + pgvector local stack
- Docker Compose orchestration
- Base documentation and environment templates

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

## Phase Workflow

- Implement one phase at a time
- Verify before approval
- Commit and push only after approval

The detailed delivery breakdown lives in [`docs/implementation-plan.md`](/Users/bellevik/git/codex/digital_company/docs/implementation-plan.md).
