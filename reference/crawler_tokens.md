# AI Crawler Tokens & robots.txt Rules

The single most important — and most verifiable — AEO fix. If a search/answer
agent is blocked, that engine literally cannot cite you.

## Two kinds of bot per vendor

Training crawlers and search/answer crawlers are **separate** and controlled by
**separate tokens**. Blocking the training bot is a values choice with no
citation cost. Blocking the search/user bot removes you from that engine's live
answers.

| Vendor | Training (optional to block) | Search / User (MUST allow to be cited) |
|---|---|---|
| OpenAI | `GPTBot` | `OAI-SearchBot` (ChatGPT search index), `ChatGPT-User` (user-triggered fetch) |
| Anthropic | `ClaudeBot` | `Claude-SearchBot` (search index), `Claude-User` (user-triggered fetch) |
| Perplexity | — | `PerplexityBot` (index), `Perplexity-User` (live fetch) |
| Google | `Google-Extended` (Gemini training opt-out) | `Googlebot` (powers AI Overviews / AI Mode) |
| Microsoft | — | `Bingbot` (feeds ChatGPT **and** Copilot) |
| Apple | `Applebot-Extended` | `Applebot` (Siri / Apple Intelligence answers) |
| Meta | `Meta-ExternalAgent` (Llama training) | `Meta-ExternalFetcher` (user-triggered) |
| Common Crawl | `CCBot` (trains many models) | — |
| ByteDance | `Bytespider` (undocumented; mixed robots.txt compliance) | — |
| xAI / Grok | no officially documented crawler token | — |

Key non-obvious facts:
- **`Google-Extended` is training-only.** Blocking it does **not** remove you
  from Google Search or AI Overviews. AI Overviews ride the normal `Googlebot`
  index. (Source: Google crawler docs.)
- **Bing is double-duty.** Bing's index feeds both ChatGPT and Copilot, so
  allowing `Bingbot` + registering in Bing Webmaster Tools is one of the
  highest-leverage, most-overlooked AEO actions.
- **Perplexity is crawl-gated.** No `PerplexityBot` access = no Perplexity
  citations, full stop. (Note: Cloudflare has reported Perplexity using
  undeclared crawlers — compliance is contested.)
- **Legacy Anthropic tokens** `anthropic-ai` and `Claude-Web` are deprecated;
  update old robots.txt to `ClaudeBot` / `Claude-SearchBot`.
- **robots.txt is honor-system.** Major vendors' training bots comply, but
  `Bytespider`, `CCBot`, and some others have mixed records. For a *hard* block,
  enforce at server/CDN level (403 by user agent or verified IP range) — and
  know that **agentic browsers** (Atlas, Comet, Claude for Chrome) present a
  normal browser UA and can't be filtered by robots.txt at all.
- **Verify, don't trust the UA string.** Spoofing is common; when it matters,
  verify crawler identity via the vendor's published IP ranges / reverse DNS.

## robots.txt parsing rules (RFC 9309)

The scanner implements these; know them when hand-auditing:

1. **One group applies per bot = the single longest matching `User-agent`.**
   Group order in the file is irrelevant.
2. **`User-agent: *` is fallback-only and is NEVER merged** with a named group.
   If a bot has its own group, only that group applies. (Most common audit bug:
   assuming `*` rules stack on top of a named group — they don't.)
3. **Allow/Disallow: longest path match wins; on a tie, Allow wins.**
4. Field names and user-agent tokens match **case-insensitively**; URL paths are
   **case-sensitive**. `*` = wildcard, `$` = end anchor.
5. robots.txt returning **4xx** = treated as "no rules" (all allowed); **5xx** =
   temporary disallow-all. It's per host+protocol+port (subdomains need their own).

## Recommended robots.txt (allow AI answers, opt out of training)

```
# Allow AI SEARCH/ANSWER agents (needed for citations)
User-agent: OAI-SearchBot
Allow: /
User-agent: ChatGPT-User
Allow: /
User-agent: Claude-SearchBot
Allow: /
User-agent: Claude-User
Allow: /
User-agent: PerplexityBot
Allow: /
User-agent: Perplexity-User
Allow: /
User-agent: Googlebot
Allow: /
User-agent: Bingbot
Allow: /

# OPTIONAL: opt out of model TRAINING (no citation impact) — delete if you
# don't care about training use.
User-agent: GPTBot
Disallow: /
User-agent: ClaudeBot
Disallow: /
User-agent: CCBot
Disallow: /
User-agent: Google-Extended
Disallow: /

# Everyone else
User-agent: *
Allow: /

Sitemap: https://example.com/sitemap.xml
```

Note: `Allow: /` under a named agent is functionally the same as having no rule
for it, but it's explicit and self-documenting. If you want maximum simplicity,
just make sure none of the search/user tokens are `Disallow: /`.

## Sources
- OpenAI bots: https://platform.openai.com/docs/bots
- Anthropic crawler docs: https://support.claude.com/en/articles/8896518
- Perplexity bots: https://docs.perplexity.ai/guides/bots
- Google crawlers: https://developers.google.com/search/docs/crawling-indexing/google-common-crawlers
- RFC 9309: https://www.rfc-editor.org/rfc/rfc9309.html
