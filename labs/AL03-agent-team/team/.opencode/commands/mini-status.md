---
description: Mini mission status from the board, Git, and a test run (no edits)
---

This is the current state of the mini mission, collected by shell before you were called.

Board:

!`cat mission/BOARD.md`

Commits since the starter:

!`git log --oneline -5`

Uncommitted files:

!`git status --short`

Test run:

!`python3 -m unittest`

Write a 3-line status. Line 1: workstreams done out of 2 and the test summary. Line 2: what is running or waiting for review. Line 3: anything blocked or failing, or "Nothing blocked." Use only the facts above. Do not run commands and do not edit files.
