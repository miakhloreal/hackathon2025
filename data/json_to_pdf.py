#!/usr/bin/env python3
"""
Script to convert cleaned review JSONL files to PDFs for RAG.
Creates one PDF per product with all reviews formatted for easy reading.
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, Any, List
import sys
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Directory paths
CLEAN_DIR = Path("reviews/clean")
PDF_DIR = Path("reviews/pdfs")


def sanitize_filename(name: str) -> str:
    """
    Sanitize product name to create valid filename.
    
    Args:
        name: Product name
        
    Returns:
        Sanitized filename
    """
    # Replace invalid characters with underscores
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        name = name.replace(char, '_')
    
    # Remove leading/trailing spaces and dots
    name = name.strip(' .')
    
    # Limit length to avoid filesystem issues
    if len(name) > 200:
        name = name[:200]
    
    return name


def get_star_rating(rating: int) -> str:
    """
    Convert numeric rating to star visualization.
    
    Args:
        rating: Numeric rating (1-5)
        
    Returns:
        Star string representation
    """
    if rating is None:
        return "No rating"
    
    filled_stars = '★' * int(rating)
    empty_stars = '☆' * (5 - int(rating))
    return f"{filled_stars}{empty_stars} ({rating}/5)"


def get_recommendation_text(is_recommended: Any) -> str:
    """
    Convert recommendation value to readable text.
    
    Args:
        is_recommended: Boolean or None
        
    Returns:
        Readable recommendation text
    """
    if is_recommended is True:
        return "Yes"
    elif is_recommended is False:
        return "No"
    else:
        return "N/A"


def create_pdf_styles():
    """
    Create custom styles for PDF formatting.
    
    Returns:
        Dictionary of custom paragraph styles
    """
    styles = getSampleStyleSheet()
    
    # Title style
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    # Product info style
    product_info_style = ParagraphStyle(
        'ProductInfo',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#444444'),
        spaceAfter=20,
        alignment=TA_CENTER
    )
    
    # Review header style
    review_header_style = ParagraphStyle(
        'ReviewHeader',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=10,
        spaceBefore=20,
        borderWidth=1,
        borderColor=colors.HexColor('#e0e0e0'),
        borderPadding=5
    )
    
    # Review metadata style
    review_meta_style = ParagraphStyle(
        'ReviewMeta',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#666666'),
        spaceAfter=5
    )
    
    # Review title style
    review_title_style = ParagraphStyle(
        'ReviewTitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#34495e'),
        fontName='Helvetica-Bold',
        spaceAfter=8
    )
    
    # Review text style
    review_text_style = ParagraphStyle(
        'ReviewText',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#2c3e50'),
        alignment=TA_JUSTIFY,
        spaceAfter=15,
        leading=14
    )
    
    return {
        'title': title_style,
        'product_info': product_info_style,
        'review_header': review_header_style,
        'review_meta': review_meta_style,
        'review_title': review_title_style,
        'review_text': review_text_style
    }


def create_product_pdf(product_data: Dict[str, Any], reviews: List[Dict[str, Any]], output_path: Path):
    """
    Create PDF for a single product with all its reviews.
    
    Args:
        product_data: Product information (from first review)
        reviews: List of review dictionaries
        output_path: Path to save PDF
    """
    # Create document
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    # Get custom styles
    styles = create_pdf_styles()
    
    # Build content
    story = []
    
    # Add title
    title = Paragraph(f"Product: {product_data['OriginalProductName']}", styles['title'])
    story.append(title)
    
    # Add product ID
    product_info = Paragraph(f"Product ID: {product_data['ProductId']}", styles['product_info'])
    story.append(product_info)
    
    # Add separator
    story.append(Spacer(1, 0.5*inch))
    
    # Add each review
    for idx, review in enumerate(reviews, 1):
        # Review header
        header = Paragraph(f"Review #{idx}", styles['review_header'])
        story.append(header)
        
        # Review metadata table
        meta_data = [
            ['Rating:', get_star_rating(review.get('Rating'))],
            ['Recommended:', get_recommendation_text(review.get('IsRecommended'))],
            ['Source:', review.get('SourceClient', 'N/A')]
        ]
        
        meta_table = Table(meta_data, colWidths=[1.5*inch, 4*inch])
        meta_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#666666')),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#2c3e50')),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(meta_table)
        
        # Review title
        if review.get('Title'):
            title_text = Paragraph(f"<b>Title:</b> {review['Title']}", styles['review_title'])
            story.append(title_text)
        
        # Review text
        if review.get('ReviewText'):
            # Escape special characters for reportlab
            review_text = review['ReviewText'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            text_para = Paragraph(review_text, styles['review_text'])
            story.append(text_para)
        
        # Add spacing between reviews
        story.append(Spacer(1, 0.3*inch))
        
        # Add page break every 3-4 reviews to keep it readable
        if idx % 3 == 0 and idx < len(reviews):
            story.append(PageBreak())
    
    # Build PDF
    doc.build(story)


def process_jsonl_to_pdf(input_path: Path) -> tuple[str, int]:
    """
    Process a single JSONL file and create PDF.
    
    Args:
        input_path: Path to cleaned JSONL file
        
    Returns:
        Tuple of (product_name, review_count) or (None, 0) on error
    """
    reviews = []
    product_data = None
    
    # Read all reviews from JSONL
    with open(input_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            try:
                review = json.loads(line)
                reviews.append(review)
                
                # Get product data from first review
                if product_data is None:
                    product_data = {
                        'ProductId': review.get('ProductId'),
                        'OriginalProductName': review.get('OriginalProductName')
                    }
            except json.JSONDecodeError:
                continue
    
    if not reviews or not product_data or not product_data.get('OriginalProductName'):
        return None, 0
    
    # Create output filename
    safe_filename = sanitize_filename(product_data['OriginalProductName'])
    output_path = PDF_DIR / f"{safe_filename}.pdf"
    
    # Check if PDF already exists
    if output_path.exists():
        return product_data['OriginalProductName'], -1  # -1 indicates skipped
    
    # Create PDF
    create_product_pdf(product_data, reviews, output_path)
    
    return product_data['OriginalProductName'], len(reviews)


def main():
    """Main function to process all cleaned JSONL files to PDFs."""
    print("JSON to PDF Conversion Script")
    print("=" * 50)
    
    # Check if clean directory exists
    if not CLEAN_DIR.exists():
        print(f"Error: Clean directory '{CLEAN_DIR}' not found!")
        print("Please run clean_reviews.py first.")
        sys.exit(1)
    
    # Create PDF directory
    PDF_DIR.mkdir(exist_ok=True)
    print(f"Created/verified PDF directory: {PDF_DIR}")
    print()
    
    # Get all cleaned JSONL files
    jsonl_files = list(CLEAN_DIR.glob("*_clean.jsonl"))
    
    if not jsonl_files:
        print("No cleaned JSONL files found!")
        sys.exit(1)
    
    print(f"Found {len(jsonl_files)} cleaned JSONL files to convert")
    print()
    
    # Process statistics
    total_files = 0
    successful_files = 0
    skipped_files = 0
    total_reviews = 0
    errors = []
    
    # Process each file
    for jsonl_file in jsonl_files:
        print(f"Processing {jsonl_file.name}...", end='', flush=True)
        
        try:
            product_name, review_count = process_jsonl_to_pdf(jsonl_file)
            
            if product_name:
                total_files += 1
                if review_count == -1:
                    skipped_files += 1
                    print(f" ⏭  (skipped - PDF already exists)")
                else:
                    successful_files += 1
                    total_reviews += review_count
                    print(f" ✓ ({review_count} reviews) → {product_name}.pdf")
            else:
                total_files += 1
                errors.append(f"{jsonl_file.name}: No valid product name found")
                print(f" ✗ No valid product name")
                
        except Exception as e:
            total_files += 1
            errors.append(f"{jsonl_file.name}: {str(e)}")
            print(f" ✗ Error: {e}")
    
    # Print summary
    print()
    print("=" * 50)
    print("Summary:")
    print(f"  - Files processed: {total_files}")
    print(f"  - PDFs created: {successful_files}")
    print(f"  - PDFs skipped (already exist): {skipped_files}")
    print(f"  - Total reviews converted: {total_reviews:,}")
    print(f"  - Errors: {len(errors)}")
    print(f"  - Output directory: {PDF_DIR}")
    
    if errors:
        print("\nErrors encountered:")
        for error in errors[:10]:  # Show first 10 errors
            print(f"  - {error}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more errors")
    
    print("\nPDF conversion complete!")


if __name__ == "__main__":
    main()