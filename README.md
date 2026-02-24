# BC Agentic Workflow

An automated development workflow where AI agents (Claude Code) autonomously
process GitHub Issues. Issues move through a Kanban board (GitHub Projects V2)
and are handled by three agent roles: Orchestrator, Developer, and Reviewer.

## Table of Contents

- [Quick Start: Full Setup](#quick-start-full-setup)
  - [Prerequisites](#prerequisites)
  - [1. Fork or Clone This Repo](#1-fork-or-clone-this-repo)
  - [2. Organization Secrets](#2-organization-secrets)
  - [3. Self-Hosted Runners](#3-self-hosted-runners)
  - [4. Webhook Relay (Cloudflare Worker)](#4-webhook-relay-cloudflare-worker)
  - [5. Organization `.github` Repository](#5-organization-github-repository)
  - [6. Add Your First Target Repo](#6-add-your-first-target-repo)
- [Adding a New Repository](#adding-a-new-repository)
- [Local Development](#local-development)
- [Configuration](#configuration)
- [How It Works](#how-it-works)
- [Project Structure](#project-structure)
- [Labels](#labels)
- [Architecture Decisions](#architecture-decisions)

---

## Quick Start: Full Setup

Follow these steps to set up the entire system from scratch for your GitHub organization.

### Prerequisites

- A GitHub organization
- A GitHub Projects V2 board with status columns: **Backlog**, **Ready**, **In Progress**, **In Review**, **Done**
- A machine for self-hosted runners (e.g. a mini PC or cloud VM)
- A Cloudflare account (free tier is sufficient)
- Claude Code CLI installed on the runner machine

### 1. Fork or Clone This Repo

Create a copy of this repo in your organization (e.g. `your-org/bc-agentic-workflow`). This is the central repo that holds all reusable workflows, agent definitions, and the webhook relay.

### 2. Organization Secrets

Set these as organization-level secrets (Settings > Secrets and variables > Actions):

| Secret | Description |
|--------|-------------|
| `CLAUDE_CODE_OAUTH_TOKEN` | Run `claude setup-token` locally to generate a 1-year OAuth token from your Claude Max subscription |
| `WORKFLOW_PAT` | A fine-grained PAT with scopes: `actions:write`, `issues:write`, `contents:write`, `pull-requests:write` |

### 3. Self-Hosted Runners

Set up two runners on your machine with these labels:

- `agentic-developer` — for the Developer agent
- `agentic-reviewer` — for the Reviewer agent

Each runner needs:

```bash
# Install Claude Code CLI
claude --version

# Ensure onboarding is complete
echo '{"hasCompletedOnboarding": true}' > ~/.claude.json

# Install jq (required by orchestrator)
sudo apt-get install -y jq
```

### 4. Webhook Relay (Cloudflare Worker)

GitHub Projects V2 does not support `projects_v2_item` as a GitHub Actions
workflow trigger. We use a Cloudflare Worker to relay webhook events as
`repository_dispatch` events that GitHub Actions can process.

**Deploy the Worker:**

```bash
cd webhook-relay
npm install
npx wrangler deploy
```

On first run, Wrangler will ask you to log in to your Cloudflare account via
the browser. After deploy, you get a URL like:
`https://github-webhook-relay.<your-account>.workers.dev`

**Set Worker Secrets:**

```bash
# A strong random string (save it — you need the same value for the GitHub webhook)
npx wrangler secret put WEBHOOK_SECRET

# The same PAT used as WORKFLOW_PAT in GitHub org secrets
npx wrangler secret put GITHUB_PAT
```

**Configure the GitHub Org Webhook:**

Go to `https://github.com/organizations/<your-org>/settings/hooks` and add a
new webhook:

| Setting | Value |
|---------|-------|
| Payload URL | Your Worker URL (e.g. `https://github-webhook-relay.<account>.workers.dev`) |
| Content type | `application/json` (must be JSON, not form-encoded) |
| Secret | The same value you entered as `WEBHOOK_SECRET` |
| Events | Select "Let me select individual events" > check only **"Projects v2 item"** |
| Active | checked |

### 5. Organization `.github` Repository

Create a repo named `.github` in your org (e.g. `your-org/.github`). This is a
special GitHub repo that receives organization-level dispatch events.

Add the trigger workflow at `.github/workflows/orchestrator-trigger.yml`
(see `examples/dot-github-repo/` for the template):

```yaml
name: Project Board Trigger

on:
  repository_dispatch:
    types: [projects_v2_item]

permissions:
  contents: write
  pull-requests: write
  issues: write
  actions: write

jobs:
  orchestrate:
    if: >-
      github.event.client_payload.projects_v2_item.content_type == 'Issue' &&
      github.event.client_payload.changes.field_value.field_type == 'single_select'
    uses: your-org/bc-agentic-workflow/.github/workflows/orchestrator.yml@main
    with:
      item_node_id: ${{ github.event.client_payload.projects_v2_item.node_id }}
      content_node_id: ${{ github.event.client_payload.projects_v2_item.content_node_id }}
      project_node_id: ${{ github.event.client_payload.projects_v2_item.project_node_id }}
    secrets: inherit
```

Replace `your-org` with your actual GitHub organization name.

### 6. Add Your First Target Repo

See the next section.

---

## Adding a New Repository

For each repo that should use the agentic workflow, copy the full template from
`examples/target-repo/`. Here's what goes into the target repo:

```
your-repo/
├── .github/workflows/
│   ├── agentic-developer.yml         # Wrapper workflow (calls reusable developer.yml)
│   └── agentic-reviewer.yml          # Wrapper workflow (calls reusable reviewer.yml)
└── .claude/
    ├── agents/
    │   ├── developer.md              # Developer agent (Dave) — CUSTOMIZE Tools & Commands!
    │   └── reviewer.md               # Reviewer agent (Rick) — CUSTOMIZE Tools & Commands!
    ├── agent-memory/
    │   ├── developer/.gitkeep        # Dave's persistent memory (auto-managed)
    │   ├── reviewer/.gitkeep         # Rick's persistent memory (auto-managed)
    │   └── logs/.gitkeep             # Shared activity logs (auto-managed)
    ├── hooks/
    │   ├── inject-default-agent.sh   # SessionStart hook — loads default agent in normal sessions
    │   └── inject-recent-logs.sh     # SessionStart hook — injects recent activity logs
    ├── settings.json                 # Claude Code project settings (hooks registration)
    └── config.yml                    # Per-repo configuration overrides (optional)
```

**Steps:**

1. Copy `examples/target-repo/.gitattributes` and `examples/target-repo/.claude/` to your repo root
2. Copy `examples/target-repo/github/workflows/` to `.github/workflows/`
3. Replace `OWNER/bc-agentic-workflow` with your org's actual path in both workflow files
4. **Customize `Tools & Commands`** in `.claude/agents/developer.md` and `.claude/agents/reviewer.md` with your repo's actual test, lint, and build commands
5. Optionally adjust `.claude/config.yml` (see [Configuration](#configuration))
6. Connect the repo to your GitHub Projects V2 board

---

## Local Development

Start a local interactive Claude session as the Developer agent:

```bash
claude --agent developer
```

Or as the Reviewer agent:

```bash
claude --agent reviewer
```

Using `--agent` is the **recommended** approach — it loads the agent as a system prompt
with full native support (model, memory, identity). This gives the agent instructions
the highest priority in Claude's context.

For convenience, normal sessions (e.g. VS Code extension or just `claude` without flags)
automatically inject the default agent context via a SessionStart hook. This ensures the
agent context is always present, even if you forget the `--agent` flag. The default agent
is configurable via `default_agent` in `.claude/config.yml` (defaults to `developer`).
Note that hook-injected context has lower priority than native `--agent` loading.

---

## Configuration

Each target repo can override organization defaults by placing a `.claude/config.yml` in its root.

```yaml
max_review_cycles: 3                    # Max re-work attempts before escalation
yolo_mode: false                        # Auto-merge on approval (no human review)
dedicated_branch: ""                    # Fixed branch name (empty = per-issue branches)
recent_logs_count: 3                    # Number of recent activity logs injected at session start
default_agent: developer                # Agent loaded in normal sessions (without --agent)
```

Organization-wide defaults are documented in `config.yml` at the root of this repo.

---

## How It Works

1. You create a GitHub Issue and move it to "Ready" on your project board
2. A Cloudflare Worker picks up the webhook event and relays it to GitHub Actions
3. The **Orchestrator** validates the issue and dispatches the Developer
4. The **Developer** reads the issue, implements a solution, writes tests, and creates a PR
5. The **Reviewer** checks the PR and approves or requests changes
6. If changes are needed, the Developer gets another pass (up to 3 cycles)
7. You review the final PR and merge manually

```
Issue moved to "Ready"
       |
GitHub Webhook --> Cloudflare Worker --> repository_dispatch
       |
Orchestrator (self-hosted runner)
  - Validates "Ready" status
  - Adds review-cycle:0 label
  - Updates board to "In Progress"
  - Dispatches Developer
       |
Developer (agentic-developer runner)
  - Reads issue + agent config
  - Runs Claude Code
  - Creates branch + PR
  - Updates board to "In Review"
  - Dispatches Reviewer
       |
Reviewer (agentic-reviewer runner)
  - Reads PR diff + agent config
  - Runs Claude Code
  - Posts review
       |
  APPROVED --> Board to "Done", user merges PR
  CHANGES  --> Back to Developer (if cycle < max)
  MAX      --> adds needs-human-review label
```

---

## Project Structure

```
bc-agentic-workflow/
├── .github/workflows/
│   ├── orchestrator.yml             # Reusable orchestrator workflow
│   ├── developer.yml                # Reusable developer workflow
│   ├── reviewer.yml                 # Reusable reviewer workflow
│   ├── agentic-developer.yml        # Developer wrapper for target repos
│   ├── agentic-reviewer.yml         # Reviewer wrapper for target repos
│   └── project-board-trigger.yml    # Template for .github repo trigger
├── .claude/
│   ├── agents/
│   │   ├── developer.md             # Developer agent (Dave)
│   │   └── reviewer.md              # Reviewer agent (Rick)
│   ├── agent-memory/
│   │   ├── developer/               # Developer's persistent memory (auto-managed)
│   │   ├── reviewer/                # Reviewer's persistent memory (auto-managed)
│   │   └── logs/                    # Shared activity logs (auto-managed)
│   ├── hooks/
│   │   ├── inject-default-agent.sh  # Default agent hook
│   │   └── inject-recent-logs.sh    # Activity logs hook
│   └── settings.json                # Hook registration
├── webhook-relay/                   # Cloudflare Worker (webhook relay)
│   ├── src/index.js
│   ├── wrangler.toml
│   └── package.json
├── examples/
│   ├── target-repo/                 # Full template for adopting repos
│   └── dot-github-repo/             # Template for org .github repo
├── config.yml                       # Organization-wide defaults
└── runners/
    └── .env.example                 # Runner environment template
```

---

## Labels

The system uses these labels automatically:

| Label | Description |
|-------|-------------|
| `review-cycle:N` | Tracks re-work iterations (0, 1, 2...) |
| `agent-error` | First failure, can retry |
| `agent-failed` | Second consecutive failure, stops processing |
| `needs-human-review` | Max review cycles reached, manual intervention needed |

---

## Architecture Decisions

- **Reusable Workflows** — Core logic lives in this repo, adopted via `workflow_call`
- **Cloudflare Worker Relay** — Bridges the gap between GitHub webhooks and Actions triggers
- **No auto-merge by default** — Users review and merge the final PR (unless `yolo_mode: true`)
- **Native Claude Code agents** — Agents defined as `.md` files with YAML frontmatter, invoked via `--agent`
- **Agent config per repo** — Each repo defines its own agent identity, tools, and memory
- **Session persistence** — Deterministic UUIDs allow agents to resume context across review cycles
- **Self-improving agents** — Agents use Claude Code's native persistent memory (`agent-memory/`) and shared activity logs
- **Cloud + self-hosted runners** — Prerequisites step auto-installs missing tools for portability
