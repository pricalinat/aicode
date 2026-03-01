"""
Paper Knowledge Base - 优化版分析器
Improved Analyzer with Better Metadata Extraction
"""

import json
import sqlite3
import subprocess
import re
from pathlib import Path
import os

DB_PATH = "/Users/rrp/Documents/aicode/knowledge_base/data/papers.db"

def extract_metadata_from_filename(file_path):
    """从文件名提取元数据"""
    filename = os.path.basename(file_path)
    name_without_ext = os.path.splitext(filename)[0]
    
    # 尝试匹配arXiv ID
    arxiv_pattern = r'(\d{4}\.\d{4,5})'
    match = re.search(arxiv_pattern, name_without_ext)
    if match:
        return {'arxiv_id': match.group(1)}
    
    return {}

def get_arxiv_metadata(arxiv_id):
    """从arXiv API获取元数据"""
    try:
        cmd = ['curl', '-s', f'http://export.arxiv.org/api/query?id_list={arxiv_id}']
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(result.stdout)
            
            for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
                title = entry.find('{http://www.w3.org/2005/Atom}title').text.strip()
                authors = [a.find('{http://www.w3.org/2005/Atom}name').text 
                          for a in entry.findall('{http://www.w3.org/2005/Atom}author')]
                published = entry.find('{http://www.w3.org/2005/Atom}published').text
                year = int(published[:4])
                
                categories = [c.text for c in entry.findall(
                    '{http://www.w3.org/2005/Atom}category')]
                
                return {
                    'title': title,
                    'authors': authors[:5],
                    'year': year,
                    'venue': 'arXiv',
                    'keywords': categories[:5]
                }
    except Exception as e:
        print(f"Error: {e}")
    
    return None

def update_paper_metadata(conn, paper_id, metadata):
    """更新论文元数据"""
    c = conn.cursor()
    c.execute('''
        UPDATE papers 
        SET title = ?, authors = ?, year = ?, venue = ?, keywords = ?
        WHERE paper_id = ?
    ''', (
        metadata.get('title'),
        json.dumps(metadata.get('authors', [])),
        metadata.get('year'),
        metadata.get('venue'),
        json.dumps(metadata.get('keywords', [])),
        paper_id
    ))
    conn.commit()

def improve_metadata_extraction():
    """改进所有论文的元数据提取"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('SELECT paper_id, file_path, title FROM papers')
    papers = c.fetchall()
    
    print(f"开始优化 {len(papers)} 篇论文的元数据...")
    
    updated = 0
    for paper_id, file_path, title in papers:
        meta_from_file = extract_metadata_from_filename(file_path)
        arxiv_id = meta_from_file.get('arxiv_id')
        
        if arxiv_id:
            arxiv_meta = get_arxiv_metadata(arxiv_id)
            
            if arxiv_meta:
                update_paper_metadata(conn, paper_id, arxiv_meta)
                updated += 1
                print(f"  更新: {arxiv_meta.get('title', '')[:50]}")
    
    print(f"\n更新了 {updated} 篇论文的元数据")
    conn.close()

if __name__ == '__main__':
    improve_metadata_extraction()
