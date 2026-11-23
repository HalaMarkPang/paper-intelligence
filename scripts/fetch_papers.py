#!/usr/bin/env python3
"""按 profile 抓取论文（arXiv RSS + HuggingFace Daily Papers），自包含无外部项目依赖。

用法：
    python3 fetch_papers.py --profile ../assets/profiles/customer-service.json \
        --start 2026-08-19 --end 2026-08-25 --out /tmp/paper_fetched.jsonl

输出：JSONL，每行一篇论文的元数据（paper_id/title/authors/abstract/url/
published_date/source/categories/pdf_url）。不做 LLM 分析，分析交给 Agent。
"""

from __future__ import annotations

import argparse
import json
import re
import ssl
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date, timedelta
from email.utils import parsedate_to_datetime

RSS_URL = "https://rss.arxiv.org/rss/{category}"
HF_API = "https://huggingface.co/api/daily_papers"


def ssl_ctx() -> ssl.SSLContext:
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


def _get(url: str, timeout: int = 30) -> bytes | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "PaperIntel/1.0 (research)"})
        with urllib.request.urlopen(req, timeout=timeout, context=ssl_ctx()) as r:
            return r.read()
    except Exception as exc:
        print(f"[fetch] 请求失败 {url}: {exc}", file=sys.stderr)
        return None


def compile_keywords(keywords: list[str]) -> list[re.Pattern]:
    pats = []
    for kw in keywords:
        esc = re.escape(kw.lower()).replace(r"\-", r"[\s\-]").replace(r"\ ", r"[\s\-]")
        pats.append(re.compile(esc, re.IGNORECASE))
    return pats


def matches(text: str, pats: list[re.Pattern]) -> bool:
    low = text.lower()
    return any(p.search(low) for p in pats)


def parse_rss_date(s: str) -> str:
    if not s:
        return ""
    try:
        return parsedate_to_datetime(s).strftime("%Y-%m-%d")
    except Exception:
        return s[:10] if len(s) >= 10 else ""


def fetch_arxiv(categories: list[str], patterns: list[re.Pattern],
                start: date, end: date) -> list[dict]:
    seen, out = set(), []
    for i, cat in enumerate(categories):
        xml = _get(RSS_URL.format(category=cat))
        if xml is None:
            continue
        try:
            root = ET.fromstring(xml)
        except ET.ParseError as exc:
            print(f"[arxiv] XML 解析失败 {cat}: {exc}", file=sys.stderr)
            continue
        channel = root.find("channel")
        if channel is None:
            continue
        n_total, n_match = 0, 0
        for item in channel.findall("item"):
            n_total += 1
            link = item.findtext("link", "")
            arxiv_id = link.split("/abs/")[-1] if "/abs/" in link else link
            if arxiv_id in seen:
                continue
            title = item.findtext("title", "").strip().replace("\n", " ")
            desc = item.findtext("description", "")
            abstract = desc
            if "Abstract:" in desc:
                abstract = desc.split("Abstract:", 1)[1]
            abstract = abstract.replace("\n", " ").strip()
            pub = parse_rss_date(item.findtext("pubDate", ""))
            # 窗口过滤：RSS 通常只含当日新论文，仍按发布日兜底过滤
            if pub and not (start.isoformat() <= pub <= end.isoformat()):
                continue
            if not matches(f"{title} {abstract}", patterns):
                continue
            creator = item.findtext("{http://purl.org/dc/elements/1.1/}creator", "")
            authors = [a.strip() for a in creator.split(",") if a.strip()]
            cats = [c.text for c in item.findall("category") if c.text]
            pdf = link.replace("/abs/", "/pdf/") + ".pdf" if "/abs/" in link else None
            seen.add(arxiv_id)
            out.append({
                "paper_id": arxiv_id, "title": title, "authors": authors,
                "abstract": abstract, "url": link, "published_date": pub,
                "source": "arxiv", "categories": cats, "pdf_url": pdf,
            })
            n_match += 1
        print(f"[arxiv] {cat} ({i+1}/{len(categories)}): {n_total} 篇, {n_match} 命中关键词",
              file=sys.stderr)
        if i < len(categories) - 1:
            time.sleep(1)
    return out


def fetch_hf(start: date, end: date, seen: set) -> list[dict]:
    out = []
    cur = start
    while cur <= end:
        ds = cur.isoformat()
        raw = _get(f"{HF_API}?date={ds}", timeout=15)
        cur += timedelta(days=1)
        if raw is None:
            continue
        try:
            data = json.loads(raw.decode("utf-8"))
        except Exception:
            continue
        cnt = 0
        for item in data:
            pd = item.get("paper", {})
            pid = pd.get("id", "")
            if not pid or pid in seen:
                continue
            authors = [a.get("name", "") for a in pd.get("authors", [])
                       if a.get("name") and not a.get("hidden", False)]
            pub_raw = pd.get("publishedAt", "")
            seen.add(pid)
            out.append({
                "paper_id": pid,
                "title": item.get("title", "") or pd.get("title", ""),
                "authors": authors,
                "abstract": item.get("summary", "") or pd.get("summary", ""),
                "url": f"https://huggingface.co/papers/{pid}",
                "published_date": pub_raw[:10] if pub_raw else ds,
                "source": "huggingface",
                "categories": pd.get("ai_keywords", [])[:5],
                "pdf_url": f"https://arxiv.org/pdf/{pid}",
                "_upvotes": pd.get("upvotes", 0),
            })
            cnt += 1
        print(f"[hf] {ds}: {cnt} 篇", file=sys.stderr)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="按 profile 抓取论文，输出 JSONL")
    ap.add_argument("--profile", required=True, help="检索对象 profile JSON 路径")
    ap.add_argument("--start", required=True, help="窗口起始 YYYY-MM-DD")
    ap.add_argument("--end", required=True, help="窗口结束 YYYY-MM-DD")
    ap.add_argument("--out", required=True, help="输出 JSONL 路径")
    args = ap.parse_args()

    with open(args.profile, encoding="utf-8") as f:
        profile = json.load(f)
    start, end = date.fromisoformat(args.start), date.fromisoformat(args.end)

    categories = profile.get("arxiv_categories", [])
    keywords = []
    for d in profile.get("research_directions", []):
        keywords.extend(d.get("keywords", []))
    patterns = compile_keywords(keywords)

    print(f"[fetch] profile={profile.get('profile_id')} 窗口 {args.start}~{args.end} "
          f"分类 {len(categories)} 个 关键词 {len(keywords)} 个", file=sys.stderr)

    arxiv_papers = fetch_arxiv(categories, patterns, start, end)
    seen = {p["paper_id"] for p in arxiv_papers}
    hf_papers = fetch_hf(start, end, seen)
    all_papers = arxiv_papers + hf_papers

    with open(args.out, "w", encoding="utf-8") as f:
        for p in all_papers:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")

    print(json.dumps({
        "fetched": len(all_papers), "arxiv": len(arxiv_papers),
        "huggingface": len(hf_papers), "out_file": args.out,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
