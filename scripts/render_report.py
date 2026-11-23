#!/usr/bin/env python3
"""渲染论文周报 HTML，自包含。

读取分析结果 JSONL（每行一篇，含 relevance_score 及四段字段）+ 顶部结论 HTML，
按 profile 的 relevance_threshold 过滤、按分数排序、按 max_papers 截断，渲染为周报。

用法：
    python3 render_report.py \
        --profile ../assets/profiles/customer-service.json \
        --analysis-file /tmp/paper_analysis.jsonl \
        --digest-file /tmp/paper_digest.html \
        --period-start 2026-08-19 --period-end 2026-08-25 \
        --out /tmp/weekly_report.html
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
TEMPLATE_PATH = SCRIPT_DIR.parent / "assets" / "report-template.html"


def load_jsonl(path: str) -> list[dict]:
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="渲染论文周报 HTML")
    ap.add_argument("--profile", required=True)
    ap.add_argument("--analysis-file", required=True, help="分析结果 JSONL")
    ap.add_argument("--digest-file", help="顶部结论 HTML 片段")
    ap.add_argument("--period-start", required=True)
    ap.add_argument("--period-end", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    try:
        from jinja2 import Template
    except ImportError:
        print("ERROR: 需要 jinja2（pip3 install jinja2）", file=sys.stderr)
        return 1

    with open(args.profile, encoding="utf-8") as f:
        profile = json.load(f)
    threshold = profile.get("relevance_threshold", 3)
    max_papers = profile.get("max_papers", 10)
    display_name = profile.get("display_name", "")

    papers = [p for p in load_jsonl(args.analysis_file)
              if p.get("relevance_score", 0) >= threshold]
    papers.sort(key=lambda p: p.get("relevance_score", 0), reverse=True)
    if len(papers) > max_papers:
        papers = papers[:max_papers]

    # 列表字段转字符串，兼容模板
    for p in papers:
        if isinstance(p.get("authors"), list):
            p["authors"] = ", ".join(str(a) for a in p["authors"])
        if isinstance(p.get("categories"), list):
            p["categories"] = ", ".join(str(c) for c in p["categories"])

    digest = ""
    if args.digest_file:
        with open(args.digest_file, encoding="utf-8") as f:
            digest = f.read()

    high_rel = sum(1 for p in papers if p.get("relevance_score", 0) >= 4)
    period_range = f"{args.period_start} ~ {args.period_end}"

    context = {
        "display_name": display_name,
        "period_label": f"{args.period_start}_{args.period_end}",
        "period_range": period_range,
        "total_papers": len(papers),
        "high_relevance_count": high_rel,
        "digest": digest,
        "papers": papers,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }

    template = Template(TEMPLATE_PATH.read_text(encoding="utf-8"))
    Path(args.out).write_text(template.render(**context), encoding="utf-8")

    print(json.dumps({
        "out_file": args.out, "papers_count": len(papers),
        "high_relevance": high_rel, "threshold": threshold, "max_papers": max_papers,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
