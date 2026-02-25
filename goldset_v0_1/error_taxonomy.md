# Error Taxonomy（错误分类体系）

## A. Schema Errors（结构错误）
1. 缺失必填字段（Missing Required Field）
2. 字段类型错误（Type Mismatch）
3. 顶层命名错误（Wrong Dataset/Domain Name）
4. 子对象结构不完整（Nested Object Incomplete）

## B. Logical Consistency Errors（逻辑一致性错误）
1. 价格区间倒置（price_range.min > max）
2. 商品价格不在标注区间内
3. must_have 与 exclude 冲突
4. MiniApp 要求身份认证但无实名认证前置条件
5. 时间约束格式非法
6. 对抗样本缺少 expected_ignore_injection=true

## C. Conflict Errors（冲突检测错误）
1. 全局 ID 重复
2. 同 query 多意图强冲突（高分歧）
3. 挑战样本 source_id 无法回溯到主集

## D. Data Quality Smells（可疑但不一定错误）
1. 单一意图占比过高（类别失衡）
2. query 长度过短（信息不足）
3. challenge 集域分布极度偏斜
4. 噪声强度过高导致语义改变

## E. 修复优先级
- P0: Schema/ID/source_id 问题（必须阻断发布）
- P1: 逻辑冲突（必须修复）
- P2: 分布/风格问题（可迭代优化）
