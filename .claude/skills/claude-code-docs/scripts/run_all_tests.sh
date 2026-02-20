#!/bin/bash
# Run all tests for the claude-code-docs skill

set -e  # Exit on any error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=================================="
echo "Claude Code Docs Skill Test Suite"
echo "=================================="
echo ""

# Change to scripts directory
cd "$SCRIPT_DIR"

# Run fetch_docs tests
echo "1. Running fetch_docs.py tests..."
python3 test_fetch_docs.py
echo ""

# Run SKILL.md validation tests
echo "2. Running SKILL.md validation tests..."
python3 test_skill_md.py
echo ""

# Check Python syntax
echo "3. Checking Python syntax..."
python3 -m py_compile fetch_docs.py test_fetch_docs.py test_skill_md.py
echo "✓ All Python files have valid syntax"
echo ""

# Verify docs_index.json exists and is valid JSON
echo "4. Verifying docs_index.json..."
if [ ! -f "../references/docs_index.json" ]; then
    echo "✗ docs_index.json not found"
    exit 1
fi

python3 -c "import json; json.load(open('../references/docs_index.json'))"
echo "✓ docs_index.json is valid JSON"
echo ""

echo "=================================="
echo "All tests passed successfully! ✓"
echo "=================================="
