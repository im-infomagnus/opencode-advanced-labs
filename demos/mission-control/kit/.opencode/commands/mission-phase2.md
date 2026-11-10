---
description: Commander executes Phase 2 (integration, reviews, fix rounds, merge, evidence)
agent: commander
---

Execute Phase 2 of the mission in mission/MISSION-PROMPT.md. Read section 9 again and load the mission-protocol skill. Finish any Phase 1 workstream that is not done first; W6 at tooling done counts as finished for Phase 1. Then integrate skyroute wx and skyroute brief, launch mission-reviewer on every finished workstream, run fix rounds with fresh engineers, merge the requirement fragments, and launch the final W6 pass, verified with python3 tools/mission_status.py --verify W6 --final. Update mission/BOARD.md on every report.

Current status before you start:

!`python3 tools/mission_status.py`
