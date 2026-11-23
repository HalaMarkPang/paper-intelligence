#!/usr/bin/env python3
"""校验论文周报分析产出的结构合法性与文风红线，profile 驱动。

检查项：
  1. 每篇含四段必需字段（summary_zh/key_insight/inspiration/actionable_idea）+ relevance_score/title/url
  2. 入选篇数 <= profile.max_papers；入选分 >= profile.relevance_threshold
  3. 归属红线：summary_zh / key_insight / actionable_idea 三段不得出现业务线名称
     （痛点/方法/局限写的是论文本身，业务线只允许出现在 inspiration 段）
  4. 无模板兜底文案

用法：
    python3 validate_selection.py \
        --profile ../assets/profiles/customer-service.json \
        --analysis-file /tmp/paper_analysis.jsonl
"""

from __future__ import annotations

import argparse
import json
import sys

REQUIRED = ["relevance_score", "title", "url",
            "summary_zh", "key_insight", "inspiration", "actionable_idea"]
PAPER_SCOPED = ["summary_zh", "key_insight", "actionable_idea"]  # 不得含业务线名
TEMPLATE_PHRASES = [
    "该论文在", "方面有重要贡献", "未发现显著的可迁移洞察",
    "暂不建议优先跟进", "具有显著的迁移潜力", "值得重点关注",
]


def main() -> int:
    ap = argparse.ArgumentParser(description="校验周报分析产出结构与红线")
    ap.add_argument("--profile", required=True)
    ap.add_argument("--analysis-file", required=True)
    args = ap.parse_args()

    with open(args.profile, encoding="utf-8") as f:
        profile = json.load(f)
    threshold = profile.get("relevance_threshold", 3)
    max_papers = profile.get("max_papers", 10)
    display_name = profile.get("display_name", "")
    # 业务线关键词：display_name 及其去掉「 Agent」等后缀的核心词
    scope_terms = {display_name}
    core = display_name.replace(" Agent", "").replace("Agent", "").strip()
    if core:
        scope_terms.add(core)
    scope_terms = {t for t in scope_terms if t}

    papers = []
    with open(args.analysis_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                papers.append(json.loads(line))

    errors, warnings = [], []
    selected = [p for p in papers if p.get("relevance_score", 0) >= threshold]

    if len(selected) > max_papers:
        errors.append(f"入选 {len(selected)} 篇 > 上限 {max_papers} 篇")

    for i, p in enumerate(papers):
        tag = p.get("title", f"#{i}")[:40]
        for field in REQUIRED:
            if field not in p or p.get(field) in ("", None):
                errors.append(f"[{tag}] 缺字段: {field}")
        # 归属红线
        for field in PAPER_SCOPED:
            val = str(p.get(field, ""))
            for term in scope_terms:
                if term and term in val:
                    errors.append(
                        f"[{tag}] 归属错误: {field} 段出现业务线名「{term}」"
                        f"（该段应描述论文本身，业务线只能出现在 inspiration 段）")
        # 模板兜底
        blob = " ".join(str(p.get(k, "")) for k in PAPER_SCOPED + ["inspiration", "relevance_reason"])
        for phrase in TEMPLATE_PHRASES:
            if phrase in blob:
                errors.append(f"[{tag}] 含模板兜底文案: 「{phrase}」")
        # 数字纪律软提示：有数字但疑似无口径
        if not p.get("inspiration"):
            warnings.append(f"[{tag}] inspiration 为空")

    result = {
        "total": len(papers), "selected": len(selected),
        "max_papers": max_papers, "threshold": threshold,
        "errors": errors, "warnings": warnings,
        "passed": not errors,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
