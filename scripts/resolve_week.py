#!/usr/bin/env python3
"""解析论文周报的覆盖窗口。

口径：每周三 11:00 运行，覆盖「上周三 00:00:00 ~ 本周二 23:59:59」，
即运行日往前推的完整 7 天（运行当天周三不计入，因为当天尚未过完）。

无论实际哪天运行，都以「最近一个已过完的周二」为窗口结束日，
从而保证窗口始终是完整的上周三到本周二 7 天。
"""

from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

# Python weekday(): Monday=0 ... Wednesday=2 ... Sunday=6
WEDNESDAY = 2
TUESDAY = 1


def resolve(today: date) -> dict:
    """给定运行日，返回覆盖窗口 [上周三, 本周二]。

    窗口结束 = 最近一个已过完的周二（含今天若今天就是周二之后）。
    以周三为运行日时：本周二是昨天，窗口 = 上周三 ~ 本周二，共 7 天。
    """
    # 找到最近的、不晚于今天的周二作为窗口结束日。
    # (today.weekday() - TUESDAY) % 7 = 距离上一个周二的天数。
    days_since_tuesday = (today.weekday() - TUESDAY) % 7
    period_end = today - timedelta(days=days_since_tuesday)
    period_start = period_end - timedelta(days=6)
    iso_year, iso_week, _ = period_start.isocalendar()
    return {
        "period_start": period_start.isoformat(),
        "period_end": period_end.isoformat(),
        "start_datetime": f"{period_start.isoformat()}T00:00:00",
        "end_datetime": f"{period_end.isoformat()}T23:59:59",
        "week_label": f"{iso_year}-W{iso_week:02d}",
        "days": 7,
        "timezone": "Asia/Shanghai",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="解析论文周报覆盖窗口（上周三~本周二）")
    parser.add_argument("--today", help="覆盖当前 Asia/Shanghai 日期用于测试 (YYYY-MM-DD)")
    args = parser.parse_args()
    today = (date.fromisoformat(args.today) if args.today
             else datetime.now(ZoneInfo("Asia/Shanghai")).date())
    print(json.dumps(resolve(today), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
