#!/usr/bin/env python3
"""
Improved citation generator with better metadata extraction
"""

import os
import sqlite3
import json
import re
from pathlib import Path
from datetime import datetime

KB_DIR = Path('/Users/rrp/Documents/aicode/knowledge_base')
DB_PATH = KB_DIR / 'data' / 'papers.db'
ANALYSIS_DIR = KB_DIR / 'analysis'
CITATIONS_DIR = KB_DIR / 'citations'

# Chapter mapping
CHAPTERS = {
    1: {"title": "Introduction", "keywords": ["introduction", "overview", "survey"]},
    2: {"title": "Tech Evolution", "keywords": ["evolution", "history", "timeline"]},
    3: {"title": "Knowledge Graph", "keywords": ["knowledge graph", "kg", "ontology"]},
    4: {"title": "Product Understanding", "keywords": ["product", "matching", "entity", "retrieval"]},
    5: {"title": "Service Understanding", "keywords": ["service", "web service", "api", "mini program"]},
    6: {"title": "Search Recommendation", "keywords": ["search", "recommendation", "ranking"]},
    7: {"title": "LLM Evaluation", "keywords": ["llm", "gpt", "evaluation", "benchmark", "judge"]},
    8: {"title": "Ecommerce Evaluation", "keywords": ["ecommerce", "evaluation", "fairness", "bias"]}
}

def get_connection():
    return sqlite3.connect(DB_PATH)

def load_analysis(paper_id):
    """Load analysis JSON for a paper"""
    analysis_file = ANALYSIS_DIR / f'{paper_id}.json'
    if analysis_file.exists():
        with open(analysis_file, 'r') as f:
            return json.load(f)
    return None

def classify_paper(paper_id, title, category, summary):
    """Classify paper into chapters based on keywords"""
    text = f"{title} {category} {summary}".lower()
    
    # Direct category mapping
    if category == "product_matching":
        return 4
    elif category == "mini_program_service":
        return 5
    elif category == "ecommerce_evaluation":
        return 8
    
    # Keyword-based classification
    for ch, info in CHAPTERS.items():
        for kw in info["keywords"]:
            if kw in text:
                return ch
    
    return 4  # Default to product understanding

def extract_innovation(summary):
    """Extract innovation points from summary"""
    if not summary:
        return "需要进一步分析"
    
    # Clean up summary - remove markdown headers
    summary = summary.replace('#', '').replace('*', '')
    
    # Look for key phrases
    lines = summary.split('\n')
    innovations = []
    
    for line in lines:
        line = line.strip()
        if not line or len(line) < 20:
            continue
        
        # Look for innovation indicators
        indicators = ['propose', 'novel', 'introduce', 'present', 'new', 'first', 'improve', 'achieve', 'address', 'solve', 'approach']
        if any(ind in line.lower() for ind in indicators):
            # Clean up the line
            line = line.strip()
            if len(line) > 20 and len(line) < 400:
                innovations.append(line)
    
    if innovations:
        return innovations[0]
    
    # Fallback: first meaningful sentence
    sentences = summary.replace('\n', '. ').split('.')
    for s in sentences[:5]:
        s = s.strip()
        if len(s) > 30:
            return s[:250]
    
    return "需要进一步分析"

def extract_limitations(summary):
    """Extract limitations from summary"""
    if not summary:
        return "需要进一步分析"
    
    summary = summary.replace('#', '').replace('*', '')
    summary_lower = summary.lower()
    
    # Look for limitation indicators
    limitation_keywords = ['limitation', 'however', 'challenge', 'drawback', 'weakness', '不足', '局限', 'future work', 'future research']
    
    # First try to find explicit limitations
    sentences = summary.replace('\n', '. ').split('.')
    for s in sentences:
        s = s.strip()
        if len(s) < 20:
            continue
        if any(kw in s.lower() for kw in limitation_keywords):
            return s[:250]
    
    # Generate limitations based on paper type
    limitations = []
    
    if 'survey' in summary_lower or 'review' in summary_lower:
        limitations.append("Survey类论文可能缺乏对最新方法的覆盖；实验对比有限")
    
    if 'baseline' in summary_lower and 'compare' not in summary_lower:
        limitations.append("实验对比可能不够全面")
    
    if 'dataset' in summary_lower:
        if 'few' in summary_lower or 'limited' in summary_lower or 'small' in summary_lower:
            limitations.append("数据集规模可能有限")
    
    if 'only' in summary_lower or 'single' in summary_lower:
        limitations.append("可能仅在特定场景或数据集上验证")
    
    if 'heuristic' in summary_lower or 'rule' in summary_lower:
        limitations.append("可能存在手工规则，可扩展性有限")
    
    if 'annotation' in summary_lower or 'label' in summary_lower:
        limitations.append("可能依赖人工标注数据")
    
    if limitations:
        return "; ".join(limitations)
    
    return "需要进一步分析"

def extract_experiments(summary):
    """Extract experimental results"""
    if not summary:
        return {}
    
    results = {}
    
    # Look for percentage improvements
    patterns = [
        r'(?:improve|increase|decrease|reduce|boost|achieve)\s+(?:by\s+)?(\d+(?:\.\d+)?)\s*%',
        r'(\d+(?:\.\d+)?)\s*%\s+(?:improvement|increase|gain)',
        r'(?:recall|ndcg|precision|f1|auc|accuracy)\s+[:=]?\s*(\d+(?:\.\d+)?)\s*%',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, summary, re.IGNORECASE)
        if matches:
            results['improvement'] = f"+{matches[0]}%" if matches else ""
    
    # Look for dataset names
    datasets = []
    common_ds = ['amazon', 'yelp', 'movielens', 'netflix', 'taobao', 'alibaba', 
                 'jd', 'tmall', 'booking', 'steam', 'goodreads', 'instacart',
                 'tafeng', 'dunnhumby', 'CiteULike', 'lastfm']
    summary_lower = summary.lower()
    for ds in common_ds:
        if ds.lower() in summary_lower:
            datasets.append(ds.title())
    if datasets:
        results['datasets'] = list(set(datasets))[:5]
    
    # Look for metrics
    metrics = []
    metric_names = ['recall', 'ndcg', 'precision', 'f1', 'auc', 'accuracy', 'mrr', 'map', 'hit rate']
    for m in metric_names:
        if m in summary_lower:
            metrics.append(m.upper())
    if metrics:
        results['metrics'] = list(set(metrics))[:5]
    
    return results

def generate_citation(paper_id, title, year, category, summary):
    """Generate a high-quality citation entry"""
    
    innovation = extract_innovation(summary)
    limitations = extract_limitations(summary)
    experiments = extract_experiments(summary)
    
    citation = f"""### {title}
**引用**: ({paper_id}, {year})
**作者**: [需要提取]
**年份**: {year}
**分类**: {category}

**创新点**: {innovation}

**实验结果**: """
    
    if experiments:
        if 'datasets' in experiments:
            citation += f"\n- 数据集: {', '.join(experiments['datasets'])}"
        if 'metrics' in experiments:
            citation += f"\n- 指标: {', '.join(experiments['metrics'])}"
        if 'improvement' in experiments:
            citation += f"\n- 提升: {experiments['improvement']}"
    else:
        citation += "需要进一步分析"
    
    citation += f"""

**局限性**: {limitations}

---
"""
    
    return citation

def update_citations():
    """Update all chapter citations"""
    conn = get_connection()
    c = conn.cursor()
    
    # Get all papers from database
    c.execute('SELECT paper_id, title, year, category FROM papers')
    all_papers = c.fetchall()
    
    # Load analysis from JSON files
    papers = []
    for paper_id, title, year, category in all_papers:
        analysis = load_analysis(paper_id)
        if analysis:
            summary = analysis.get('summary', '')
            papers.append((paper_id, title, year, category, summary))
    
    print(f"Processing {len(papers)} papers with analysis...")
    
    # Group by chapter
    chapter_papers = {i: [] for i in range(1, 9)}
    
    for paper_id, title, year, category, summary in papers:
        chapter = classify_paper(paper_id, title, category, summary)
        chapter_papers[chapter].append((paper_id, title, year, category, summary))
    
    # Generate citations for each chapter
    for ch in range(1, 9):
        chapter_file = CITATIONS_DIR / f'chapter_{ch}_{CHAPTERS[ch]["title"].lower().replace(" ", "_")}.md'
        
        citations_content = f"# 第{ch}章 - {CHAPTERS[ch]['title']}\n\n"
        citations_content += f"共 {len(chapter_papers[ch])} 篇参考文献\n\n"
        
        for paper_id, title, year, category, summary in chapter_papers[ch]:
            citation = generate_citation(paper_id, title, year, category, summary)
            citations_content += citation
        
        with open(chapter_file, 'w') as f:
            f.write(citations_content)
        
        print(f"Chapter {ch}: {len(chapter_papers[ch])} papers")
    
    conn.close()
    print("\nCitations updated successfully!")

if __name__ == '__main__':
    update_citations()
