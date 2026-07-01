# JSON-LD Schema Templates

**Honest positioning:** schema does *not* meaningfully lift AI citations (Ahrefs
A/B test: ~+2%, noise; standalone LLMs read JSON-LD as plain text). Use it for
what it *does* do: **entity disambiguation** (`Organization` + `sameAs`),
knowledge-graph inclusion, and eligibility for traditional rich results that
feed index-based AI surfaces (Google AIO, Bing/Copilot). The single highest-value
type for AEO is `Organization` with `sameAs`.

Rules: absolute URLs; ISO-8601 dates; omit empty fields (don't ship empty
strings); put it in the **raw HTML** server-side (JS-injected JSON-LD is invisible
to AI crawlers); never fabricate values.

## Organization (site-wide — the priority) — put on homepage

```json
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "",
  "url": "https://example.com",
  "logo": "https://example.com/logo.png",
  "description": "",
  "foundingDate": "",
  "sameAs": [
    "https://en.wikipedia.org/wiki/...",
    "https://www.wikidata.org/wiki/Q...",
    "https://www.linkedin.com/company/...",
    "https://www.crunchbase.com/organization/...",
    "https://x.com/..."
  ]
}
```
`sameAs` is the mechanism that links your site to your knowledge-graph entity.
Point it at Wikipedia, Wikidata, LinkedIn, Crunchbase, and primary social
profiles. This is the one schema field worth chasing for AEO.

## Article / BlogPosting — content pages

```json
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "",
  "description": "",
  "image": "https://example.com/hero.jpg",
  "author": { "@type": "Person", "name": "", "url": "" },
  "publisher": {
    "@type": "Organization", "name": "",
    "logo": { "@type": "ImageObject", "url": "https://example.com/logo.png" }
  },
  "datePublished": "2026-01-01",
  "dateModified": "2026-06-01"
}
```
`author` (a real `Person` with a `url`/bio) + `dateModified` carry E-E-A-T and
freshness signals AI attributes.

## Product — commerce (the one area schema clearly helps AI)

```json
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "",
  "description": "",
  "image": "",
  "brand": { "@type": "Brand", "name": "" },
  "offers": {
    "@type": "Offer", "price": "", "priceCurrency": "USD",
    "availability": "https://schema.org/InStock"
  },
  "aggregateRating": { "@type": "AggregateRating", "ratingValue": "", "reviewCount": "" }
}
```
Price/availability in `Offer` genuinely feed AI shopping surfaces.

## FAQPage — keep the visible Q&A, markup is optional

```json
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    { "@type": "Question", "name": "",
      "acceptedAnswer": { "@type": "Answer", "text": "" } }
  ]
}
```
Note: Google retired FAQ rich results. The *visible* Q&A content is what helps AI
extraction — don't add FAQPage markup with no visible FAQ, and don't expect the
markup itself to drive citations.

## BreadcrumbList — still a supported rich result

```json
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    { "@type": "ListItem", "position": 1, "name": "Home", "item": "https://example.com" },
    { "@type": "ListItem", "position": 2, "name": "Category", "item": "https://example.com/category" }
  ]
}
```

## HowTo — tutorials (rich result deprecated; low AEO weight, include only if relevant)

```json
{
  "@context": "https://schema.org",
  "@type": "HowTo",
  "name": "",
  "step": [ { "@type": "HowToStep", "name": "", "text": "" } ]
}
```

## Don't bother with
- `WebSite` `SearchAction` / sitelinks searchbox — **deprecated** (Nov 2024).
- Schema as a "citation hack" — it isn't one. Ship it for entity clarity and
  rich results, then move budget to content + off-site.

Validate: https://search.google.com/test/rich-results and https://validator.schema.org
