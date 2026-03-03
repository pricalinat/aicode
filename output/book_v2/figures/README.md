# 书籍图表索引（第2-13章）

## 第2章：技术演进

| 图表编号 | 文件名 | 标题 | 说明 |
|---------|--------|------|------|
| 图2.1 | chapter_02_fig1_transformer_mermaid.plantuml | Transformer架构图 | 展示Transformer的Encoder-Decoder结构，包括输入嵌入、多头注意力、前馈网络等核心组件 |
| 图2.2 | chapter_02_fig2_attention_mermaid.plantuml | 自注意力机制计算流程 | 展示自注意力的四步计算过程：QKV生成、注意力分数计算、Softmax归一化、加权求和输出 |
| 图2.3 | chapter_02_fig3_bert_pretrain_mermaid.plantuml | BERT预训练流程 | 展示BERT的MLM（掩码语言模型）和NSP（下一句预测）两个预训练任务 |
| 图2.4 | chapter_02_fig4_gpt_evolution_mermaid.plantuml | GPT系列演进 | 展示GPT系列模型从2018年到2023年的发展历程，参数规模从117M增长到超大规模 |
| 图2.5 | chapter_02_fig5_pretrain_finetune_mermaid.plantuml | 预训练 vs 微调对比 | 展示预训练阶段和微调阶段的流程对比，预训练学习通用表示，微调适配下游任务 |

## 第3章：知识图谱

| 图表编号 | 文件名 | 标题 | 说明 |
|---------|--------|------|------|
| 图3.1 | chapter_03_fig1_kg_architecture_mermaid.plantuml | 知识图谱架构图 | 展示知识图谱的完整架构，包括数据源、知识抽取、融合、推理、存储和服务层 |
| 图3.2 | chapter_03_fig2_transe_mermaid.plantuml | TransE模型原理 | 展示TransE的核心思想h+r≈t，以及得分函数和局限性 |
| 图3.3 | chapter_03_fig3_alicoco_mermaid.plantuml | AliCoCo体系结构图 | 展示阿里巴巴商品知识图谱AliCoCo的三层架构：概念层、原子概念层和实例层 |
| 图3.4 | chapter_03_fig4_entity_alignment_mermaid.plantuml | 实体对齐流程图 | 展示跨知识图谱实体对齐的完整流程，包括预处理、分块、相似度匹配和实体合并 |
| 图3.5 | chapter_03_fig5_kg_pipeline_mermaid.plantuml | 知识图谱构建流水线 | 展示知识图谱从数据源到API服务的完整构建流水线，包括抽取、融合、推理和存储 |

## 第4章：商品理解

| 图表编号 | 文件名 | 标题 | 说明 |
|---------|--------|------|------|
| 图4.1 | chapter_04_fig1_product_system_mermaid.plantuml | 商品理解系统架构 | 展示商品理解系统的完整架构，包括多模态特征编码和下游任务 |
| 图4.2 | chapter_04_fig2_hierarchy_mermaid.plantuml | 商品分类层次结构 | 展示电商商品的层次化分类体系，从根类目到叶子类目 |
| 图4.3 | chapter_04_fig3_attribute_mermaid.plantuml | 属性识别流程图 | 展示商品属性识别的完整流程，包括属性检测、值抽取、归一化和验证 |
| 图4.4 | chapter_04_fig4_embedding_mermaid.plantuml | 商品向量表示模型 | 展示商品多模态向量表示的学习方法，包括文本、图像、图结构编码和多种训练目标 |

## 第5章：小程序服务理解

| 图表编号 | 文件名 | 标题 | 说明 |
|---------|--------|------|------|
| 图5.1 | chapter_05_fig1_service_understanding_mermaid.md | 服务理解系统架构 | 展示小程序服务理解的完整技术架构，包括服务分类、意图理解、内容理解、质量评估等模块 |
| 图5.2 | chapter_05_fig2_service_taxonomy_mermaid.md | 服务分类层次体系 | 展示小程序服务的多维度分类体系，按性质、行业、需求三个维度组织 |
| 图5.3 | chapter_05_fig3_intent_slot_mermaid.md | 意图识别与槽位填充流程 | 展示从用户查询到意图理解和槽位填充的完整处理流程 |
| 图5.4 | chapter_05_fig4_service_kg_mermaid.md | 服务知识图谱结构 | 展示服务知识图谱的核心实体类型和关系类型 |
| 图5.5 | chapter_05_fig5_quality_assessment_mermaid.md | 服务质量评估框架 | 展示服务质量多维评估的指标体系和评估方法 |

## 第6章：双向匹配

| 图表编号 | 文件名 | 标题 | 说明 |
|---------|--------|------|------|
| 图6.1 | chapter_06_fig1_search_matching_mermaid.md | 搜索匹配技术框架 | 展示搜索匹配的完整技术pipeline，包括查询理解、召回、粗排、精排、重排 |
| 图6.2 | chapter_06_fig2_recommendation_mermaid.md | 推荐匹配技术框架 | 展示推荐系统的完整技术架构，包括用户理解、供给理解、召回、排序、场景化推荐 |
| 图6.3 | chapter_06_fig3_semantic_matching_mermaid.md | 语义匹配模型对比 | 展示基于表示的语义匹配与基于交互的语义匹配的对比 |
| 图6.4 | chapter_06_fig4_bidirectional_mermaid.md | 双向匹配协同机制 | 展示搜索与推荐的融合架构和协同机制 |

## 第7章：LLM-as-Judge

| 图表编号 | 文件名 | 标题 | 说明 |
|---------|--------|------|------|
| 图7.1 | chapter_07_fig1_judge_flow_mermaid.md | LLM-as-Judge评估流程 | 展示LLM-as-Judge的完整评估流程，包括输入、提示工程、LLM评判、输出 |
| 图7.2 | chapter_07_fig2_judge_modes_mermaid.md | LLM评估模式对比 | 展示评分模式、排序模式、判断模式、对话模式四种评估模式 |
| 图7.3 | chapter_07_fig3_bias_mermaid.md | 偏见类型与对抗策略 | 展示LLM评判中的位置偏见、长度偏见、自利偏见及对抗策略 |

## 第8章：电商评测基准

| 图表编号 | 文件名 | 标题 | 说明 |
|---------|--------|------|------|
| 图8.1 | chapter_08_fig1_eval_history_mermaid.md | 电商评测发展历程 | 展示电商评测从早期静态评测到行为驱动评测再到端到端评测的演进 |
| 图8.2 | chapter_08_fig2_eval_methods_mermaid.md | 评测方法对比 | 展示离线评测、线上评测、人工评测、自动化评测四种方法的对比 |

## 第9章：服务理解评测体系

| 图表编号 | 文件名 | 标题 | 说明 |
|---------|--------|------|------|
| 图9.1 | chapter_09_fig1_evaluation_framework.plantuml | 服务理解评测体系框架 | 展示服务理解评测的完整框架，包括服务分类、意图识别、服务匹配、服务质量评测 |
| 图9.2 | chapter_09_fig2_intent_recognition.plantuml | 意图识别与槽位填充流程 | 展示用户查询到意图理解的完整流程，包括多意图检测和槽位填充 |
| 图9.3 | chapter_09_fig3_service_matching.plantuml | 服务匹配评测流程 | 展示服务匹配从查询分析到结果输出的评测流程，包括多路召回和重排序 |
| 图9.4 | chapter_09_fig4_service_quality.plantuml | 服务质量多维评估模型 | 展示服务质量的四个核心维度：功能完备性、性能稳定性、用户感知、合规性 |

## 第10章：评测数据构建与闭环

| 图表编号 | 文件名 | 标题 | 说明 |
|---------|--------|------|------|
| 图10.1 | chapter_10_fig1_data_collection.plantuml | 评测数据采集体系 | 展示评测数据的多来源采集体系，包括公开数据集、业务数据、主动采集 |
| 图10.2 | chapter_10_fig2_evaluation_loop.plantuml | 评测闭环流程 | 展示评测数据与模型迭代的闭环流程，实现数据与模型的协同进化 |
| 图10.3 | chapter_10_fig3_annotation_workflow.plantuml | 数据标注工作流 | 展示数据标注的完整工作流，包括标注任务设计、标注执行和质量控制 |
| 图10.4 | chapter_10_fig4_active_learning.plantuml | 主动学习流程 | 展示主动学习的循环流程，通过智能采样策略选择最有价值的样本 |

## 第11章：多模态理解与文档解析

| 图表编号 | 文件名 | 标题 | 说明 |
|---------|--------|------|------|
| 图11.1 | chapter_11_fig1_multimodal_overview.plantuml | 多模态数据理解概览 | 展示电商场景中的多模态数据类型及其对应的理解技术 |
| 图11.2 | chapter_11_fig2_fusion_methods.plantuml | 跨模态融合方法对比 | 对比早期融合、晚期融合和注意力融合三种主流跨模态融合方法 |
| 图11.3 | chapter_11_fig3_document_parsing.plantuml | 文档解析流水线 | 展示从文档图像到结构化信息的完整解析流水线 |
| 图11.4 | chapter_11_fig4_vision_language.plantuml | 视觉-语言预训练模型 | 展示CLIP等视觉-语言预训练模型的工作原理 |

## 第12章：工业实践案例

| 图表编号 | 文件名 | 标题 | 说明 |
|---------|--------|------|------|
| 图12.1 | chapter_12_fig1_search_system.plantuml | 工业级搜索系统架构 | 展示工业级搜索系统的多阶段架构，从召回到重排的完整流程 |
| 图12.2 | chapter_12_fig2_recommendation_system.plantuml | 工业级推荐系统架构 | 展示工业级推荐系统的多阶段架构，包括召回、排序和重排 |
| 图12.3 | chapter_12_fig3_ab_testing.plantuml | A/B测试流程 | 展示A/B测试的完整流程，包括流量分配、指标收集、统计检验和决策 |
| 图12.4 | chapter_12_fig4_kg_application.plantuml | 知识图谱在工业系统中的应用 | 展示知识图谱在搜索推荐系统中的应用，包括实体链接、语义增强和排序增强 |

## 第13章：未来展望与挑战

| 图表编号 | 文件名 | 标题 | 说明 |
|---------|--------|------|------|
| 图13.1 | chapter_13_fig1_evolution_roadmap.plantuml | 供给理解技术演进路线图 | 展示供给理解技术从当前挑战到技术趋势再到未来应用的演进路线 |
| 图13.2 | chapter_13_fig2_llm_application.plantuml | LLM在供给理解中的应用架构 | 展示LLM与RAG技术结合在供给理解中的应用架构 |
| 图13.3 | chapter_13_fig3_social_responsibility.plantuml | AI社会责任与伦理框架 | 展示AI系统在隐私保护、公平性、可解释性和可持续发展四个方面的社会责任框架 |

## 使用说明

每个图表提供两种格式：
1. **Mermaid源码** (*_mermaid.md): 可直接在支持Mermaid的编辑器中查看
2. **PlantUML** (*.plantuml): 可导入Draw.io进行进一步编辑和导出

### 导入Draw.io步骤：
1. 打开 https://draw.io 或 Draw.io桌面版
2. 点击 Arrange > Insert > Advanced > PlantUML (SVG)
3. 粘贴PlantUML代码
4. 点击 Insert 即可编辑

### 导出为图片
导入Draw.io后可导出为：
- PNG (图片)
- SVG (矢量图)
- PDF (文档)
- XML (可编辑)

建议导出PNG或SVG用于书籍排版，图片保存路径为 `figures/chapter_X/`

---
生成时间: 2026-03-01
