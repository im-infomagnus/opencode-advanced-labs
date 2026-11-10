---
description: Presenter summary of what is built and what is left (deterministic status plus a 5-line summary)
---

This is the deterministic mission status from `tools/mission_status.py` (board, files on disk, each workstream's own tests, the full suite, git log):

!`python3 tools/mission_status.py`

Write a 5-line summary for the presenter to read aloud to the class. Line 1: overall progress: workstreams complete out of 6 from the `Built:` line, and the Own tests results. Line 2: everything built so far, cumulative, from the `Built:` line and the commits since baseline. Line 3: what is running now (board `in progress` or `review`). Line 4: what is left, from the `Remaining:` line. Line 5: anything blocked, any `Attention:` line, or any Own tests failure on a workstream that is not in progress; otherwise "Nothing blocked." A red Full suite line while workstreams are in progress is expected: mention it only if the line says it must be OK. Use only facts in the output above. Do not run other commands and do not edit files.
