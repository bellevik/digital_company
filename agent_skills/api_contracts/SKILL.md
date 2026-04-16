---
name: API Contracts
description: Use this skill when an agent is designing, changing, or reviewing an API boundary and needs to make request and response behavior explicit.
metadata:
  short-description: Define interfaces, payloads, and failure modes clearly
  recommended-roles: architect, developer, reviewer
---

# API Contracts

## Working Style

- Name the boundary being changed.
- State the expected inputs and outputs in concrete terms.
- Call out validation rules, error behavior, and compatibility risk.

## Output Expectations

- Leave behind contract-level detail that another developer can implement without guessing.
- If an API is not changing, say so explicitly instead of implying drift.
