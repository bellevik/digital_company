---
name: Debugging Discipline
description: Use this skill when an agent is diagnosing a failure and should isolate causes methodically rather than guessing at fixes.
metadata:
  short-description: Trace failures with evidence before changing code
  recommended-roles: developer, tester, review_agent
---

# Debugging Discipline

## Working Style

- Start from observable failure, not from a theory.
- Narrow the scope by checking assumptions one by one.
- Prefer confirming the root cause before applying a fix.

## Output Expectations

- State what failed, why it failed, and what evidence supports that conclusion.
- Avoid speculative language when the cause is not yet proven.
