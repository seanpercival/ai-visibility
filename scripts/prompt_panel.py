#!/usr/bin/env python3
"""
prompt_panel.py - Measure a brand's share of voice in AI answers (Mode B).

Two subcommands:
  generate  Build a prompt-panel config from a brand + competitors + category.
  run       Run the panel N times per engine, aggregate appearance frequency,
            share of voice, and coarse sentiment. Report per engine.

Standard library only. Engines are called via their HTTP APIs when the matching
API key is present as an environment variable; engines without a key are skipped.

    OPENAI_API_KEY       -> openai      (gpt-4o-mini; model knowledge, no live web)
    PERPLEXITY_API_KEY   -> perplexity  (sonar; DOES retrieve live web)
    ANTHROPIC_API_KEY    -> anthropic   (claude; model knowledge unless tools added)
    GEMINI_API_KEY       -> gemini      (gemini-1.5-flash; model knowledge)

HONESTY NOTES (surface these in any report):
- AI answers are non-deterministic. Report *appearance frequency* across N runs,
  never a "rank". Same prompt returns the same brand list <1-in-100 runs.
- Base model APIs reflect *training-knowledge* visibility, not the live-search
  citations users see in the consumer UIs. Perplexity's API is the exception
  (it retrieves). For true consumer-UI citation tracking you need a scraping
  service or a commercial tool. Label results accordingly.
- Report per engine; never blend into one score (cross-engine overlap ~10-20%).

Usage:
  python3 prompt_panel.py generate --brand "Acme" --competitors "Foo,Bar" \
        --category "project management software" --out panel.json
  python3 prompt_panel.py run --config panel.json --runs 5 --json results.json
"""

import argparse
import json
import os
import re
import sys
import time
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

# --------------------------------------------------------------- panel gen

BUCKETS = {
    "category": [
        "What are the best {category} in 2026?",
        "Recommend the top 3 {category} for most people.",
        "What {category} do people recommend most?",
    ],
    "alternative": [
        "What is the best alternative to {competitor}?",
        "{brand} vs {competitor}: which is better?",
        "What are cheaper alternatives to {competitor}?",
    ],
    "use_case": [
        "I'm looking for {category}. What should I choose?",
        "What {category} is best for someone just getting started?",
    ],
    "brand": [
        "What is {brand}?",
        "Is {brand} any good?",
    ],
    "trust": [
        "What are the downsides of {brand}?",
        "Is {brand} legit and safe to use?",
    ],
}


def generate_panel(brand, competitors, category):
    prompts = []
    comp = competitors[0] if competitors else "the market leader"
    for bucket, templates in BUCKETS.items():
        for t in templates:
            text = t.format(brand=brand, competitor=comp, category=category or "tools")
            prompts.append({"bucket": bucket, "prompt": text})
    return {
        "brand": brand,
        "competitors": competitors,
        "category": category,
        "prompts": prompts,
    }


# --------------------------------------------------------------- engines

def _post(url, headers, payload, timeout=60):
    data = json.dumps(payload).encode("utf-8")
    req = Request(url, data=data, headers=headers, method="POST")
    try:
        with urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8", "replace"))
    except HTTPError as e:
        try:
            return {"_error": f"HTTP {e.code}: {e.read().decode('utf-8','replace')[:200]}"}
        except Exception:
            return {"_error": f"HTTP {e.code}"}
    except (URLError, TimeoutError, ValueError) as e:
        return {"_error": str(e)}


def call_openai(prompt):
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        return None
    out = _post("https://api.openai.com/v1/chat/completions",
                {"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                {"model": os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
                 "messages": [{"role": "user", "content": prompt}],
                 "temperature": 1.0})
    if "_error" in out:
        return f"[error] {out['_error']}"
    try:
        return out["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        return "[error] unexpected response"


def call_perplexity(prompt):
    key = os.environ.get("PERPLEXITY_API_KEY")
    if not key:
        return None
    out = _post("https://api.perplexity.ai/chat/completions",
                {"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                {"model": os.environ.get("PERPLEXITY_MODEL", "sonar"),
                 "messages": [{"role": "user", "content": prompt}]})
    if "_error" in out:
        return f"[error] {out['_error']}"
    try:
        return out["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        return "[error] unexpected response"


def call_anthropic(prompt):
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return None
    out = _post("https://api.anthropic.com/v1/messages",
                {"x-api-key": key, "anthropic-version": "2023-06-01",
                 "Content-Type": "application/json"},
                {"model": os.environ.get("ANTHROPIC_MODEL", "claude-3-5-haiku-20241022"),
                 "max_tokens": 1024,
                 "messages": [{"role": "user", "content": prompt}]})
    if "_error" in out:
        return f"[error] {out['_error']}"
    try:
        return "".join(b.get("text", "") for b in out["content"])
    except (KeyError, TypeError):
        return "[error] unexpected response"


def call_gemini(prompt):
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        return None
    model = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")
    out = _post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}",
                {"Content-Type": "application/json"},
                {"contents": [{"parts": [{"text": prompt}]}]})
    if "_error" in out:
        return f"[error] {out['_error']}"
    try:
        return "".join(p.get("text", "") for p in out["candidates"][0]["content"]["parts"])
    except (KeyError, IndexError):
        return "[error] unexpected response"


ENGINES = {"openai": call_openai, "perplexity": call_perplexity,
           "anthropic": call_anthropic, "gemini": call_gemini}

POS = re.compile(r"\b(best|great|excellent|leading|popular|recommend|reliable|powerful|top|strong|favorite)\b", re.I)
NEG = re.compile(r"\b(bad|poor|worst|avoid|expensive|limited|lacks?|weak|complaint|scam|risky|downside)\b", re.I)


def mentioned(text, name):
    return bool(re.search(r"\b" + re.escape(name) + r"\b", text, re.I))


def sentiment_near(text, name):
    """Coarse heuristic sentiment on sentences mentioning the brand."""
    hits = [s for s in re.split(r"(?<=[.!?])\s+", text) if mentioned(s, name)]
    if not hits:
        return None
    pos = sum(len(POS.findall(s)) for s in hits)
    neg = sum(len(NEG.findall(s)) for s in hits)
    if pos > neg:
        return "positive"
    if neg > pos:
        return "negative"
    return "neutral"


# --------------------------------------------------------------- run

def run_panel(cfg, runs, engines):
    brand = cfg["brand"]
    competitors = cfg.get("competitors", [])
    # Detect available engines by env var (no API call needed).
    active = {}
    keymap = {"openai": "OPENAI_API_KEY", "perplexity": "PERPLEXITY_API_KEY",
              "anthropic": "ANTHROPIC_API_KEY", "gemini": "GEMINI_API_KEY"}
    for name, fn in ENGINES.items():
        if engines and name not in engines:
            continue
        if os.environ.get(keymap[name]):
            active[name] = fn

    if not active:
        print("No engine API keys found. Set one or more of:")
        for k in keymap.values():
            print(f"   export {k}=...")
        print("\nPanel is ready to run once a key is set. Prompts:")
        for p in cfg["prompts"]:
            print(f"   [{p['bucket']}] {p['prompt']}")
        print("\nLite alternative: paste these prompts into ChatGPT/Claude/Perplexity")
        print("logged-out, run each 3-5x, and tally how often the brand appears.")
        return None

    results = {name: {"prompts": [], "appear": 0, "total": 0,
                      "sov_brand": 0, "sov_all": 0,
                      "sentiment": {"positive": 0, "neutral": 0, "negative": 0}}
               for name in active}

    for p in cfg["prompts"]:
        for name, fn in active.items():
            appear = 0
            for _ in range(runs):
                resp = fn(p["prompt"]) or ""
                results[name]["total"] += 1
                if mentioned(resp, brand):
                    appear += 1
                    results[name]["appear"] += 1
                    s = sentiment_near(resp, brand)
                    if s:
                        results[name]["sentiment"][s] += 1
                # share of voice: brand vs competitors mention counts
                bc = len(re.findall(r"\b" + re.escape(brand) + r"\b", resp, re.I))
                cc = sum(len(re.findall(r"\b" + re.escape(c) + r"\b", resp, re.I)) for c in competitors)
                results[name]["sov_brand"] += bc
                results[name]["sov_all"] += bc + cc
                time.sleep(0.2)
            results[name]["prompts"].append(
                {"prompt": p["prompt"], "bucket": p["bucket"],
                 "appeared": appear, "runs": runs})

    return results


def render_run(cfg, results, runs):
    if not results:
        return ""
    brand = cfg["brand"]
    out = ["=" * 64, f"  SHARE OF VOICE - {brand}   ({runs} runs/prompt)", "=" * 64,
           "  Frequency, not rank. Base model APIs reflect model knowledge,",
           "  not live-search citations (except Perplexity). Per-engine below.", ""]
    for name, d in results.items():
        freq = (d["appear"] / d["total"] * 100) if d["total"] else 0
        sov = (d["sov_brand"] / d["sov_all"] * 100) if d["sov_all"] else 0
        st = d["sentiment"]
        out.append(f"  {name.upper()}")
        out.append(f"    Appearance rate : {freq:.0f}%  ({d['appear']}/{d['total']} responses)")
        out.append(f"    Share of voice  : {sov:.0f}%  (vs {', '.join(cfg.get('competitors')) or 'competitors'})")
        out.append(f"    Sentiment       : +{st['positive']} / ~{st['neutral']} / -{st['negative']}")
        # weakest buckets
        weak = [p for p in d["prompts"] if p["appeared"] == 0]
        if weak:
            out.append(f"    Never appeared for: " + "; ".join(f'"{w["prompt"]}"' for w in weak[:3]))
        out.append("")
    out.append("  Re-baseline after any model update. Track the trend, not one run.")
    out.append("=" * 64)
    return "\n".join(out)


# --------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description="Measure brand share of voice in AI answers.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("generate", help="Build a panel config")
    g.add_argument("--brand", required=True)
    g.add_argument("--competitors", default="", help="comma-separated")
    g.add_argument("--category", default="")
    g.add_argument("--out", default="panel.json")

    r = sub.add_parser("run", help="Run a panel config")
    r.add_argument("--config", required=True)
    r.add_argument("--runs", type=int, default=5)
    r.add_argument("--engines", default="", help="comma-separated subset (default: all with keys)")
    r.add_argument("--json", default="")

    args = ap.parse_args()

    if args.cmd == "generate":
        comps = [c.strip() for c in args.competitors.split(",") if c.strip()]
        cfg = generate_panel(args.brand, comps, args.category)
        with open(args.out, "w") as f:
            json.dump(cfg, f, indent=2)
        print(f"[written] {args.out}  ({len(cfg['prompts'])} prompts)")
        print("Review/edit the prompts to match real buyer language, then:")
        print(f"   python3 prompt_panel.py run --config {args.out} --runs 5")

    elif args.cmd == "run":
        with open(args.config) as f:
            cfg = json.load(f)
        engines = [e.strip() for e in args.engines.split(",") if e.strip()]
        results = run_panel(cfg, args.runs, engines)
        report = render_run(cfg, results, args.runs)
        if report:
            print(report)
        if args.json and results:
            with open(args.json, "w") as f:
                json.dump({"config": cfg, "runs": args.runs, "results": results}, f, indent=2)
            print(f"\n[written] {args.json}")


if __name__ == "__main__":
    main()
