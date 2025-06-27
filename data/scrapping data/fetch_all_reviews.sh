#!/bin/bash

# Script to fetch reviews for all products in products.jsonl
# Creates separate files for each product: productID.jsonl
# Usage: ./fetch_all_reviews.sh PASSKEY [products_file] [output_directory]

set -euo pipefail

PASSKEY="${1:-}"
PRODUCTS_FILE="${2:-products.jsonl}"
OUTPUT_DIR="${3:-reviews}"

if [[ -z "$PASSKEY" ]]; then
    echo "Usage: $0 PASSKEY [products_file] [output_directory]" >&2
    echo "Example: $0 caWJuNyYsn660UOOYFJFZgtXmIgCfxu0iqSHOj0GCAUIo products.jsonl reviews" >&2
    echo "This will create files like: reviews/ASK09.jsonl, reviews/ASK10.jsonl, etc." >&2
    exit 1
fi

if [[ ! -f "$PRODUCTS_FILE" ]]; then
    echo "Error: Products file '$PRODUCTS_FILE' not found" >&2
    exit 1
fi

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Extract product IDs
echo "Extracting product IDs from $PRODUCTS_FILE..." >&2
PRODUCT_IDS=($(jq -r '.id' "$PRODUCTS_FILE"))
TOTAL=${#PRODUCT_IDS[@]}

echo "Found $TOTAL products. Starting review extraction to directory: $OUTPUT_DIR" >&2

# Track progress
SUCCESS_COUNT=0
ERROR_COUNT=0
REVIEW_COUNT=0
FILES_CREATED=0

for i in "${!PRODUCT_IDS[@]}"; do
    PRODUCT_ID="${PRODUCT_IDS[$i]}"
    CURRENT=$((i + 1))
    OUTPUT_FILE="$OUTPUT_DIR/${PRODUCT_ID}.jsonl"
    
    echo "[$CURRENT/$TOTAL] Processing product: $PRODUCT_ID" >&2
    
    # Fetch reviews for this product directly to its file
    if bvdl reviews "$PASSKEY" --product-id "$PRODUCT_ID" > "$OUTPUT_FILE" 2>/dev/null; then
        # Count reviews fetched
        PRODUCT_REVIEW_COUNT=$(wc -l < "$OUTPUT_FILE")
        if [[ $PRODUCT_REVIEW_COUNT -gt 0 ]]; then
            REVIEW_COUNT=$((REVIEW_COUNT + PRODUCT_REVIEW_COUNT))
            FILES_CREATED=$((FILES_CREATED + 1))
            echo "  ✓ Found $PRODUCT_REVIEW_COUNT reviews → $OUTPUT_FILE" >&2
        else
            echo "  - No reviews found" >&2
            # Remove empty file
            rm -f "$OUTPUT_FILE"
        fi
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    else
        echo "  ✗ Error fetching reviews" >&2
        ERROR_COUNT=$((ERROR_COUNT + 1))
        # Remove any partial file
        rm -f "$OUTPUT_FILE"
    fi
    
    # Add small delay to be respectful to the API
    sleep 0.1
done

echo "" >&2
echo "Summary:" >&2
echo "  Products processed: $TOTAL" >&2
echo "  Successful: $SUCCESS_COUNT" >&2
echo "  Errors: $ERROR_COUNT" >&2
echo "  Total reviews extracted: $REVIEW_COUNT" >&2
echo "  Review files created: $FILES_CREATED" >&2
echo "  Files saved in directory: $OUTPUT_DIR" >&2