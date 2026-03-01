"""
Paper Knowledge Base Schema
SQLite database for storing paper metadata and analysis
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "papers.db"

def init_db():
    """Initialize database with schema"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Papers metadata table
    c.execute('''CREATE TABLE IF NOT EXISTS papers (
        paper_id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        authors TEXT,
        year INTEGER,
        venue TEXT,
        arxiv_id TEXT,
        file_path TEXT NOT NULL,
        category TEXT,
        keywords TEXT,
        abstract TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Paper analysis table
    c.execute('''CREATE TABLE IF NOT EXISTS analysis (
        paper_id TEXT PRIMARY KEY,
        novelty TEXT,
        method TEXT,
        architecture TEXT,
        datasets TEXT,
        metrics TEXT,
        results TEXT,
        baselines TEXT,
        conclusions TEXT,
        limitations TEXT,
        related_work TEXT,
        FOREIGN KEY (paper_id) REFERENCES papers(paper_id)
    )''')
    
    # Topics table
    c.execute('''CREATE TABLE IF NOT EXISTS topics (
        topic_id INTEGER PRIMARY KEY AUTOINCREMENT,
        topic_name TEXT UNIQUE NOT NULL,
        description TEXT,
        chapter_id INTEGER
    )''')
    
    # Chapter references table
    c.execute('''CREATE TABLE IF NOT EXISTS chapter_references (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chapter_id INTEGER,
        chapter_title TEXT,
        paper_id TEXT,
        usage TEXT,
        quote TEXT,
        FOREIGN KEY (paper_id) REFERENCES papers(paper_id)
    )''')
    
    # Paper-Topic mapping
    c.execute('''CREATE TABLE IF NOT EXISTS paper_topics (
        paper_id TEXT,
        topic_id INTEGER,
        FOREIGN KEY (paper_id) REFERENCES papers(paper_id),
        FOREIGN KEY (topic_id) REFERENCES topics(topic_id)
    )''')
    
    conn.commit()
    return conn

def insert_paper(conn, paper_data):
    """Insert paper metadata"""
    c = conn.cursor()
    c.execute('''INSERT OR REPLACE INTO papers 
        (paper_id, title, authors, year, venue, arxiv_id, file_path, category, keywords, abstract)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (
            paper_data.get('paper_id'),
            paper_data.get('title'),
            json.dumps(paper_data.get('authors', [])),
            paper_data.get('year'),
            paper_data.get('venue'),
            paper_data.get('arxiv_id'),
            paper_data.get('file_path'),
            paper_data.get('category'),
            json.dumps(paper_data.get('keywords', [])),
            paper_data.get('abstract')
        ))
    conn.commit()

def insert_analysis(conn, paper_id, analysis_data):
    """Insert paper analysis"""
    c = conn.cursor()
    c.execute('''INSERT OR REPLACE INTO analysis 
        (paper_id, novelty, method, architecture, datasets, metrics, results, baselines, conclusions, limitations, related_work)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (
            paper_id,
            analysis_data.get('novelty'),
            analysis_data.get('method'),
            analysis_data.get('architecture'),
            json.dumps(analysis_data.get('datasets', [])),
            json.dumps(analysis_data.get('metrics', [])),
            json.dumps(analysis_data.get('results', {})),
            json.dumps(analysis_data.get('baselines', [])),
            analysis_data.get('conclusions'),
            analysis_data.get('limitations'),
            json.dumps(analysis_data.get('related_work', []))
        ))
    conn.commit()

def get_paper(conn, paper_id):
    """Get paper with analysis"""
    c = conn.cursor()
    c.execute('''SELECT p.*, a.novelty, a.method, a.architecture, a.datasets, 
        a.metrics, a.results, a.baselines, a.conclusions, a.limitations, a.related_work
        FROM papers p LEFT JOIN analysis a ON p.paper_id = a.paper_id
        WHERE p.paper_id = ?''', (paper_id,))
    return c.fetchone()

def query_by_topic(conn, topic_name):
    """Query papers by topic"""
    c = conn.cursor()
    c.execute('''SELECT p.* FROM papers p
        JOIN paper_topics pt ON p.paper_id = pt.paper_id
        JOIN topics t ON pt.topic_id = t.topic_id
        WHERE t.topic_name = ?''', (topic_name,))
    return c.fetchall()

def query_by_category(conn, category):
    """Query papers by category"""
    c = conn.cursor()
    c.execute('SELECT * FROM papers WHERE category = ?', (category,))
    return c.fetchall()

def query_by_method(conn, method_keyword):
    """Query papers by method keyword in analysis"""
    c = conn.cursor()
    c.execute('''SELECT p.*, a.method FROM papers p
        JOIN analysis a ON p.paper_id = a.paper_id
        WHERE a.method LIKE ?''', (f'%{method_keyword}%',))
    return c.fetchall()

def get_chapter_references(conn, chapter_id):
    """Get all references for a chapter"""
    c = conn.cursor()
    c.execute('''SELECT p.title, p.authors, p.year, cr.usage, cr.quote
        FROM chapter_references cr
        JOIN papers p ON cr.paper_id = p.paper_id
        WHERE cr.chapter_id = ?''', (chapter_id,))
    return c.fetchall()

def get_all_papers(conn):
    """Get all papers"""
    c = conn.cursor()
    c.execute('SELECT paper_id, title, category FROM papers')
    return c.fetchall()

def get_statistics(conn):
    """Get database statistics"""
    c = conn.cursor()
    stats = {}
    c.execute('SELECT category, COUNT(*) FROM papers GROUP BY category')
    stats['by_category'] = c.fetchall()
    c.execute('SELECT COUNT(*) FROM papers')
    stats['total_papers'] = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM analysis')
    stats['analyzed_papers'] = c.fetchone()[0]
    return stats

if __name__ == '__main__':
    conn = init_db()
    print(f"Database initialized at {DB_PATH}")
    stats = get_statistics(conn)
    print(f"Statistics: {stats}")
