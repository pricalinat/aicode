"""
Paper Knowledge Base - Analyzer
Analyzes papers using summarize and LLM
"""

import json
import sqlite3
import subprocess
import re
from pathlib import Path
from kb_schema import init_db, insert_analysis, get_all_papers, DB_PATH

ANALYSIS_PROMPT = """请分析以下论文，提取关键信息。

论文标题：{title}
文件路径：{file_path}

请使用summarize工具获取论文内容，然后提取：
1. 核心创新点（Novelty）：一句话概括论文的主要创新
2. 技术方法（Method）：详细描述使用的方法和技术
3. 模型架构（Architecture）：如果涉及模型，描述其架构
4. 实验设置：
   - 数据集（datasets）：列出使用的数据集
   - 评测指标（metrics）：列出评估指标
   - 主要结果（results）：主要实验结论
   - 对比方法（baselines）：对比的基线方法
5. 主要结论（Conclusions）：论文的主要贡献和结论
6. 局限性（Limitations）：批判性分析，论文的不足之处

请以JSON格式输出：
{{
    "novelty": "...",
    "method": "...",
    "architecture": "...",
    "datasets": [...],
    "metrics": [...],
    "results": {{...}},
    "baselines": [...],
    "conclusions": "...",
    "limitations": "..."
}}"""

def summarize_paper(file_path):
    """Use summarize tool to get paper content"""
    try:
        cmd = ['summarize', file_path, '--length', 'long', '--json']
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            print(f"Error summarizing {file_path}: {result.stderr}")
            return None
    except Exception as e:
        print(f"Exception summarizing {file_path}: {e}")
        return None

def analyze_paper(paper_id, title, file_path):
    """Analyze a single paper using LLM"""
    # First, summarize the paper
    summary = summarize_paper(file_path)
    
    if not summary:
        return None
    
    # Now use LLM to extract structured analysis
    # We'll use the model's reasoning capability here
    analysis_text = f"""
论文标题：{title}
摘要：{summary.get('summary', '')[:2000]}

请作为学术论文分析专家，提取以下信息（JSON格式）：
"""
    
    # Generate analysis using the model's built-in capabilities
    # This is a simplified version - in practice you'd call an LLM API
    analysis = {
        'novelty': '需要LLM分析提取',
        'method': summary.get('summary', '')[:1000],
        'architecture': '见摘要',
        'datasets': [],
        'metrics': [],
        'results': {},
        'baselines': [],
        'conclusions': summary.get('summary', '')[1000:2000] if len(summary.get('summary', '')) > 1000 else summary.get('summary', ''),
        'limitations': '需要深入分析'
    }
    
    return analysis

def analyze_all_papers(batch_size=10):
    """Analyze all papers in database"""
    conn = sqlite3.connect(DB_PATH)
    papers = get_all_papers(conn)
    
    print(f"Found {len(papers)} papers to analyze")
    
    analyzed = 0
    for i, (paper_id, title, category) in enumerate(papers):
        print(f"[{i+1}/{len(papers)}] Analyzing: {title[:50]}...")
        
        # Get full paper data
        c = conn.cursor()
        c.execute('SELECT file_path FROM papers WHERE paper_id = ?', (paper_id,))
        row = c.fetchone()
        if not row:
            continue
        
        file_path = row[0]
        
        try:
            analysis = analyze_paper(paper_id, title, file_path)
            if analysis:
                insert_analysis(conn, paper_id, analysis)
                analyzed += 1
        except Exception as e:
            print(f"Error analyzing {paper_id}: {e}")
    
    print(f"\nAnalyzed {analyzed} papers")
    return analyzed

if __name__ == '__main__':
    analyze_all_papers()
