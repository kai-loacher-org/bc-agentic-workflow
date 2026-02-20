#!/usr/bin/env python3
"""
Comprehensive validation script for the claude-code-docs skill.
Validates structure, content, and integrity of the skill package.
"""

import json
import sys
from pathlib import Path
import hashlib


def test_directory_structure():
    """Test that all required directories and files exist."""
    base_dir = Path(__file__).parent.parent

    required_paths = [
        "SKILL.md",
        "README.md",
        "references/docs_index.json",
        "scripts/fetch_docs.py",
        "scripts/test_fetch_docs.py",
        "scripts/test_skill_md.py",
        "scripts/run_all_tests.sh",
    ]

    missing = []
    for path in required_paths:
        full_path = base_dir / path
        if not full_path.exists():
            missing.append(str(path))

    if missing:
        raise AssertionError(f"Missing required files/directories: {', '.join(missing)}")

    print("✓ Directory structure is complete")


def test_docs_index_integrity():
    """Test docs_index.json for data integrity and completeness."""
    json_path = Path(__file__).parent.parent / "references" / "docs_index.json"

    with open(json_path) as f:
        data = json.load(f)

    # Check it's a list
    if not isinstance(data, list):
        raise AssertionError(f"docs_index.json should be a list, got {type(data)}")

    # Check we have the expected number of entries
    if len(data) != 57:
        raise AssertionError(f"Expected 57 entries, got {len(data)}")

    # Check each entry has required fields with meaningful content
    for i, entry in enumerate(data):
        if not all(key in entry for key in ["title", "url", "description"]):
            raise AssertionError(f"Entry {i} missing required fields")

        # Check for non-empty values
        if not entry["title"] or not entry["url"] or not entry["description"]:
            raise AssertionError(f"Entry {i} has empty field(s)")

        # Check URL format
        if not entry["url"].startswith("https://code.claude.com/docs/en/"):
            raise AssertionError(f"Entry {i} has invalid URL: {entry['url']}")

        # Check description is not just the default
        if entry["description"] == "Documentation page" and not entry["title"].startswith("Error"):
            print(f"⚠ Warning: Entry {i} ({entry['title']}) has generic description")

    print(f"✓ docs_index.json integrity validated ({len(data)} entries)")


def test_no_duplicates():
    """Test that there are no duplicate URLs in the index."""
    json_path = Path(__file__).parent.parent / "references" / "docs_index.json"

    with open(json_path) as f:
        data = json.load(f)

    urls = [entry["url"] for entry in data]
    unique_urls = set(urls)

    if len(urls) != len(unique_urls):
        duplicates = [url for url in unique_urls if urls.count(url) > 1]
        raise AssertionError(f"Found duplicate URLs: {duplicates}")

    print("✓ No duplicate URLs found")


def test_skill_metadata():
    """Test that SKILL.md has complete and accurate metadata."""
    skill_path = Path(__file__).parent.parent / "SKILL.md"
    content = skill_path.read_text()

    # Check for specific skill characteristics
    required_terms = [
        "claude-code-docs",
        "documentation",
        "Claude Code",
        "references/docs_index.json",
    ]

    for term in required_terms:
        if term not in content:
            raise AssertionError(f"SKILL.md should contain '{term}'")

    # Check that it mentions the correct number of pages
    if "50+" not in content and "57" not in content:
        print("⚠ Warning: SKILL.md should mention the number of documentation pages")

    print("✓ SKILL.md metadata is complete")


def test_readme_completeness():
    """Test that README.md is comprehensive."""
    readme_path = Path(__file__).parent.parent / "README.md"
    content = readme_path.read_text()

    required_sections = [
        "## Overview",
        "## Structure",
        "## Features",
        "## Usage",
        "## Testing",
    ]

    for section in required_sections:
        if section not in content:
            raise AssertionError(f"README.md should contain section: {section}")

    # Check for usage instructions
    if "fetch_docs.py" not in content:
        raise AssertionError("README.md should document fetch_docs.py usage")

    if "run_all_tests.sh" not in content:
        raise AssertionError("README.md should document test execution")

    print("✓ README.md is comprehensive")


def test_script_executability():
    """Test that scripts have proper permissions and shebang lines."""
    scripts_dir = Path(__file__).parent

    python_scripts = [
        "fetch_docs.py",
        "test_fetch_docs.py",
        "test_skill_md.py",
        "validate_skill.py",
    ]

    for script_name in python_scripts:
        script_path = scripts_dir / script_name

        if not script_path.exists():
            continue

        # Check shebang line
        with open(script_path) as f:
            first_line = f.readline()
            if not first_line.startswith("#!/usr/bin/env python3"):
                print(f"⚠ Warning: {script_name} should have proper shebang line")

    # Check bash script
    bash_script = scripts_dir / "run_all_tests.sh"
    if bash_script.exists():
        with open(bash_script) as f:
            first_line = f.readline()
            if not first_line.startswith("#!/bin/bash"):
                print(f"⚠ Warning: run_all_tests.sh should have proper shebang line")

        # Check if executable
        if not bash_script.stat().st_mode & 0o111:
            print(f"⚠ Warning: run_all_tests.sh should be executable")

    print("✓ Scripts have proper structure")


def test_file_sizes():
    """Test that files are within reasonable size limits."""
    base_dir = Path(__file__).parent.parent

    size_limits = {
        "SKILL.md": 50 * 1024,  # 50 KB
        "README.md": 20 * 1024,  # 20 KB
        "references/docs_index.json": 500 * 1024,  # 500 KB
    }

    for path, max_size in size_limits.items():
        file_path = base_dir / path
        if file_path.exists():
            size = file_path.stat().st_size
            if size > max_size:
                print(f"⚠ Warning: {path} is {size} bytes (limit: {max_size})")
            if size == 0:
                raise AssertionError(f"{path} is empty")

    print("✓ File sizes are reasonable")


def generate_checksum():
    """Generate checksums for key files."""
    base_dir = Path(__file__).parent.parent

    files_to_check = [
        "SKILL.md",
        "references/docs_index.json",
        "scripts/fetch_docs.py",
    ]

    checksums = {}
    for file_path in files_to_check:
        full_path = base_dir / file_path
        if full_path.exists():
            with open(full_path, 'rb') as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
                checksums[file_path] = file_hash

    print("\nFile Checksums (SHA-256):")
    for path, checksum in checksums.items():
        print(f"  {path}: {checksum[:16]}...")


def main():
    """Run all validation tests."""
    print("=" * 60)
    print("Claude Code Docs Skill - Comprehensive Validation")
    print("=" * 60)
    print()

    tests = [
        test_directory_structure,
        test_docs_index_integrity,
        test_no_duplicates,
        test_skill_metadata,
        test_readme_completeness,
        test_script_executability,
        test_file_sizes,
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

    print()
    print("=" * 60)

    if failed > 0:
        print(f"Validation completed: {len(tests) - failed}/{len(tests)} passed")
        print("=" * 60)
        sys.exit(1)
    else:
        print(f"All validation tests passed! ({len(tests)}/{len(tests)})")
        print("=" * 60)
        generate_checksum()
        sys.exit(0)


if __name__ == "__main__":
    main()
