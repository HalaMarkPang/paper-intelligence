#!/usr/bin/env python3
"""解析论文周报的覆盖窗口（滚动 7 天）。

口径：以 Asia/Shanghai 的「昨天」为窗口结束日（最近一个已过完的自然日），
往前共 7 天，即 [昨天-6, 昨天]。运行当天不计入，避免半日窗口。

示例：若今天是 2026-09-17，则窗口为 2026-09-10 ~ 2026-09-16。
"""

from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo


def resolve(today: date) -> dict:
    """给定运行日，返回滚动 7 天窗口 [昨天-6, 昨天]。"""
    period_end = today - timedelta(days=1)
    period_start = period_end - timedelta(days=6)
    iso_year, iso_week, _ = period_start.isocalendar()
    return {
        "period_start": period_start.isoformat(),
        "period_end": period_end.isoformat(),
        "start_datetime": f"{period_start.isoformat()}T00:00:00",
        "end_datetime": f"{period_end.isoformat()}T23:59:59",
        "week_label": f"{iso_year}-W{iso_week:02d}",
        "days": 7,
        "mode": "rolling_7d",
        "timezone": "Asia/Shanghai",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="解析论文周报覆盖窗口（滚动近 7 天）")
    parser.add_argument("--today", help="覆盖当前 Asia/Shanghai 日期用于测试 (YYYY-MM-DD)")
    args = parser.parse_args()
    today = (date.fromisoformat(args.today) if args.today
             else datetime.now(ZoneInfo("Asia/Shanghai")).date())
    print(json.dumps(resolve(today), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
