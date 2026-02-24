# Testing Checklist

## Phase 0: Prerequisites

### Secrets

- [x] Run `claude setup-token` locally and copy the token
- [x] Add `CLAUDE_CODE_OAUTH_TOKEN` as org secret in `kai-loacher-org` (Settings > Secrets > Actions)
- [x] Create a fine-grained PAT with scopes: `actions:write`, `issues:write`, `contents:write`, `pull-requests:write`
- [x] Add `WORKFLOW_PAT` as org secret in `kai-loacher-org`

### Self-hosted runners

- [x] Runner `runner-developer-1` is online with label `agentic-developer`
- [x] Runner `runner-developer-2` is online with label `agentic-developer`
- [x] Runner `runner-reviewer-1` is online with label `agentic-reviewer`
- [x] At least one runner has the `self-hosted` label (for orchestrator)
- [x] Claude Code CLI is installed on all runners (`claude --version`)
- [x] Each runner has `~/.claude.json` with `{"hasCompletedOnboarding": true}`

### Config

- [x] Update `config.yml`: set `project.org` to `kai-loacher-org`
- [x] Update `config.yml`: set `project.number` to your GitHub Project number

---

## Phase 1: Target repo setup

Pick a test repo in `kai-loacher-org` (or create one).

- [ ] Copy `examples/target-repo/github/workflows/agentic-developer.yml` to `TARGET_REPO/.github/workflows/agentic-developer.yml`
- [ ] Copy `examples/target-repo/github/workflows/agentic-reviewer.yml` to `TARGET_REPO/.github/workflows/agentic-reviewer.yml`
- [ ] In both files, replace `OWNER/bc-agentic-workflow` with `kai-loacher-org/bc-agentic-workflow`
- [ ] Copy `.claude/agents/developer.md` to target repo (customize Tools & Commands section!)
- [ ] Copy `.claude/agents/reviewer.md` to target repo (customize Tools & Commands section!)
- [ ] Push all files to target repo `main` branch
- [ ] Verify both workflows appear in target repo's Actions tab

---

## Phase 2: Manual developer test (no project board)

Create a simple test issue in the target repo first.

```bash
gh issue create --repo kai-loacher-org/TARGET_REPO \
  --title "Add a hello world script" \
  --body "Create a simple hello.py that prints 'Hello, World!'"
```

- [ ] Issue created (note the issue number)

Trigger the developer workflow manually:

```bash
gh workflow run agentic-developer.yml \
  --repo kai-loacher-org/TARGET_REPO \
  -f issue_number="ISSUE_NUMBER" \
  -f review_cycle="0"
```

- [ ] Workflow triggered successfully (`gh run list --repo kai-loacher-org/TARGET_REPO`)
- [ ] Workflow run started on `agentic-developer` runner
- [ ] Claude Code executed (check logs for claude output)
- [ ] Branch `issue/ISSUE_NUMBER-add-a-hello-world-script` was created
- [ ] Commits were pushed to the branch
- [ ] PR was created with title "Issue #N: Add a hello world script"
- [ ] PR body contains `Closes #N`
- [ ] Label `review-cycle:0` was NOT added (orchestrator adds this, not developer)

---

## Phase 3: Manual reviewer test

After Phase 2 PR exists, trigger the reviewer:

```bash
gh workflow run agentic-reviewer.yml \
  --repo kai-loacher-org/TARGET_REPO \
  -f issue_number="ISSUE_NUMBER" \
  -f pr_number="PR_NUMBER" \
  -f review_cycle="0"
```

- [ ] Workflow triggered successfully
- [ ] Workflow run started on `agentic-reviewer` runner
- [ ] Claude Code executed (check logs)
- [ ] A review was posted on the PR (check PR > Conversations)
- [ ] Review is either APPROVED or CHANGES_REQUESTED

### If APPROVED:

- [ ] Issue comment posted: "PR #N has been approved by the Reviewer agent..."
- [ ] PR is ready for manual merge

### If CHANGES_REQUESTED:

- [ ] Developer workflow was re-dispatched automatically
- [ ] New commits appeared on the branch
- [ ] Reviewer was triggered again for cycle 1

---

## Phase 4: Orchestrator test (manual dispatch)

```bash
gh workflow run orchestrator.yml \
  --repo kai-loacher-org/bc-agentic-workflow \
  -f issue_repo="kai-loacher-org/TARGET_REPO" \
  -f issue_number="ISSUE_NUMBER"
```

- [ ] Orchestrator workflow triggered
- [ ] Orchestrator ran on `self-hosted` runner
- [ ] Label `review-cycle:0` was added to the issue
- [ ] Developer workflow was dispatched in target repo
- [ ] Full pipeline ran: developer -> PR -> reviewer -> decision

---

## Phase 5: Full integration test (with project board)

### Setup .github repo trigger

- [ ] Copy `examples/dot-github-repo/workflows/orchestrator-trigger.yml` to `kai-loacher-org/.github` repo at `.github/workflows/orchestrator-trigger.yml`
- [ ] Replace `OWNER/bc-agentic-workflow` with `kai-loacher-org/bc-agentic-workflow`
- [ ] Push to `.github` repo

### Setup GitHub Project

- [ ] Org-level GitHub Project exists with columns: **Backlog**, **Ready**, **In Progress**, **In Review**, **Done**
- [ ] Project number matches `config.yml`

### Run the full pipeline

- [ ] Create a new issue in target repo
- [ ] Add issue to the GitHub Project board (Backlog)
- [ ] Move issue to **Ready**
- [ ] Orchestrator trigger fires (check `.github` repo Actions tab)
- [ ] Orchestrator verifies "Ready" status via GraphQL
- [ ] Project status updated to **In Progress**
- [ ] Developer workflow dispatched and runs
- [ ] PR created
- [ ] Project status updated to **In Review**
- [ ] Reviewer workflow dispatched and runs
- [ ] Review posted on PR

### If reviewer approves:

- [ ] Project status updated to **Done**
- [ ] Issue comment posted about approval
- [ ] PR ready for manual merge

### If reviewer requests changes:

- [ ] `review-cycle` label incremented
- [ ] Project status moved back to **Ready**
- [ ] Developer re-dispatched for next cycle

---

## Phase 6: Error handling tests

### Agent failure

- [ ] Create an issue with an impossible task (e.g., "Rewrite the entire codebase in Brainfuck")
- [ ] Developer agent fails -> `agent-error` label added
- [ ] Trigger again -> second failure -> `agent-failed` label added
- [ ] Trigger again -> orchestrator skips issue with `agent-failed` label

### Max review cycles

- [ ] Manually set `max_review_cycles` to `1` in the workflow dispatch
- [ ] After reviewer requests changes once -> `needs-human-review` label added
- [ ] Issue comment explains max cycles reached

---

## Debugging tips

If something fails, check:

1. **Workflow run logs**: Actions tab > click the run > expand each step
2. **Annotations**: Look for `::notice::` and `::error::` messages
3. **Issue comments**: Agents post failure notifications as comments
4. **Labels**: Check `agent-error`, `agent-failed`, `review-cycle:N`, `needs-human-review`
5. **Runner logs**: On the Beelink, check runner diagnostics at `_diag/` folder
6. **Claude auth**: Verify `CLAUDE_CODE_OAUTH_TOKEN` is valid (`claude setup-token` expires after 1 year)
