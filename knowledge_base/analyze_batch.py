#!/usr/bin/env python3
"""
Batch analyzer for papers - processes papers with summarize and saves results
"""

import os
import json
import sqlite3
import subprocess
import time
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
import argparse

DB_PATH = Path(__file__).parent / "data" / "papers.db"
ANALYSIS_DIR = Path(__file__).parent / "analysis"

def init_analysis_dir():
    """Initialize analysis output directory"""
    ANALYSIS_DIR.mkdir(exist_ok=True)

def get_pending_papers():
    """Get papers that haven't been analyzed yet"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT p.paper_id, p.title, p.file_path, p.category 
                FROM papers p 
                LEFT JOIN analysis a ON p.paper_id = a.paper_id 
                WHERE a.paper_id IS NULL''')
    results = c.fetchall()
    conn.close()
    return results

def analyze_single_paper(paper_info):
    """Analyze a single paper using summarize"""
    paper_id, title, file_path, category = paper_info
    
    # Skip if file doesn't exist
    if not os.path.exists(file_path):
        return {'paper_id': paper_id, 'status': 'error', 'error': 'File not found'}
    
    try:
        # Run summarize command
        cmd = ['summarize', file_path, '--length', 'long', '--json']
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            return {'paper_id': paper_id, 'status': 'error', 'error': result.stderr[:200]}
        
        # Parse JSON output
        summary_data = json.loads(result.stdout)
        
        return {
            'paper_id': paper_id,
            'title': title,
            'category': category,
            'status': 'success',
            'summary': summary_data.get('summary', ''),
            'file_path': file_path
        }
    except subprocess.TimeoutExpired:
        return {'paper_id': paper_id, 'status': 'error', 'error': 'Timeout'}
    except json.JSONDecodeError:
        return {'paper_id': paper_id, 'status': 'error', 'error': 'JSON parse error'}
    except Exception as e:
        return {'paper_id': paper_id, 'status': 'error', 'error': str(e)[:200]}

def save_analysis_result(result):
    """Save analysis result to file"""
    output_file = ANALYSIS_DIR / f"{result['paper_id']}.json"
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

def process_batch(batch_size=20, max_workers=4):
    """Process papers in batch"""
    init_analysis_dir()
    
    pending = get_pending_papers()
    print(f"Pending papers to analyze: {len(pending)}")
    
    if not pending:
        print("No pending papers!")
        return
    
    processed = 0
    errors = 0
    
    # Process in batches
    for i in range(0, len(pending), batch_size):
        batch = pending[i:i+batch_size]
        print(f"\nProcessing batch {i//batch_size + 1}: papers {i+1}-{min(i+batch_size, len(pending))}")
        
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(analyze_single_paper, p): p for p in batch}
            
            for future in as_completed(futures):
                result = future.result()
                save_analysis_result(result)
                
                if result['status'] == 'success':
                    processed += 1
                    print(f"  ✓ {result['paper_id'][:20]}...")
                else:
                    errors += 1
                    print(f"  ✗ {result['paper_id'][:20]}: {result.get('error', 'unknown')[:50]}")
        
        # Small delay between batches
        time.sleep(1)
    
    print(f"\n=== Summary ===")
    print(f"Processed: {processed}")
    print(f"Errors: {errors}")
    print(f"Results saved to: {ANALYSIS_DIR}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--batch-size', type=int, default=20)
    parser.add_argument('--workers', type=int, default=4)
    args = parser.parse_args()
    
    process_batch(args.batch_size, args.workers)
