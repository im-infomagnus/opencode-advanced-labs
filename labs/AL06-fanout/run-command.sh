#!/usr/bin/env bash
# Create a session in this workspace and run one custom command through the API.
#   bash "$COURSE/labs/AL06-fanout/run-command.sh" <command-name> [arguments]
set -euo pipefail
cmd="${1:?usage: run-command.sh <command-name> [arguments]}"; args="${2:-}"
python="${PYTHON:-python3}"
sid=$(opencode api session.create \
  --data "{\"title\":\"API: /$cmd\",\"location\":{\"directory\":\"$(pwd -W 2>/dev/null || pwd)\"}}" |
  $python -c 'import json,sys; print(json.load(sys.stdin)["data"]["id"])')
opencode api session.command --param sessionID="$sid" --data "{\"name\":\"$cmd\",\"text\":\"$args\"}"
echo "$sid"
