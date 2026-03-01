"""
Topic Classifier - Classify papers by chapter/topic
"""

import sqlite3
import json
import os
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "papers.db"
ANALYSIS_DIR = Path(__file__).parent / "analysis"

# Chapter definitions based on the design document
CHAPTERS = {
    1: {"title": "绪论", "topic": "introduction"},
    2: {"title": "技术演进", "topic": "tech_evolution"},
    3: {"title": "知识图谱", "topic": "knowledge_graph"},
    4: {"title": "商品理解", "topic": "product_understanding"},
    5: {"title": "服务理解", "topic": "service_understanding"},
    6: {"title": "搜索推荐", "topic": "search_recommendation"},
    7: {"title": "LLM评测", "topic": "llm_evaluation"},
    8: {"title": "电商评测", "topic": "ecommerce_evaluation"},
}

# Topic keywords mapping
TOPIC_KEYWORDS = {
    "tech_evolution": ["bert", "transformer", "gpt", "预训练", "预训练模型", "encoder", "decoder", 
                       "attention", "self-attention", "lstm", "rnn", "cnn", "迁移学习", "微调"],
    "knowledge_graph": ["知识图谱", "kg", "knowledge graph", "entity", "relation", "embedding",
                      "图神经网络", "gnn", "gcn", "gat", "知识表示"],
    "product_understanding": ["product", "商品", "item", "matching", "匹配", "商品匹配", 
                             "商品理解", "商品表示", "商品Embedding", "品类", "类目", "品类预测"],
    "service_understanding": ["service", "服务", "mini program", "小程序", "小程序服务", 
                            "service matching", "服务匹配", "服务推荐", "小程序推荐"],
    "search_recommendation": ["search", "搜索", "recommendation", "推荐", "ranking", 
                              "排序", "retrieval", "召回", "ctr", "cvr", "推荐系统"],
    "llm_evaluation": ["llm", "大语言模型", "gpt-4", "gpt-3", "claude", "gemini",
                      "benchmark", "评测", "评估", "judge", "评估基准", "chatgpt"],
    "ecommerce_evaluation": ["evaluation", "评测", "评估", "指标", "metric", "quality",
                             "电商评价", "review", "评论", "sentiment", "情感分析", "电商评测"]
}

def get_connection():
    return sqlite3.connect(DB_PATH)

def get_paper_summary(paper_id):
    """Get paper summary from analysis file if available"""
    analysis_file = ANALYSIS_DIR / f"{paper_id}.json"
    if analysis_file.exists():
        try:
            with open(analysis_file) as f:
                data = json.load(f)
                return data.get('summary', '')
        except:
            pass
    return ''

def classify_paper(paper_id, title, category):
    """Classify a paper into topics based on title and content"""
    summary = get_paper_summary(paper_id)
    text = f"{title} {category} {summary}".lower()
    
    scores = {}
    for topic, keywords in TOPIC_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw.lower() in text)
        if score > 0:
            scores[topic] = score
    
    if not scores:
        # Default based on category
        if category == "product_matching":
            return "product_understanding"
        elif category == "ecommerce_evaluation":
            return "ecommerce_evaluation"
        elif category == "mini_program_service":
            return "service_understanding"
        return "search_recommendation"
    
    return max(scores, key=scores.get)

def classify_all_papers():
    """Classify all papers in database"""
    conn = get_connection()
    c = conn.cursor()
    
    # Get all papers
    c.execute('SELECT paper_id, title, category FROM papers')
    
    papers = c.fetchall()
    
    classified = {}
    for paper_id, title, category in papers:
        topic = classify_paper(paper_id, title, category)
        classified[paper_id] = topic
        
        # Insert into database if not exists
        c.execute('SELECT topic_id FROM topics WHERE topic_name = ?', (topic,))
        row = c.fetchone()
        
        if row:
            topic_id = row[0]
        else:
            c.execute('INSERT INTO topics (topic_name, description) VALUES (?, ?)', 
                     (topic, f"主题: {topic}"))
            topic_id = c.lastrowid
        
        # Link paper to topic
        c.execute('INSERT OR IGNORE INTO paper_topics (paper_id, topic_id) VALUES (?, ?)',
                 (paper_id, topic_id))
    
    conn.commit()
    conn.close()
    
    # Print statistics
    from collections import Counter
    topic_counts = Counter(classified.values())
    print("Classification results:")
    for topic, count in topic_counts.most_common():
        print(f"  {topic}: {count}")
    
    return classified

if __name__ == '__main__':
    classify_all_papers()
