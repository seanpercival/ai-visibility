#!/usr/bin/env python3
"""
bot_traffic.py - AI bot-traffic analysis from a web-server access log.

The only non-probabilistic signal in AEO: which AI crawlers/agents *actually*
hit the site, how often, and what they fetched. Free equivalent of the "agent
analytics" commercial AEO platforms sell.

Works on standard nginx/Apache combined logs and most CDN log exports (any
line-per-request text where the user-agent string appears in the line).
Standard library only. Python 3.8+.

Usage:
    python3 bot_traffic.py access.log
    python3 bot_traffic.py access.log --top 10 --json out.json
    zcat access.log.*.gz | python3 bot_traffic.py -

Honesty notes:
- UA strings can be spoofed; for decisions that matter, verify against vendor
  IP ranges / reverse DNS.
- Agentic browsers (ChatGPT Atlas, Perplexity Comet, Claude for Chrome) present
  a normal browser UA and will NOT appear here. These counts are a floor.
"""

import argparse
import json
import re
import sys
from collections import defaultdict

# token -> (vendor, kind)  kind: search = powers citations, training = model
# training, fetch = user-triggered live fetch, other
BOTS = {
    "OAI-SearchBot":      ("OpenAI", "search"),
    "ChatGPT-User":       ("OpenAI", "fetch"),
    "GPTBot":             ("OpenAI", "training"),
    "Claude-SearchBot":   ("Anthropic", "search"),
    "Claude-User":        ("Anthropic", "fetch"),
    "ClaudeBot":          ("Anthropic", "training"),
    "PerplexityBot":      ("Perplexity", "search"),
    "Perplexity-User":    ("Perplexity", "fetch"),
    "Googlebot":          ("Google", "search"),
    "Google-Extended":    ("Google", "training"),
    "Bingbot":            ("Microsoft", "search"),
    "Applebot-Extended":  ("Apple", "training"),
    "Applebot":           ("Apple", "search"),
    "Meta-ExternalAgent": ("Meta", "training"),
    "Meta-ExternalFetcher": ("Meta", "fetch"),
    "CCBot":              ("Common Crawl", "training"),
    "Bytespider":         ("ByteDance", "training"),
    "Amazonbot":          ("Amazon", "search"),
    "DuckAssistBot":      ("DuckDuckGo", "search"),
}
# Longest tokens first so e.g. Applebot-Extended matches before Applebot.
ORDERED = sorted(BOTS, key=len, reverse=True)

DATE_RE = re.compile(r"\[(\d{2}/\w{3}/\d{4})")          # apache/nginx [01/Jul/2026
ISO_RE = re.compile(r"\b(\d{4}-\d{2}-\d{2})[T ]")        # json/CDN 2026-07-01T
PATH_RE = re.compile(r'"(?:GET|POST|HEAD)\s+(\S+)')


def classify(line):
    for tok in ORDERED:
        if tok in line:
            return tok
    return None


def main():
    ap = argparse.ArgumentParser(description="AI bot-traffic report from an access log.")
    ap.add_argument("logfile", help="path to access log, or - for stdin")
    ap.add_argument("--top", type=int, default=5, help="top paths per bot (default 5)")
    ap.add_argument("--json", default="", help="write full results to this JSON path")
    args = ap.parse_args()

    stream = sys.stdin if args.logfile == "-" else open(args.logfile, errors="replace")

    total_lines = 0
    hits = defaultdict(int)                 # token -> count
    paths = defaultdict(lambda: defaultdict(int))  # token -> path -> count
    dates = defaultdict(set)                # token -> dates seen
    all_dates = set()

    with stream:
        for line in stream:
            total_lines += 1
            m = DATE_RE.search(line) or ISO_RE.search(line)
            d = m.group(1) if m else None
            if d:
                all_dates.add(d)
            tok = classify(line)
            if not tok:
                continue
            hits[tok] += 1
            if d:
                dates[tok].add(d)
            pm = PATH_RE.search(line)
            if pm:
                paths[tok][pm.group(1)] += 1

    ai_total = sum(hits.values())
    print("=" * 66)
    print("  AI BOT TRAFFIC REPORT")
    print("=" * 66)
    print(f"  Requests scanned : {total_lines:,}")
    print(f"  AI bot requests  : {ai_total:,}"
          + (f"  ({ai_total / total_lines * 100:.2f}% of log)" if total_lines else ""))
    if all_dates:
        print(f"  Log date range   : {min(all_dates)} .. {max(all_dates)}")
    print()

    if not hits:
        print("  No known AI bot user agents found.")
        print("  Either AI engines aren't crawling this site (a finding in itself),")
        print("  or the log format doesn't include the user-agent string.")
        print("=" * 66)
        return

    by_kind = defaultdict(list)
    for tok, n in sorted(hits.items(), key=lambda kv: -kv[1]):
        by_kind[BOTS[tok][1]].append((tok, n))

    LABEL = {"search": "SEARCH / ANSWER BOTS (power citations)",
             "fetch": "USER-TRIGGERED FETCHERS (live answers)",
             "training": "TRAINING CRAWLERS",
             "other": "OTHER"}
    for kind in ("search", "fetch", "training", "other"):
        if kind not in by_kind:
            continue
        print(f"  {LABEL[kind]}")
        for tok, n in by_kind[kind]:
            vendor = BOTS[tok][0]
            days = f", {len(dates[tok])} day(s)" if dates.get(tok) else ""
            print(f"    {tok:<22} {vendor:<12} {n:>8,} hits{days}")
            for p, c in sorted(paths[tok].items(), key=lambda kv: -kv[1])[:args.top]:
                print(f"        {c:>6,}  {p[:80]}")
        print()

    # insights
    print("  READ-OUT")
    seen_search = {BOTS[t][0] for t in hits if BOTS[t][1] == "search"}
    for vendor, tok in [("OpenAI", "OAI-SearchBot"), ("Anthropic", "Claude-SearchBot"),
                        ("Perplexity", "PerplexityBot")]:
        if vendor not in seen_search:
            print(f"    [ ] No {tok} hits — {vendor}'s answer index may not have "
                  "this site. Check robots.txt and (for OpenAI) Bing indexing.")
    fetchers = [t for t in hits if BOTS[t][1] == "fetch"]
    if fetchers:
        print("    [+] User-triggered fetches present — real people are getting "
              "live AI answers that read this site.")
    print("    [i] Agentic browsers (Atlas/Comet/Claude for Chrome) use normal "
          "browser UAs and are invisible here — these counts are a floor.")
    print("=" * 66)

    if args.json:
        payload = {"total_requests": total_lines, "ai_requests": ai_total,
                   "bots": {t: {"vendor": BOTS[t][0], "kind": BOTS[t][1],
                                "hits": n, "days": sorted(dates.get(t, [])),
                                "top_paths": sorted(paths[t].items(),
                                                    key=lambda kv: -kv[1])[:args.top]}
                            for t, n in hits.items()}}
        with open(args.json, "w") as f:
            json.dump(payload, f, indent=2)
        print(f"[written] {args.json}")


if __name__ == "__main__":
    main()
