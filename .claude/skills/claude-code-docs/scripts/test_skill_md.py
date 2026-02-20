#!/usr/bin/env python3
"""
Tests for SKILL.md file to ensure it's well-formed and complete.
"""

import sys
from pathlib import Path
import re


def test_skill_file_exists():
    """Test that SKILL.md exists."""
    skill_path = Path(__file__).parent.parent / "SKILL.md"
    assert skill_path.exists(), "SKILL.md file not found"
    print("✓ test_skill_file_exists passed")


def test_skill_has_frontmatter():
    """Test that SKILL.md has proper YAML frontmatter."""
    skill_path = Path(__file__).parent.parent / "SKILL.md"
    content = skill_path.read_text()

    # Check for frontmatter delimiters
    assert content.startswith("---"), "SKILL.md should start with YAML frontmatter (---)"

    # Find the closing delimiter
    lines = content.split('\n')
    closing_delimiter_index = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            closing_delimiter_index = i
            break

    assert closing_delimiter_index is not None, "SKILL.md frontmatter should have closing delimiter (---)"

    frontmatter = '\n'.join(lines[1:closing_delimiter_index])

    # Check required frontmatter fields
    assert "name:" in frontmatter, "Frontmatter should include 'name' field"
    assert "description:" in frontmatter, "Frontmatter should include 'description' field"

    # Check that name and description have values
    assert "name: claude-code-docs" in frontmatter, "Name should be 'claude-code-docs'"

    # Check description is meaningful (not TODO)
    assert "TODO" not in frontmatter, "Frontmatter should not contain TODO placeholders"

    print("✓ test_skill_has_frontmatter passed")


def test_skill_has_required_sections():
    """Test that SKILL.md has all required sections."""
    skill_path = Path(__file__).parent.parent / "SKILL.md"
    content = skill_path.read_text()

    required_sections = [
        "# Claude Code Documentation",
        "## Overview",
        "## When to Use This Skill",
        "## Documentation Index",
    ]

    for section in required_sections:
        assert section in content, f"SKILL.md should contain section: {section}"

    print("✓ test_skill_has_required_sections passed")


def test_skill_has_no_todos():
    """Test that SKILL.md has no TODO placeholders."""
    skill_path = Path(__file__).parent.parent / "SKILL.md"
    content = skill_path.read_text()

    # Skip frontmatter for this check since we already verified it
    lines = content.split('\n')
    closing_delimiter_index = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            closing_delimiter_index = i
            break

    main_content = '\n'.join(lines[closing_delimiter_index+1:])

    # Check for TODO markers
    todo_patterns = [
        r'\[TODO:',
        r'TODO:',
    ]

    for pattern in todo_patterns:
        matches = re.findall(pattern, main_content, re.IGNORECASE)
        assert len(matches) == 0, f"SKILL.md should not contain TODO placeholders. Found {len(matches)} instances."

    print("✓ test_skill_has_no_todos passed")


def test_skill_references_docs_index():
    """Test that SKILL.md references the docs_index.json file."""
    skill_path = Path(__file__).parent.parent / "SKILL.md"
    content = skill_path.read_text()

    assert "docs_index.json" in content, "SKILL.md should reference docs_index.json"
    assert "references/" in content, "SKILL.md should mention the references/ directory"

    print("✓ test_skill_references_docs_index passed")


def test_skill_has_example_interactions():
    """Test that SKILL.md includes example interactions."""
    skill_path = Path(__file__).parent.parent / "SKILL.md"
    content = skill_path.read_text()

    assert "Example" in content or "example" in content, "SKILL.md should include examples"
    assert "User asks" in content or "user asks" in content, "SKILL.md should include user interaction examples"

    print("✓ test_skill_has_example_interactions passed")


def test_skill_describes_when_to_use():
    """Test that SKILL.md clearly describes when to use the skill."""
    skill_path = Path(__file__).parent.parent / "SKILL.md"
    content = skill_path.read_text()

    # Should mention specific triggers or scenarios
    trigger_keywords = ["when", "use", "trigger", "ask"]
    found_triggers = sum(1 for keyword in trigger_keywords if keyword.lower() in content.lower())

    assert found_triggers >= 3, "SKILL.md should clearly describe when to use the skill"

    print("✓ test_skill_describes_when_to_use passed")


def test_skill_content_length():
    """Test that SKILL.md has substantial content."""
    skill_path = Path(__file__).parent.parent / "SKILL.md"
    content = skill_path.read_text()

    # Should be at least 500 characters of meaningful content
    assert len(content) > 500, "SKILL.md should have substantial content (>500 characters)"

    # Should have multiple sections (indicated by ## headers)
    section_count = len(re.findall(r'^##\s+', content, re.MULTILINE))
    assert section_count >= 4, f"SKILL.md should have at least 4 sections, found {section_count}"

    print("✓ test_skill_content_length passed")


def main():
    """Run all tests."""
    print("Running tests for SKILL.md...\n")

    tests = [
        test_skill_file_exists,
        test_skill_has_frontmatter,
        test_skill_has_required_sections,
        test_skill_has_no_todos,
        test_skill_references_docs_index,
        test_skill_has_example_interactions,
        test_skill_describes_when_to_use,
        test_skill_content_length,
    ]

    failed = 0
    for test in tests:
        try:
            test()
        except AssertionError as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} error: {e}")
            failed += 1

    print(f"\n{'='*50}")
    print(f"Tests completed: {len(tests) - failed}/{len(tests)} passed")

    if failed > 0:
        sys.exit(1)
    else:
        print("All tests passed! ✓")
        sys.exit(0)


if __name__ == "__main__":
    main()
