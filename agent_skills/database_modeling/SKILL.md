---
name: Database Modeling
description: Use this skill when an agent is creating or modifying persisted data structures and must reason about constraints, lifecycle, and migrations.
metadata:
  short-description: Shape schemas, constraints, and record lifecycle carefully
  recommended-roles: architect, developer, reviewer
---

# Database Modeling

## Working Style

- Think about ownership, constraints, indexes, and deletion behavior together.
- Prefer schema changes that are easy to migrate and easy to operate.
- Call out backfill or migration consequences when records already exist.

## Output Expectations

- Describe the intended data shape, not just the code change.
- Surface any irreversible or risky migration decisions directly.
