# Digital Company Implementation Plan

This project starts from an empty repository and is being built in approval-gated phases until it is a working product.

## Delivery Rules

- Every phase ends with verification.
- After each phase, approval is required before commit and push.
- The system must remain runnable locally at the end of each phase.

## Phase 0: Foundation

- Monorepo scaffold for backend, frontend, and docs
- Docker Compose local environment with Postgres + pgvector
- FastAPI service shell and React UI shell
- Shared environment templates and operator documentation

## Phase 1: Core Backend and Database

- SQLAlchemy models and Alembic migrations
- Task, agent, memory, and embedding tables
- Audit/event model
- Atomic task locking and core CRUD API

## Phase 2: Agent Runtime

- Worker process and role registry
- Prompt builder and execution adapters
- Codex CLI command runner with structured result capture
- Task progression and retry model

## Phase 3: Memory System

- Memory ingestion pipeline
- Summaries, keyword search, and vector retrieval
- Context builder for agent prompts

## Phase 4: Workflow and Approval Gate

- Review flow and approval states
- Branch/run tracking
- Action logs and operator visibility

## Phase 5: UI

- Task board
- Task detail and chat stream
- Activity feed
- Realtime updates

## Phase 6: Self-Improvement and Hardening

- Scheduled improvement loop
- Deployment and operations docs
- End-to-end flows and demo data
- Product hardening for a finished MVP

