#!/usr/bin/env python3
"""
Fetches Claude Code documentation pages and extracts metadata.
Outputs a JSON array with title, url, and description for each page.
"""

import json
import re
import urllib.request
from typing import List, Dict

# Full list of documentation URLs to fetch
DOCS_URLS = [
    "https://code.claude.com/docs/en/agent-teams.md",
    "https://code.claude.com/docs/en/amazon-bedrock.md",
    "https://code.claude.com/docs/en/analytics.md",
    "https://code.claude.com/docs/en/authentication.md",
    "https://code.claude.com/docs/en/best-practices.md",
    "https://code.claude.com/docs/en/changelog.md",
    "https://code.claude.com/docs/en/checkpointing.md",
    "https://code.claude.com/docs/en/chrome.md",
    "https://code.claude.com/docs/en/claude-code-on-the-web.md",
    "https://code.claude.com/docs/en/cli-reference.md",
    "https://code.claude.com/docs/en/common-workflows.md",
    "https://code.claude.com/docs/en/costs.md",
    "https://code.claude.com/docs/en/data-usage.md",
    "https://code.claude.com/docs/en/desktop.md",
    "https://code.claude.com/docs/en/desktop-quickstart.md",
    "https://code.claude.com/docs/en/devcontainer.md",
    "https://code.claude.com/docs/en/discover-plugins.md",
    "https://code.claude.com/docs/en/fast-mode.md",
    "https://code.claude.com/docs/en/features-overview.md",
    "https://code.claude.com/docs/en/github-actions.md",
    "https://code.claude.com/docs/en/gitlab-ci-cd.md",
    "https://code.claude.com/docs/en/google-vertex-ai.md",
    "https://code.claude.com/docs/en/headless.md",
    "https://code.claude.com/docs/en/hooks.md",
    "https://code.claude.com/docs/en/hooks-guide.md",
    "https://code.claude.com/docs/en/how-claude-code-works.md",
    "https://code.claude.com/docs/en/interactive-mode.md",
    "https://code.claude.com/docs/en/jetbrains.md",
    "https://code.claude.com/docs/en/keybindings.md",
    "https://code.claude.com/docs/en/legal-and-compliance.md",
    "https://code.claude.com/docs/en/llm-gateway.md",
    "https://code.claude.com/docs/en/mcp.md",
    "https://code.claude.com/docs/en/memory.md",
    "https://code.claude.com/docs/en/microsoft-foundry.md",
    "https://code.claude.com/docs/en/model-config.md",
    "https://code.claude.com/docs/en/monitoring-usage.md",
    "https://code.claude.com/docs/en/network-config.md",
    "https://code.claude.com/docs/en/output-styles.md",
    "https://code.claude.com/docs/en/overview.md",
    "https://code.claude.com/docs/en/permissions.md",
    "https://code.claude.com/docs/en/plugin-marketplaces.md",
    "https://code.claude.com/docs/en/plugins.md",
    "https://code.claude.com/docs/en/plugins-reference.md",
    "https://code.claude.com/docs/en/quickstart.md",
    "https://code.claude.com/docs/en/sandboxing.md",
    "https://code.claude.com/docs/en/security.md",
    "https://code.claude.com/docs/en/server-managed-settings.md",
    "https://code.claude.com/docs/en/settings.md",
    "https://code.claude.com/docs/en/setup.md",
    "https://code.claude.com/docs/en/skills.md",
    "https://code.claude.com/docs/en/slack.md",
    "https://code.claude.com/docs/en/statusline.md",
    "https://code.claude.com/docs/en/sub-agents.md",
    "https://code.claude.com/docs/en/terminal-config.md",
    "https://code.claude.com/docs/en/third-party-integrations.md",
    "https://code.claude.com/docs/en/troubleshooting.md",
    "https://code.claude.com/docs/en/vs-code.md",
]


def extract_title_from_markdown(content: str) -> str:
    """Extract the first # heading from markdown content."""
    lines = content.split('\n')
    for line in lines:
        line = line.strip()
        if line.startswith('# '):
            return line[2:].strip()
    return "Untitled"


def extract_description_from_markdown(content: str) -> str:
    """Extract the first 1-2 meaningful sentences as description."""
    lines = content.split('\n')

    # Skip the title and empty lines, find the first paragraph
    in_paragraph = False
    paragraph_lines = []
    skip_blockquote = False

    for line in lines:
        line = line.strip()

        # Skip title, empty lines, and frontmatter
        if line.startswith('#') or line.startswith('---') or not line:
            continue

        # Skip blockquotes (like the documentation index note)
        if line.startswith('>'):
            skip_blockquote = True
            continue
        elif skip_blockquote and not line.startswith('>'):
            skip_blockquote = False

        if skip_blockquote:
            continue

        # Skip common metadata lines
        if line.startswith(':::') or line.startswith('```'):
            break

        # Collect paragraph text
        if line and not line.startswith('[') and not line.startswith('!'):
            paragraph_lines.append(line)
            in_paragraph = True
        elif in_paragraph:
            # End of first paragraph
            break

    if not paragraph_lines:
        return "Documentation page"

    # Join and extract first 1-2 sentences
    text = ' '.join(paragraph_lines)

    # Split by sentence terminators
    sentences = re.split(r'(?<=[.!?])\s+', text)

    # Take first 1-2 sentences, up to ~150 chars
    description = sentences[0] if sentences else text
    if len(sentences) > 1 and len(description) < 100:
        description = f"{sentences[0]} {sentences[1]}"

    # Trim to reasonable length
    if len(description) > 200:
        description = description[:197] + "..."

    return description


def fetch_page_metadata(url: str) -> Dict[str, str]:
    """Fetch a documentation page and extract its metadata."""
    try:
        # Fetch the page
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0 (Claude Code Docs Fetcher)'}
        )

        with urllib.request.urlopen(req, timeout=10) as response:
            content = response.read().decode('utf-8')

        # Extract title and description
        title = extract_title_from_markdown(content)
        description = extract_description_from_markdown(content)

        return {
            "title": title,
            "url": url,
            "description": description
        }

    except Exception as e:
        # Return error information but continue processing other URLs
        return {
            "title": f"Error: {url.split('/')[-1].replace('.md', '')}",
            "url": url,
            "description": f"Failed to fetch: {str(e)}"
        }


def main():
    """Fetch all documentation pages and output JSON."""
    results: List[Dict[str, str]] = []

    for url in DOCS_URLS:
        metadata = fetch_page_metadata(url)
        results.append(metadata)

    # Output JSON to stdout
    print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
