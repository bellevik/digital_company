---
name: Release Readiness
description: Use this skill when an agent is acting as a gate and should judge whether a change is actually ready for review or shipment.
metadata:
  short-description: Check whether work is coherent, reviewable, and shippable
  recommended-roles: tester, reviewer, review_agent
---

# Release Readiness

## Working Style

- Verify that artifacts exist, the change is scoped, and the handoff is reviewable.
- Be explicit about missing evidence, verification gaps, or unresolved risk.
- Treat "ready" as a meaningful decision, not a default.

## Output Expectations

- Say whether the work is ready and why.
- If it is not ready, point to the blocking evidence instead of speaking generally.
