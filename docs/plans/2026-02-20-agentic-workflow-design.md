# Agentic Development Workflow Design

## Overview

An automated development workflow where AI agents (Claude Code) autonomously
process GitHub Issues. Issues move through a Kanban board (GitHub Projects V2)
and are handled by three agent roles: Orchestrator, Developer, and Reviewer.

## Architecture

```
┌─────────────┐     projects_v2_item      ┌──────────────────┐
│  User moves  │────── webhook event ──────▶│   Orchestrator   │
│  issue to    │                           │  (GitHub Action)  │
│  "Ready"     │                           │  runs-on:         │
│              │                           │  self-hosted       │
└─────────────┘                           └────────┬─────────┘
                                                    │
                                           workflow_dispatch
                                                    │
                                                    ▼
                                           ┌──────────────────┐
                                           │    Developer      │
                                           │  runs-on:         │
                                           │  agentic-developer│
                                           └────────┬─────────┘
                                                    │
                                           workflow_dispatch
                                                    │
                                                    ▼
                                           ┌──────────────────┐
                                           │    Reviewer       │
                                           │  runs-on:         │
                                           │  agentic-reviewer │
                                           └────────┬─────────┘
                                                    │
                                          ┌─────────┴─────────┐
                                     Approved              Changes needed
                                          │                     │
                                     Move to "Done"      Move back to "Ready"
                                     User merges PR      (if cycle < max)
```

## Flow

1. User creates an issue and moves it to "Ready" on the Kanban board
2. Orchestrator detects the status change via `projects_v2_item` webhook
3. Orchestrator validates the item, adds `review-cycle:0` label, moves to "In Progress"
4. Orchestrator dispatches the Developer workflow
5. Developer clones the repo, reads issue context and agent config files
6. Developer creates branch `issue/<number>-<slug>`, implements, tests, commits
7. Developer creates PR with `Closes #<N>` and moves issue to "In Review"
8. Developer dispatches the Reviewer workflow
9. Reviewer checks out the PR, reads the diff and agent config files
10. Reviewer posts a PR review (APPROVE or REQUEST_CHANGES)
11. If approved: issue moves to "Done"
12. If changes needed and cycle < max (3): increment cycle label, move to "Ready"
13. If changes needed and cycle >= max: add `needs-human-review` label, notify user
14. User reviews the final PR and merges manually

## Workflow Files

All workflows live in this repo (`bc-agentic-workflow`) and are referenced
by other repos as reusable workflows.

### orchestrator.yml

- **Trigger**: `projects_v2_item` event (status change to "Ready")
- **Runs on**: `self-hosted`
- **Steps**:
  1. Validate item moved to "Ready"
  2. Extract issue number and repository
  3. Add `review-cycle:0` label
  4. Move issue to "In Progress"
  5. Dispatch Developer workflow via `workflow_dispatch`

### developer.yml

- **Trigger**: `workflow_dispatch` with inputs: `issue_number`, `review_cycle`
- **Runs on**: `agentic-developer`
- **Steps**:
  1. Check out the target repo
  2. Fetch issue body + comments via `gh` CLI
  3. Read agent config: `.claude/agents/developer/{IDENTITY,TOOLS,MEMORY}.md`
  4. Read last 3 log files from `.claude/agents/developer/logs/`
  5. Assemble prompt and run `claude -p`
  6. Claude creates branch, implements, commits, pushes
  7. Create PR with `Closes #<N>`
  8. Move issue to "In Review"
  9. Dispatch Reviewer workflow

### reviewer.yml

- **Trigger**: `workflow_dispatch` with inputs: `issue_number`, `pr_number`, `review_cycle`
- **Runs on**: `agentic-reviewer`
- **Steps**:
  1. Check out the PR branch
  2. Fetch PR diff and issue context via `gh` CLI
  3. Read agent config: `.claude/agents/reviewer/{IDENTITY,TOOLS,MEMORY}.md`
  4. Assemble review prompt and run `claude -p`
  5. Claude posts PR review
  6. If approved: move issue to "Done"
  7. If changes needed, cycle < max: increment label, move to "Ready"
  8. If changes needed, cycle >= max: add `needs-human-review` label

## Authentication

Claude Code is authenticated via **Claude Max subscription** using OAuth tokens,
not API keys (zero per-token costs).

- `claude setup-token` generates a 1-year OAuth token
- Token is stored as GitHub secret: `CLAUDE_CODE_OAUTH_TOKEN`
- Workflows set `CLAUDE_CODE_OAUTH_TOKEN` as an environment variable
- Self-hosted runners need `~/.claude.json` with `{"hasCompletedOnboarding": true}`

### Secrets

| Secret | Source | Purpose |
|--------|--------|---------|
| `CLAUDE_CODE_OAUTH_TOKEN` | `claude setup-token` | Claude Max subscription auth |
| `GITHUB_TOKEN` | Automatic | GitHub API access |

## Agent Configuration

### Per-repo structure

```
<any-repo>/
└── .claude/
    └── agents/
        ├── developer/
        │   ├── IDENTITY.md
        │   ├── TOOLS.md
        │   ├── MEMORY.md
        │   └── logs/
        │       └── <yyyy-MM-dd>.md
        └── reviewer/
            ├── IDENTITY.md
            ├── TOOLS.md
            ├── MEMORY.md
            └── logs/
                └── <yyyy-MM-dd>.md
```

### Prompt assembly

The workflow assembles the prompt by concatenating:

1. IDENTITY.md content
2. TOOLS.md content
3. MEMORY.md content
4. Last 3 log files
5. Issue/PR context (title, body, comments, diff)
6. Task-specific instructions

If no repo-specific agent configs exist, defaults from this repo are used.

## Global Configuration

`config.yml` in this repo:

```yaml
max_review_cycles: 3
branch_pattern: "issue/{number}-{slug}"
pr_auto_close_issue: true
runners:
  orchestrator: "self-hosted"
  developer: "agentic-developer"
  reviewer: "agentic-reviewer"
```

## Error Handling

### Review cycle tracking
- Label `review-cycle:N` tracks iterations
- Configurable max (default: 3) in `config.yml`
- Exceeding max adds `needs-human-review` label

### Claude Code failures
- Non-zero exit: comment on issue with workflow run link, move to "Ready"
- 2 consecutive failures on same issue: add `agent-failed` label, stop retrying

### Concurrency
- Each Developer job uses a fresh clone (no conflicts between parallel runs)
- GitHub Actions job queuing handles more issues than available runners (FIFO)

## What the system does NOT do

- Does not merge PRs (user merges manually)
- Does not deploy anything
- Does not modify issues beyond status labels and comments
- Reviewer does not run tests/linting (separate CI handles that)

## Adopting in other repos

1. Add wrapper workflow calling reusable workflows from this repo
2. Create `.claude/agents/developer/` and `.claude/agents/reviewer/` with repo-specific configs
3. Ensure the GitHub Project board is connected to the repo

## Self-hosted runners

Already configured on Beelink Mini-PC:
- `runner-developer-1` (label: `agentic-developer`)
- `runner-developer-2` (label: `agentic-developer`)
- `runner-reviewer-1` (label: `agentic-reviewer`)

### One-time runner setup
- Install Claude Code CLI
- Run `claude setup-token` and configure token
- Create `~/.claude.json` with `{"hasCompletedOnboarding": true}`
