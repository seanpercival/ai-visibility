#!/usr/bin/env python3
"""
weekly_rescan.py - Re-scan a site, append the score to a history CSV, and print
the trend. Zero-dependency. Designed to be run on a schedule (see below) so a
brand's AEO score is tracked over time rather than as a one-shot.

Usage:
    python3 weekly_rescan.py https://example.com --brand "Example" \
        --history history.csv

Schedule it:
- Cowork / Claude: ask Claude to "run the AEO re-scan for example.com every
  Monday and tell me if the score dropped" (creates a scheduled task).
- Cron (weekly, Mondays 8am):
    0 8 * * 1 cd /path/to/ai-visibility/scripts && python3 weekly_rescan.py \
        https://example.com --brand "Example" --history /path/history.csv
"""

import argparse
import csv
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scan


def main():
    ap = argparse.ArgumentParser(description="Scheduled AEO re-scan with trend history.")
    ap.add_argument("url")
    ap.add_argument("--brand", default="")
    ap.add_argument("--history", default="aeo_history.csv")
    ap.add_argument("--no-apis", action="store_true")
    args = ap.parse_args()

    url = args.url if args.url.startswith("http") else "https://" + args.url
    results, meta = scan.run_checks(url, args.brand.strip(), not args.no_apis)
    total, by, gate = scan.score(results)

    row = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
        "url": meta["final_url"],
        "brand": args.brand,
        "score": total,
        "access_gate_failed": gate,
        "offsite": by.get("offsite", {}).get("pts", 0),
        "content": by.get("content", {}).get("pts", 0),
        "entity": by.get("entity", {}).get("pts", 0),
    }

    exists = os.path.isfile(args.history)
    with open(args.history, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(row.keys()))
        if not exists:
            w.writeheader()
        w.writerow(row)

    # trend
    prev = None
    try:
        with open(args.history) as f:
            rows = [r for r in csv.DictReader(f) if r["url"] == meta["final_url"]]
        if len(rows) >= 2:
            prev = int(rows[-2]["score"])
    except (OSError, ValueError, KeyError):
        pass

    print(f"AEO score for {meta['final_url']}: {total}/100 ({scan.band(total)})")
    if prev is not None:
        delta = total - prev
        arrow = "up" if delta > 0 else "down" if delta < 0 else "flat"
        print(f"  vs last run: {prev} -> {total}  ({arrow} {abs(delta)})")
        if delta <= -5:
            print("  ALERT: score dropped 5+ points - check crawler access and recent site changes.")
    print(f"  History: {args.history}")


if __name__ == "__main__":
    main()
