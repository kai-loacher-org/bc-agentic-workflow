#!/usr/bin/env bash
# SessionStart hook: injects a default agent's context when no --agent flag is used.
# This allows normal "claude" sessions (e.g. in VS Code) to automatically
# load the developer agent context without affecting --agent sessions.
#
# The default agent is configurable via `default_agent` in
# .claude/config.yml or config.yml. Defaults to "developer" if not set.
#
# Usage: Registered as a SessionStart hook in .claude/settings.json
# The stdout of this script is injected into the conversation.

set -euo pipefail

# Read JSON input from stdin and check if an agent was explicitly specified.
# Uses grep instead of jq to avoid external dependencies.
input=$(cat)

if echo "$input" | grep -q '"agent_type"'; then
  # An agent is already set via --agent — skip, the agent loads its own context
  exit 0
fi

# Read default_agent from per-repo config (check both locations)
default_agent="developer"
for config in ".claude/config.yml" "config.yml"; do
  if [ -f "$config" ]; then
    parsed=$(grep -E '^default_agent:\s*\S+' "$config" 2>/dev/null | head -1 | sed 's/default_agent:\s*//' | tr -d ' "'"'" || true)
    if [ -n "$parsed" ]; then
      default_agent=$parsed
      break
    fi
  fi
done

# Find and inject the agent's .md file
agent_file=".claude/agents/${default_agent}.md"
if [ ! -f "$agent_file" ]; then
  exit 0
fi

echo "## Default Agent Context (${default_agent})"
echo ""
# Strip YAML frontmatter (between --- markers) and output the body
sed -n '/^---$/,/^---$/!p' "$agent_file"

# Inject the agent's persistent memory (mirrors native --agent behavior)
memory_file=".claude/agent-memory/${default_agent}/MEMORY.md"
if [ -f "$memory_file" ]; then
  echo ""
  echo "## Agent Memory (${default_agent})"
  echo ""
  # Native --agent loads first 200 lines — match that behavior
  head -200 "$memory_file"
fi
