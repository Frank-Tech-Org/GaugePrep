#!/usr/bin/env bash
# Registers the Scrapling research server, allows its read tools and shows the diff to read.
# Usage: bash .claude/proposed/apply.sh
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"
src=.claude/proposed
tools=(make_request open_request_session session_make_request close_session list_sessions
  browser_open browser_fetch_once browser_fetch browser_extract browser_actions browser_observe
  browser_screenshot browser_network_requests browser_network_request)

install -m 644 "$src/mcp.json" .mcp.json
allow=$(printf 'mcp__scrapling__%s\n' "${tools[@]}" | jq -R . | jq -s .)
tmp=$(mktemp)
jq --argjson add "$allow" '.enabledMcpjsonServers = ((.enabledMcpjsonServers // []) + ["scrapling"] | unique)
  | .permissions.allow += ($add - .permissions.allow)' .claude/settings.json > "$tmp"
mv "$tmp" .claude/settings.json

# WHY: the browser fetchers need their browsers downloaded once per machine.
uvx --from 'scrapling[ai]==0.5.1' scrapling install

git add -N .mcp.json
git --no-pager diff -- .mcp.json .claude/settings.json
echo "Read the diff, then commit it on chore/agency-operating-model and restart Claude Code."
