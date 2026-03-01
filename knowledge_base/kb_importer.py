"""
Paper Knowledge Base - Importer
Scans paper directories and imports metadata into the database
"""

import os
import re
import json
import sqlite3
from pathlib import Path
from kb_schema import init_db, insert_paper, DB_PATH

PAPER_DIRS = {
    'product_matching': '/Users/rrp/Documents/aicode/data/papers/product_matching/',
    'ecommerce_evaluation': '/Users/rrp/Documents/aicode/data/papers/ecommerce_evaluation/',
    'mini_program_service': '/Users/rrp/Documents/aicode/data/papers/mini_program_service/',
}

def extract_arxiv_id(filename):
    """Extract arxiv ID from filename like '1409.2944_collaborative_deep_learning.pdf'"""
    match = re.match(r'^(\d{4}\.\d{4,5})', filename)
    if match:
        return match.group(1)
    return None

def extract_title_from_filename(filename):
    """Extract title from filename"""
    # Remove .pdf and arxiv ID prefix
    name = re.sub(r'^\d{4}\.\d{4,5}_', '', filename.replace('.pdf', ''))
    # Replace underscores with spaces
    name = name.replace('_', ' ')
    # Capitalize
    return name.title()

def scan_papers():
    """Scan all paper directories and return paper metadata"""
    papers = []
    
    for category, dir_path in PAPER_DIRS.items():
        if not os.path.exists(dir_path):
            print(f"Warning: Directory not found: {dir_path}")
            continue
            
        for filename in os.listdir(dir_path):
            if not filename.endswith('.pdf'):
                continue
                
            file_path = os.path.join(dir_path, filename)
            arxiv_id = extract_arxiv_id(filename)
            title = extract_title_from_filename(filename)
            
            # Extract year from arxiv ID if available
            year = None
            if arxiv_id:
                year = int('20' + arxiv_id[:2]) if arxiv_id.startswith('1') or arxiv_id.startswith('2') else None
            
            paper = {
                'paper_id': arxiv_id or filename.replace('.pdf', ''),
                'title': title,
                'authors': [],
                'year': year,
                'venue': 'arXiv' if arxiv_id else 'Unknown',
                'arxiv_id': arxiv_id,
                'file_path': file_path,
                'category': category,
                'keywords': [],
                'abstract': ''
            }
            papers.append(paper)
    
    return papers

def import_all_papers():
    """Import all papers from directories into database"""
    conn = init_db()
    papers = scan_papers()
    
    imported = 0
    for paper in papers:
        insert_paper(conn, paper)
        imported += 1
    
    print(f"Imported {imported} papers into database")
    return papers

if __name__ == '__main__':
    papers = import_all_papers()
    print(f"\nTotal papers found:")
    for category, dir_path in PAPER_DIRS.items():
        count = len([p for p in papers if p['category'] == category])
        print(f"  {category}: {count}")
