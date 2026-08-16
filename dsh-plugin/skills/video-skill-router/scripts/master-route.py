#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""master-route.py — 段级视频路由决策脚本

读取 routing.json（单一事实源），对任务描述做关键词/特征匹配，
输出「命中规则 × 引擎 × 编排契约 × 依赖顺序」的方案表。

用法：
    python master-route.py "做一个最短路径的科普动画，金句排版，女声解说" --json
    python master-route.py --text "..." 
    echo "..." | python master-route.py --json
"""

import argparse
import json
import sys
from pathlib import Path

# scripts/ 的上级即 skill 根目录，routing.json 与之同级
ROUTING_JSON = Path(__file__).resolve().parent.parent / "routing.json"

# 内容型规则：命中 >= 2 个即触发多段总装 R30
CONTENT_RULE_IDS = {"R01", "R02", "R03", "R04", "R05", "R06"}


def load_rules():
    """读取 routing.json 的 rules 列表。"""
    with open(ROUTING_JSON, encoding="utf-8") as f:
        return json.load(f)["rules"]


def route(text, rules):
    """纯函数：任务描述 + 规则列表 -> 路由方案。

    返回 dict：
      matched_rule_ids  命中的规则 id（已按依赖顺序排序）
      segments          每段的路由结果
      contracts         涉及的契约名列表
      assembly          总装提示（来自 routing.json.assembly，由调用方注入）
    """
    lowered = (text or "").lower()
    matched = []

    for rule in rules:
        trigger = rule.get("trigger", {})
        keywords = trigger.get("keywords", [])
        if keywords and any(kw.lower() in lowered for kw in keywords):
            matched.append(rule)

    # 多段总装：内容型规则命中 >= 2 -> 触发 R30
    content_hits = [r for r in matched if r["id"] in CONTENT_RULE_IDS]
    if len(content_hits) >= 2:
        for rule in rules:
            if rule["id"] == "R30" and rule not in matched:
                matched.append(rule)

    # 去重（按 id 保留首个），并按依赖顺序排序
    seen = {}
    for r in matched:
        seen.setdefault(r["id"], r)
    matched = list(seen.values())

    def sort_key(r):
        dep = r.get("dependency", "")
        if dep == "run-before-others":
            return (0, r["id"])
        if dep == "after-tts":
            return (1, r["id"])
        return (2, r["id"])

    matched.sort(key=sort_key)

    contracts = []
    for r in matched:
        for c in r.get("contracts", []):
            if c not in contracts:
                contracts.append(c)

    return {
        "matched_rule_ids": [r["id"] for r in matched],
        "segments": [
            {
                "id": r["id"],
                "contentType": r.get("trigger", {}).get("contentType", ""),
                "segment": r.get("segment"),
                "alternatives": r.get("alternatives"),
                "dependency": r.get("dependency"),
                "params": r.get("params"),
                "contracts": r.get("contracts"),
                "decision": r.get("decision"),
            }
            for r in matched
        ],
        "contracts": contracts,
    }


def render_human(result):
    """人类可读的方案表。"""
    lines = []
    lines.append("命中的路由规则：%s" % ", ".join(result["matched_rule_ids"]) or "(无)")
    for seg in result["segments"]:
        head = "[%s] %s → %s" % (seg["id"], seg["contentType"], seg["segment"])
        if seg.get("alternatives"):
            head += "（备选: %s）" % ", ".join(seg["alternatives"])
        if seg.get("dependency"):
            head += "  依赖: %s" % seg["dependency"]
        lines.append("  " + head)
        if seg.get("decision"):
            lines.append("      决策提示: %s" % seg["decision"])
    if result["contracts"]:
        lines.append("编排契约：")
        for c in result["contracts"]:
            lines.append("  - %s" % c)
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description="段级视频路由决策")
    parser.add_argument("text", nargs="?", help="任务描述文本")
    parser.add_argument("--json", dest="as_json", action="store_true", help="输出 JSON")
    args = parser.parse_args(argv)

    text = args.text if args.text is not None else sys.stdin.read()
    rules = load_rules()
    result = route(text, rules)
    # 注入总装提示
    with open(ROUTING_JSON, encoding="utf-8") as f:
        result["assembly"] = json.load(f).get("assembly", {})

    if args.as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(render_human(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
