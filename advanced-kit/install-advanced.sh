#!/usr/bin/env bash
# Install the OpenCode advanced kit into a SkyRoute workspace.
#
#   advanced-kit/install-advanced.sh [--force] <workspace>
#
# Copies the four plugins to <workspace>/.opencode/plugins/<id>/index.ts and the
# navdata MCP server to <workspace>/.opencode/mcp/navdata_server.py, and the kit
# commands to <workspace>/.opencode/commands/. Writes the kit
# config (plugin options, audit-log permissions, MCP server, references) to <workspace>/opencode.jsonc when
# the workspace has no OpenCode config, or to opencode.advanced.jsonc next to an
# existing one for you to merge by hand. Never overwrites an existing opencode.jsonc.
# Adds .opencode/audit/ (the audit-log output) to <workspace>/.gitignore when the
# line is not there yet.
# Safe to rerun: identical files are left alone. A different file is replaced only
# with --force, and the previous version is kept as <file>.bak.
set -euo pipefail

usage() {
  echo "usage: $0 [--force] <workspace>" >&2
  exit 2
}

force=0
target=""
for arg in "$@"; do
  case "$arg" in
    --force) force=1 ;;
    -h|--help) usage ;;
    -*) echo "unknown option: $arg" >&2; usage ;;
    *) [ -z "$target" ] || usage; target="$arg" ;;
  esac
done
[ -n "$target" ] || usage
[ -d "$target" ] || { echo "error: $target is not a directory" >&2; exit 1; }

kit="$(cd "$(dirname "$0")" && { pwd -W 2>/dev/null || pwd; })"
target="$(cd "$target" && pwd)"
[ -f "$target/skyroute/navdata.py" ] || echo "warning    $target has no skyroute/navdata.py; the navdata MCP server and skyroute_trace need a SkyRoute workspace"
created=0 updated=0 unchanged=0 skipped=0

# place <content-file-or-dash> <destination relative to target>; reads stdin for "-"
place() {
  local src="$1" rel="$2" dest="$target/$2" content
  if [ "$src" = "-" ]; then content="$(cat)"; else content="$(cat "$src")"; fi
  if [ ! -e "$dest" ]; then
    mkdir -p "$(dirname "$dest")"
    printf '%s\n' "$content" > "$dest"
    echo "created    $rel"
    created=$((created + 1))
  elif [ "$(cat "$dest")" = "$content" ]; then
    unchanged=$((unchanged + 1))
  elif [ "$force" -eq 1 ]; then
    cp "$dest" "$dest.bak"
    printf '%s\n' "$content" > "$dest"
    echo "updated    $rel (previous version saved as $rel.bak)"
    updated=$((updated + 1))
  else
    echo "skipped    $rel (exists with different content; rerun with --force to replace)"
    skipped=$((skipped + 1))
  fi
}

for plugin in verify-on-edit skyroute-trace audit-log ai-gate; do
  place "$kit/plugins/$plugin/index.ts" ".opencode/plugins/$plugin/index.ts"
done
place "$kit/mcp/navdata_server.py" ".opencode/mcp/navdata_server.py"
for command in "$kit"/commands/*.md; do
  place "$command" ".opencode/commands/$(basename "$command")"
done

reference_dir="$kit/reference/skyroute-docs"
escaped="$(printf '%s' "$reference_dir" | sed 's/[&|\\]/\\&/g')"
config="$(sed "s|__REFERENCE_DIR__|$escaped|" "$kit/opencode.advanced.jsonc")"
config_rel="opencode.jsonc"
if [ ! -e "$target/opencode.jsonc" ] || [ "$(cat "$target/opencode.jsonc")" != "$config" ]; then
  for existing in opencode.jsonc opencode.json .opencode/opencode.jsonc .opencode/opencode.json; do
    if [ -e "$target/$existing" ]; then
      config_rel="opencode.advanced.jsonc"
      echo "note       $existing already exists; writing the kit config to opencode.advanced.jsonc instead"
      break
    fi
  done
fi
place - "$config_rel" <<<"$config"

# The audit log is local evidence, not source. Add the ignore line once.
if ! grep -qxF '.opencode/audit/' "$target/.gitignore" 2>/dev/null; then
  if [ -s "$target/.gitignore" ] && [ -n "$(tail -c 1 "$target/.gitignore")" ]; then echo >> "$target/.gitignore"; fi
  echo '.opencode/audit/' >> "$target/.gitignore"
  echo "gitignore  added .opencode/audit/ to .gitignore"
fi

echo "done       $created created, $updated updated, $unchanged unchanged, $skipped skipped in $target"
if [ "$config_rel" = "opencode.advanced.jsonc" ]; then
  echo "action     merge the plugins, permissions, mcp.servers.navdata, and references blocks of opencode.advanced.jsonc into your config"
fi
echo "verify     cd \"$target\" && opencode api GET \"/api/plugin?location%5Bdirectory%5D=\$(pwd -W 2>/dev/null || pwd -P)\""
[ "$skipped" -eq 0 ]
