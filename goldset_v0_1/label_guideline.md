# 标注指南（goldset_v0_1）

## 1. 目标
本数据集用于两类理解任务：
1. 电商商品理解（商品检索/筛选/决策）
2. MiniApp服务理解（查询/办理/追踪/预约）

## 2. 通用原则
- 语言统一：`zh-CN`
- 标签优先反映**用户真实任务意图**，而不是表面词汇。
- `gold_*` 为主任务真值；`challenge_*` 为扰动样本，`gold_intent`保持与源样本一致。
- 不允许同一记录内出现自相矛盾槽位（如价格区间倒置）。

## 3. 电商标签说明
- `intent`：
  - 商品检索
  - 属性筛选
  - 价格约束
  - 对比决策
  - 搭配推荐
- `target_category`：精确到二级类目（如“运动鞋”）。
- `price_range`：闭区间，且必须覆盖目标商品价格。
- `must_have`：硬性条件。
- `exclude`：排除条件，不能与 `must_have` 重叠。
- `sort_by`：可选策略（销量/价格/好评率/上新）。

## 4. MiniApp标签说明
- `intent`：
  - 服务查询
  - 服务办理
  - 状态追踪
  - 预约
  - 投诉反馈
- `required_slots`：识别任务所需字段（至少包含 `city`,`service_name`）。
- 若包含 `identity_auth`，则 `preconditions` 必须含“实名认证”。
- `expected_action`：系统应给出的下一步动作。
- `time_constraint.before`：`HH:MM` 格式。

## 5. 挑战集标签说明
- `challenge_confusion`：语义不变但词面易混淆。
- `challenge_long_tail`：小众需求/冷门表达。
- `challenge_robustness`：噪声扰动（错别字/符号/emoji等）。
- `challenge_adversarial`：注入/误导攻击；必须要求忽略恶意指令。

## 6. 质检阈值
- 样本规模：主集 >=1000，挑战集各 >=300。
- 结构完整率：100%。
- 逻辑冲突率：0（由 validator 强校验）。
