# Prompt Library

Two uses: (1) build a **measurement panel** (Mode B) to see how often a brand
appears in AI answers, and (2) **optimize content** with LLM rewrite prompts.

---

## Part 1 — Measurement panel (Mode B)

Ground prompts in **real buyer language** (pull from Search Console queries,
Reddit threads, sales-call notes, "People Also Ask") — not invented phrasing.
15–50 prompts. Run each **N times per engine** and report appearance frequency,
not a rank. More constraints = closer to a real buying decision.

Fill in `[category]`, `[brand]`, `[competitor]`, `[use case]`, `[persona]`.

**Category recommendation** (highest priority — what buyers actually type)
- "What are the best [category] tools in 2026?"
- "Recommend the top 3 [category] platforms for [persona]."
- "What [category] tool do most [persona] use?"

**Alternative-to / competitor** (higher intent)
- "What's the best alternative to [competitor]?"
- "[brand] vs [competitor] — which is better for [use case]?"
- "Open-source / cheaper alternatives to [competitor]?"

**Use-case / problem** (model must reason problem → product)
- "I'm a [persona] and I need to [job-to-be-done]. What should I use?"
- "My team struggles with [pain point]. What's a good fix?"

**Brand awareness** (does the model know you / describe you correctly)
- "What is [brand]?"  ·  "What does [brand] do?"  ·  "Is [brand] any good?"

**Trust / risk** (surfaces negative framing + hallucinations)
- "Is [brand] legit / safe?"  ·  "What are the downsides of [brand]?"

For each result, record the 4-outcome grid: **named correctly / named wrong /
not named / hallucinated** — each maps to a different fix.

Constraint upgrade examples (weak → strong):
- "Best CRM" → "Best CRM for a 20-person B2B SaaS team already using Slack, under $50/user."
- "Best running shoes" → "Best beginner running shoes for wet city pavement under €120."

---

## Part 2 — Content optimization prompts (Mode C)

### Answer-first restructure
```
Restructure the article below so the single strongest, most citable claim sits
in the first 30% of the text. Give each H2 a question a user would actually ask,
and open each section with a self-contained 40–60 word answer. Cap average
sentence length ~18 words. Output headings + opening sentences only.
```

### Definitive-statement rewriter (kills hedging → citable)
```
Rewrite to replace hedging ("it depends", "typically", "can vary") with
specific, quotable claims. Add concrete numbers or ranges. Keep the meaning.
Flag any claim that needs a source with [CITE].
```

### Evidence injection (the Princeton tactics)
```
Strengthen this content for AI citation by adding: (1) relevant statistics with
sources, (2) a short expert quotation, (3) 2–3 citations to authoritative
(.gov/.edu/industry) sources. Do not keyword-stuff. Return the edited passage
with citations inline.
```

### Comparison-table builder
```
Create an honest comparison table for [brand] vs [2–3 competitors]: rows for
pricing (real numbers), 5–7 key features, "best for", and honest limitations.
End with a one-line "bottom line" recommendation per use case.
```

### FAQ generator (visible Q&A + optional schema)
```
Generate 6–8 FAQs for this page using the real questions buyers ask about
[topic]. Each answer 40–60 words, direct, no fluff. Output as visible Q&A, then
(optional) matching FAQPage JSON-LD.
```

### GEO content audit (score a page 1–5)
```
Score this page 1–5 on: definitive statements, extractable structure, evidence/
citations, entity clarity, question coverage, conversational tone, freshness.
For each score below 4, give one specific rewrite with an example.
```

---

## Off-site / earned-media targeting (the real lever)

When generating a Mode C action list, name specifics, e.g.:
- **Reviews:** claim Trustpilot; B2B → G2, Capterra, Gartner Peer Insights, TrustRadius.
- **Reddit:** the 3–5 subreddits where the category is actually discussed.
- **Best-of listicles:** the ranking articles competitors appear in — pitch to be added.
- **Wikipedia/Wikidata:** fill the entity gap if notability supports it.
- **YouTube:** a channel or getting featured in review videos (~200× any other video source in AI citations).
- **Digital PR:** earned media drives ~84% of AI citations — a single well-placed feature outperforms months of blog posts.
