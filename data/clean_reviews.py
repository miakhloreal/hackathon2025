#!/usr/bin/env python3
"""
Script to clean review JSONL files by keeping only specified fields.
Creates cleaned versions in a 'clean' subdirectory with '_clean.jsonl' suffix.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
import sys

# Fields to keep in the cleaned data
FIELDS_TO_KEEP = [
    "ProductId",
    "OriginalProductName",
    "Rating",
    "IsRecommended",
    "ReviewText",
    "Title",
    "SourceClient"
]

# Directory paths
REVIEWS_DIR = Path("reviews")
CLEAN_DIR = REVIEWS_DIR / "clean"


def clean_review_object(review: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract only the required fields from a review object.
    
    Args:
        review: Original review dictionary
        
    Returns:
        Dictionary containing only the required fields
    """
    cleaned_review = {}
    for field in FIELDS_TO_KEEP:
        # Use None for missing fields
        cleaned_review[field] = review.get(field, None)
    return cleaned_review


def process_jsonl_file(input_path: Path, output_path: Path) -> tuple[int, int]:
    """
    Process a single JSONL file, cleaning each review.
    
    Args:
        input_path: Path to input JSONL file
        output_path: Path to output cleaned JSONL file
        
    Returns:
        Tuple of (reviews_processed, errors_count)
    """
    reviews_processed = 0
    errors_count = 0
    
    with open(input_path, 'r', encoding='utf-8') as infile, \
         open(output_path, 'w', encoding='utf-8') as outfile:
        
        for line_num, line in enumerate(infile, 1):
            try:
                # Skip empty lines
                line = line.strip()
                if not line:
                    continue
                
                # Parse JSON
                review = json.loads(line)
                
                # Clean the review
                cleaned_review = clean_review_object(review)
                
                # Write cleaned review
                json.dump(cleaned_review, outfile, ensure_ascii=False)
                outfile.write('\n')
                
                reviews_processed += 1
                
            except json.JSONDecodeError as e:
                print(f"  Warning: JSON error in {input_path.name} line {line_num}: {e}")
                errors_count += 1
            except Exception as e:
                print(f"  Warning: Unexpected error in {input_path.name} line {line_num}: {e}")
                errors_count += 1
    
    return reviews_processed, errors_count


def main():
    """Main function to process all JSONL files in the reviews directory."""
    print("Review Files Cleanup Script")
    print("=" * 50)
    
    # Check if reviews directory exists
    if not REVIEWS_DIR.exists():
        print(f"Error: Reviews directory '{REVIEWS_DIR}' not found!")
        sys.exit(1)
    
    # Create clean subdirectory
    CLEAN_DIR.mkdir(exist_ok=True)
    print(f"Created/verified clean directory: {CLEAN_DIR}")
    print()
    
    # Get all JSONL files
    jsonl_files = list(REVIEWS_DIR.glob("*.jsonl"))
    
    if not jsonl_files:
        print("No JSONL files found in reviews directory!")
        sys.exit(1)
    
    print(f"Found {len(jsonl_files)} JSONL files to process")
    print()
    
    # Process statistics
    total_files = 0
    total_reviews = 0
    total_errors = 0
    successful_files = 0
    
    # Process each file
    for jsonl_file in jsonl_files:
        # Create output filename
        output_filename = f"{jsonl_file.stem}_clean.jsonl"
        output_path = CLEAN_DIR / output_filename
        
        print(f"Processing {jsonl_file.name}...", end='', flush=True)
        
        try:
            reviews_count, errors_count = process_jsonl_file(jsonl_file, output_path)
            
            total_files += 1
            total_reviews += reviews_count
            total_errors += errors_count
            
            if errors_count == 0:
                successful_files += 1
                print(f" ✓ ({reviews_count} reviews)")
            else:
                print(f" ⚠ ({reviews_count} reviews, {errors_count} errors)")
                
        except Exception as e:
            print(f" ✗ Failed: {e}")
            total_files += 1
    
    # Print summary
    print()
    print("=" * 50)
    print("Summary:")
    print(f"  - Files processed: {total_files}")
    print(f"  - Files successful: {successful_files}")
    print(f"  - Total reviews cleaned: {total_reviews:,}")
    print(f"  - Total errors: {total_errors}")
    print(f"  - Output directory: {CLEAN_DIR}")
    
    if total_errors > 0:
        print("\nNote: Some reviews had errors. Check warnings above for details.")
    
    print("\nCleanup complete!")


if __name__ == "__main__":
    main()