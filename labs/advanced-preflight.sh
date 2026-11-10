#!/usr/bin/env bash
# Preflight for the advanced labs (AL01 to AL06). Run it in Git Bash on Windows, or in any
# Bash on macOS and Linux, from the root of the course repository clone:
#   bash labs/advanced-preflight.sh               check only
#   bash labs/advanced-preflight.sh --fix-python3 Windows: also create python3.exe next to python.exe
# Every line starts with PASS, WARN, or FAIL. Fix every FAIL before Lab AL01 step 1.
set -uo pipefail

fix=0
[ "${1:-}" = "--fix-python3" ] && fix=1
fails=0
pass() { printf 'PASS  %s\n' "$*"; }
warn() { printf 'WARN  %s\n' "$*"; }
fail() { printf 'FAIL  %s\n' "$*"; fails=$((fails + 1)); }

windows=0
case "$(uname -s)" in MINGW*|MSYS*|CYGWIN*) windows=1 ;; esac

# 1. Bash. PowerShell and cmd strip or split the quotes in the lab commands.
if [ -n "${BASH_VERSION:-}" ]; then pass "bash $BASH_VERSION"; else fail "not running in bash; on Windows open Git Bash"; fi

# 2. Git and OpenCode.
if command -v git >/dev/null 2>&1; then pass "$(git --version)"; else fail "git not found"; fi
if command -v opencode >/dev/null 2>&1; then
  pass "opencode $(opencode --version 2>/dev/null | tr -d '\r')"
else
  fail "opencode not found on PATH"
fi

# 3. python3 must be a real Python 3.10 or later, not the Microsoft Store stub (exit code 49).
#    Use `type -P` so a Bash function named python3 does not hide the real program:
#    OpenCode's shell tool, `!` commands, plugins, and MCP servers never see Bash functions.
real_python3="$(type -P python3 2>/dev/null || true)"
version=""
if [ -n "$real_python3" ]; then
  version="$("$real_python3" -c 'import sys; print("%d.%d" % sys.version_info[:2])' 2>/dev/null | tr -d '\r')"
fi
if [ -n "$version" ] && [ "${version%%.*}" -ge 3 ] && [ "${version#*.}" -ge 10 ]; then
  pass "python3 $version ($real_python3)"
elif [ "$windows" -eq 1 ]; then
  if [ -n "$real_python3" ] && [[ "$real_python3" == *WindowsApps* ]]; then
    msg="python3 is the Microsoft Store stub ($real_python3)"
  else
    msg="no working python3 program"
  fi
  py_exe="$(py -3 -c 'import sys; print(sys.executable)' 2>/dev/null | tr -d '\r')"
  if [ -z "$py_exe" ]; then
    fail "$msg, and py -3 does not work either. Install Python 3.10+ from python.org."
  elif [ "$fix" -eq 1 ]; then
    target="$(dirname "$(cygpath -u "$py_exe")")/python3.exe"
    if cp "$(cygpath -u "$py_exe")" "$target" 2>/dev/null; then
      pass "created $target. Run this script again to confirm."
      echo "      If python3 still resolves to the stub, turn off the python3.exe and python.exe App execution"
      echo "      aliases (Settings > Apps > Advanced app settings > App execution aliases), then run"
      echo "      'opencode service restart' (only when no OpenCode session is running) and this script again."
    else
      fail "$msg; could not write $target (ask your platform team)"
    fi
  else
    fail "$msg. The Git Bash python3 function does not help here: OpenCode's shell, plugins, and MCP servers never see it. Run: bash labs/advanced-preflight.sh --fix-python3 (see labs/README.md, Windows)"
  fi
else
  fail "python3 3.10 or later not found (got '${version:-nothing}')"
fi

# 4. Windows specifics.
if [ "$windows" -eq 1 ]; then
  if [ "${PYTHONUTF8:-}" = "1" ]; then pass "PYTHONUTF8=1"; else warn "PYTHONUTF8 is not 1; add 'export PYTHONUTF8=1' to ~/.bashrc (session exports are UTF-8)"; fi
  autocrlf="$(git config --get core.autocrlf 2>/dev/null || echo unset)"
  warn "core.autocrlf=$autocrlf; compare files with diff --strip-trailing-cr (the guides do)"
fi

# 5. COURSE points at this clone.
if [ -n "${COURSE:-}" ] && [ -d "$COURSE/advanced-kit" ]; then
  pass "COURSE=$COURSE"
else
  warn "COURSE is not set to the course clone; run: export COURSE=\"\$(pwd -W 2>/dev/null || pwd)\" from the clone root"
fi

# 6. A default model, so `opencode run` and new sessions do not fall back to the newest model.
if command -v opencode >/dev/null 2>&1; then
  if [ -n "$version" ]; then pyrun=("$real_python3"); elif [ "$windows" -eq 1 ]; then pyrun=(py -3); else pyrun=(python3); fi
  model="$(opencode debug config 2>/dev/null | "${pyrun[@]}" -c '
import json, sys
try:
    docs = json.load(sys.stdin)
except Exception:
    sys.exit()
found = [d.get("info", {}).get("model") for d in (docs if isinstance(docs, list) else []) if isinstance(d, dict)]
found = [m for m in found if m]
m = found[-1] if found else ""
if isinstance(m, dict):
    m = "%s/%s" % (m.get("providerID", "?"), m.get("model") or m.get("id") or "?")
print(m)
' 2>/dev/null | tr -d '\r')"
  if [ -n "$model" ]; then
    pass "default model $model"
  else
    fail "no \"model\" in your global opencode.jsonc; opencode run and forks would use the newest available model. See Before the course in the repository README."
  fi
fi

echo
if [ "$fails" -eq 0 ]; then echo "Preflight passed."; else echo "Preflight: $fails FAIL line(s). Fix them before Lab AL01."; fi
exit $(( fails > 0 ))
