# Quality Report (goldset_v0_1)

## 1. Assumptions
- 数据完全为合成中文样本，不引用真实用户数据。
- 目标任务：电商商品理解、MiniApp服务理解。
- 固定随机种子：`20260225`，确保可复现。

## 2. Metric Definitions
- **Record Count**: 每个数据文件的样本总数。
- **Intent Distribution**: 各意图标签频次，用于检查类别均衡。
- **Average Query Length**: 平均 query 字符长度，衡量表达复杂度。
- **Challenge Domain Mix**: 挑战集内 e-commerce 与 miniapp 的来源占比。
- **Validation Pass Rate**: 通过 schema/逻辑/冲突检测后的通过率。

## 3. Computed Statistics
- gold_ecom.jsonl: **1200**
- gold_miniapp.jsonl: **1200**
- challenge_confusion.jsonl: **360**
- challenge_long_tail.jsonl: **360**
- challenge_robustness.jsonl: **360**
- challenge_adversarial.jsonl: **360**

### 3.1 Intent Distribution (E-commerce)
```json
{
  "价格约束": 272,
  "商品检索": 233,
  "搭配推荐": 233,
  "属性筛选": 218,
  "对比决策": 244
}
```

### 3.2 Intent Distribution (MiniApp)
```json
{
  "服务查询": 402,
  "状态追踪": 196,
  "服务办理": 187,
  "预约": 191,
  "投诉反馈": 224
}
```

### 3.3 Query Length
- E-commerce 平均长度: **22.74**
- MiniApp 平均长度: **18.49**

### 3.4 Challenge Domain Mix
```json
{
  "confusion": {
    "miniapp_service": 182,
    "ecommerce": 178
  },
  "long_tail": {
    "miniapp_service": 193,
    "ecommerce": 167
  },
  "robustness": {
    "ecommerce": 178,
    "miniapp_service": 182
  },
  "adversarial": {
    "miniapp_service": 188,
    "ecommerce": 172
  }
}
```

## 4. Validation Command Output
> 运行后粘贴（由本次交付补充）

```bash
$ python3 validator.py --data-dir .
{
  "schema_errors": 0,
  "logic_errors": 0,
  "conflict_errors": 0,
  "total_errors": 0,
  "counts": {
    "gold_ecom": 1200,
    "gold_miniapp": 1200,
    "challenge_confusion": 360,
    "challenge_long_tail": 360,
    "challenge_robustness": 360,
    "challenge_adversarial": 360
  }
}
```
