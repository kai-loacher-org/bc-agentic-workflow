# Agentic Workflow Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build GitHub Actions workflows that let AI agents (Claude Code) automatically process GitHub Issues through a Kanban board pipeline.

**Architecture:** Three GitHub Actions workflows (orchestrator, developer, reviewer) in this repo, exposed as reusable workflows. The org's `.github` repo gets a thin trigger for `projects_v2_item` events. Target repos get thin `workflow_dispatch` wrappers. Claude Code runs on self-hosted runners, authenticated via OAuth token from a Max subscription.

**Tech Stack:** GitHub Actions (YAML), GitHub GraphQL API, Claude Code CLI, `gh` CLI, Bash

**Important constraint:** For org-level GitHub Projects V2, `projects_v2_item` events can only trigger workflows in the org's `.github` repository. This repo holds the reusable workflow logic; the `.github` repo holds the trigger.

**Org secrets required (set up before testing):**

| Secret | How to create | Purpose |
|--------|--------------|---------|
| `CLAUDE_CODE_OAUTH_TOKEN` | Run `claude setup-token` locally | Claude Max subscription auth |
| `WORKFLOW_PAT` | Fine-grained PAT with `actions:write` + `issues:write` + `contents:write` on org repos | Cross-repo workflow dispatch |

---

### Task 1: Create global config file

**Files:**
- Create: `config.yml`

**Step 1: Write config.yml**

```yaml
# Organization-wide defaults for the agentic workflow.
# These values are used as defaults in reusable workflow inputs.
# Target repos can override them in their wrapper workflows.

max_review_cycles: 3
branch_pattern: "issue/{number}-{slug}"
pr_auto_close_issue: true

project:
  # Replace with your GitHub org name
  org: "REPLACE_WITH_ORG"
  # Replace with your GitHub Project number (visible in project URL)
  number: 0

runners:
  orchestrator: "self-hosted"
  developer: "agentic-developer"
  reviewer: "agentic-reviewer"
```

**Step 2: Validate YAML syntax**

Run: `python3 -c "import yaml; yaml.safe_load(open('config.yml')); print('Valid YAML')"`
Expected: `Valid YAML`

**Step 3: Commit**

```bash
git add config.yml
git commit -m "feat: add global config with workflow defaults"
```

---

### Task 2: Create default developer agent templates

**Files:**
- Create: `.claude/agents/developer/IDENTITY.md`
- Create: `.claude/agents/developer/TOOLS.md`
- Create: `.claude/agents/developer/MEMORY.md`

**Step 1: Write IDENTITY.md**

```markdown
# Developer Agent

You are an autonomous developer agent. You receive GitHub Issues and implement
solutions by writing code, tests, and documentation.

## Communication

- Write commit messages and PR descriptions in English
- Be concise and specific in commit messages
- Focus on the "why", not the "what"

## Principles

- Write clean, maintainable code that follows existing patterns in the repo
- Always write tests for new functionality
- Keep changes focused on the issue — don't refactor unrelated code
- Prefer simple solutions over clever ones
- Don't add features that weren't requested
```

**Step 2: Write TOOLS.md**

```markdown
# Tools & Commands

This file defines the build, test, and lint commands for this repository.
Override this file in each target repo with repo-specific commands.

## Default Commands

These are placeholders. Each target repo MUST customize this file.

- **Install dependencies**: `echo "No install command configured"`
- **Run tests**: `echo "No test command configured"`
- **Run linter**: `echo "No lint command configured"`
- **Build**: `echo "No build command configured"`

## Git

- Create feature branches from `main`
- Use conventional commit messages: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`
```

**Step 3: Write MEMORY.md**

```markdown
# Memory

## Startup Rule

At the start of every session, read the last 3 log files from
`.claude/agents/developer/logs/` to understand recent project context.

## Learned Patterns

(This section grows over time as the agent learns from tasks)
```

**Step 4: Create logs directory with .gitkeep**

Run: `mkdir -p .claude/agents/developer/logs && touch .claude/agents/developer/logs/.gitkeep`

**Step 5: Commit**

```bash
git add .claude/agents/developer/
git commit -m "feat: add default developer agent templates"
```

---

### Task 3: Create default reviewer agent templates

**Files:**
- Create: `.claude/agents/reviewer/IDENTITY.md`
- Create: `.claude/agents/reviewer/TOOLS.md`
- Create: `.claude/agents/reviewer/MEMORY.md`

**Step 1: Write IDENTITY.md**

```markdown
# Reviewer Agent

You are an autonomous code reviewer agent. You receive Pull Requests linked to
GitHub Issues and review the code for correctness, quality, and adherence to
the issue requirements.

## Communication

- Post PR reviews using `gh pr review`
- Be constructive and specific in feedback
- Reference line numbers and file paths in comments
- Explain WHY something should change, not just WHAT

## Review Criteria

1. Does the code fulfill the issue requirements?
2. Are there tests for new functionality?
3. Is the code clean, readable, and maintainable?
4. Are there security concerns (injection, auth, data exposure)?
5. Does the code follow existing patterns in the repo?

## Decision

- **APPROVE** if the code meets all criteria or has only minor style nits
- **REQUEST_CHANGES** if there are bugs, missing tests, security issues,
  or the code doesn't fulfill the issue requirements
```

**Step 2: Write TOOLS.md**

```markdown
# Tools & Commands

This file defines the commands available to the reviewer.
Override this file in each target repo with repo-specific commands.

## Default Commands

- **Run tests**: `echo "No test command configured"`
- **Run linter**: `echo "No lint command configured"`

## Review Process

1. Read the issue requirements
2. Read the PR diff
3. Check if tests exist and cover the changes
4. Post review with `gh pr review`
```

**Step 3: Write MEMORY.md**

```markdown
# Memory

## Startup Rule

At the start of every session, read the last 3 log files from
`.claude/agents/reviewer/logs/` to understand recent project context.

## Learned Patterns

(This section grows over time as the agent learns from reviews)
```

**Step 4: Create logs directory with .gitkeep**

Run: `mkdir -p .claude/agents/reviewer/logs && touch .claude/agents/reviewer/logs/.gitkeep`

**Step 5: Commit**

```bash
git add .claude/agents/reviewer/
git commit -m "feat: add default reviewer agent templates"
```

---

### Task 4: Create orchestrator reusable workflow

This is the brain of the system. It validates that an issue moved to "Ready",
extracts issue details, updates the project board, and dispatches the developer.

**Files:**
- Create: `.github/workflows/orchestrator.yml`

**Step 1: Write orchestrator.yml**

```yaml
name: Orchestrator

on:
  workflow_call:
    inputs:
      item_node_id:
        description: "Project item node ID (from projects_v2_item event)"
        type: string
        required: true
      content_node_id:
        description: "Content node ID - the issue node ID"
        type: string
        required: true
      project_node_id:
        description: "Project node ID"
        type: string
        required: true
    secrets:
      WORKFLOW_PAT:
        description: "PAT with actions:write for cross-repo dispatch"
        required: true

  # Manual trigger for testing without the project board
  workflow_dispatch:
    inputs:
      issue_repo:
        description: "Target repository (owner/repo)"
        type: string
        required: true
      issue_number:
        description: "Issue number to process"
        type: string
        required: true

permissions:
  issues: write
  contents: read
  actions: write

jobs:
  orchestrate:
    runs-on: self-hosted
    steps:
      - name: Determine trigger source
        id: trigger
        run: |
          if [ "${{ github.event_name }}" = "workflow_dispatch" ]; then
            echo "source=manual" >> "$GITHUB_OUTPUT"
            echo "issue_repo=${{ inputs.issue_repo }}" >> "$GITHUB_OUTPUT"
            echo "issue_number=${{ inputs.issue_number }}" >> "$GITHUB_OUTPUT"
          else
            echo "source=project" >> "$GITHUB_OUTPUT"
          fi

      - name: Get issue details from project item
        if: steps.trigger.outputs.source == 'project'
        id: issue_from_project
        env:
          GH_TOKEN: ${{ secrets.WORKFLOW_PAT || secrets.GITHUB_TOKEN }}
        run: |
          # Verify the item is in "Ready" status
          CURRENT_STATUS=$(gh api graphql -f query='
            query($itemId: ID!) {
              node(id: $itemId) {
                ... on ProjectV2Item {
                  fieldValueByName(name: "Status") {
                    ... on ProjectV2ItemFieldSingleSelectValue {
                      name
                    }
                  }
                }
              }
            }' -f itemId="${{ inputs.item_node_id }}" \
            --jq '.data.node.fieldValueByName.name')

          if [ "$CURRENT_STATUS" != "Ready" ]; then
            echo "::notice::Item status is '$CURRENT_STATUS', not 'Ready'. Skipping."
            echo "skip=true" >> "$GITHUB_OUTPUT"
            exit 0
          fi

          # Get issue number and repository from content node
          ISSUE_DATA=$(gh api graphql -f query='
            query($nodeId: ID!) {
              node(id: $nodeId) {
                ... on Issue {
                  number
                  title
                  repository {
                    nameWithOwner
                  }
                }
              }
            }' -f nodeId="${{ inputs.content_node_id }}" \
            --jq '.data.node')

          ISSUE_NUMBER=$(echo "$ISSUE_DATA" | jq -r '.number')
          ISSUE_REPO=$(echo "$ISSUE_DATA" | jq -r '.repository.nameWithOwner')

          echo "issue_number=$ISSUE_NUMBER" >> "$GITHUB_OUTPUT"
          echo "issue_repo=$ISSUE_REPO" >> "$GITHUB_OUTPUT"
          echo "skip=false" >> "$GITHUB_OUTPUT"

      - name: Set issue variables
        if: steps.issue_from_project.outputs.skip != 'true'
        id: issue
        run: |
          if [ "${{ steps.trigger.outputs.source }}" = "manual" ]; then
            echo "number=${{ steps.trigger.outputs.issue_number }}" >> "$GITHUB_OUTPUT"
            echo "repo=${{ steps.trigger.outputs.issue_repo }}" >> "$GITHUB_OUTPUT"
          else
            echo "number=${{ steps.issue_from_project.outputs.issue_number }}" >> "$GITHUB_OUTPUT"
            echo "repo=${{ steps.issue_from_project.outputs.issue_repo }}" >> "$GITHUB_OUTPUT"
          fi

      - name: Check for agent-failed label
        if: steps.issue_from_project.outputs.skip != 'true'
        id: check_failed
        env:
          GH_TOKEN: ${{ secrets.WORKFLOW_PAT || secrets.GITHUB_TOKEN }}
        run: |
          LABELS=$(gh issue view "${{ steps.issue.outputs.number }}" \
            --repo "${{ steps.issue.outputs.repo }}" \
            --json labels --jq '.labels[].name')
          if echo "$LABELS" | grep -q "agent-failed"; then
            echo "::warning::Issue has 'agent-failed' label. Skipping."
            echo "skip=true" >> "$GITHUB_OUTPUT"
          else
            echo "skip=false" >> "$GITHUB_OUTPUT"
          fi

      - name: Add review-cycle label
        if: steps.issue_from_project.outputs.skip != 'true' && steps.check_failed.outputs.skip != 'true'
        env:
          GH_TOKEN: ${{ secrets.WORKFLOW_PAT || secrets.GITHUB_TOKEN }}
        run: |
          # Remove any existing review-cycle labels
          EXISTING=$(gh issue view "${{ steps.issue.outputs.number }}" \
            --repo "${{ steps.issue.outputs.repo }}" \
            --json labels --jq '.labels[].name' | grep "^review-cycle:" || true)
          for label in $EXISTING; do
            gh issue edit "${{ steps.issue.outputs.number }}" \
              --repo "${{ steps.issue.outputs.repo }}" \
              --remove-label "$label" 2>/dev/null || true
          done

          # Add review-cycle:0 (create label if needed)
          gh label create "review-cycle:0" --repo "${{ steps.issue.outputs.repo }}" \
            --color "0E8A16" --description "Review cycle counter" 2>/dev/null || true
          gh issue edit "${{ steps.issue.outputs.number }}" \
            --repo "${{ steps.issue.outputs.repo }}" \
            --add-label "review-cycle:0"

      - name: Update project status to In Progress
        if: steps.trigger.outputs.source == 'project' && steps.issue_from_project.outputs.skip != 'true' && steps.check_failed.outputs.skip != 'true'
        env:
          GH_TOKEN: ${{ secrets.WORKFLOW_PAT || secrets.GITHUB_TOKEN }}
        run: |
          # Get Status field ID and "In Progress" option ID
          FIELD_DATA=$(gh api graphql -f query='
            query($projectId: ID!) {
              node(id: $projectId) {
                ... on ProjectV2 {
                  fields(first: 20) {
                    nodes {
                      ... on ProjectV2SingleSelectField {
                        id
                        name
                        options { id name }
                      }
                    }
                  }
                }
              }
            }' -f projectId="${{ inputs.project_node_id }}" \
            --jq '.data.node.fields.nodes[] | select(.name == "Status")')

          FIELD_ID=$(echo "$FIELD_DATA" | jq -r '.id')
          OPTION_ID=$(echo "$FIELD_DATA" | jq -r '.options[] | select(.name == "In Progress") | .id')

          # Update status
          gh api graphql -f query='
            mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $optionId: String!) {
              updateProjectV2ItemFieldValue(input: {
                projectId: $projectId
                itemId: $itemId
                fieldId: $fieldId
                value: { singleSelectOptionId: $optionId }
              }) {
                projectV2Item { id }
              }
            }' \
            -f projectId="${{ inputs.project_node_id }}" \
            -f itemId="${{ inputs.item_node_id }}" \
            -f fieldId="$FIELD_ID" \
            -f optionId="$OPTION_ID"

      - name: Dispatch developer workflow
        if: steps.issue_from_project.outputs.skip != 'true' && steps.check_failed.outputs.skip != 'true'
        env:
          GH_TOKEN: ${{ secrets.WORKFLOW_PAT }}
        run: |
          gh workflow run agentic-developer.yml \
            --repo "${{ steps.issue.outputs.repo }}" \
            -f issue_number="${{ steps.issue.outputs.number }}" \
            -f review_cycle="0" \
            -f project_node_id="${{ inputs.project_node_id || '' }}" \
            -f item_node_id="${{ inputs.item_node_id || '' }}"
```

**Step 2: Validate YAML syntax**

Run: `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/orchestrator.yml')); print('Valid YAML')"`
Expected: `Valid YAML`

**Step 3: Commit**

```bash
git add .github/workflows/orchestrator.yml
git commit -m "feat: add orchestrator reusable workflow"
```

---

### Task 5: Create developer reusable workflow

The developer workflow runs on self-hosted runners. It checks out the repo,
assembles a prompt from agent configs and issue context, runs Claude Code,
then creates a PR and dispatches the reviewer.

**Files:**
- Create: `.github/workflows/developer.yml`

**Step 1: Write developer.yml**

```yaml
name: Developer Agent

on:
  workflow_call:
    inputs:
      issue_number:
        description: "Issue number to implement"
        type: string
        required: true
      review_cycle:
        description: "Current review cycle (0 = first attempt)"
        type: string
        required: true
        default: "0"
      max_review_cycles:
        description: "Max review cycles before escalation"
        type: string
        required: false
        default: "3"
      project_node_id:
        description: "Project node ID for status updates"
        type: string
        required: false
        default: ""
      item_node_id:
        description: "Project item node ID for status updates"
        type: string
        required: false
        default: ""
    secrets:
      CLAUDE_CODE_OAUTH_TOKEN:
        description: "OAuth token for Claude Code CLI"
        required: true
      WORKFLOW_PAT:
        description: "PAT for cross-repo dispatch and project updates"
        required: true

permissions:
  contents: write
  pull-requests: write
  issues: write
  actions: write

jobs:
  develop:
    runs-on: agentic-developer
    timeout-minutes: 60
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Fetch issue context
        id: issue
        env:
          GH_TOKEN: ${{ secrets.WORKFLOW_PAT || secrets.GITHUB_TOKEN }}
        run: |
          ISSUE_JSON=$(gh issue view "${{ inputs.issue_number }}" --json title,body,comments)

          TITLE=$(echo "$ISSUE_JSON" | jq -r '.title')
          BODY=$(echo "$ISSUE_JSON" | jq -r '.body')
          COMMENTS=$(echo "$ISSUE_JSON" | jq -r '.comments[] | "**\(.author.login):** \(.body)"' 2>/dev/null || echo "")

          echo "title=$TITLE" >> "$GITHUB_OUTPUT"

          # Generate branch slug from title
          SLUG=$(echo "$TITLE" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9äöüß]/-/g' | sed 's/--*/-/g' | sed 's/^-//' | sed 's/-$//' | head -c 50)
          BRANCH="issue/${{ inputs.issue_number }}-${SLUG}"
          echo "branch=$BRANCH" >> "$GITHUB_OUTPUT"

          # Save full context to files for prompt assembly
          echo "$BODY" > /tmp/issue_body.md
          echo "$COMMENTS" > /tmp/issue_comments.md

      - name: Check for existing branch and PR
        id: existing
        env:
          GH_TOKEN: ${{ secrets.WORKFLOW_PAT || secrets.GITHUB_TOKEN }}
        run: |
          # Check if branch already exists (from previous review cycle)
          if git ls-remote --heads origin "${{ steps.issue.outputs.branch }}" | grep -q .; then
            echo "branch_exists=true" >> "$GITHUB_OUTPUT"
            git checkout "${{ steps.issue.outputs.branch }}"
            git pull origin "${{ steps.issue.outputs.branch }}"
          else
            echo "branch_exists=false" >> "$GITHUB_OUTPUT"
            git checkout -b "${{ steps.issue.outputs.branch }}"
          fi

          # Check if PR already exists
          PR_NUMBER=$(gh pr list --head "${{ steps.issue.outputs.branch }}" --json number --jq '.[0].number' 2>/dev/null || echo "")
          echo "pr_number=${PR_NUMBER}" >> "$GITHUB_OUTPUT"

      - name: Assemble prompt
        id: prompt
        run: |
          PROMPT=""

          # Add agent identity
          if [ -f ".claude/agents/developer/IDENTITY.md" ]; then
            PROMPT+="$(cat .claude/agents/developer/IDENTITY.md)"
            PROMPT+=$'\n\n'
          fi

          # Add tools config
          if [ -f ".claude/agents/developer/TOOLS.md" ]; then
            PROMPT+="$(cat .claude/agents/developer/TOOLS.md)"
            PROMPT+=$'\n\n'
          fi

          # Add memory
          if [ -f ".claude/agents/developer/MEMORY.md" ]; then
            PROMPT+="$(cat .claude/agents/developer/MEMORY.md)"
            PROMPT+=$'\n\n'
          fi

          # Add last 3 log files
          LOG_DIR=".claude/agents/developer/logs"
          if [ -d "$LOG_DIR" ]; then
            for logfile in $(ls -1 "$LOG_DIR"/*.md 2>/dev/null | sort -r | head -3 | sort); do
              PROMPT+="## Log: $(basename "$logfile")"
              PROMPT+=$'\n'
              PROMPT+="$(cat "$logfile")"
              PROMPT+=$'\n\n'
            done
          fi

          # Add issue context
          PROMPT+="---"
          PROMPT+=$'\n\n'
          PROMPT+="## Your Task"
          PROMPT+=$'\n\n'
          PROMPT+="Issue #${{ inputs.issue_number }}: ${{ steps.issue.outputs.title }}"
          PROMPT+=$'\n\n'
          PROMPT+="### Description:"
          PROMPT+=$'\n\n'
          PROMPT+="$(cat /tmp/issue_body.md)"
          PROMPT+=$'\n\n'

          COMMENTS="$(cat /tmp/issue_comments.md)"
          if [ -n "$COMMENTS" ]; then
            PROMPT+="### Comments:"
            PROMPT+=$'\n\n'
            PROMPT+="$COMMENTS"
            PROMPT+=$'\n\n'
          fi

          # Add review feedback if this is a re-work cycle
          if [ "${{ inputs.review_cycle }}" != "0" ] && [ -n "${{ steps.existing.outputs.pr_number }}" ]; then
            PROMPT+="### Review Feedback (cycle ${{ inputs.review_cycle }}):"
            PROMPT+=$'\n\n'
            PROMPT+="Review comments from the previous cycle are on the PR. Read them with:"
            PROMPT+=$'\n'
            PROMPT+="gh pr view ${{ steps.existing.outputs.pr_number }} --comments"
            PROMPT+=$'\n\n'
          fi

          # Add instructions
          PROMPT+="---"
          PROMPT+=$'\n\n'
          PROMPT+="## Instructions"
          PROMPT+=$'\n\n'
          PROMPT+="1. Read and understand the issue requirements"
          PROMPT+=$'\n'
          PROMPT+="2. Implement the solution"
          PROMPT+=$'\n'
          PROMPT+="3. Write tests as specified in TOOLS.md"
          PROMPT+=$'\n'
          PROMPT+="4. Run the test and lint commands from TOOLS.md"
          PROMPT+=$'\n'
          PROMPT+="5. Commit your changes with clear, conventional commit messages"
          PROMPT+=$'\n'
          PROMPT+="6. Write a log entry for today to .claude/agents/developer/logs/$(date +%Y-%m-%d).md"
          PROMPT+=$'\n\n'
          PROMPT+="IMPORTANT: Do NOT create a branch or push. Do NOT create a PR. Just implement, test, and commit locally."

          # Save prompt to file
          echo "$PROMPT" > /tmp/developer_prompt.md

      - name: Run Claude Code
        id: claude
        env:
          CLAUDE_CODE_OAUTH_TOKEN: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}
        run: |
          claude -p "$(cat /tmp/developer_prompt.md)" \
            --dangerously-skip-permissions \
            --output-format json \
            --max-turns 100 \
            --model sonnet \
            > /tmp/claude_output.json 2>&1 || {
              EXIT_CODE=$?
              echo "claude_failed=true" >> "$GITHUB_OUTPUT"
              echo "::error::Claude Code exited with code $EXIT_CODE"
              exit 0
            }
          echo "claude_failed=false" >> "$GITHUB_OUTPUT"

      - name: Handle Claude failure
        if: steps.claude.outputs.claude_failed == 'true'
        env:
          GH_TOKEN: ${{ secrets.WORKFLOW_PAT || secrets.GITHUB_TOKEN }}
        run: |
          gh issue comment "${{ inputs.issue_number }}" \
            --body "Developer agent failed on cycle ${{ inputs.review_cycle }}. [See workflow run](${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }})"

          # Check if this is a repeated failure
          LABELS=$(gh issue view "${{ inputs.issue_number }}" --json labels --jq '.labels[].name')
          if echo "$LABELS" | grep -q "agent-error"; then
            # Second consecutive failure — mark as failed
            gh label create "agent-failed" --color "B60205" --description "Agent failed repeatedly" 2>/dev/null || true
            gh issue edit "${{ inputs.issue_number }}" --add-label "agent-failed"
            gh issue edit "${{ inputs.issue_number }}" --remove-label "agent-error" 2>/dev/null || true
          else
            # First failure — mark as error, will retry on next trigger
            gh label create "agent-error" --color "D93F0B" --description "Agent encountered an error" 2>/dev/null || true
            gh issue edit "${{ inputs.issue_number }}" --add-label "agent-error"
          fi
          exit 1

      - name: Push changes
        if: steps.claude.outputs.claude_failed != 'true'
        run: |
          # Check if there are any commits to push
          if git diff --quiet origin/main..HEAD 2>/dev/null; then
            echo "::warning::No new commits from Claude. Nothing to push."
            echo "has_changes=false" >> "$GITHUB_OUTPUT"
          else
            git push origin "${{ steps.issue.outputs.branch }}" --force-with-lease
            echo "has_changes=true" >> "$GITHUB_OUTPUT"

            # Remove agent-error label if present (successful run clears it)
            gh issue edit "${{ inputs.issue_number }}" --remove-label "agent-error" 2>/dev/null || true
          fi
        env:
          GH_TOKEN: ${{ secrets.WORKFLOW_PAT || secrets.GITHUB_TOKEN }}

      - name: Create or update PR
        if: steps.claude.outputs.claude_failed != 'true'
        id: pr
        env:
          GH_TOKEN: ${{ secrets.WORKFLOW_PAT || secrets.GITHUB_TOKEN }}
        run: |
          if [ -n "${{ steps.existing.outputs.pr_number }}" ]; then
            # PR already exists (re-work cycle) — just get the number
            echo "pr_number=${{ steps.existing.outputs.pr_number }}" >> "$GITHUB_OUTPUT"
            echo "::notice::Updated existing PR #${{ steps.existing.outputs.pr_number }}"
          else
            # Create new PR
            PR_URL=$(gh pr create \
              --title "Issue #${{ inputs.issue_number }}: ${{ steps.issue.outputs.title }}" \
              --body "$(cat <<EOF
Closes #${{ inputs.issue_number }}

## Summary

Automated implementation by Developer Agent (cycle ${{ inputs.review_cycle }}).

See issue #${{ inputs.issue_number }} for requirements.
EOF
)" \
              --head "${{ steps.issue.outputs.branch }}" \
              --base main)

            PR_NUMBER=$(echo "$PR_URL" | grep -oP '\d+$')
            echo "pr_number=$PR_NUMBER" >> "$GITHUB_OUTPUT"
            echo "::notice::Created PR #$PR_NUMBER"
          fi

      - name: Update project status to In Review
        if: steps.claude.outputs.claude_failed != 'true' && inputs.project_node_id != ''
        env:
          GH_TOKEN: ${{ secrets.WORKFLOW_PAT || secrets.GITHUB_TOKEN }}
        run: |
          FIELD_DATA=$(gh api graphql -f query='
            query($projectId: ID!) {
              node(id: $projectId) {
                ... on ProjectV2 {
                  fields(first: 20) {
                    nodes {
                      ... on ProjectV2SingleSelectField {
                        id
                        name
                        options { id name }
                      }
                    }
                  }
                }
              }
            }' -f projectId="${{ inputs.project_node_id }}" \
            --jq '.data.node.fields.nodes[] | select(.name == "Status")')

          FIELD_ID=$(echo "$FIELD_DATA" | jq -r '.id')
          OPTION_ID=$(echo "$FIELD_DATA" | jq -r '.options[] | select(.name == "In Review") | .id')

          gh api graphql -f query='
            mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $optionId: String!) {
              updateProjectV2ItemFieldValue(input: {
                projectId: $projectId
                itemId: $itemId
                fieldId: $fieldId
                value: { singleSelectOptionId: $optionId }
              }) {
                projectV2Item { id }
              }
            }' \
            -f projectId="${{ inputs.project_node_id }}" \
            -f itemId="${{ inputs.item_node_id }}" \
            -f fieldId="$FIELD_ID" \
            -f optionId="$OPTION_ID"

      - name: Dispatch reviewer workflow
        if: steps.claude.outputs.claude_failed != 'true'
        env:
          GH_TOKEN: ${{ secrets.WORKFLOW_PAT }}
        run: |
          gh workflow run agentic-reviewer.yml \
            --repo "${{ github.repository }}" \
            -f issue_number="${{ inputs.issue_number }}" \
            -f pr_number="${{ steps.pr.outputs.pr_number }}" \
            -f review_cycle="${{ inputs.review_cycle }}" \
            -f max_review_cycles="${{ inputs.max_review_cycles }}" \
            -f project_node_id="${{ inputs.project_node_id }}" \
            -f item_node_id="${{ inputs.item_node_id }}"
```

**Step 2: Validate YAML syntax**

Run: `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/developer.yml')); print('Valid YAML')"`
Expected: `Valid YAML`

**Step 3: Commit**

```bash
git add .github/workflows/developer.yml
git commit -m "feat: add developer agent reusable workflow"
```

---

### Task 6: Create reviewer reusable workflow

The reviewer checks out the PR branch, assembles a review prompt, runs Claude
Code to review the code, then handles the approve/reject outcome.

**Files:**
- Create: `.github/workflows/reviewer.yml`

**Step 1: Write reviewer.yml**

```yaml
name: Reviewer Agent

on:
  workflow_call:
    inputs:
      issue_number:
        description: "Issue number being reviewed"
        type: string
        required: true
      pr_number:
        description: "PR number to review"
        type: string
        required: true
      review_cycle:
        description: "Current review cycle"
        type: string
        required: true
        default: "0"
      max_review_cycles:
        description: "Max review cycles before escalation"
        type: string
        required: false
        default: "3"
      project_node_id:
        description: "Project node ID for status updates"
        type: string
        required: false
        default: ""
      item_node_id:
        description: "Project item node ID for status updates"
        type: string
        required: false
        default: ""
    secrets:
      CLAUDE_CODE_OAUTH_TOKEN:
        description: "OAuth token for Claude Code CLI"
        required: true
      WORKFLOW_PAT:
        description: "PAT for cross-repo dispatch and project updates"
        required: true

permissions:
  contents: write
  pull-requests: write
  issues: write
  actions: write

jobs:
  review:
    runs-on: agentic-reviewer
    timeout-minutes: 30
    steps:
      - name: Checkout PR branch
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Checkout PR branch
        env:
          GH_TOKEN: ${{ secrets.WORKFLOW_PAT || secrets.GITHUB_TOKEN }}
        run: |
          PR_BRANCH=$(gh pr view "${{ inputs.pr_number }}" --json headRefName --jq '.headRefName')
          git checkout "$PR_BRANCH"

      - name: Gather review context
        id: context
        env:
          GH_TOKEN: ${{ secrets.WORKFLOW_PAT || secrets.GITHUB_TOKEN }}
        run: |
          # Get issue details
          ISSUE_JSON=$(gh issue view "${{ inputs.issue_number }}" --json title,body)
          ISSUE_TITLE=$(echo "$ISSUE_JSON" | jq -r '.title')
          ISSUE_BODY=$(echo "$ISSUE_JSON" | jq -r '.body')

          # Get PR diff
          PR_DIFF=$(gh pr diff "${{ inputs.pr_number }}")

          # Save to files
          echo "$ISSUE_BODY" > /tmp/issue_body.md
          echo "$PR_DIFF" > /tmp/pr_diff.txt
          echo "issue_title=$ISSUE_TITLE" >> "$GITHUB_OUTPUT"

      - name: Assemble review prompt
        run: |
          PROMPT=""

          # Add agent identity
          if [ -f ".claude/agents/reviewer/IDENTITY.md" ]; then
            PROMPT+="$(cat .claude/agents/reviewer/IDENTITY.md)"
            PROMPT+=$'\n\n'
          fi

          # Add tools config
          if [ -f ".claude/agents/reviewer/TOOLS.md" ]; then
            PROMPT+="$(cat .claude/agents/reviewer/TOOLS.md)"
            PROMPT+=$'\n\n'
          fi

          # Add memory
          if [ -f ".claude/agents/reviewer/MEMORY.md" ]; then
            PROMPT+="$(cat .claude/agents/reviewer/MEMORY.md)"
            PROMPT+=$'\n\n'
          fi

          # Add last 3 log files
          LOG_DIR=".claude/agents/reviewer/logs"
          if [ -d "$LOG_DIR" ]; then
            for logfile in $(ls -1 "$LOG_DIR"/*.md 2>/dev/null | sort -r | head -3 | sort); do
              PROMPT+="## Log: $(basename "$logfile")"
              PROMPT+=$'\n'
              PROMPT+="$(cat "$logfile")"
              PROMPT+=$'\n\n'
            done
          fi

          # Add review context
          PROMPT+="---"
          PROMPT+=$'\n\n'
          PROMPT+="## Your Task"
          PROMPT+=$'\n\n'
          PROMPT+="Review PR #${{ inputs.pr_number }} for Issue #${{ inputs.issue_number }}: ${{ steps.context.outputs.issue_title }}"
          PROMPT+=$'\n\n'
          PROMPT+="### Issue Description:"
          PROMPT+=$'\n\n'
          PROMPT+="$(cat /tmp/issue_body.md)"
          PROMPT+=$'\n\n'
          PROMPT+="### PR Diff:"
          PROMPT+=$'\n\n'
          PROMPT+='```diff'
          PROMPT+=$'\n'
          PROMPT+="$(cat /tmp/pr_diff.txt)"
          PROMPT+=$'\n'
          PROMPT+='```'
          PROMPT+=$'\n\n'

          # Add instructions
          PROMPT+="---"
          PROMPT+=$'\n\n'
          PROMPT+="## Instructions"
          PROMPT+=$'\n\n'
          PROMPT+="1. Read and understand the issue requirements"
          PROMPT+=$'\n'
          PROMPT+="2. Review the code changes in the PR diff above"
          PROMPT+=$'\n'
          PROMPT+="3. Check: Does the code fulfill the issue requirements?"
          PROMPT+=$'\n'
          PROMPT+="4. Check: Are there tests for new functionality?"
          PROMPT+=$'\n'
          PROMPT+="5. Check: Is the code clean, secure, and maintainable?"
          PROMPT+=$'\n'
          PROMPT+="6. Post your review using gh pr review:"
          PROMPT+=$'\n'
          PROMPT+="   - If approved: gh pr review ${{ inputs.pr_number }} --approve --body \"Your approval message\""
          PROMPT+=$'\n'
          PROMPT+="   - If changes needed: gh pr review ${{ inputs.pr_number }} --request-changes --body \"Your detailed feedback\""
          PROMPT+=$'\n'
          PROMPT+="7. Write a log entry for today to .claude/agents/reviewer/logs/$(date +%Y-%m-%d).md"
          PROMPT+=$'\n\n'
          PROMPT+="IMPORTANT: You MUST post exactly one review using gh pr review. Either --approve or --request-changes."

          echo "$PROMPT" > /tmp/reviewer_prompt.md

      - name: Run Claude Code
        id: claude
        env:
          CLAUDE_CODE_OAUTH_TOKEN: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}
          GH_TOKEN: ${{ secrets.WORKFLOW_PAT || secrets.GITHUB_TOKEN }}
        run: |
          claude -p "$(cat /tmp/reviewer_prompt.md)" \
            --dangerously-skip-permissions \
            --output-format json \
            --max-turns 30 \
            --model sonnet \
            > /tmp/claude_output.json 2>&1 || {
              EXIT_CODE=$?
              echo "claude_failed=true" >> "$GITHUB_OUTPUT"
              echo "::error::Claude Code (reviewer) exited with code $EXIT_CODE"
              exit 0
            }
          echo "claude_failed=false" >> "$GITHUB_OUTPUT"

      - name: Handle Claude failure
        if: steps.claude.outputs.claude_failed == 'true'
        env:
          GH_TOKEN: ${{ secrets.WORKFLOW_PAT || secrets.GITHUB_TOKEN }}
        run: |
          gh issue comment "${{ inputs.issue_number }}" \
            --body "Reviewer agent failed on cycle ${{ inputs.review_cycle }}. [See workflow run](${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }})"
          exit 1

      - name: Check review decision
        if: steps.claude.outputs.claude_failed != 'true'
        id: decision
        env:
          GH_TOKEN: ${{ secrets.WORKFLOW_PAT || secrets.GITHUB_TOKEN }}
        run: |
          # Check the latest review on the PR
          REVIEW_STATE=$(gh pr view "${{ inputs.pr_number }}" \
            --json reviews --jq '.reviews | sort_by(.submittedAt) | last | .state')

          echo "review_state=$REVIEW_STATE" >> "$GITHUB_OUTPUT"
          echo "::notice::Review decision: $REVIEW_STATE"

      - name: Handle approval
        if: steps.decision.outputs.review_state == 'APPROVED'
        env:
          GH_TOKEN: ${{ secrets.WORKFLOW_PAT || secrets.GITHUB_TOKEN }}
        run: |
          echo "::notice::PR #${{ inputs.pr_number }} approved! Moving issue to Done."

          # Update project status to Done
          if [ -n "${{ inputs.project_node_id }}" ]; then
            FIELD_DATA=$(gh api graphql -f query='
              query($projectId: ID!) {
                node(id: $projectId) {
                  ... on ProjectV2 {
                    fields(first: 20) {
                      nodes {
                        ... on ProjectV2SingleSelectField {
                          id
                          name
                          options { id name }
                        }
                      }
                    }
                  }
                }
              }' -f projectId="${{ inputs.project_node_id }}" \
              --jq '.data.node.fields.nodes[] | select(.name == "Status")')

            FIELD_ID=$(echo "$FIELD_DATA" | jq -r '.id')
            OPTION_ID=$(echo "$FIELD_DATA" | jq -r '.options[] | select(.name == "Done") | .id')

            gh api graphql -f query='
              mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $optionId: String!) {
                updateProjectV2ItemFieldValue(input: {
                  projectId: $projectId
                  itemId: $itemId
                  fieldId: $fieldId
                  value: { singleSelectOptionId: $optionId }
                }) {
                  projectV2Item { id }
                }
              }' \
              -f projectId="${{ inputs.project_node_id }}" \
              -f itemId="${{ inputs.item_node_id }}" \
              -f fieldId="$FIELD_ID" \
              -f optionId="$OPTION_ID"
          fi

          gh issue comment "${{ inputs.issue_number }}" \
            --body "PR #${{ inputs.pr_number }} has been approved by the Reviewer agent. Ready for your final review and merge."

      - name: Handle changes requested
        if: steps.decision.outputs.review_state == 'CHANGES_REQUESTED'
        env:
          GH_TOKEN: ${{ secrets.WORKFLOW_PAT }}
        run: |
          NEXT_CYCLE=$(( ${{ inputs.review_cycle }} + 1 ))

          if [ "$NEXT_CYCLE" -ge "${{ inputs.max_review_cycles }}" ]; then
            echo "::warning::Max review cycles (${{ inputs.max_review_cycles }}) reached. Escalating to human."

            gh label create "needs-human-review" --color "FBCA04" \
              --description "Agent review cycles exhausted" 2>/dev/null || true
            gh issue edit "${{ inputs.issue_number }}" --add-label "needs-human-review"
            gh issue comment "${{ inputs.issue_number }}" \
              --body "Reviewer agent requested changes after $NEXT_CYCLE cycles (max: ${{ inputs.max_review_cycles }}). Please review PR #${{ inputs.pr_number }} manually."
          else
            echo "::notice::Changes requested. Starting cycle $NEXT_CYCLE."

            # Update review-cycle label
            gh label create "review-cycle:${NEXT_CYCLE}" --color "0E8A16" \
              --description "Review cycle counter" 2>/dev/null || true
            gh issue edit "${{ inputs.issue_number }}" \
              --remove-label "review-cycle:${{ inputs.review_cycle }}" 2>/dev/null || true
            gh issue edit "${{ inputs.issue_number }}" \
              --add-label "review-cycle:${NEXT_CYCLE}"

            # Update project status back to Ready
            if [ -n "${{ inputs.project_node_id }}" ]; then
              FIELD_DATA=$(gh api graphql -f query='
                query($projectId: ID!) {
                  node(id: $projectId) {
                    ... on ProjectV2 {
                      fields(first: 20) {
                        nodes {
                          ... on ProjectV2SingleSelectField {
                            id
                            name
                            options { id name }
                          }
                        }
                      }
                    }
                  }
                }' -f projectId="${{ inputs.project_node_id }}" \
                --jq '.data.node.fields.nodes[] | select(.name == "Status")')

              FIELD_ID=$(echo "$FIELD_DATA" | jq -r '.id')
              OPTION_ID=$(echo "$FIELD_DATA" | jq -r '.options[] | select(.name == "Ready") | .id')

              gh api graphql -f query='
                mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $optionId: String!) {
                  updateProjectV2ItemFieldValue(input: {
                    projectId: $projectId
                    itemId: $itemId
                    fieldId: $fieldId
                    value: { singleSelectOptionId: $optionId }
                  }) {
                    projectV2Item { id }
                  }
                }' \
                -f projectId="${{ inputs.project_node_id }}" \
                -f itemId="${{ inputs.item_node_id }}" \
                -f fieldId="$FIELD_ID" \
                -f optionId="$OPTION_ID"
            fi

            # Dispatch developer again
            gh workflow run agentic-developer.yml \
              --repo "${{ github.repository }}" \
              -f issue_number="${{ inputs.issue_number }}" \
              -f review_cycle="${NEXT_CYCLE}" \
              -f project_node_id="${{ inputs.project_node_id }}" \
              -f item_node_id="${{ inputs.item_node_id }}"
          fi
```

**Step 2: Validate YAML syntax**

Run: `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/reviewer.yml')); print('Valid YAML')"`
Expected: `Valid YAML`

**Step 3: Commit**

```bash
git add .github/workflows/reviewer.yml
git commit -m "feat: add reviewer agent reusable workflow"
```

---

### Task 7: Create target repo wrapper workflows

These are the thin wrappers that each target repo needs. They receive
`workflow_dispatch` events and call the reusable workflows from this repo.

**Files:**
- Create: `examples/target-repo/github/workflows/agentic-developer.yml`
- Create: `examples/target-repo/github/workflows/agentic-reviewer.yml`

**Step 1: Write agentic-developer.yml wrapper**

```yaml
# Copy this file to your repo at: .github/workflows/agentic-developer.yml
# Replace OWNER/bc-agentic-workflow with your org's repo path.

name: Agentic Developer

on:
  workflow_dispatch:
    inputs:
      issue_number:
        description: "Issue number to implement"
        type: string
        required: true
      review_cycle:
        description: "Current review cycle"
        type: string
        required: true
        default: "0"
      max_review_cycles:
        description: "Max review cycles"
        type: string
        required: false
        default: "3"
      project_node_id:
        description: "Project node ID"
        type: string
        required: false
        default: ""
      item_node_id:
        description: "Project item node ID"
        type: string
        required: false
        default: ""

jobs:
  develop:
    uses: OWNER/bc-agentic-workflow/.github/workflows/developer.yml@main
    with:
      issue_number: ${{ inputs.issue_number }}
      review_cycle: ${{ inputs.review_cycle }}
      max_review_cycles: ${{ inputs.max_review_cycles }}
      project_node_id: ${{ inputs.project_node_id }}
      item_node_id: ${{ inputs.item_node_id }}
    secrets: inherit
```

**Step 2: Write agentic-reviewer.yml wrapper**

```yaml
# Copy this file to your repo at: .github/workflows/agentic-reviewer.yml
# Replace OWNER/bc-agentic-workflow with your org's repo path.

name: Agentic Reviewer

on:
  workflow_dispatch:
    inputs:
      issue_number:
        description: "Issue number being reviewed"
        type: string
        required: true
      pr_number:
        description: "PR number to review"
        type: string
        required: true
      review_cycle:
        description: "Current review cycle"
        type: string
        required: true
        default: "0"
      max_review_cycles:
        description: "Max review cycles"
        type: string
        required: false
        default: "3"
      project_node_id:
        description: "Project node ID"
        type: string
        required: false
        default: ""
      item_node_id:
        description: "Project item node ID"
        type: string
        required: false
        default: ""

jobs:
  review:
    uses: OWNER/bc-agentic-workflow/.github/workflows/reviewer.yml@main
    with:
      issue_number: ${{ inputs.issue_number }}
      pr_number: ${{ inputs.pr_number }}
      review_cycle: ${{ inputs.review_cycle }}
      max_review_cycles: ${{ inputs.max_review_cycles }}
      project_node_id: ${{ inputs.project_node_id }}
      item_node_id: ${{ inputs.item_node_id }}
    secrets: inherit
```

**Step 3: Write README for the examples directory**

Create `examples/target-repo/README.md` with adoption instructions:

```markdown
# Target Repo Setup

To enable the agentic workflow in your repository:

1. Copy `github/workflows/agentic-developer.yml` to `.github/workflows/agentic-developer.yml`
2. Copy `github/workflows/agentic-reviewer.yml` to `.github/workflows/agentic-reviewer.yml`
3. Replace `OWNER/bc-agentic-workflow` with your org's actual path
4. Create agent config directories:

   ```
   .claude/agents/developer/IDENTITY.md
   .claude/agents/developer/TOOLS.md  (customize for your repo!)
   .claude/agents/developer/MEMORY.md
   .claude/agents/developer/logs/.gitkeep
   .claude/agents/reviewer/IDENTITY.md
   .claude/agents/reviewer/TOOLS.md
   .claude/agents/reviewer/MEMORY.md
   .claude/agents/reviewer/logs/.gitkeep
   ```

5. Ensure these org-level secrets exist:
   - `CLAUDE_CODE_OAUTH_TOKEN`
   - `WORKFLOW_PAT`
```

**Step 4: Commit**

```bash
git add examples/
git commit -m "feat: add target repo wrapper examples and adoption guide"
```

---

### Task 8: Create orchestrator trigger for .github repo

This is the thin trigger workflow that goes in the org's `.github` repository.
It catches `projects_v2_item` events and calls the orchestrator.

**Files:**
- Create: `examples/dot-github-repo/workflows/orchestrator-trigger.yml`

**Step 1: Write orchestrator-trigger.yml**

```yaml
# This file goes in your org's .github repository at:
# .github/workflows/orchestrator-trigger.yml
#
# It triggers when items on an org-level GitHub Project change status.
# Replace OWNER/bc-agentic-workflow with your org's actual path.

name: Orchestrator Trigger

on:
  projects_v2_item:
    types: [edited]

jobs:
  orchestrate:
    # Only run for issue items (not PRs or draft issues)
    if: github.event.projects_v2_item.content_type == 'Issue'
    uses: OWNER/bc-agentic-workflow/.github/workflows/orchestrator.yml@main
    with:
      item_node_id: ${{ github.event.projects_v2_item.node_id }}
      content_node_id: ${{ github.event.projects_v2_item.content_node_id }}
      project_node_id: ${{ github.event.projects_v2_item.project_node_id }}
    secrets: inherit
```

**Step 2: Commit**

```bash
git add examples/dot-github-repo/
git commit -m "feat: add orchestrator trigger example for .github repo"
```

---

### Task 9: Update .gitignore and clean up

**Files:**
- Modify: `.gitignore`

**Step 1: Add entries for agent logs and temp files**

Add to `.gitignore`:

```
# Agent logs are repo-specific, don't track defaults
# (each target repo tracks its own logs)

# Temp files from prompt assembly
/tmp/
```

**Step 2: Commit all remaining files**

```bash
git add .gitignore
git commit -m "chore: update gitignore for agent workflow"
```

---

## Testing Guide

After implementing all tasks, test the system:

### Manual test (no project board needed)

1. In a target repo with the wrapper workflows installed, manually trigger:
   ```bash
   gh workflow run agentic-developer.yml \
     --repo OWNER/TARGET_REPO \
     -f issue_number=1 \
     -f review_cycle=0
   ```

2. Watch the workflow run in GitHub Actions

3. Verify:
   - Branch was created: `issue/1-<slug>`
   - Claude Code ran and made commits
   - PR was created with `Closes #1`
   - Reviewer workflow was dispatched automatically
   - Reviewer posted a review on the PR

### Full integration test (with project board)

1. Set up the `.github` repo trigger
2. Create an issue in a target repo
3. Add the issue to your GitHub Project board
4. Move it to "Ready"
5. Watch the full pipeline execute

### Debugging

- Check workflow run logs in GitHub Actions
- Look for `::notice::` and `::error::` annotations
- Check issue comments for agent status updates
- Verify labels are being applied correctly
