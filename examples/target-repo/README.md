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

5. Create agent definitions (customize the Tools & Commands section for your repo!):

   ```
   .claude/agents/developer.md   # Copy from bc-agentic-workflow, customize tools
   .claude/agents/reviewer.md    # Copy from bc-agentic-workflow, customize tools
   ```

6. Ensure these org-level secrets exist:
   - `CLAUDE_CODE_OAUTH_TOKEN`
   - `WORKFLOW_PAT`
