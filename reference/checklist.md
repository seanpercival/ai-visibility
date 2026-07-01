# The 31-Point AEO Checklist

Grouped into 5 pillars. `scan.py` automates most of these; this file is the
canonical logic + rationale (for hand-audits and for explaining findings).

**Scoring:** Off-site 30 · Content 30 · Entity 20 · Technical 20 (bonus) = 100.
**Access is a GATE** — any Access failure caps the total at 40. Checks that
can't run (blocked APIs) are excluded from the denominator, not scored as fails.

Evidence anchors: Princeton GEO paper (arXiv 2311.09735); Ahrefs 75K-brand
correlations; Vercel 500M-crawler study; Seer/Trustpilot 800K study.

---

## (A) Crawler Access & Renderability — GATE

| # | Check | Detection | Why |
|---|---|---|---|
| A1 | AI search/user agents not `Disallow`'d | Parse robots.txt; test `/` for `OAI-SearchBot`, `Claude-SearchBot`, `Claude-User`, `PerplexityBot`, `Googlebot`, `Bingbot` | Blocked = cannot be cited by that engine |
| A2 | Content is server-rendered, not JS-only | Count visible words in raw HTML; detect framework shells (`#root`, `#__next`, react/vue/ng) | AI crawlers don't execute JS (Vercel: 500M+ GPTBot requests, zero JS) — JS-only content is invisible |
| A3 | Page reachable, 200, HTTPS | HTTP status + scheme of final URL | Baseline accessibility |

## (B) / (E) Technical & Freshness — bonus 20

| # | Check | Detection | Why |
|---|---|---|---|
| T1 | sitemap.xml present/referenced | GET `/sitemap.xml` or `Sitemap:` in robots | Crawl coverage |
| T2 | Canonical in raw HTML | `<link rel=canonical>` in source (not JS-injected) | Indexing clarity |
| T3 | llms.txt (INFORMATIONAL) | GET `/llms.txt` | **Not a citation driver** (97% never fetched). Report, don't score. Recommend only for docs/dev sites |
| T4 | Image alt coverage | % `<img>` with non-empty `alt` | Multimodal signal; quality proxy |

## (C) Content Citation-Readiness — 30

| # | Check | Detection | Why |
|---|---|---|---|
| C1 | Answer-first capsule | A top paragraph of ~20–90 words, complete sentence | ~44% of AI citations come from the first ~30% of a page |
| C2 | Evidence density ⭐ | Count stats (`%`, `$`, million/billion/x), `<blockquote>`, authoritative external links | **Top Princeton tactics:** quotes +42%, stats +33%, cite sources +28% |
| C3 | Question-style H2/H3 | Headings ending `?` or starting how/what/why/best… | Matches passage-level retrieval / query fan-out |
| C4 | Exactly one H1 | Count `<h1>` | Unambiguous topic |
| C5 | Tables + lists | `<table>` w/ `<th>`, `<ul>/<ol>` | AI reproduces these heavily for "best/compare/steps" |
| C6 | Freshness signal | `dateModified`, `<time>`, "Updated…" text | AI-cited content is ~26% fresher on average |
| — | (Penalty) keyword stuffing | keyword over-density | Princeton: stuffing **hurts** (−~10% on Perplexity) |

## (D) Off-site Authority & Earned Media — 30 (the highest-correlation pillar)

| # | Check | Detection | Why |
|---|---|---|---|
| D1 | Wikipedia entry | MediaWiki `opensearch` API | #1 cited domain for ChatGPT; core training data |
| D2 | Wikidata entity | `wbsearchentities` API | Machine-readable KG anchor; feeds Google KG |
| D3 | Reddit presence | `reddit.com/search.json` (rate-limits → verify manually) | Top AI-cited source across engines |
| D4 | Review platforms | Trustpilot `/review/{domain}`; G2/Capterra/Gartner by vertical | Active reviews → cited ~75% vs ~1% (Seer, 800K responses) |
| D5 | Brand-mention volume | SERP API (approx) | **Strongest single correlate:** mentions 0.66 vs backlinks 0.22 |

*Not auto-checked (do manually or with a SERP/YouTube API):* YouTube channel
(~200× any other video source), Crunchbase, G2/Capterra/Gartner presence,
best-of listicle inclusion, consistent NAP across the web.

## (E-entity) Entity Clarity — 20

| # | Check | Detection | Why |
|---|---|---|---|
| N1 | Organization + `sameAs` | JSON-LD `Organization`/`LocalBusiness` with `sameAs[]` | Strongest entity/disambiguation signal |
| N2 | JSON-LD in raw HTML | `<script type=application/ld+json>` in source | Must be server-rendered to be seen |
| N3 | Title + meta description | `<title>` ~50–60 chars; `meta description` ~120–160 | Topic identity + summary the engine can lift |

---

## Interpreting the score

- **70+** — effective foundation; focus shifts to off-site + measurement.
- **50–69** — real gaps; work the Quick Wins, then earned media.
- **Under 50** — likely an Access gate failure or missing entity/off-site base.
- Most brands' **first** scan lands 25–45. That's normal, not a crisis.

## Honesty rules baked into scoring
- A blocked/rate-limited external check is **not** a fail — it's excluded and
  flagged, so the score never punishes what it couldn't verify.
- llms.txt and schema are **not** treated as citation levers.
- The scan covers on-site + entity signals only; live share-of-voice is a
  separate measurement (`prompt_panel.py`).
