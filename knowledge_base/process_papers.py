#!/usr/bin/env python3
"""
Process papers: summarize each paper and extract analysis
"""

import os
import sys
import json
import sqlite3
import subprocess
import time
from pathlib import Path
from datetime import datetime

# Configuration
PAPERS_DIR = Path('/Users/rrp/Documents/aicode/data/papers')
KB_DIR = Path('/Users/rrp/Documents/aicode/knowledge_base')
DB_PATH = KB_DIR / 'data' / 'papers.db'
ANALYSIS_DIR = KB_DIR / 'analysis'

# Ensure directories exist
ANALYSIS_DIR.mkdir(exist_ok=True)

def get_connection():
    return sqlite3.connect(DB_PATH)

def get_pending_papers(limit=None):
    """Get papers that haven't been analyzed yet"""
    conn = get_connection()
    c = conn.cursor()
    
    # Get papers without analysis
    query = '''SELECT p.paper_id, p.title, p.file_path, p.category, p.year
               FROM papers p 
               LEFT JOIN analysis a ON p.paper_id = a.paper_id 
               WHERE a.paper_id IS NULL'''
    
    if limit:
        query += f' LIMIT {limit}'
    
    c.execute(query)
    results = c.fetchall()
    conn.close()
    return results

def summarize_paper(file_path):
    """Summarize a single paper"""
    try:
        cmd = ['summarize', file_path, '--length', 'long', '--json']
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return {
                'success': True,
                'summary': data.get('summary', ''),
                'llm': data.get('llm', {})
            }
        else:
            return {
                'success': False,
                'error': result.stderr[:200]
            }
    except subprocess.TimeoutExpired:
        return {'success': False, 'error': 'Timeout'}
    except json.JSONDecodeError as e:
        return {'success': False, 'error': f'JSON error: {str(e)[:100]}'}
    except Exception as e:
        return {'success': False, 'error': str(e)[:200]}

def save_analysis(paper_id, analysis_data):
    """Save analysis to file"""
    output_file = ANALYSIS_DIR / f'{paper_id}.json'
    with open(output_file, 'w') as f:
        json.dump(analysis_data, f, indent=2, ensure_ascii=False)

def insert_analysis_to_db(paper_id, analysis_data):
    """Insert analysis into database"""
    conn = get_connection()
    c = conn.cursor()
    
    # Extract structured data from analysis
    summary = analysis_data.get('summary', '')
    
    # Simple extraction - in production would use LLM for this
    analysis = {
        'paper_id': paper_id,
        'novelty': extract_novelty(summary),
        'method': extract_method(summary),
        'architecture': extract_architecture(summary),
        'datasets': extract_datasets(summary),
        'metrics': extract_metrics(summary),
        'results': extract_results(summary),
        'baselines': extract_baselines(summary),
        'conclusions': extract_conclusions(summary),
        'limitations': '需要进一步分析'  # Placeholder
    }
    
    c.execute('''INSERT OR REPLACE INTO analysis 
        (paper_id, novelty, method, architecture, datasets, metrics, results, baselines, conclusions, limitations)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (analysis['paper_id'], analysis['novelty'], analysis['method'], 
         analysis['architecture'], json.dumps(analysis['datasets']),
         json.dumps(analysis['metrics']), json.dumps(analysis['results']),
         json.dumps(analysis['baselines']), analysis['conclusions'],
         analysis['limitations']))
    
    conn.commit()
    conn.close()
    return analysis

# Simple extraction functions (would be replaced with LLM in production)
def extract_novelty(summary):
    if not summary:
        return "需要分析"
    # Look for key phrases indicating novelty
    if 'propose' in summary.lower() or 'introduce' in summary.lower() or 'present' in summary.lower():
        lines = summary.split('\n')
        for line in lines[:5]:
            if any(kw in line.lower() for kw in ['propose', 'introduce', 'present', 'novel', 'new']):
                return line.strip()[:200]
    return summary[:200] if summary else "需要分析"

def extract_method(summary):
    if not summary:
        return "需要分析"
    # Extract method-related content
    if 'method' in summary.lower() or 'approach' in summary.lower():
        lines = summary.split('\n')
        for line in lines:
            if any(kw in line.lower() for kw in ['method', 'approach', 'model', 'framework']):
                return line.strip()[:300]
    return summary[200:600] if len(summary) > 200 else summary

def extract_architecture(summary):
    return "见方法描述"

def extract_datasets(summary):
    # Look for common dataset names
    datasets = []
    common_ds = ['amazon', 'yelp', 'movielens', 'netflix', 'citeulike', 
                 'booking', 'taobao', 'alibaba', 'jd', 'tmall', 'steam',
                 'steam', 'goodreads', 'lastfm', 'spotify']
    summary_lower = summary.lower()
    for ds in common_ds:
        if ds in summary_lower:
            datasets.append(ds.title())
    return list(set(datasets))[:5]

def extract_metrics(summary):
    metrics = []
    common_metrics = ['precision', 'recall', 'f1', 'ndcg', 'hit rate', 
                      'accuracy', 'auc', 'rmse', 'mae', 'mrr', 'map',
                      'conversion', 'ctr', 'cvr', 'rpm', 'engagement']
    summary_lower = summary.lower()
    for m in common_metrics:
        if m in summary_lower:
            metrics.append(m.upper())
    return list(set(metrics))[:5]

def extract_results(summary):
    # Look for percentage improvements
    import re
    results = {}
    percentages = re.findall(r'(\w+)\s+(?:improved?|increased?|decreased?|boosted?)\s+by\s+(\d+(?:\.\d+)?)%', summary.lower())
    for metric, value in percentages[:5]:
        results[metric] = f"+{value}%"
    return results

def extract_baselines(summary):
    baselines = []
    baseline_methods = ['bert', 'gpt', 'gcn', 'gat', 'sage', 'fm', 'dfm',
                       'wide&deep', 'deepfm', 'dcn', 'ngcf', 'lightgcn',
                       'bpr', 'mf', 'svd', 'neumf', 'autoint']
    summary_lower = summary.lower()
    for bl in baseline_methods:
        if bl in summary_lower:
            baselines.append(bl.upper())
    return list(set(baselines))[:5]

def extract_conclusions(summary):
    if not summary:
        return "需要分析"
    if 'conclusion' in summary.lower():
        lines = summary.split('\n')
        for i, line in enumerate(lines):
            if 'conclusion' in line.lower():
                if i + 1 < len(lines):
                    return lines[i+1].strip()[:300]
    return summary[-300:] if len(summary) > 300 else summary

def process_papers(start=0, batch_size=50):
    """Process papers in batches"""
    pending = get_pending_papers()
    total = len(pending)
    
    print(f"Total pending papers: {total}")
    print(f"Processing from index {start}, batch size {batch_size}")
    
    papers_to_process = pending[start:start+batch_size]
    
    success_count = 0
    error_count = 0
    
    for i, (paper_id, title, file_path, category, year) in enumerate(papers_to_process):
        print(f"[{start+i+1}/{total}] Processing: {paper_id} - {title[:40]}...")
        
        # Check if file exists
        if not os.path.exists(file_path):
            print(f"  ✗ File not found: {file_path}")
            error_count += 1
            continue
        
        # Summarize paper
        result = summarize_paper(file_path)
        
        if result['success']:
            # Save raw analysis
            analysis_data = {
                'paper_id': paper_id,
                'title': title,
                'category': category,
                'year': year,
                'timestamp': datetime.now().isoformat(),
                'summary': result['summary'],
                'llm_info': result.get('llm', {})
            }
            
            # Save to file
            save_analysis(paper_id, analysis_data)
            
            # Insert structured analysis to DB
            try:
                insert_analysis_to_db(paper_id, analysis_data)
                print(f"  ✓ Success")
                success_count += 1
            except Exception as e:
                print(f"  ✗ DB error: {e}")
                error_count += 1
        else:
            print(f"  ✗ Summarize error: {result.get('error', 'unknown')}")
            error_count += 1
        
        # Small delay to avoid rate limiting
        time.sleep(0.5)
    
    print(f"\n=== Summary ===")
    print(f"Processed: {success_count}")
    print(f"Errors: {error_count}")
    print(f"Next start index: {start + batch_size}")
    
    return success_count, error_count

if __name__ == '__main__':
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    batch_size = int(sys.argv[2]) if len(sys.argv) > 2 else 50
    
    process_papers(start, batch_size)
