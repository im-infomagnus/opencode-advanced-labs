---
description: Generate mission/MISSION-PROMPT.md from the brief and template, then validate it
agent: build
---

Read mission/BRIEF.md and follow mission/PROMPT-TEMPLATE.md to write the full commander prompt to mission/MISSION-PROMPT.md. Then run `python3 mission/check_prompt.py mission/MISSION-PROMPT.md` and fix the file until the check prints PASS.
