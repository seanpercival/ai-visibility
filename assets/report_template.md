# Report Template

Use this structure whenever presenting scan or measurement results. Lead with
the answer; keep prose tight; never bury an Access gate failure.

---

## AI-Visibility Report — {Brand}

**Site:** {url}  ·  **Scan date:** {date}
**Score:** {N}/100 — {band}
{if access gate failed: **⚠ Access gate failed — AI crawlers can't fully read this site. Fix this first; nothing else matters until it's done.**}
{if checks skipped: *Note: {k} checks couldn't be auto-verified (blocked/rate-limited) — verify manually. Score reflects verified checks only.*}

**Bottom line (3 sentences max):** the biggest gap, the highest-leverage fix,
and one line on share of voice vs a named competitor if known.

### Pillar scores
| Pillar | Score | Read |
|---|---|---|
| Crawler Access (gate) | {x}/25 | {pass/fail} |
| Off-site Authority | {x}/30 | {strength} |
| Content Citation-Readiness | {x}/30 | {strength} |
| Entity Clarity | {x}/20 | {strength} |
| Technical & Freshness | {x}/20 | {strength} |

### Findings
Severity-tagged; each is `[what we found] → [why it matters] → [fix]`.

| Severity | Finding | Why it matters | Fix |
|---|---|---|---|
| Critical | | | |
| High | | | |
| Medium | | | |

### Quick Wins — do this week (mostly on-site, < ~2 hrs each)
- [ ] …

### Strategic Investments — this quarter (off-site, compounding)
- [ ] … *(earned media: reviews, Reddit, best-of listicles, PR, Wikipedia/Wikidata)*

### What we did NOT measure
- Live share of voice across engines → run **Mode B** (`prompt_panel.py`).
- Brand-mention volume / backlinks → needs a SERP or SEO API.
- {any skipped checks}

---

### Follow-up menu (always offer)
Would you like me to:
- **Generate the fixes** — corrected robots.txt, `Organization`+`sameAs` schema, answer-first rewrites of your top pages, and an earned-media target list?
- **Measure live visibility** — build a prompt panel and run it across engines (frequency + share of voice)?
- **Benchmark a competitor** — run the same scan on a rival and diff?
- **Schedule a weekly re-scan** — track the score over time?

---

## Tone reminders
- "Frequency, not rank." Never promise an "AI ranking."
- Off-site > on-site. If someone wants one thing to do, it's almost always
  earned media / reviews, not more blog posts.
- Be honest about weak levers (schema ≈ noise for citations; llms.txt not
  consumed by AI search). That honesty is why they should trust the report.
- AI mentions ≠ traffic yet (<1% of web traffic). Frame as brand presence with
  a compounding head start.
