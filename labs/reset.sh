#!/usr/bin/env bash
# Restore labs/skyroute.
#   bash labs/reset.sh            restore your last commit (committed lab work on your branch survives)
#   bash labs/reset.sh --starter  restore the original starter (tag skyroute-starter-v2), discarding lab work
# Override the source with SKYROUTE_REF=<ref>. Touches nothing outside labs/skyroute. Safe to rerun.
set -euo pipefail

target="labs/skyroute"
root="$(git -C "$(dirname "$0")" rev-parse --show-toplevel 2>/dev/null)" || {
  echo "reset.sh: not inside a Git repository. Clone the course repository and try again." >&2
  exit 1
}
cd "$root"

if ! git rev-parse --verify --quiet HEAD >/dev/null; then
  echo "reset.sh: this repository has no commits yet, so there is no starter state to restore." >&2
  echo "reset.sh: nothing was changed. Commit $target first, then run this script again." >&2
  exit 1
fi

ref="${SKYROUTE_REF:-HEAD}"
starter=0
if [ "${1:-}" = "--starter" ]; then
  # skyroute-starter-v2 replaced the original tag when the planted token changed (v1.3.0).
  for tag in skyroute-starter-v2 skyroute-starter; do
    if git rev-parse --verify --quiet "refs/tags/$tag" >/dev/null; then
      ref="$tag"
      if [ "$tag" = skyroute-starter ]; then
        echo "reset.sh: WARNING: tag skyroute-starter-v2 not found, so this uses the old tag skyroute-starter." >&2
        echo "reset.sh: WARNING: the old starter has the old planted token, so lab checks that name the token will not match." >&2
        echo "reset.sh: WARNING: run git fetch --tags to get skyroute-starter-v2 (created at release), then run this again." >&2
      fi
      starter=1
      break
    fi
  done
  [ "$starter" = 1 ] || echo "reset.sh: tag skyroute-starter-v2 not found (run git fetch --tags); using HEAD." >&2
fi

if ! git cat-file -e "$ref:$target" 2>/dev/null; then
  echo "reset.sh: $ref does not contain $target, so there is no starter state to restore." >&2
  echo "reset.sh: nothing was changed." >&2
  exit 1
fi

# Tracked files: match the starter in the index and the working tree, including
# files staged as new or deleted since. Files added after the starter are removed.
git restore --source="$ref" --staged --worktree -- "$target"
git ls-files -- "$target" | while IFS= read -r f; do
  if ! git cat-file -e "$ref:$f" 2>/dev/null; then
    git rm -q --cached -f -- "$f"
    rm -f -- "$f"
  fi
done
# Untracked and ignored files (new tests, out/, __pycache__, .opencode/).
git clean -fdxq -- "$target"

echo "reset.sh: $target matches $ref."
git status --short -- "$target"
if [ "$starter" = 1 ] && [ -n "$(git status --porcelain -- "$target")" ]; then
  echo "reset.sh: the lines above are the starter files, staged but not committed. Your branch still points at your last lab commit."
  echo "reset.sh: to keep the starter, run: git commit -m \"Back to SkyRoute starter\". A plain reset.sh without that commit brings your lab work back."
fi
