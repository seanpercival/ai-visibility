---
name: ai-visibility
description: >-
  Audit and improve how a brand appears in AI answer engines (ChatGPT, Claude,
  Perplexity, Gemini, Google AI Overviews). Use for AEO, GEO, "answer engine
  optimization", "generative engine optimization", "AI visibility", "LLM
  visibility", "AI search", "how does my brand show up in ChatGPT/Claude", or
  when someone wants to "scan my site for AI" or get recommended by AI
  assistants. Has three modes — Scan a URL, Measure share-of-voice, and
  Optimize content — backed by a bundled scanner and reference data.
license: MIT
---

# AI Visibility (AEO / GEO)

Make a brand show up — accurately — when people ask AI assistants for
recommendations. This skill scans a site, measures how often the brand appears
in AI answers, and generates the fixes.

It is built on evidence, not hype. Read **Operating principles** before doing
anything — they are what separate this from the snake oil in this category.

---

## Operating principles (non-negotiable)

1. **Frequency, not rank.** AI answers are non-deterministic — the same prompt
   returns a different brand list >99% of the time, the same *order* ~1 in 1,000
   runs. Never report an "AI ranking position." Report *appearance frequency* and
   *share of voice* across many runs.

2. **Off-site beats on-site.** Branded mentions across third-party sites
   correlate ~0.66 with AI visibility; backlinks ~0.22; a brand's own page count
   ~0.17 (no real relationship). Weight recommendations accordingly: reviews,
   Reddit, Wikipedia, and best-of lists outrank "write more blog posts."

3. **Measure per engine, never blend.** Cross-engine source overlap is ~10–20%.
   A single blended score is misleading.

4. **Be honest about weak levers.** Schema moves citations ~2% (noise) — keep it
   for entity clarity. `llms.txt` isn't consumed by AI search engines. Keyword
   stuffing *hurts*. Say so.

5. **AI mentions ≠ traffic, yet** (<1% of web traffic). Frame as brand presence
   with a compounding head start, not a performance channel.

6. **Never fabricate.** Report only what a check actually found. A check that
   couldn't run is "not checked," never "passed."

---

## Getting started — the interactive flow

When this skill triggers, run this flow. Guide the user; don't make them format
a perfect request. Use **AskUserQuestion** (multiple-choice) for each prompt
below, always leaving the built-in free-text "Other" as an escape hatch.

### Step 0 — Resolve the target domain (infer first, then ask)

Do **not** open with a blank "what's your URL?" if you can infer it. In order:

1. **Use what's in front of you.** A domain the user just named; the site in the
   current message; the project/folder name; files open in the session that
   reveal a domain (`package.json` homepage, `CNAME`, a sitemap, deploy config,
   a Shopify/store connector).
2. **Check memory.** If a saved memory names the user's brand, site, or domain,
   use it. (A brand/domain fact is often already stored from earlier work.)
3. **One strong candidate → confirm it** with a single AskUserQuestion
   ("Scan `example.com`?  Yes / Pick another") rather than an open prompt.
4. **Unknown or several candidates → ask** with AskUserQuestion. Offer the
   candidates you found as options plus "Other". Capture the **brand name** too
   (needed for off-site/entity checks) — infer it from the domain, or ask in the
   same round.

Only fall back to a plain open-ended question if AskUserQuestion isn't available.

### Step 1 — Offer enrichment (optional API keys)

The URL scan needs nothing. Live multi-engine measurement (Mode B) is richer but
optional. After the domain is set, ask with AskUserQuestion whether to enrich:

- **"Basic scan"** (default, works now) — on-site + entity + off-site signals.
- **"Add AI API keys for live share-of-voice"** — measures how often the brand
  actually appears in ChatGPT / Perplexity / Claude / Gemini. If chosen, tell
  them to set whichever env vars they have — *any one is enough to start*:
  `OPENAI_API_KEY`, `PERPLEXITY_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`.
  Perplexity is the most representative (it retrieves live web). **Never ask them
  to paste a key into chat** — it's an environment variable they set themselves.

Keys are optional enrichment, never a blocker. If skipped, run the basic scan and
note the manual "lite panel" is available anytime.

### Step 2 — Run the scan and present

Run the scanner (Mode A), present using `assets/report_template.md`. Lead with the
score and the biggest gap. If the **Access gate failed**, lead with that.

### Step 3 — Offer the weekly re-scan (after every scan)

AEO shifts monthly with model updates, so a one-shot score has a short shelf life.
After presenting results, ask with AskUserQuestion whether to track it:

- **"Set up a weekly re-scan"** — schedule `weekly_rescan.py` to run weekly, log
  the score to a history CSV, and alert on a 5+ point drop.
- **"Not now."**

If yes, confirm cadence (default: Monday morning) and set it up per **Scheduling**
below. This closes the loop from one-off audit to ongoing monitoring — the single
thing that most separates a real practice from a drive-by report.

---

## The three modes

### Mode A — Scan

After Step 0/1 above, run:

```bash
python3 scripts/scan.py https://example.com --brand "Example" --json out.json
```

Zero-dependency (Python 3.8+ stdlib). Fetches `robots.txt`, raw HTML,
`sitemap.xml`, and free public APIs (Wikipedia, Wikidata, Reddit, Trustpilot),
runs the 31-point checklist in `reference/checklist.md`, prints a scored report.

Present: executive summary (score, biggest problem, top 3 fixes) → Quick Wins vs
Strategic Investments → offer Mode C or Mode B. If the **Access gate failed** (AI
bots blocked, or JS-only content), lead with it — nothing else matters first.

If Python is unavailable, fetch the URL and `robots.txt` yourself and walk
`reference/checklist.md` by hand.

### Mode B — Measure (share of voice)

Quantify how often the brand appears in AI answers.

1. Build a panel with the buckets in `reference/prompt_library.md` (category,
   alternative-to, use-case, brand, trust). Ground it in real buyer language.
2. Generate and run:

```bash
python3 scripts/prompt_panel.py generate --brand "Example" --competitors "A,B" --category "..." --out panel.json
python3 scripts/prompt_panel.py run --config panel.json --runs 5
```

3. Engines run when their API key (Step 1) is present; otherwise the script prints
   the panel for manual logged-out testing. Base model APIs reflect
   *training-knowledge* visibility; Perplexity's API retrieves live web. Label
   accordingly.
4. Report a **distribution, not a point**: "appears in 4 of 5 runs on Perplexity;
   12% share of voice vs the leader's 38%." Re-baseline after model updates.

### Mode C — Optimize (generate the fixes)

Turn findings into artifacts, drawing on the reference files.

- **Crawler access patch** — corrected `robots.txt` (`reference/crawler_tokens.md`).
- **Answer-first rewrites** — self-contained ~40–60 word answers per section; add
  statistics, quotations, cited sources (Princeton GEO tactics); cut hedging and
  keyword stuffing. Prompts in `reference/prompt_library.md`.
- **Structured data** — `Organization`+`sameAs`, `Article`, `Product`, `FAQPage`
  from `reference/schema_templates.md` (positioned as entity clarity, not a hack).
- **Earned-media target list** — the highest-leverage output: specific subreddits,
  review platforms (Trustpilot / G2 / Capterra / Gartner by vertical), best-of
  listicles, and Wikipedia/Wikidata gaps.
- **Bing Webmaster Tools** — flag if unregistered; Bing feeds ChatGPT and Copilot.

---

## Scheduling (Step 3 setup)

Run `weekly_rescan.py` on a schedule to track the score over time:

```bash
python3 scripts/weekly_rescan.py https://example.com --brand "Example" --history history.csv
```

It appends `timestamp, url, brand, score, pillars` to the CSV and prints the delta
vs the previous run (alerting on a 5+ point drop).

To automate it:
- **In Cowork / an agent environment:** use the environment's scheduling
  capability to create a recurring task that runs the command weekly (e.g. "run
  the AEO re-scan for example.com every Monday at 8am and tell me if the score
  dropped"). Confirm site, brand, and cadence with the user first.
- **Anywhere else:** add the cron line documented in `weekly_rescan.py`'s header.

---

## Scoring model

Five pillars. **Access is a gate** — if AI crawlers can't read the site, the total
is capped at 40.

| Pillar | Points | Measures |
|---|---|---|
| 1. Crawler Access & Renderability | **Gate** | AI bots allowed; content in raw HTML; sitemap; canonical |
| 2. Off-site Authority & Earned Media | 30 | Wikipedia/Wikidata, reviews, Reddit, YouTube, mentions |
| 3. Content Citation-Readiness | 30 | Answer-first, stat/quote/citation density, question headers, tables, freshness |
| 4. Entity Clarity | 20 | `Organization`+`sameAs`, knowledge-graph, NAP |
| 5. Live AI Visibility | 20 | Appearance frequency / share of voice (only if Mode B is run) |

70+ = effective foundation; most first scans land 25–45. Full logic:
`reference/checklist.md`.

---

## Reference files

- `reference/checklist.md` — the 31 checks, detection logic, weights.
- `reference/engine_cheatsheet.md` — per-engine index & tactics (incl. Claude/Brave).
- `reference/crawler_tokens.md` — bot tokens + robots.txt rules + sample file.
- `reference/schema_templates.md` — JSON-LD library (honestly positioned).
- `reference/prompt_library.md` — measurement panels + optimization prompts.
- `assets/report_template.md` — output skeleton.

---

## Output format

Follow `assets/report_template.md`: executive summary → severity-tagged findings
(`[found] → [why] → [fix]`) → Quick Wins vs Strategic Investments → follow-up menu.
Keep prose tight. Lead with the answer. Don't bury a gate failure.

## Graceful degradation

- No Python → analyze manually against the checklist.
- No API keys → run the lite panel and label it.
- Fetch blocked / JS-only → say so; recommend server-side rendering.
- Brand absent from Wikipedia/Wikidata/reviews → that's a *finding*, not an error.
- AskUserQuestion unavailable → ask in plain text instead.

---

*`ai-visibility` skill by Sean Percival — https://seanpercival.com · MIT licensed.*
