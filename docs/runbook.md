# Digital Company Runbook

## Local Startup

1. Copy `.env.example` to `.env` when overriding defaults.
2. Run `docker compose up --build`.
3. Open the operator console at `http://localhost:5173`.
4. Use the backend docs at `http://localhost:8000/docs` when inspecting raw APIs.

## First Demo Flow

1. Use the operator UI or `POST /api/v1/operations/seed-demo` to seed demo data.
2. Run an idle agent from the UI.
3. Inspect the resulting task run and memory entry.
4. Submit a completed task for review.
5. Record an approval or change request.
6. Trigger `POST /api/v1/operations/self-improvement/run` to generate improvement tasks.

## Scheduler

- The self-improvement scheduler is controlled by `SCHEDULER_ENABLED`.
- `SELF_IMPROVEMENT_INTERVAL_SECONDS` defines the run interval.
- In local development the default is disabled; enable it explicitly in the backend environment when you want periodic runs.

## Operational Expectations

- Agents do not auto-merge anything.
- Review approval is explicit and human-driven.
- Self-improvement creates tasks and proposes branch/PR metadata; it does not directly modify git state.
- The operator console is the primary control surface for day-to-day use.
