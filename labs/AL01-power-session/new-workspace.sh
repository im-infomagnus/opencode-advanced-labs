#!/usr/bin/env bash
# Create a standalone SkyRoute Git workspace for the advanced labs.
#   bash labs/AL01-power-session/new-workspace.sh                 creates ~/skyroute-adv
#   bash labs/AL01-power-session/new-workspace.sh PATH            creates PATH
#   bash labs/AL01-power-session/new-workspace.sh [PATH] --force  deletes and recreates an earlier workspace
# The workspace holds the SkyRoute starter (tag skyroute-starter-v2, or HEAD) as one commit on branch main,
# so git diff and the /diff viewer show only your lab work. Override the source with SKYROUTE_REF=<ref>.
set -euo pipefail

dest="$HOME/skyroute-adv"
force=0
for arg in "$@"; do
  case "$arg" in
    --force) force=1 ;;
    -h|--help) sed -n '2,7p' "$0"; exit 0 ;;
    *) dest="$arg" ;;
  esac
done

root="$(git -C "$(dirname "$0")" rev-parse --show-toplevel 2>/dev/null)" || {
  echo "new-workspace.sh: run this from a clone of the course repository." >&2
  exit 1
}

ref="${SKYROUTE_REF:-}"
if [ -z "$ref" ]; then
  for tag in skyroute-starter-v2 skyroute-starter; do
    if git -C "$root" rev-parse --verify --quiet "refs/tags/$tag" >/dev/null; then
      ref="$tag"
      if [ "$tag" = skyroute-starter ]; then
        echo "new-workspace.sh: WARNING: tag skyroute-starter-v2 not found, so this uses the old tag skyroute-starter." >&2
        echo "new-workspace.sh: WARNING: the old starter has the old planted token, so lab checks that name the token will not match." >&2
        echo "new-workspace.sh: WARNING: run git fetch --tags to get skyroute-starter-v2 (created at release), then run this again." >&2
      fi
      break
    fi
  done
  if [ -z "$ref" ]; then
    ref="HEAD"
    echo "new-workspace.sh: tag skyroute-starter-v2 not found (run git fetch --tags); using HEAD." >&2
  fi
fi

if [ -e "$dest" ]; then
  if [ "$force" -ne 1 ]; then
    echo "new-workspace.sh: $dest already exists. Add --force to delete and recreate it." >&2
    exit 1
  fi
  # Only delete what this script creates: a Git repository with the SkyRoute package in it.
  if [ ! -d "$dest/.git" ] || [ ! -f "$dest/skyroute/route.py" ]; then
    echo "new-workspace.sh: $dest is not a SkyRoute workspace; refusing to delete it." >&2
    exit 1
  fi
  # On Windows the service can hold the folder for a moment after the files are gone; retry briefly.
  removed=0
  for attempt in 1 2 3 4 5; do
    if rm -rf -- "$dest" 2>/dev/null; then removed=1; break; fi
    sleep 2
  done
  if [ "$removed" -ne 1 ]; then
    echo "new-workspace.sh: could not delete $dest. On Windows, the OpenCode service keeps files open in a" >&2
    echo "new-workspace.sh: workspace it has loaded (plugins, MCP servers). Quit every OpenCode TUI in it, then run:" >&2
    echo "new-workspace.sh:   opencode service stop" >&2
    echo "new-workspace.sh:   bash $0 $*" >&2
    echo "new-workspace.sh:   opencode service start" >&2
    echo "new-workspace.sh: If the rerun says it is not a SkyRoute workspace, the first try deleted part of it: run rm -rf \"$dest\" yourself (often no service stop is needed), then rerun without --force." >&2
    exit 1
  fi
fi

mkdir -p "$dest"
git -C "$root" archive --format=tar "$ref" labs/skyroute | tar -x -C "$dest" --strip-components=2
printf '__pycache__/\n*.pyc\nout/\n' > "$dest/.gitignore"

cd "$dest"
git init -q -b main
git add -A
# Later lab steps commit too. Without a global identity, set one in this repository only.
if [ -z "$(git config user.name || true)" ]; then
  git config user.name "SkyRoute Lab"
  echo "new-workspace.sh: no Git user.name configured; set user.name \"SkyRoute Lab\" in $dest only."
fi
if [ -z "$(git config user.email || true)" ]; then
  git config user.email "lab@example.invalid"
  echo "new-workspace.sh: no Git user.email configured; set user.email lab@example.invalid in $dest only."
fi
git commit -q -m "SkyRoute starter"

echo "new-workspace.sh: created $dest from $ref."
# A rebuilt folder keeps the service's old view of it until a reload; harmless for a new folder.
if command -v opencode >/dev/null 2>&1; then opencode reload >/dev/null 2>&1 || true; fi
# PYTHON overrides the Python command, for example PYTHON="py -3" in Git Bash on Windows.
python="${PYTHON:-python3}"
status=0
tests="$($python -m unittest 2>&1)" || status=$?
printf '%s\n' "$tests" | tail -n 1
echo "new-workspace.sh: python -m unittest exit status $status (the starter has one known failure, so 1 is expected)."
