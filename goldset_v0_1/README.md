# goldset_v0_1

全合成中文 GOLD 数据集（电商商品理解 + MiniApp 服务理解）。

## 文件清单
- `gold_ecom.jsonl`
- `gold_miniapp.jsonl`
- `challenge_confusion.jsonl`
- `challenge_long_tail.jsonl`
- `challenge_robustness.jsonl`
- `challenge_adversarial.jsonl`
- `schema.json`
- `label_guideline.md`
- `error_taxonomy.md`
- `quality_report.md`
- `generator.py`
- `validator.py`

## 快速 CLI
```bash
cd /Users/rrp/.openclaw/workspace/goldset_v0_1

# 1) 重新生成（固定随机种子，默认规模：1200/1200/360*4）
python3 generator.py --out-dir .

# 2) 校验（多阶段：schema + logic + conflict）
python3 validator.py --data-dir .
```

## 生成参数（可选）
```bash
python3 generator.py --out-dir . --ecom 1500 --miniapp 1500 --challenge 500
```

## 复现性
- 生成脚本内固定 `SEED=20260225`
- 相同参数下输出稳定可复现
