#!/usr/bin/env python3
"""
Tests for fetch_docs.py script.
"""

import json
import sys
from pathlib import Path

# Add the scripts directory to the path so we can import fetch_docs
sys.path.insert(0, str(Path(__file__).parent))

import fetch_docs


def test_extract_title_from_markdown():
    """Test title extraction from markdown content."""
    content = """# Test Title

This is a test paragraph.
"""
    title = fetch_docs.extract_title_from_markdown(content)
    assert title == "Test Title", f"Expected 'Test Title', got '{title}'"
    print("✓ test_extract_title_from_markdown passed")


def test_extract_description_from_markdown():
    """Test description extraction from markdown content."""
    content = """# Test Title

> This is a blockquote that should be skipped
> More blockquote content

This is the first real paragraph. It has multiple sentences.
This is still part of the first paragraph.

This is the second paragraph.
"""
    description = fetch_docs.extract_description_from_markdown(content)
    assert "first real paragraph" in description, f"Description should contain 'first real paragraph': {description}"
    assert "blockquote" not in description.lower(), f"Description should not contain blockquote content: {description}"
    print("✓ test_extract_description_from_markdown passed")


def test_extract_description_handles_empty_content():
    """Test description extraction with empty or minimal content."""
    content = """# Test Title

"""
    description = fetch_docs.extract_description_from_markdown(content)
    assert description == "Documentation page", f"Expected default description, got '{description}'"
    print("✓ test_extract_description_handles_empty_content passed")


def test_docs_urls_list():
    """Test that DOCS_URLS list is properly formatted."""
    assert len(fetch_docs.DOCS_URLS) == 57, f"Expected 57 URLs, got {len(fetch_docs.DOCS_URLS)}"

    for url in fetch_docs.DOCS_URLS:
        assert url.startswith("https://code.claude.com/docs/en/"), f"Invalid URL format: {url}"
        assert url.endswith(".md"), f"URL should end with .md: {url}"

    print("✓ test_docs_urls_list passed")


def test_output_json_format():
    """Test that the output JSON file has the correct format."""
    json_path = Path(__file__).parent.parent / "references" / "docs_index.json"

    if not json_path.exists():
        print("⚠ Warning: docs_index.json not found, skipping format test")
        return

    with open(json_path) as f:
        data = json.load(f)

    assert isinstance(data, list), f"Expected list, got {type(data)}"
    assert len(data) == 57, f"Expected 57 entries, got {len(data)}"

    # Check first entry has required fields
    entry = data[0]
    assert "title" in entry, "Entry missing 'title' field"
    assert "url" in entry, "Entry missing 'url' field"
    assert "description" in entry, "Entry missing 'description' field"

    assert isinstance(entry["title"], str), "Title should be a string"
    assert isinstance(entry["url"], str), "URL should be a string"
    assert isinstance(entry["description"], str), "Description should be a string"

    assert len(entry["title"]) > 0, "Title should not be empty"
    assert len(entry["url"]) > 0, "URL should not be empty"
    assert len(entry["description"]) > 0, "Description should not be empty"

    print(f"✓ test_output_json_format passed ({len(data)} entries)")


def main():
    """Run all tests."""
    print("Running tests for fetch_docs.py...\n")

    tests = [
        test_extract_title_from_markdown,
        test_extract_description_from_markdown,
        test_extract_description_handles_empty_content,
        test_docs_urls_list,
        test_output_json_format,
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
