# BC Agentic Workflow

An automated development workflow where AI agents (Claude Code) autonomously
process GitHub Issues. Issues move through a Kanban board (GitHub Projects V2)
and are handled by three agent roles: Orchestrator, Developer, and Reviewer.

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
├── .claude/agents/
│   ├── developer/                   # Default developer agent config
│   │   ├── SYSTEM.md                # System prompt (bootstrap + instructions)
│   │   ├── IDENTITY.md              # Agent personality and principles
│   │   ├── TOOLS.md                 # Build/test/lint commands
│   │   ├── MEMORY.md                # Persistent learnings
│   │   └── logs/                    # Daily activity logs
│   └── reviewer/                    # Default reviewer agent config
│       ├── SYSTEM.md
│       ├── IDENTITY.md
│       ├── TOOLS.md
│       ├── MEMORY.md
│       └── logs/
├── webhook-relay/                   # Cloudflare Worker (webhook relay)
│   ├── src/index.js                 # Worker source code
│   ├── wrangler.toml                # Cloudflare Worker config
│   └── package.json
├── examples/
│   ├── target-repo/                 # Template for adopting repos
│   └── dot-github-repo/             # Template for org .github repo
├── runners/
│   └── .env.example                 # Runner environment template
├── config.yml                       # Organization-wide defaults
├── docs/plans/                      # Design docs and implementation plans
└── Idea.md                          # Original project vision
```

## Setup Guide

### Prerequisites

- A GitHub organization
- A GitHub Projects V2 board with status columns (Backlog, Ready, In Progress, In Review, Done)
- A machine for self-hosted runners (e.g. a mini PC)
- A Cloudflare account (free tier is sufficient)
- Claude Code CLI installed on the runner machine

### 1. Organization Secrets

Set these as organization-level secrets (Settings > Secrets and variables > Actions):

- **`CLAUDE_CODE_OAUTH_TOKEN`** — Run `claude setup-token` locally to generate a 1-year OAuth token from your Claude Max subscription
- **`WORKFLOW_PAT`** — A fine-grained Personal Access Token with scopes: `actions:write`, `issues:write`, `contents:write`, `pull-requests:write`

### 2. Self-Hosted Runners

Set up runners on your machine with these labels:

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

### 3. Webhook Relay (Cloudflare Worker)

GitHub Projects V2 does not support `projects_v2_item` as a GitHub Actions
workflow trigger. We use a Cloudflare Worker to relay webhook events as
`repository_dispatch` events that GitHub Actions can process.

#### Deploy the Worker

```bash
cd webhook-relay
npm install
npx wrangler deploy
```

On first run, Wrangler will ask you to log in to your Cloudflare account via
the browser. After deploy, you get a URL like:
`https://github-webhook-relay.<your-account>.workers.dev`

#### Set Worker Secrets

```bash
# A strong random string (save it — you need the same value for the GitHub webhook)
npx wrangler secret put WEBHOOK_SECRET

# The same PAT used as WORKFLOW_PAT in GitHub org secrets
npx wrangler secret put GITHUB_PAT
```

#### Configure the GitHub Org Webhook

Go to `https://github.com/organizations/<your-org>/settings/hooks` and add a
new webhook:

- **Payload URL**: Your Worker URL (e.g. `https://github-webhook-relay.<account>.workers.dev`)
- **Content type**: `application/json` (important — must be JSON, not form-encoded)
- **Secret**: The same value you entered as `WEBHOOK_SECRET`
- **Events**: Select "Let me select individual events" > check only **"Projects v2 item"**
- **Active**: checked

### 4. Organization `.github` Repository

Create a repo named `.github` in your org (e.g. `your-org/.github`). This is a
special GitHub repo that receives organization-level events.

Add the trigger workflow at `.github/workflows/orchestrator-trigger.yml`:

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

### 5. Adopting in Target Repositories

For each repo that should use the agentic workflow:

1. Copy the wrapper workflows from `examples/target-repo/`:
   - `.github/workflows/agentic-developer.yml`
   - `.github/workflows/agentic-reviewer.yml`

2. Create agent configuration:
   ```
   .claude/agents/developer/IDENTITY.md
   .claude/agents/developer/TOOLS.md     # Customize with repo-specific commands!
   .claude/agents/developer/MEMORY.md
   .claude/agents/developer/logs/.gitkeep
   .claude/agents/reviewer/IDENTITY.md
   .claude/agents/reviewer/TOOLS.md
   .claude/agents/reviewer/MEMORY.md
   .claude/agents/reviewer/logs/.gitkeep
   ```

3. Connect the repo to your GitHub Projects V2 board

## Configuration

`config.yml` controls organization-wide defaults:

```yaml
max_review_cycles: 3                    # Max re-work attempts before escalation
branch_pattern: "issue/{number}-{slug}" # Branch naming convention
pr_auto_close_issue: true               # PR links auto-close the issue
runners:
  orchestrator: "self-hosted"
  developer: "agentic-developer"
  reviewer: "agentic-reviewer"
```

## Labels

The system uses these labels automatically:

- **`review-cycle:N`** — Tracks re-work iterations (0, 1, 2...)
- **`agent-error`** — First failure, can retry
- **`agent-failed`** — Second consecutive failure, stops processing
- **`needs-human-review`** — Max review cycles reached, manual intervention needed

## Local Development with Claude Code

You can start a local interactive Claude session with the Developer agent context:

```bash
claude --append-system-prompt "$(cat .claude/agents/developer/SYSTEM.md)"
```

Or with the Reviewer agent:

```bash
claude --append-system-prompt "$(cat .claude/agents/reviewer/SYSTEM.md)"
```

This loads the agent's bootstrap instructions (identity, tools, memory) into the system prompt so Claude knows who it is from the start.

## Architecture Decisions

- **Reusable Workflows** — Core logic lives in this repo, adopted via `workflow_call`
- **Cloudflare Worker Relay** — Bridges the gap between GitHub webhooks and Actions triggers
- **No auto-merge** — Users always manually review and merge the final PR
- **Agent config per repo** — Each repo defines its own agent identity, tools, and memory
- **Daily logs** — Agents write daily logs to maintain context across sessions
