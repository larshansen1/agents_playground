OUTPUT="ALL_DOCS.md"

# Truncate first
echo "" > "$OUTPUT"

# Find all MD files **excluding** README and the output file and heavy dirs
find . -type f -name "*.md" \
    ! -path "./README.md" \
    ! -path "./$OUTPUT" \
    -not -path "*/.git/*" \
    -not -path "*/node_modules/*" \
    -not -path "*/venv/*" \
    | sort \
    | while IFS= read -r file; do
        echo "# $file" >> "$OUTPUT"
        echo "" >> "$OUTPUT"
        cat "$file" >> "$OUTPUT"
        echo -e "\n\n" >> "$OUTPUT"
    done
