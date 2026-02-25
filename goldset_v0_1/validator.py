#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Multi-pass validator for synthetic GOLD datasets."""

from __future__ import annotations
import argparse
import json
from collections import defaultdict
from pathlib import Path

FILES = {
    "gold_ecom": "gold_ecom.jsonl",
    "gold_miniapp": "gold_miniapp.jsonl",
    "challenge_confusion": "challenge_confusion.jsonl",
    "challenge_long_tail": "challenge_long_tail.jsonl",
    "challenge_robustness": "challenge_robustness.jsonl",
    "challenge_adversarial": "challenge_adversarial.jsonl",
}


def load_jsonl(path: Path):
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception as e:
                raise ValueError(f"{path.name}:{i} JSON解析失败: {e}")
    return rows


def assert_required(obj, required, ctx, errors):
    for k, t in required.items():
        if k not in obj:
            errors.append(f"{ctx}: 缺失字段 {k}")
            continue
        if t is not None and not isinstance(obj[k], t):
            errors.append(f"{ctx}: 字段 {k} 类型错误，期望 {t}, 实际 {type(obj[k])}")


def schema_pass(rows_by_name):
    errors = []
    for name, rows in rows_by_name.items():
        for idx, r in enumerate(rows, 1):
            ctx = f"{name}[{idx}]"
            if name.startswith("gold_"):
                assert_required(r, {"id": str, "dataset": str, "domain": str, "query": str, "language": str, "label": dict}, ctx, errors)
                if name == "gold_ecom":
                    assert_required(r, {"product": dict}, ctx, errors)
                    if isinstance(r.get("product"), dict):
                        assert_required(r["product"], {"title": str, "category_lv1": str, "category_lv2": str, "brand": str, "price": int, "attributes": dict}, ctx + ".product", errors)
                elif name == "gold_miniapp":
                    assert_required(r, {"service": dict}, ctx, errors)
                    if isinstance(r.get("service"), dict):
                        assert_required(r["service"], {"category": str, "name": str, "city": str, "channel": str}, ctx + ".service", errors)
            else:
                assert_required(r, {"challenge_type": str, "source_id": str, "base_query": str, "perturbed_query": str, "gold_intent": str}, ctx, errors)

    return errors


def logic_pass(rows_by_name):
    errors = []

    for idx, r in enumerate(rows_by_name["gold_ecom"], 1):
        ctx = f"gold_ecom[{idx}]"
        label = r.get("label", {})
        pr = label.get("price_range", {})
        if not isinstance(pr, dict) or "min" not in pr or "max" not in pr:
            errors.append(f"{ctx}: 缺失price_range.min/max")
        else:
            if pr["min"] > pr["max"]:
                errors.append(f"{ctx}: price_range min>max")
            price = r.get("product", {}).get("price")
            if isinstance(price, int) and not (pr["min"] <= price <= pr["max"]):
                errors.append(f"{ctx}: 商品价格不在标注区间内")

        must = set(label.get("must_have", []))
        exc = set(label.get("exclude", []))
        overlap = must & exc
        if overlap:
            errors.append(f"{ctx}: must_have/exclude冲突: {overlap}")

    for idx, r in enumerate(rows_by_name["gold_miniapp"], 1):
        ctx = f"gold_miniapp[{idx}]"
        label = r.get("label", {})
        req = set(label.get("required_slots", []))
        pre = set(label.get("preconditions", []))
        if "identity_auth" in req and "实名认证" not in pre:
            errors.append(f"{ctx}: identity_auth要求但缺少实名认证前置条件")
        tc = label.get("time_constraint", {})
        before = tc.get("before", "")
        if len(before) != 5 or before[2] != ":":
            errors.append(f"{ctx}: time_constraint.before格式错误")

    for idx, r in enumerate(rows_by_name["challenge_adversarial"], 1):
        ctx = f"challenge_adversarial[{idx}]"
        if r.get("expected_ignore_injection") is not True:
            errors.append(f"{ctx}: adversarial缺少expected_ignore_injection=true")

    return errors


def conflict_pass(rows_by_name):
    errors = []
    all_rows = []
    for k, rows in rows_by_name.items():
        all_rows.extend((k, x) for x in rows)

    # 1) ID uniqueness global
    seen = {}
    for name, r in all_rows:
        rid = r.get("id")
        if rid in seen:
            errors.append(f"ID冲突: {rid} in {name} and {seen[rid]}")
        else:
            seen[rid] = name

    # 2) same canonical query with conflicting intent (for gold sets)
    by_query = defaultdict(set)
    for name in ["gold_ecom", "gold_miniapp"]:
        for r in rows_by_name[name]:
            q = "".join(r.get("query", "").split())
            it = r.get("label", {}).get("intent")
            if q and it:
                by_query[q].add(it)

    for q, intents in by_query.items():
        if len(intents) > 2:
            errors.append(f"潜在标签冲突: 同query意图过多 {list(intents)[:4]} :: {q[:40]}")

    # 3) source id must exist
    source_ids = {r["id"] for r in rows_by_name["gold_ecom"]} | {r["id"] for r in rows_by_name["gold_miniapp"]}
    for name in ["challenge_confusion", "challenge_long_tail", "challenge_robustness", "challenge_adversarial"]:
        for idx, r in enumerate(rows_by_name[name], 1):
            sid = r.get("source_id")
            if sid not in source_ids:
                errors.append(f"{name}[{idx}]: source_id不存在 {sid}")

    return errors


def main():
    parser = argparse.ArgumentParser(description="Validate generated gold datasets")
    parser.add_argument("--data-dir", default=".")
    args = parser.parse_args()

    d = Path(args.data_dir)
    rows_by_name = {k: load_jsonl(d / v) for k, v in FILES.items()}

    e1 = schema_pass(rows_by_name)
    e2 = logic_pass(rows_by_name)
    e3 = conflict_pass(rows_by_name)

    result = {
        "schema_errors": len(e1),
        "logic_errors": len(e2),
        "conflict_errors": len(e3),
        "total_errors": len(e1) + len(e2) + len(e3),
        "counts": {k: len(v) for k, v in rows_by_name.items()},
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["total_errors"]:
        for section, errs in [("schema", e1), ("logic", e2), ("conflict", e3)]:
            if errs:
                print(f"\n[{section}] top errors:")
                for e in errs[:20]:
                    print("-", e)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
