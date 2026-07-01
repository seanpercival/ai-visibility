# Agentic Commerce Readiness (stores)

New in 2026: AI assistants don't just *recommend* products — they complete the
purchase. If the brand sells online, being citable is half the job; being
**transactable by an agent** is the other half.

## The two rails

| Protocol | Owner | Live where | Merchant path |
|---|---|---|---|
| **ACP** (Agentic Commerce Protocol) | OpenAI + Stripe (open-sourced) | ChatGPT Instant Checkout (since Sept 2025) | Shopify/Etsy merchants largely ride platform integrations; others need Stripe + an ACP-compliant product feed. OpenAI takes ~4% per completed checkout (buyer price unchanged) |
| **UCP** (Universal Commerce Protocol) | Google + coalition (Walmart, Target, Shopify, 20+ partners, announced Jan 2026) | Google Search / Gemini agentic checkout | Rides Merchant Center; keep the feed complete and current |

Most stores will eventually need **both**. Neither replaces the basics below —
agents shop from the same product data crawlers read.

## Readiness checklist (in priority order)

1. **Crawler access** — `OAI-SearchBot`, `Googlebot`, `Bingbot`, `PerplexityBot`
   allowed (see `crawler_tokens.md`). An agent can't buy what it can't see.
2. **Product JSON-LD, server-rendered, complete** — `name`, `description`,
   `image`, `brand`, `offers.price`, `priceCurrency`, `availability`, GTIN/MPN
   where they exist, `aggregateRating` if real. This is the one schema area with
   clear AI payoff (`schema_templates.md`).
3. **Merchant feed hygiene** — Google Merchant Center feed at high attribute
   completeness (aim 95%+): identifiers, availability, shipping, returns.
   The feed is what UCP-style agents transact against.
4. **Bing/Copilot** — register in Bing Webmaster Tools; submit the feed to
   Microsoft Merchant Center if the market supports it.
5. **PDP content that survives extraction** — spec tables, honest comparison
   vs alternatives, real review content on-page. Agents compare across tabs; a
   thin PDP loses silently.
6. **Reviews off-site** — Trustpilot (consumer) / category review sites; agents
   check trust signals before recommending a checkout.
7. **ACP/UCP enrollment** — platform-dependent; on Shopify much of this ships
   via platform settings. Flag it; don't guess at store-specific steps.

## Multi-market note

Feeds, review platforms, and agent availability differ by country. For a brand
running many regional storefronts, audit the *biggest market first*, then diff
the others against it — gaps are usually config drift, not strategy.

## Honesty notes

- Agentic checkout volume is early; treat it like AEO overall — a compounding
  head start, not this quarter's revenue line.
- Fees are real (ACP ~4% + processing). For low-margin categories, note the
  margin math in the report rather than cheerleading adoption.
- Protocols are moving fast; verify current enrollment paths at
  https://ucp.dev and OpenAI's ACP docs before advising specifics.
