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
