---
name: claude-code-docs
description: Access comprehensive Claude Code documentation for questions about features, configuration, integrations, workflows, and troubleshooting. Use when users ask about Claude Code capabilities, setup, permissions, hooks, skills, MCP, IDE integrations, or any official documentation topics.
---

# Claude Code Documentation

## Overview

This skill provides access to the complete official Claude Code documentation index. Use it when users have questions about Claude Code features, configuration, best practices, integrations, or troubleshooting. The skill maintains a searchable index of all documentation pages with titles, URLs, and descriptions.

## When to Use This Skill

Trigger this skill when users ask about:

- **Setup & Configuration**: Installation, authentication, settings, permissions, model configuration
- **Features & Capabilities**: Tools, workflows, interactive mode, fast mode, memory, checkpointing
- **Integrations**: VS Code, JetBrains, Chrome, Slack, GitHub Actions, GitLab CI/CD
- **Extensibility**: Skills, plugins, hooks, MCP servers, subagents, output styles
- **Enterprise & Deployment**: Cloud providers (Bedrock, Vertex AI, Microsoft Foundry), LLM gateways, network config, analytics, monitoring
- **Platform-Specific**: Desktop app, web version, development containers
- **Best Practices**: Common workflows, security, cost management, troubleshooting
- **Legal & Compliance**: Terms of service, data usage, security policies

## Documentation Index

The skill includes a comprehensive index of Claude Code documentation (`references/docs_index.json`) with metadata for 50+ documentation pages covering:

### Core Concepts
- Claude Code Overview & How It Works
- Quickstart Guide
- Best Practices
- Common Workflows

### Setup & Configuration
- Setup & Installation
- Authentication (Teams, Enterprise, API)
- Settings & Permissions
- Model Configuration
- Keyboard Shortcuts (Keybindings)

### Features
- Interactive Mode
- Fast Mode
- Memory Management
- Checkpointing
- Sandboxing
- Output Styles

### Extensibility
- Skills
- Plugins & Plugin Marketplaces
- Hooks (Automation)
- MCP (Model Context Protocol)
- Custom Subagents

### Integrations
- VS Code Extension
- JetBrains IDEs
- Chrome Browser Extension
- Slack
- GitHub Actions
- GitLab CI/CD

### Enterprise & Cloud
- Amazon Bedrock
- Google Vertex AI
- Microsoft Foundry
- LLM Gateway Configuration
- Network Configuration
- Server-Managed Settings
- Analytics & Monitoring
- Third-Party Integrations

### Additional Topics
- Security & Legal Compliance
- Data Usage & Privacy
- Cost Management
- Troubleshooting
- Desktop App & Web Version
- Agent Teams (Experimental)
- Development Containers

## How to Use This Skill

1. **Search the Index**: When a user asks about a Claude Code topic, reference the documentation index to find relevant pages
2. **Provide Specific URLs**: Direct users to the exact documentation page(s) that answer their question
3. **Summarize Key Information**: Extract and present relevant information from the index descriptions
4. **Multiple Sources**: For complex questions, reference multiple documentation pages that cover different aspects

## Example Interactions

**User asks**: "How do I set up Claude Code with VS Code?"
**Response**: Reference the VS Code documentation (https://code.claude.com/docs/en/vs-code.md) and Setup documentation (https://code.claude.com/docs/en/setup.md)

**User asks**: "What are hooks and how do I use them?"
**Response**: Reference the Hooks Guide (https://code.claude.com/docs/en/hooks-guide.md) and Hooks Reference (https://code.claude.com/docs/en/hooks.md)

**User asks**: "How can I extend Claude Code?"
**Response**: Reference Features Overview (https://code.claude.com/docs/en/features-overview.md), Skills (https://code.claude.com/docs/en/skills.md), Plugins (https://code.claude.com/docs/en/plugins.md), and MCP (https://code.claude.com/docs/en/mcp.md)

**User asks**: "How do I deploy Claude Code for my enterprise team?"
**Response**: Reference Authentication (https://code.claude.com/docs/en/authentication.md), Enterprise Deployment (https://code.claude.com/docs/en/third-party-integrations.md), and cloud provider-specific docs (Bedrock, Vertex AI, or Foundry)

## Resources

### references/
- `docs_index.json`: Complete searchable index of all Claude Code documentation pages with titles, URLs, and descriptions

### scripts/
- `fetch_docs.py`: Python script to fetch and update the documentation index from the official Claude Code documentation site
- `test_fetch_docs.py`: Test suite for the documentation fetcher

## Maintaining the Documentation Index

To update the documentation index with the latest content:

```bash
cd .claude/skills/claude-code-docs/scripts
python3 fetch_docs.py > ../references/docs_index.json
```

The script fetches all documentation pages, extracts titles and descriptions, and outputs a JSON index. Run this periodically to keep the index up-to-date with new or updated documentation.
