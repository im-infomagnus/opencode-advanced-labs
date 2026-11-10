---
description: Ranked review of staged changes, read-only
agent: plan
---
Review only these staged changes:
!`git diff --cached`

Check correctness, error handling, shared state, data leaks, and tests.
Report each finding on one line, most severe first:
severity (high, medium, low) | category (Security, Reliability, Maintainability,
Best Practices) | evidence (path:line) | smallest fix | follow-up test.
No evidence, no finding. Do not edit files.
End with VERDICT: PASS or FAIL.
