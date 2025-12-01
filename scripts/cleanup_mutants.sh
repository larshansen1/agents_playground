#!/bin/bash
# Script to clean up mutation testing artifacts

echo "Cleaning up mutation testing artifacts..."

# Remove mutation testing directories
rm -rf mutants/
echo "✓ Removed mutants/ directory"

# Remove mutation testing log files
rm -f mutmut.log mutmut_export.json mutmut_summary.json surviving_mutants.json mutant_categories.json
echo "✓ Removed mutation testing logs and JSON files"

# Remove mutation testing scripts (now in scripts/ directory instead)
rm -f categorize_survivors.py export_for_ai.py extract_mutants.py
echo "✓ Removed mutation testing scripts from root"

# Remove temporary development files
rm -f debug_mock.py test_search.py test_tool.py
echo "✓ Removed temporary development files"

# Remove old fix documentation
rm -f fix_tests_*.md
echo "✓ Removed old fix documentation"

echo ""
echo "Cleanup complete! All mutation testing artifacts removed."
echo "These files are now in .gitignore and won't be committed."
