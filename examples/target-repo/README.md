# Target Repo Setup

To enable the agentic workflow in your repository:

## 1. Workflow Files

Copy the GitHub Actions wrapper workflows:

- `github/workflows/agentic-developer.yml` → `.github/workflows/agentic-developer.yml`
- `github/workflows/agentic-reviewer.yml` → `.github/workflows/agentic-reviewer.yml`

Replace `OWNER/bc-agentic-workflow` with your org's actual path in both files.

## 2. Agent Definitions

Copy the `.claude/` directory to your repo root. This includes:

```
.claude/
├── agents/
│   ├── developer.md              # Developer agent (Dave) — customize Tools & Commands!
│   └── reviewer.md               # Reviewer agent (Rick) — customize Tools & Commands!
├── agent-memory/
│   ├── developer/.gitkeep        # Dave's persistent memory (auto-managed)
│   ├── reviewer/.gitkeep         # Rick's persistent memory (auto-managed)
│   └── logs/.gitkeep             # Shared activity logs (auto-managed)
├── hooks/
│   └── inject-recent-logs.sh     # SessionStart hook — injects recent logs
├── settings.json                 # Claude Code project settings (hooks)
└── config.yml                    # Per-repo configuration overrides
```

**Important**: Edit the `Tools & Commands` section in both agent `.md` files to match your repo's actual commands (test runner, linter, build, etc.).

## 3. Configuration

`.claude/config.yml` — only set what you want to override:

```yaml
max_review_cycles: 3       # Max re-work attempts before escalation
yolo_mode: false           # Auto-merge on reviewer approval
dedicated_branch: ""       # Fixed branch (empty = per-issue branches)
recent_logs_count: 3       # Number of recent activity logs injected at session start
```

## 4. Org-Level Secrets

Ensure these organization secrets exist:

- `CLAUDE_CODE_OAUTH_TOKEN` — Claude Code OAuth token (`claude setup-token`)
- `WORKFLOW_PAT` — Fine-grained PAT with `actions:write`, `issues:write`, `contents:write`, `pull-requests:write`

## Local Development

Start a local interactive session as the Developer agent:

```bash
claude --agent developer
```

Or as the Reviewer agent:

```bash
claude --agent reviewer
```
