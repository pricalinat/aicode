"""
Citation Generator - Generate citations and chapter references
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / "data" / "papers.db"
OUTPUT_DIR = Path(__file__).parent / "citations"

def get_connection():
    return sqlite3.connect(DB_PATH)

def generate_citation(paper_id, style="academic"):
    """Generate a citation for a paper"""
    conn = get_connection()
    c = conn.cursor()
    
    c.execute('''SELECT title, authors, year, venue, arxiv_id 
                 FROM papers WHERE paper_id = ?''', (paper_id,))
    row = c.fetchone()
    conn.close()
    
    if not row:
        return None
    
    title, authors_json, year, venue, arxiv_id = row
    authors = json.loads(authors_json) if authors_json else []
    
    if style == "academic":
        # Format: (Author et al., Year)
        if authors:
            author_str = f"{authors[0]} et al."
        else:
            author_str = "Unknown"
        return f"({author_str}, {year})"
    elif style == "bibtex":
        # Format: @article{paper_id, ...}
        author_str = " and ".join(authors) if authors else "Unknown"
        return f"""@article{{{paper_id},
  title={{{title}}},
  author={{{author_str}}},
  year={{{year}}},
  venue={{{venue}}}
}}"""
    else:
        # Simple format
        return f"{title} ({year})"

def generate_chapter_references(chapter_id, topic_name):
    """Generate references for a specific chapter/topic"""
    conn = get_connection()
    c = conn.cursor()
    
    # Get topic ID
    c.execute('SELECT topic_id FROM topics WHERE topic_name = ?', (topic_name,))
    row = c.fetchone()
    
    if not row:
        conn.close()
        return []
    
    topic_id = row[0]
    
    # Get papers for this topic
    c.execute('''SELECT p.paper_id, p.title, p.authors, p.year, 
                 a.novelty, a.conclusions, a.limitations
                 FROM papers p
                 JOIN paper_topics pt ON p.paper_id = pt.paper_id
                 LEFT JOIN analysis a ON p.paper_id = a.paper_id
                 WHERE pt.topic_id = ?
                 ORDER BY p.year DESC''', (topic_id,))
    
    papers = c.fetchall()
    conn.close()
    
    references = []
    for paper in papers:
        paper_id, title, authors_json, year, novelty, conclusions, limitations = paper
        authors = json.loads(authors_json) if authors_json else []
        
        ref = {
            'paper_id': paper_id,
            'title': title,
            'authors': authors,
            'year': year,
            'citation': generate_citation(paper_id),
            'novelty': novelty,
            'conclusions': conclusions,
            'limitations': limitations
        }
        references.append(ref)
    
    return references

def generate_markdown_references(chapter_id, topic_name):
    """Generate markdown formatted references"""
    references = generate_chapter_references(chapter_id, topic_name)
    
    if not references:
        return f"## 第{chapter_id}章 - {topic_name}\n\n暂无引用"
    
    md = f"## 第{chapter_id}章 - {topic_name}\n\n"
    md += f"共 {len(references)} 篇参考文献\n\n"
    
    for i, ref in enumerate(references, 1):
        md += f"### {i}. {ref['title']}\n"
        md += f"**引用**: {ref['citation']}\n"
        md += f"**作者**: {', '.join(ref['authors']) if ref['authors'] else 'Unknown'}\n"
        md += f"**年份**: {ref['year']}\n"
        
        if ref.get('novelty'):
            md += f"\n**创新点**: {ref['novelty'][:200]}...\n"
        
        if ref.get('conclusions'):
            md += f"\n**结论**: {ref['conclusions'][:200]}...\n"
        
        if ref.get('limitations'):
            md += f"\n**局限性**: {ref['limitations'][:200]}...\n"
        
        md += "\n---\n\n"
    
    return md

def export_all_chapters():
    """Export all chapter references to markdown files"""
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    chapters = {
        1: ("绪论", "introduction"),
        2: ("技术演进", "tech_evolution"),
        3: ("知识图谱", "knowledge_graph"),
        4: ("商品理解", "product_understanding"),
        5: ("服务理解", "service_understanding"),
        6: ("搜索推荐", "search_recommendation"),
        7: ("LLM评测", "llm_evaluation"),
        8: ("电商评测", "ecommerce_evaluation"),
    }
    
    for chapter_id, (title, topic) in chapters.items():
        md = generate_markdown_references(chapter_id, topic)
        
        output_file = OUTPUT_DIR / f"chapter_{chapter_id}_{topic}.md"
        with open(output_file, 'w') as f:
            f.write(md)
        
        print(f"Generated: {output_file}")

def get_statistics():
    """Get overall statistics"""
    conn = get_connection()
    c = conn.cursor()
    
    stats = {}
    
    # Total papers
    c.execute('SELECT COUNT(*) FROM papers')
    stats['total_papers'] = c.fetchone()[0]
    
    # Papers with analysis
    c.execute('SELECT COUNT(*) FROM analysis')
    stats['analyzed_papers'] = c.fetchone()[0]
    
    # Papers by category
    c.execute('SELECT category, COUNT(*) FROM papers GROUP BY category')
    stats['by_category'] = dict(c.fetchall())
    
    # Papers by topic
    c.execute('''SELECT t.topic_name, COUNT(pt.paper_id) 
                 FROM topics t LEFT JOIN paper_topics pt ON t.topic_id = pt.topic_id
                 GROUP BY t.topic_id''')
    stats['by_topic'] = dict(c.fetchall())
    
    conn.close()
    return stats

if __name__ == '__main__':
    stats = get_statistics()
    print("=== Knowledge Base Statistics ===")
    print(f"Total papers: {stats['total_papers']}")
    print(f"Analyzed papers: {stats['analyzed_papers']}")
    print(f"\nBy category:")
    for cat, count in stats['by_category'].items():
        print(f"  {cat}: {count}")
    print(f"\nBy topic:")
    for topic, count in stats['by_topic'].items():
        print(f"  {topic}: {count}")
