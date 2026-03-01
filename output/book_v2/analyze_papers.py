#!/usr/bin/env python3
"""
论文分析脚本 - 遍历所有论文，按主题分类到章节引用库
"""
import os
import re
import json
from pathlib import Path

# 定义论文目录
PAPER_DIRS = {
    'product_matching': '/Users/rrp/Documents/aicode/data/papers/product_matching/',
    'ecommerce_evaluation': '/Users/rrp/Documents/aicode/data/papers/ecommerce_evaluation/',
    'mini_program_service': '/Users/rrp/Documents/aicode/data/papers/mini_program_service/'
}

# 定义章节主题关键词映射
CHAPTER_TAGS = {
    'ch01_foundation': ['embedding', 'representation', 'tfidf', 'word2vec', 'glove', 
                        'foundation', 'concept', 'definition', 'survey', 'overview'],
    'ch02_deep_learning': ['transformer', 'bert', 'gpt', 'deep learning', 'neural',
                           'lstm', 'rnn', 'attention', 'pre-train', 'fine-tune'],
    'ch03_knowledge_graph': ['knowledge graph', 'kg', 'entity', 'link', 'embedding',
                             'transE', 'transR', 'graph'],
    'ch04_product': ['product', 'classification', 'categorization', 'matching',
                     'retrieval', 'search', 'ranking', 'recommendation', 'ecommerce'],
    'ch05_service': ['service', 'chatbot', 'dialog', 'intent', 'slot', 'nlu',
                     'api', 'mini program', 'wechat', 'xiaochengxu'],
    'ch06_matching': ['matching', 'alignment', 'entity matching', 'product matching',
                      'similarity', 'duplicate', 'deduplication'],
    'ch07_evaluation': ['evaluation', 'metric', 'benchmark', 'assessment', 'measure'],
    'ch08_llm_judge': ['llm', 'gpt', 'judge', 'preference', 'chatgpt', 'instruction'],
    'ch09_benchmark': ['benchmark', 'dataset', 'test', 'challenge', 'leaderboard'],
    'ch10_metrics': ['metric', 'recall', 'precision', 'ndcg', 'auc', 'hit rate'],
    'ch11_application': ['application', 'system', 'platform', 'practice', 'case'],
    'ch12_future': ['future', 'trend', 'outlook', 'challenge', 'opportunity']
}

def extract_paper_info(filename):
    """从文件名提取论文信息"""
    # 移除.pdf后缀
    name = filename.replace('.pdf', '')
    
    # 尝试提取arXiv ID和标题
    parts = name.split('_', 1)
    if len(parts) == 2 and parts[0].replace('.', '').isdigit():
        arxiv_id = parts[0]
        title = parts[1].replace('_', ' ')
    else:
        arxiv_id = None
        title = name.replace('_', ' ')
    
    return {
        'filename': filename,
        'arxiv_id': arxiv_id,
        'title': title
    }

def classify_paper(filename, title):
    """根据文件名和标题分类论文"""
    text = (filename + ' ' + title).lower()
    
    scores = {}
    for chapter, keywords in CHAPTER_TAGS.items():
        score = sum(1 for kw in keywords if kw in text)
        scores[chapter] = score
    
    # 返回得分最高的章节
    if max(scores.values()) > 0:
        return max(scores, key=scores.get)
    else:
        return 'ch04_product'  # 默认归类到商品理解

def analyze_papers():
    """分析所有论文"""
    all_papers = []
    
    for category, dir_path in PAPER_DIRS.items():
        if not os.path.exists(dir_path):
            continue
            
        files = os.listdir(dir_path)
        for f in files:
            if f.endswith('.pdf'):
                info = extract_paper_info(f)
                info['category'] = category
                info['chapter'] = classify_paper(f, info['title'])
                all_papers.append(info)
    
    return all_papers

def generate_reference_files(papers):
    """生成各章节的引用文件"""
    base_dir = '/Users/rrp/Documents/aicode/output/book_v2/references/'
    
    # 按章节分组
    chapter_papers = {}
    for p in papers:
        ch = p['chapter']
        if ch not in chapter_papers:
            chapter_papers[ch] = []
        chapter_papers[ch].append(p)
    
    # 生成每个章节的引用文件
    for chapter, paper_list in chapter_papers.items():
        output_file = os.path.join(base_dir, chapter, 'papers.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(paper_list, f, indent=2, ensure_ascii=False)
        
        print(f"{chapter}: {len(paper_list)} papers")

def main():
    print("开始分析论文...")
    papers = analyze_papers()
    print(f"共分析 {len(papers)} 篇论文")
    
    generate_reference_files(papers)
    
    # 统计各章节论文数量
    chapter_counts = {}
    for p in papers:
        ch = p['chapter']
        chapter_counts[ch] = chapter_counts.get(ch, 0) + 1
    
    print("\n各章节论文分布:")
    for ch, count in sorted(chapter_counts.items()):
        print(f"  {ch}: {count}")

if __name__ == '__main__':
    main()
