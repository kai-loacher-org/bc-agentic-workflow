# Bootstrap

Read these files IMMEDIATELY before doing anything else:
- `.claude/agents/reviewer/IDENTITY.md` — your identity and review criteria
- `.claude/agents/reviewer/TOOLS.md` — build, test, and lint commands
- `.claude/agents/reviewer/MEMORY.md` — your persistent memory

Then read your recent logs from `.claude/agents/reviewer/logs/` (last 3 entries).

These files belong to you. Update `MEMORY.md` to persist learnings across sessions.

# Instructions

1. Read your bootstrap files above FIRST
2. Read and understand the issue requirements
3. Read the PR diff using `gh pr diff`
4. Check: Does the code fulfill the issue requirements?
5. Check: Are there tests for new functionality?
6. Check: Is the code clean, secure, and maintainable?
7. Post your review using `gh pr review`:
   - If approved: `gh pr review --approve --body "Your approval message"`
   - If changes needed: `gh pr review --request-changes --body "Your detailed feedback"`
8. Update `.claude/agents/reviewer/MEMORY.md` with any learnings
9. Write a log entry to `.claude/agents/reviewer/logs/YYYY-MM-DD.md`

IMPORTANT: You MUST post exactly one review using gh pr review. Either --approve or --request-changes.
