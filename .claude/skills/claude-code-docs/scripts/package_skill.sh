#!/bin/bash
# Package the claude-code-docs skill for distribution

set -e  # Exit on any error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
SKILL_NAME="claude-code-docs"
OUTPUT_DIR="${SKILL_DIR}/dist"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
ARCHIVE_NAME="${SKILL_NAME}_${TIMESTAMP}.tar.gz"

echo "========================================"
echo "Packaging Skill: ${SKILL_NAME}"
echo "========================================"
echo ""

# Step 1: Run validation
echo "Step 1: Running validation..."
cd "$SCRIPT_DIR"
python3 validate_skill.py
if [ $? -ne 0 ]; then
    echo "✗ Validation failed. Cannot package skill."
    exit 1
fi
echo ""

# Step 2: Run all tests
echo "Step 2: Running test suite..."
./run_all_tests.sh
if [ $? -ne 0 ]; then
    echo "✗ Tests failed. Cannot package skill."
    exit 1
fi
echo ""

# Step 3: Clean up any Python cache files
echo "Step 3: Cleaning up cache files..."
find "$SKILL_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$SKILL_DIR" -type f -name "*.pyc" -delete 2>/dev/null || true
find "$SKILL_DIR" -type f -name "*.pyo" -delete 2>/dev/null || true
echo "✓ Cache files cleaned"
echo ""

# Step 4: Create distribution directory
echo "Step 4: Creating distribution directory..."
mkdir -p "$OUTPUT_DIR"
echo "✓ Distribution directory created: $OUTPUT_DIR"
echo ""

# Step 5: Create archive
echo "Step 5: Creating archive..."
cd "$(dirname "$SKILL_DIR")"
tar -czf "$OUTPUT_DIR/$ARCHIVE_NAME" \
    --exclude="dist" \
    --exclude="__pycache__" \
    --exclude="*.pyc" \
    --exclude="*.pyo" \
    --exclude=".DS_Store" \
    "$SKILL_NAME/"

if [ $? -eq 0 ]; then
    echo "✓ Archive created: $OUTPUT_DIR/$ARCHIVE_NAME"
else
    echo "✗ Failed to create archive"
    exit 1
fi
echo ""

# Step 6: Generate package manifest
echo "Step 6: Generating package manifest..."
MANIFEST_FILE="$OUTPUT_DIR/manifest.txt"

cat > "$MANIFEST_FILE" << EOF
Claude Code Docs Skill Package
================================

Package: ${SKILL_NAME}
Version: 1.0
Created: $(date +"%Y-%m-%d %H:%M:%S")
Archive: ${ARCHIVE_NAME}

Contents:
---------
EOF

tar -tzf "$OUTPUT_DIR/$ARCHIVE_NAME" | sort >> "$MANIFEST_FILE"

cat >> "$MANIFEST_FILE" << EOF

Installation:
-------------
1. Extract the archive to your .claude/skills/ directory:
   tar -xzf ${ARCHIVE_NAME} -C ~/.claude/skills/

2. Verify installation:
   cd ~/.claude/skills/${SKILL_NAME}/scripts
   ./run_all_tests.sh

3. The skill is now available to Claude Code

Checksums:
----------
EOF

# Generate checksums
cd "$OUTPUT_DIR"
sha256sum "$ARCHIVE_NAME" >> "$MANIFEST_FILE"

echo "✓ Manifest created: $MANIFEST_FILE"
echo ""

# Step 7: Create README for distribution
echo "Step 7: Creating distribution README..."
DIST_README="$OUTPUT_DIR/README.txt"

cat > "$DIST_README" << 'EOF'
Claude Code Documentation Skill
================================

This package contains the claude-code-docs skill for Claude Code.

WHAT IT DOES
------------
Provides Claude with access to comprehensive Claude Code documentation,
enabling it to answer questions about features, configuration, integrations,
workflows, and troubleshooting.

FEATURES
--------
- 57 indexed documentation pages
- Searchable metadata (title, URL, description)
- Auto-update script for latest docs
- Complete test suite

INSTALLATION
------------
1. Extract to your Claude skills directory:
   tar -xzf claude-code-docs_*.tar.gz -C ~/.claude/skills/

2. Verify installation:
   cd ~/.claude/skills/claude-code-docs/scripts
   ./run_all_tests.sh

3. The skill will be automatically available to Claude Code

USAGE
-----
The skill triggers automatically when you ask Claude Code questions like:
- "How do I set up Claude Code with VS Code?"
- "What are hooks and how do I use them?"
- "How can I extend Claude Code?"

UPDATING DOCUMENTATION
----------------------
To update the documentation index:
   cd ~/.claude/skills/claude-code-docs/scripts
   python3 fetch_docs.py > ../references/docs_index.json

REQUIREMENTS
------------
- Python 3.6 or higher (no external dependencies)
- Claude Code (desktop app or VS Code extension)

SUPPORT
-------
For issues or questions, visit:
https://github.com/anthropics/claude-code

LICENSE
-------
This skill is part of the claude-agentic-workflow project.
EOF

echo "✓ Distribution README created: $DIST_README"
echo ""

# Step 8: Display package summary
echo "========================================"
echo "Package Summary"
echo "========================================"
echo ""
echo "Archive: $OUTPUT_DIR/$ARCHIVE_NAME"
echo "Size: $(du -h "$OUTPUT_DIR/$ARCHIVE_NAME" | cut -f1)"
echo "Files: $(tar -tzf "$OUTPUT_DIR/$ARCHIVE_NAME" | wc -l)"
echo ""
echo "Distribution files:"
echo "  - $ARCHIVE_NAME"
echo "  - manifest.txt"
echo "  - README.txt"
echo ""
echo "========================================"
echo "Packaging complete! ✓"
echo "========================================"
echo ""
echo "To distribute, share the files in: $OUTPUT_DIR"
