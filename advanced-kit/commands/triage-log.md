---
description: Triage a large log with filters and counts, read-only
agent: plan
---
$ARGUMENTS is a large log. Do not read the whole file. Use grep and shell
pipelines to count failed runs by their final error line, then list each
failure class with its count, one example input, and the file:line in the code
where it fails. Separate bad input from valid input that crashes.
End with one line: TOP CAUSE: <file:line> <one sentence>.
