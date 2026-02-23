# Target Repo Setup

To enable the agentic workflow in your repository:

1. Copy `github/workflows/agentic-developer.yml` to `.github/workflows/agentic-developer.yml`
2. Copy `github/workflows/agentic-reviewer.yml` to `.github/workflows/agentic-reviewer.yml`
3. Replace `OWNER/bc-agentic-workflow` with your org's actual path
4. Optionally create `.claude/config.yml` for per-repo settings:

   ```yaml
   yolo_mode: false       # auto-merge on reviewer approval
   dedicated_branch: ""   # fixed branch (empty = per-issue)
   ```

5. Create agent config directories:

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

6. Ensure these org-level secrets exist:
   - `CLAUDE_CODE_OAUTH_TOKEN`
   - `WORKFLOW_PAT`
