#!/usr/bin/env bash
# _install.sh — runs once after the skill is extracted into the sandbox.
# (Triggered by enterprise_runtime apply.py.)
#
# Exposes the `msgraph` wrapper on PATH so the agent can simply call
# `msgraph <subcommand>` instead of long absolute paths. The wrapper itself
# resolves symlinks back to the bundled binary and loads .env.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MSGRAPH_CLI="$SCRIPT_DIR/msgraph"

chmod +x "$MSGRAPH_CLI" "$SCRIPT_DIR/.bin"

CLI_LINK="/usr/local/bin/msgraph"
if [[ -e "$CLI_LINK" || -L "$CLI_LINK" ]]; then
  rm -f "$CLI_LINK"
fi
ln -s "$MSGRAPH_CLI" "$CLI_LINK"
echo "[microsoft] linked $CLI_LINK -> $MSGRAPH_CLI"
