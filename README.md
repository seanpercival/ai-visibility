# ai-visibility — an AEO / AI-Visibility skill for Claude

**Scan any website and find out why AI assistants do (or don't) recommend it — then fix it.**

Built by [Sean Percival](https://seanpercival.com). I made this to sharpen how my
own brands show up in AI answers, and I'm open-sourcing the whole thing.

`ai-visibility` is a [Claude](https://claude.com) skill that audits and improves a
brand's presence in AI answer engines — ChatGPT, Claude, Perplexity, Gemini, and
Google AI Overviews. It's built on evidence, not hype: it's deliberately honest
about what actually moves AI citations and what's snake oil.

> **AEO** = Answer Engine Optimization. **GEO** = Generative Engine Optimization.
> Same idea: getting recommended when someone asks an AI instead of Googling.

---

## Why this exists

People increasingly ask an AI for recommendations instead of scrolling a search
page. If the AI doesn't mention your brand — or describes it wrong — you're
invisible at the exact moment of decision. Most "AEO tools" charge $500/mo to tell
you a fake "AI ranking." This does the honest version, for free, and tells you the
few things that genuinely matter.

Three design truths it's built around, each from real data (sources at the bottom):

- **Frequency, not rank.** AI answers are non-deterministic — the same prompt
  returns a different brand list >99% of the time. There is no "rank." Anyone
  selling you one is selling baloney. This measures *how often* you appear.
- **Off-site beats on-site.** Branded mentions across third-party sites correlate
  ~0.66 with AI visibility; backlinks ~0.22; your own page count ~0.17 (basically
  zero). So it weights reviews, Reddit, Wikipedia, and best-of lists far above
  "write more blog posts."
- **Some famous levers are noise.** Schema markup moves AI citations ~2%. `llms.txt`
  is fetched by almost no AI engine (97% of files never get read). Keyword stuffing
  actively *hurts*. The skill says so plainly.

---

## What it does — three modes

| Mode | What you get |
|---|---|
| **Scan** | Paste a URL → a 0–100 AEO score across 5 pillars in ~60 seconds, with severity-tagged findings and fixes. |
| **Measure** | Run a prompt panel across engines to see how often your brand appears vs competitors (share of voice — never a fake rank). |
| **Optimize** | Generate the actual fixes: a corrected `robots.txt`, `Organization`+`sameAs` schema, answer-first content rewrites, and an earned-media target list. |

It's **guided**: when it runs, it resolves the target domain from context or memory
(only asking if it can't infer one), offers optional AI API keys to enrich the run
with live multi-engine measurement, and offers to schedule a weekly re-scan after
the first scan.

---

## How it works

### The scanner (`scripts/scan.py`)

Zero dependencies — Python 3.8+ standard library only. Given a URL it fetches
`robots.txt`, the **raw** HTML (what a non-JS-executing AI crawler actually sees),
`sitemap.xml`, and queries free public APIs (Wikipedia, Wikidata, Reddit,
Trustpilot). Then it runs a **31-point checklist** across five pillars and prints a
scored report.

### The scoring model

**Crawler Access is a gate.** If AI bots are blocked or your content is JavaScript-only
(invisible to AI crawlers, which don't run JS), the total is capped at 40 — because
nothing else matters until the bots can read you.

| Pillar | Points | What it measures |
|---|---|---|
| 1. Crawler Access & Renderability | **Gate** | AI bots allowed in robots.txt; content in raw HTML; sitemap; canonical |
| 2. Off-site Authority & Earned Media | 30 | Wikipedia/Wikidata, reviews, Reddit, brand mentions |
| 3. Content Citation-Readiness | 30 | Answer-first capsules, stat/quote/citation density, question headers, tables, freshness |
| 4. Entity Clarity | 20 | `Organization`+`sameAs`, knowledge-graph presence, NAP |
| 5. Live AI Visibility | 20 | Appearance frequency / share of voice (when you run Mode B) |

70+ is an effective foundation. Most first scans land 25–45 — that's normal.

### Honesty is a feature

When a check can't run — Reddit rate-limits the anonymous API, Trustpilot bot-blocks
the request — the scanner reports it as **"not verified"** and drops it from the
score, instead of faking a failure. The number never punishes what it couldn't
actually check. That's the whole point.

### Example output

```
==================================================================
  AI-VISIBILITY / AEO SCAN
==================================================================
  Site:   https://example.com
  Brand:  Example
  Score:  79/100   (Effective foundation)

  PILLARS
    - Crawler Access & Renderability (GATE)      25/25
    - Off-site Authority & Earned Media          12/12
    - Content Citation-Readiness                 16/30
    - Entity Clarity                             17/20
    - Technical & Freshness                      7/9

  CONTENT CITATION-READINESS
    [CRITICAL] Little quantitative evidence or sourcing — the strongest GEO lever.
               -> Add concrete stats, expert quotes, and cited sources.
    ...
```

---

## Install

### As a Claude skill (easiest)

Grab `ai-visibility.skill` from the [Releases](../../releases) page — or build it
yourself with `./build_skill.sh` — and install it in Claude. Or just drop the
`ai-visibility/` folder into your Claude skills directory. Claude loads `SKILL.md`
and triggers on "AEO", "AI visibility", "scan my site for AI", etc.

### Run the scripts directly (zero dependencies)

```bash
# Scan a site
python3 scripts/scan.py https://example.com --brand "Example"

# Measure share of voice (generate a panel, then run it)
python3 scripts/prompt_panel.py generate --brand "Example" --competitors "A,B" --category "widgets" --out panel.json
python3 scripts/prompt_panel.py run --config panel.json --runs 5

# Track the score over time (schedule this weekly)
python3 scripts/weekly_rescan.py https://example.com --brand "Example" --history history.csv
```

### Optional add-ons

- **MCP server** (only dependency in the project) — makes the scan callable from any
  MCP client: `pip install "mcp[cli]"` then `python3 scripts/mcp_server.py`.
- **Live multi-engine measurement** — add any of `OPENAI_API_KEY`,
  `PERPLEXITY_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY` in a local `.env`
  file (one `KEY=value` per line) or as env vars. Run
  `python3 scripts/prompt_panel.py keys` to see where to get each key and which
  are set. Without keys, the panel prints for manual logged-out testing.
  Perplexity's API is the most representative (it retrieves live web). See
  [`reference/api_keys.md`](reference/api_keys.md).

### Build the `.skill` bundle yourself

```bash
./build_skill.sh
```

---

## Repo layout

```
ai-visibility/
├── SKILL.md                    # the router: 3 modes, interactive flow, scoring, honesty rules
├── README.md                   # you're reading it
├── LICENSE                     # MIT
├── build_skill.sh              # builds the installable .skill bundle
├── scripts/
│   ├── scan.py                 # 31-point URL scanner → scored report + JSON
│   ├── prompt_panel.py         # share-of-voice measurement across engines
│   ├── weekly_rescan.py        # scheduled re-scan + trend history + drop alerts
│   └── mcp_server.py           # optional MCP wrapper
├── reference/
│   ├── checklist.md            # the 31 checks + detection logic + weights
│   ├── engine_cheatsheet.md    # per-engine index & tactics (incl. Claude → Brave)
│   ├── crawler_tokens.md       # exact bot tokens + robots.txt rules + a sample file
│   ├── schema_templates.md     # JSON-LD library (honestly positioned)
│   └── prompt_library.md       # measurement panels + content-optimization prompts
└── assets/
    └── report_template.md      # the output skeleton
```

---

## Limitations (stated honestly, because that's the brand)

- True multi-engine measurement needs API keys or a scraping service; base model
  APIs reflect training-knowledge visibility, not the live-search citations the
  consumer UIs show (Perplexity's API is the exception).
- Brand-mention *volume* needs a SERP API — v1 uses free APIs and flags the rest.
- Name-based entity matches (Wikipedia/Wikidata) should be human-confirmed.
- AI visibility ≠ traffic yet — LLMs send <1% of web traffic today. This is brand-
  presence work with a compounding head start, not a performance-marketing channel.

---

## The evidence base

This isn't vibes. Key sources:

- **Princeton GEO paper** (KDD 2024, arXiv [2311.09735](https://arxiv.org/abs/2311.09735)) — the only controlled study; adding statistics/quotations/citations lifts AI citations, keyword stuffing hurts.
- **Ahrefs**, 75K brands — [brand mentions vs. AI visibility correlations](https://ahrefs.com/blog/ai-brand-visibility-correlations/); [llms.txt is ignored](https://ahrefs.com/blog/llmstxt-study/); [schema ≈ noise](https://ahrefs.com/blog/schema-ai-citations/).
- **Vercel** — [AI crawlers don't execute JavaScript](https://vercel.com/blog/the-rise-of-the-ai-crawler) (500M+ requests).
- **Seer Interactive** — [reviews and AI citation rates](https://www.seerinteractive.com/insights/study-of-800k-ai-responses-how-reviews-shape-brand-presence-in-ai-search) (800K responses).
- **SparkToro** — [AI recommendations are non-deterministic](https://sparktoro.com/blog/new-research-ais-are-highly-inconsistent-when-recommending-brands-or-products/).
- Official crawler docs: [OpenAI](https://platform.openai.com/docs/bots), [Anthropic](https://support.claude.com/en/articles/8896518), [Perplexity](https://docs.perplexity.ai/guides/bots), [Google](https://developers.google.com/search/docs/crawling-indexing/google-common-crawlers).

---

## About the author

I'm **Sean Percival** — [seanpercival.com](https://seanpercival.com). I build
brands and the tools that grow them, I write and speak about startups, and I made
this because I wanted to know why AI assistants were (and weren't) recommending my
own products. If it's useful to you, great. If you improve it, send a PR.

Find more of what I'm building at **[seanpercival.com](https://seanpercival.com)**.

---

## License

[MIT](LICENSE) © Sean Percival. Use it, fork it, ship it.
