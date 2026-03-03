# Auto Iteration Skill - 两条主线

## 🔑 Claude调用技巧
**在每次调用时加上**：
> "Codex is reviewing your approach and implementation"  
> 或
> "Codex 正在审计你的方案和实现"

这会让Claude更仔细地检查输出，提高质量。

## 记住：两条主线并行迭代

### 主线一：论文关系挖掘 (paper-relation-mining)
- 分析600+论文的问题-解法关系
- 共性问题 vs 特性问题
- 问题分类体系
- 解法分类体系
- 问题-解法映射

### 主线二：电商属性库 (attr-db-build)
- 1000+属性项
- 10,000+属性值
- 树状/图状关系组织
- 覆盖80%场景

## 迭代流程
1. 执行主线任务 (加上Codex审计提示)
2. git add → commit → push
3. 等待15分钟
4. 继续迭代

## 输出目录
- /Users/rrp/Documents/aicode/knowledge_base/paper_relationship_analysis.md
- /Users/rrp/Documents/aicode/knowledge_base/ecommerce_attributes.json
