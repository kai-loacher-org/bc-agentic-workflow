# Claude Code Documentation Skill

A comprehensive skill that provides Claude with access to the complete official Claude Code documentation index.

## Overview

This skill enables Claude to help users with questions about Claude Code features, configuration, integrations, workflows, and troubleshooting. It maintains a searchable index of 50+ documentation pages covering all aspects of Claude Code.

## Structure

```
claude-code-docs/
├── SKILL.md                    # Main skill definition
├── README.md                   # This file
├── references/
│   └── docs_index.json         # Documentation index (57 pages)
└── scripts/
    ├── fetch_docs.py           # Script to update docs index
    ├── test_fetch_docs.py      # Tests for fetch_docs.py
    ├── test_skill_md.py        # Tests for SKILL.md validation
    ├── validate_skill.py       # Comprehensive skill validation
    ├── package_skill.sh        # Package skill for distribution
    └── run_all_tests.sh        # Run complete test suite
```

## Features

- **Comprehensive Coverage**: Indexes 57 documentation pages across all Claude Code topics
- **Searchable Metadata**: Each page includes title, URL, and description
- **Auto-Update Script**: Fetch latest documentation with a single command
- **Complete Test Suite**: Validates skill integrity and documentation index

## Documentation Coverage

The skill provides access to documentation on:

- **Core Concepts**: Overview, quickstart, best practices, common workflows
- **Setup & Configuration**: Installation, authentication, settings, permissions
- **Features**: Interactive mode, fast mode, memory, checkpointing, sandboxing
- **Extensibility**: Skills, plugins, hooks, MCP servers, subagents
- **Integrations**: VS Code, JetBrains, Chrome, Slack, GitHub Actions, GitLab
- **Enterprise**: Cloud providers, LLM gateways, analytics, monitoring
- **Security & Compliance**: Data usage, legal policies, security practices

## Usage

The skill is automatically available to Claude when users ask questions about Claude Code. Example triggers:

- "How do I set up Claude Code with VS Code?"
- "What are hooks and how do I use them?"
- "How can I extend Claude Code?"
- "How do I deploy Claude Code for my enterprise team?"

## Maintaining the Documentation Index

To update the documentation index with the latest content:

```bash
cd .claude/skills/claude-code-docs/scripts
python3 fetch_docs.py > ../references/docs_index.json
```

The script:
1. Fetches all documentation pages from code.claude.com
2. Extracts titles and descriptions from markdown
3. Outputs a JSON index with metadata for each page

## Validation and Testing

### Comprehensive Validation

Run the complete validation suite to ensure skill integrity:

```bash
cd .claude/skills/claude-code-docs/scripts
./validate_skill.py
```

This validates:
- Directory structure and file existence
- Documentation index integrity (57 entries)
- No duplicate URLs
- SKILL.md metadata completeness
- README.md comprehensiveness
- Script executability and structure
- File sizes are reasonable

### Testing

Run the complete test suite:

```bash
cd .claude/skills/claude-code-docs/scripts
./run_all_tests.sh
```

Or run individual test suites:

```bash
# Test the documentation fetcher
python3 test_fetch_docs.py

# Test SKILL.md validation
python3 test_skill_md.py

# Comprehensive skill validation
python3 validate_skill.py
```

### Test Coverage

- **fetch_docs.py tests** (5 tests):
  - Title extraction from markdown
  - Description extraction from markdown
  - Empty content handling
  - URL list validation
  - Output JSON format validation

- **SKILL.md tests** (8 tests):
  - File existence
  - YAML frontmatter validation
  - Required sections presence
  - No TODO placeholders
  - References to docs_index.json
  - Example interactions included
  - When-to-use descriptions
  - Content length and structure

- **validate_skill.py tests** (7 tests):
  - Directory structure completeness
  - Documentation index integrity
  - No duplicate URLs
  - SKILL.md metadata validation
  - README.md comprehensiveness
  - Script executability checks
  - File size validation

## Packaging

To package the skill for distribution:

```bash
cd .claude/skills/claude-code-docs/scripts
./package_skill.sh
```

This will:
1. Run comprehensive validation
2. Run complete test suite
3. Clean up cache files
4. Create a distributable archive (.tar.gz)
5. Generate package manifest with checksums
6. Create distribution README with installation instructions

The packaged skill will be available in `.claude/skills/claude-code-docs/dist/`

## Requirements

- Python 3.6+
- No external dependencies (uses only standard library)

## License

This skill is part of the claude-agentic-workflow project.
