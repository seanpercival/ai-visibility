# Per-Engine Cheat Sheet

Cross-engine source overlap is only ~10–20%. Optimize and report **per engine** —
never blend into one score.

## The map

| Engine | Index / backend | Cites most | How to win it |
|---|---|---|---|
| **ChatGPT** | Bing + own `OAI-SearchBot` index (+ growing Google use) | Wikipedia (~48% of its top-10), Reddit, major publishers | Least correlated with Google rank → **most winnable for small brands.** Register in **Bing Webmaster Tools**. Get a Wikipedia entry. |
| **Perplexity** | Own index (`PerplexityBot`) | Cites the *most* sources; YouTube-heavy since the Oct 2025 Reddit lawsuit | **Allow `PerplexityBot` or you're invisible.** Strong freshness bias — refresh key pages every 60–90 days. |
| **Google AI Overviews / AI Mode** | `Googlebot` index + Gemini | UGC-heavy: Reddit, YouTube, Quora | Rides normal Google indexing + rankings. `Google-Extended` is training-only and doesn't affect AIO. |
| **Gemini (app)** | Google grounding | Institutional / brand-owned sites (~52% owned) | "Trusts what the brand says." Keep your own site authoritative and current. |
| **Claude** | **Brave Search** | Niche / trade / practitioner sources; PubMed; ~10-week freshness window | **The edge:** being cited by Claude = winning **Brave** visibility, not Google. Almost nobody optimizes for Brave. |

## What this means operationally

- **Small / challenger brand?** Start with ChatGPT and Claude — both are less
  tied to entrenched Google authority. Bing registration + a few strong Reddit
  and review-site presences move ChatGPT fast.
- **B2B?** Reviews (G2, Capterra, Gartner Peer Insights) and comparison content
  punch above their weight across all engines.
- **Local / consumer?** Google AIO dominates; consistent NAP, Google Business
  Profile, and review volume matter most.
- **The universal levers** (help every engine): be readable in raw HTML (no
  JS-only content), have a clean entity (`Organization`+`sameAs`, Wikipedia/
  Wikidata), publish answer-first content with real statistics and citations,
  and get talked about on third-party sites.

## The Brave angle (Claude-specific, under-exploited)

Anthropic's Claude web search is powered by Brave Search (verified via
Anthropic's published subprocessor list, Mar 2025). Practical implications:
- Brave has its own index and its own crawler considerations; strong Google SEO
  does not automatically transfer.
- Brave surfaces independent / less mainstream sources more than Google does,
  which fits Claude's observed preference for niche and trade content.
- If Claude visibility matters to a client, check Brave Search results for the
  target queries directly — it's the closest proxy to "what Claude sees."

## Volatility warning

Every citation-share number here shifts monthly with model updates and
licensing deals (e.g., the Oct 2025 Reddit–Perplexity lawsuit reshuffled
Perplexity's sources; Gemini 3 becoming the AIO default replaced ~42% of cited
domains). Re-baseline measurements after any known model release; never treat a
citation statistic as permanent.
