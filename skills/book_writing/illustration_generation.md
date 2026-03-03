# Illustration Generation Skill - 书籍插图生成与验证

## Skill Description
Generate high-quality illustrations for the book "供给理解及其评测体系" including flowcharts, architecture diagrams, system designs, and technical drawings. AFTER generating each diagram, verify its correctness using multimodal LLM or visual inspection.

## Critical Requirement: Verify Every Diagram
1. **Generate diagram** with code (Mermaid/Graphviz/Python)
2. **Visual verification** - render and inspect the diagram
3. **LLM validation** - use multimodal model to verify diagram correctness
4. **Iterate** if issues found until diagram is correct
5. **Document** verification result

## Supported Formats
1. **Mermaid** - Flowcharts, sequence diagrams, class diagrams
2. **Graphviz** - DOT language diagrams
3. **PlantUML** - UML diagrams
4. **ASCII Art** - Text-based diagrams for simple cases
5. **draw.io / diagrams.net** - External diagram editing reference
6. **Python (Matplotlib/NetworkX)** - Data visualization
7. **Python (Graphviz)** - Programmatic diagram generation

## Verification Workflow
- 编写插图代码 -> 渲染检查 -> LLM验证 -> 如有问题返回修改 -> 保存并记录验证结果

## Per-Chapter Illustration Requirements (Minimum)

### Chapter 1: 供给定义 (5+ diagrams)
- 供给层次结构图
- 供给理解任务框图
- 供需匹配概念图
- 核心要素关系图
- 场景应用图

### Chapter 2: 技术演进 (5+ diagrams)
- 技术发展时间线
- 模型演进架构图
- 方法对比表/图
- 各时期代表性模型

### Chapter 3: 知识图谱 (8+ diagrams)
- 知识图谱架构图
- 实体关系模型
- 图谱构建流水线
- AliCoCo体系结构
- 实体对齐流程
- 关系抽取流程
- 图谱查询流程

### Chapter 4: 商品理解 (6+ diagrams)
- 商品理解系统框图
- 商品分类流程
- 属性识别流程
- 商品质量评估流程
- 商品编码流程

### Chapter 5: 服务理解 (6+ diagrams)
- 服务理解系统框图
- 意图识别流程
- 槽位填充流程
- 服务质量评估
- 服务分类体系
- 服务知识图谱结构

### Chapter 6: 双向匹配 (8+ diagrams)
- 搜索匹配流程
- 推荐匹配流程
- 搜索推荐融合架构
- 双向匹配协同图
- 召回-粗排-精排-重排流程
- 用户意图理解流程
- 商品/服务编码流程

### Chapter 7: LLM Judge (6+ diagrams)
- LLM Judge工作流
- 多维度评测框架
- 评测质量保障流程
- 偏差检测流程
- Prompt工程图

### Chapter 8: 电商评测 (6+ diagrams)
- 电商评测基准框架
- 指标体系图
- A/B测试流程
- 数据采集流程

### Chapter 9: 服务评测 (5+ diagrams)
- 服务评测指标图
- 对话评测流程
- 任务完成评测
- Intent-Slot评测

### Chapter 10: 数据闭环 (6+ diagrams)
- 数据构建流程
- 标注质量管理
- 闭环迭代流程
- 特征工程流程

## Output Requirements
- Save diagrams to: `/Users/rrp/Documents/aicode/output/book/figures/`
- Format: .mmd (Mermaid) + .png (rendered) + .py (source code)
- Naming: `chXX_figure_XX_description.mmd`
- Include verification report after each diagram

## Verification Checklist (Per Diagram)
- [ ] 语法正确，可渲染
- [ ] 逻辑正确，流程完整
- [ ] 标签清晰，中文准确
- [ ] 布局合理，层次分明
- [ ] 颜色恰当，便于区分
- [ ] LLM验证通过（如果有使用）

## Quality Standards
- [ ] Clear visual hierarchy
- [ ] Consistent color scheme
- [ ] Proper labels in Chinese
- [ ] Legend when needed
- [ ] Source code included for reproducibility
- [ ] Verification completed and documented
