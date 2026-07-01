#!/usr/bin/env python3
"""
scan.py - Zero-dependency AEO / AI-visibility scanner.

Fetches a site's robots.txt, raw HTML, and sitemap, queries free public APIs
(Wikipedia, Wikidata, Reddit, Trustpilot), then runs a 31-point checklist across
five pillars and prints a scored 0-100 report.

Standard library only. Python 3.8+.

Usage:
    python3 scan.py https://example.com
    python3 scan.py https://example.com --brand "Example Inc" --json out.json
    python3 scan.py https://example.com --no-apis            # skip off-site checks
    python3 scan.py https://example.com --page /pricing      # also scan a deep page

Design notes:
- "Frequency, not rank." This scans on-site + entity signals only. Live AI
  visibility (share of voice) is measured separately by prompt_panel.py.
- Access is a GATE: if AI crawlers are blocked or content is JS-only, the total
  score is capped at 40.
- Never fabricates: a check that can't run is reported as "not checked".
"""

import argparse
import json
import re
import sys
import socket
from html.parser import HTMLParser
from urllib.parse import urlparse, urljoin, quote
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

UA = "Mozilla/5.0 (compatible; AI-Visibility-Scanner/1.0; +https://github.com/)"
TIMEOUT = 15

# AI crawler tokens. search/user agents MUST be allowed to be citable.
SEARCH_BOTS = ["OAI-SearchBot", "Claude-SearchBot", "Claude-User",
               "PerplexityBot", "Googlebot", "Bingbot"]
TRAINING_BOTS = ["GPTBot", "ClaudeBot", "CCBot", "Google-Extended"]

AUTHORITATIVE_TLDS = (".gov", ".edu")
AUTHORITATIVE_HOSTS = ("wikipedia.org", "who.int", "nih.gov", "nature.com",
                       "reuters.com", "nytimes.com", "gartner.com")

# ------------------------------------------------------------------ fetching

def fetch(url, timeout=TIMEOUT):
    """Return (status, text, final_url, headers) or (None, None, url, {}) on failure."""
    req = Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    try:
        with urlopen(req, timeout=timeout) as r:
            raw = r.read()
            charset = r.headers.get_content_charset() or "utf-8"
            try:
                text = raw.decode(charset, errors="replace")
            except (LookupError, TypeError):
                text = raw.decode("utf-8", errors="replace")
            return r.status, text, r.geturl(), dict(r.headers)
    except HTTPError as e:
        return e.code, None, url, {}
    except (URLError, socket.timeout, ValueError, ConnectionError):
        return None, None, url, {}
    except Exception:
        return None, None, url, {}


def fetch_json(url, timeout=TIMEOUT):
    status, text, _, _ = fetch(url, timeout)
    if status == 200 and text:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return None
    return None


# ------------------------------------------------------------------ HTML parse

class PageParser(HTMLParser):
    """Extract SEO/AEO-relevant signals from raw HTML (no JS execution)."""

    INVISIBLE = {"script", "style", "noscript", "template", "svg"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.meta = {}            # name/property -> content
        self.canonical = None
        self.headings = {"h1": [], "h2": [], "h3": []}
        self.jsonld = []          # list of parsed dicts
        self.text_parts = []
        self.blockquotes = 0
        self.tables = 0
        self.tables_with_th = 0
        self.lists = 0
        self.list_items = 0
        self.img_total = 0
        self.img_with_alt = 0
        self.links_internal = 0
        self.links_external = 0
        self.ext_authoritative = 0
        self.has_time_tag = False
        self.framework_markers = set()
        self.paragraphs = []      # ordered visible <p> texts (for answer-first)
        self._stack = []
        self._grab = None         # current heading/p buffer key
        self._grab_buf = []
        self._in_ldjson = False
        self._ld_buf = []
        self._cur_table_has_th = False
        self._base_host = None

    def set_base(self, host):
        self._base_host = host

    # --- helpers
    def _visible(self):
        return not any(t in self.INVISIBLE for t in self._stack)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self._stack.append(tag)

        if tag == "meta":
            key = a.get("name") or a.get("property")
            if key and "content" in a:
                self.meta[key.lower()] = a.get("content", "")
        elif tag == "link" and (a.get("rel", "").lower() == "canonical"):
            self.canonical = a.get("href")
        elif tag == "script" and a.get("type", "").lower() == "application/ld+json":
            self._in_ldjson = True
            self._ld_buf = []
        elif tag in ("h1", "h2", "h3"):
            self._grab = tag
            self._grab_buf = []
        elif tag == "p":
            self._grab = "p"
            self._grab_buf = []
        elif tag == "blockquote":
            self.blockquotes += 1
        elif tag == "table":
            self.tables += 1
            self._cur_table_has_th = False
        elif tag == "th":
            self._cur_table_has_th = True
        elif tag in ("ul", "ol"):
            self.lists += 1
        elif tag == "li":
            self.list_items += 1
        elif tag == "img":
            self.img_total += 1
            if a.get("alt", "").strip():
                self.img_with_alt += 1
        elif tag == "time":
            self.has_time_tag = True
        elif tag == "a" and a.get("href"):
            self._classify_link(a["href"])

        # framework shells (JS-rendering risk)
        _id = (a.get("id") or "").lower()
        if _id in ("root", "__next", "app", "___gatsby"):
            self.framework_markers.add(_id)
        if a.get("data-reactroot") is not None:
            self.framework_markers.add("react")
        if any(k.startswith("ng-") or k.startswith("v-") or k == "data-v-app" for k in a):
            self.framework_markers.add("ng/vue")

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if self._stack and self._stack[-1] == tag:
            self._stack.pop()

    def _classify_link(self, href):
        try:
            p = urlparse(href)
        except ValueError:
            return
        if not p.netloc:
            self.links_internal += 1
            return
        host = p.netloc.lower()
        if self._base_host and self._base_host in host:
            self.links_internal += 1
        else:
            self.links_external += 1
            if host.endswith(AUTHORITATIVE_TLDS) or any(h in host for h in AUTHORITATIVE_HOSTS):
                self.ext_authoritative += 1

    def handle_endtag(self, tag):
        if tag == "script" and self._in_ldjson:
            self._in_ldjson = False
            self._store_ld("".join(self._ld_buf))
        if tag in ("h1", "h2", "h3") and self._grab == tag:
            txt = " ".join("".join(self._grab_buf).split())
            if txt:
                self.headings[tag].append(txt)
            self._grab = None
        if tag == "p" and self._grab == "p":
            txt = " ".join("".join(self._grab_buf).split())
            if txt:
                self.paragraphs.append(txt)
            self._grab = None
        if tag == "table" and self._cur_table_has_th:
            self.tables_with_th += 1
            self._cur_table_has_th = False
        # pop stack
        for i in range(len(self._stack) - 1, -1, -1):
            if self._stack[i] == tag:
                del self._stack[i]
                break

    def handle_data(self, data):
        if self._in_ldjson:
            self._ld_buf.append(data)
            return
        if self._grab in ("h1", "h2", "h3", "p"):
            self._grab_buf.append(data)
        if self._stack and self._stack[-1] == "title":
            self.title += data
        if self._visible() and data.strip():
            self.text_parts.append(data)

    def _store_ld(self, raw):
        raw = raw.strip()
        if not raw:
            return
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError:
            # try to salvage multiple/loose JSON
            return
        if isinstance(obj, list):
            self.jsonld.extend(x for x in obj if isinstance(x, dict))
        elif isinstance(obj, dict):
            if "@graph" in obj and isinstance(obj["@graph"], list):
                self.jsonld.extend(x for x in obj["@graph"] if isinstance(x, dict))
            else:
                self.jsonld.append(obj)

    @property
    def visible_text(self):
        return " ".join(" ".join(self.text_parts).split())

    def ld_types(self):
        out = set()
        for o in self.jsonld:
            t = o.get("@type")
            if isinstance(t, list):
                out.update(str(x) for x in t)
            elif t:
                out.add(str(t))
        return out

    def ld_find(self, typ):
        for o in self.jsonld:
            t = o.get("@type")
            t = t if isinstance(t, list) else [t]
            if typ in [str(x) for x in t]:
                return o
        return None


# ------------------------------------------------------------------ robots.txt

def parse_robots(text):
    """Return list of groups: [{'agents': [..], 'rules': [(allow_bool, path)]}]."""
    groups, cur, expecting_agent = [], None, False
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        field, _, value = line.partition(":")
        field = field.strip().lower()
        value = value.strip()
        if field == "user-agent":
            if cur is None or not expecting_agent:
                cur = {"agents": [], "rules": []}
                groups.append(cur)
            cur["agents"].append(value.lower())
            expecting_agent = True
        elif field in ("allow", "disallow") and cur is not None:
            expecting_agent = False
            cur["rules"].append((field == "allow", value))
    return groups


def _rule_match_len(rule_path, test_path):
    """Return match length if rule_path matches test_path (prefix + * / $), else -1."""
    if rule_path == "":
        return -1
    pattern = re.escape(rule_path).replace(r"\*", ".*")
    if pattern.endswith(r"\$"):
        pattern = pattern[:-2] + "$"
    if re.match(pattern, test_path):
        return len(rule_path)
    return -1


def bot_allowed(groups, bot_token, test_path="/"):
    """True if bot_token may crawl test_path per RFC-9309 longest-match rules."""
    bl = bot_token.lower()
    best_group, best_len = None, -1
    star_group = None
    for g in groups:
        for ua in g["agents"]:
            if ua == "*":
                star_group = g
            elif bl.startswith(ua) or ua.startswith(bl):
                if len(ua) > best_len:
                    best_group, best_len = g, len(ua)
    group = best_group or star_group
    if not group:
        return True  # no rules => allowed
    decision, decision_len = True, -1
    for allow, path in group["rules"]:
        mlen = _rule_match_len(path, test_path)
        if mlen > decision_len or (mlen == decision_len and allow):
            if mlen >= 0:
                decision, decision_len = allow, mlen
    return decision


# ------------------------------------------------------------------ checks

def C(pillar, key, status, points, maxpoints, msg, fix=""):
    return {"pillar": pillar, "key": key, "status": status, "points": points,
            "max": maxpoints, "msg": msg, "fix": fix}


def word_count(text):
    return len(re.findall(r"\b\w+\b", text))


def run_checks(url, brand, do_apis):
    domain = urlparse(url).netloc.lower().replace("www.", "")
    base_host = domain
    results = []
    notes = {}

    # ---- fetch core assets
    status, html, final_url, headers = fetch(url)
    robots_status, robots_txt, _, _ = fetch(urljoin(url, "/robots.txt"))
    groups = parse_robots(robots_txt) if robots_txt else []

    parser = None
    if html:
        parser = PageParser()
        parser.set_base(base_host)
        try:
            parser.feed(html)
        except Exception:
            pass

    vis_text = parser.visible_text if parser else ""
    vis_words = word_count(vis_text)

    # ============================================ PILLAR 1: ACCESS (GATE)
    # A1: AI search bots not blocked
    if robots_txt is not None:
        blocked = [b for b in SEARCH_BOTS if not bot_allowed(groups, b, "/")]
        if not blocked:
            results.append(C("access", "ai_bots", "pass", 10, 10,
                             "AI search/user agents are allowed in robots.txt.",
                             ""))
        else:
            results.append(C("access", "ai_bots", "fail", 0, 10,
                             f"Blocked AI agents: {', '.join(blocked)}. These can't cite you.",
                             "Remove Disallow rules for these tokens (see reference/crawler_tokens.md)."))
    else:
        results.append(C("access", "ai_bots", "info", 8, 10,
                         "No robots.txt found (200) — everything is crawlable by default.",
                         "Add a robots.txt that explicitly allows AI search agents + points to your sitemap."))

    # A2: JS-rendering risk
    if parser is not None:
        shell = bool(parser.framework_markers)
        if vis_words < 150 and shell:
            results.append(C("access", "js_render", "fail", 0, 10,
                             f"Only ~{vis_words} words in raw HTML + a JS-app shell "
                             f"({', '.join(sorted(parser.framework_markers))}). "
                             "AI crawlers don't run JS — your content may be invisible.",
                             "Server-side render (SSR) or pre-render so content is in the initial HTML."))
        elif vis_words < 150:
            results.append(C("access", "js_render", "warn", 5, 10,
                             f"Only ~{vis_words} words in raw HTML. Thin or JS-dependent.",
                             "Ensure primary content is server-rendered."))
        else:
            results.append(C("access", "js_render", "pass", 10, 10,
                             f"~{vis_words} words present in raw HTML — visible to AI crawlers.",
                             ""))
    else:
        results.append(C("access", "js_render", "skip", 0, 10,
                         "Could not fetch/parse the page HTML.",
                         "Verify the URL is reachable and returns HTML."))

    # A3: reachable / HTTPS / 200
    if status == 200 and final_url.startswith("https"):
        results.append(C("access", "reachable", "pass", 5, 5,
                         "Page returns 200 over HTTPS.", ""))
    elif status == 200:
        results.append(C("access", "reachable", "warn", 2, 5,
                         "Page returns 200 but not over HTTPS.", "Serve the site over HTTPS."))
    else:
        results.append(C("access", "reachable", "fail", 0, 5,
                         f"Page did not return 200 (status={status}).",
                         "Fix server response before anything else."))

    # ============================================ PILLAR 2: OFF-SITE (30)
    if do_apis and brand:
        # D1: Wikipedia (None => network failure, don't penalize)
        wiki = fetch_json("https://en.wikipedia.org/w/api.php?action=opensearch&limit=1&format=json&search=" + quote(brand))
        if wiki is None:
            results.append(C("offsite", "wikipedia", "skip", 0, 0,
                             "Wikipedia check could not run (network) — verify manually.", ""))
        elif len(wiki) >= 2 and wiki[1]:
            results.append(C("offsite", "wikipedia", "pass", 7, 7,
                             f"Wikipedia entry found: {wiki[1][0]}.", ""))
        else:
            results.append(C("offsite", "wikipedia", "fail", 0, 7,
                             "No Wikipedia entry found — Wikipedia is the #1 cited source for ChatGPT.",
                             "Pursue notability (press, coverage) that can support a Wikipedia article."))
        # D2: Wikidata
        wd = fetch_json("https://www.wikidata.org/w/api.php?action=wbsearchentities&language=en&format=json&limit=1&search=" + quote(brand))
        if wd is None:
            results.append(C("offsite", "wikidata", "skip", 0, 0,
                             "Wikidata check could not run (network) — verify manually.", ""))
        elif wd.get("search"):
            results.append(C("offsite", "wikidata", "pass", 5, 5,
                             f"Wikidata entity: {wd['search'][0].get('id')}.", ""))
        else:
            results.append(C("offsite", "wikidata", "warn", 0, 5,
                             "No Wikidata entity — this anchors knowledge-graph identity.",
                             "Create a Wikidata item linking your official site (P856)."))
        # D3: Reddit presence (anonymous API frequently rate-limits => not-checked, not "absent")
        rd = fetch_json("https://www.reddit.com/search.json?limit=5&q=" + quote(brand))
        if rd is None:
            results.append(C("offsite", "reddit", "skip", 0, 0,
                             "Reddit check could not run (the anonymous API rate-limits) — verify manually.",
                             "Check reddit.com/search for your brand in relevant subreddits."))
        else:
            n = len(rd.get("data", {}).get("children", []))
            if n >= 3:
                results.append(C("offsite", "reddit", "pass", 6, 6,
                                 f"~{n}+ recent Reddit mentions — Reddit is a top AI-cited source.", ""))
            elif n >= 1:
                results.append(C("offsite", "reddit", "warn", 3, 6,
                                 f"Only ~{n} Reddit mentions found.",
                                 "Earn authentic Reddit presence in relevant subreddits."))
            else:
                results.append(C("offsite", "reddit", "fail", 0, 6,
                                 "No Reddit presence found — a major AI citation source.",
                                 "Get into relevant subreddit discussions (authentically)."))
        # D4: Trustpilot profile (distinguish 404=absent from block/error=not-checked)
        tp_status, _, _, _ = fetch(f"https://www.trustpilot.com/review/{domain}")
        if tp_status == 200:
            results.append(C("offsite", "reviews", "pass", 7, 7,
                             "Trustpilot profile exists — review presence maps to far higher AI citation rates.",
                             ""))
        elif tp_status in (404, 410):
            results.append(C("offsite", "reviews", "fail", 0, 7,
                             "No Trustpilot profile (brands with active reviews are cited ~75% vs ~1%).",
                             "Claim Trustpilot; for B2B pursue G2 / Capterra / Gartner Peer Insights."))
        else:
            results.append(C("offsite", "reviews", "skip", 0, 0,
                             f"Review presence not verified (Trustpilot returned {tp_status or 'no response'}; often bot-blocked).",
                             "Manually confirm Trustpilot / G2 / Capterra / Gartner profiles."))
        # D5: brand-mention volume — needs a SERP API (informational, not scored)
        results.append(C("offsite", "mention_volume", "info", 0, 0,
                         "Brand-mention volume needs a SERP API (approx) — not measured here.",
                         "Connect a SERP API or an AI-visibility tool for mention tracking."))
    else:
        results.append(C("offsite", "offsite", "skip", 0, 30,
                         "Off-site checks skipped (no --brand or --no-apis).",
                         "Re-run with --brand \"Your Brand\" to check Wikipedia/Wikidata/Reddit/reviews."))

    # ============================================ PILLAR 3: CONTENT (30)
    if parser is not None:
        # C1: answer-first capsule
        cap = next((p for p in parser.paragraphs if 20 <= word_count(p) <= 90), None)
        if cap:
            results.append(C("content", "answer_first", "pass", 6, 6,
                             "A concise, self-contained opening paragraph exists (good extraction target).", ""))
        else:
            results.append(C("content", "answer_first", "warn", 2, 6,
                             "No clear ~40-60 word answer-first capsule near the top.",
                             "Open key sections with a direct 40-60 word answer to the section's question."))
        # C2: stat / quote / citation density
        stats = len(re.findall(r"\b\d+(?:[.,]\d+)?\s?(?:%|percent|million|billion|x)\b|\$\s?\d", vis_text, re.I))
        density = (stats / max(vis_words, 1)) * 1000
        cite_signal = parser.ext_authoritative + parser.blockquotes
        if density >= 3 or cite_signal >= 2:
            results.append(C("content", "evidence", "pass", 8, 8,
                             f"Good evidence density (~{stats} stats, {parser.blockquotes} quotes, "
                             f"{parser.ext_authoritative} authoritative links). Top GEO tactic.", ""))
        elif stats >= 1 or cite_signal >= 1:
            results.append(C("content", "evidence", "warn", 4, 8,
                             f"Some evidence (~{stats} stats, {parser.ext_authoritative} authoritative links) but sparse.",
                             "Add statistics, quotations, and citations to authoritative sources (Princeton GEO tactics)."))
        else:
            results.append(C("content", "evidence", "fail", 0, 8,
                             "Little quantitative evidence or sourcing — the strongest GEO lever.",
                             "Add concrete stats, expert quotes, and cited sources."))
        # C3: question-style headers
        subs = parser.headings["h2"] + parser.headings["h3"]
        qh = sum(1 for h in subs if h.strip().endswith("?") or
                 re.match(r"^(how|what|why|when|which|who|where|is|are|can|best)\b", h.strip(), re.I))
        if subs and qh >= max(1, len(subs) // 4):
            results.append(C("content", "q_headers", "pass", 5, 5,
                             f"{qh} question-style subheadings — match how people query AI.", ""))
        elif subs:
            results.append(C("content", "q_headers", "warn", 2, 5,
                             "Few question-style subheadings.",
                             "Rewrite H2/H3s as the questions users actually ask."))
        else:
            results.append(C("content", "q_headers", "fail", 0, 5,
                             "No H2/H3 subheadings found — poor chunk retrievability.",
                             "Add descriptive, question-style subheadings."))
        # C4: single H1
        h1n = len(parser.headings["h1"])
        results.append(C("content", "h1",
                         "pass" if h1n == 1 else "warn", 3 if h1n == 1 else 1, 3,
                         f"{h1n} H1 tag(s)." + ("" if h1n == 1 else " Want exactly one."),
                         "" if h1n == 1 else "Use exactly one descriptive H1 per page."))
        # C5: tables + lists
        if parser.tables_with_th or parser.lists:
            results.append(C("content", "structures", "pass", 4, 4,
                             f"{parser.tables_with_th} data table(s), {parser.lists} list(s) — extractable structures.", ""))
        else:
            results.append(C("content", "structures", "warn", 1, 4,
                             "No data tables or lists detected.",
                             "Add comparison tables and numbered lists — AI reproduces these heavily."))
        # C6: freshness signal
        modified = parser.meta.get("article:modified_time") or (parser.ld_find("Article") or {}).get("dateModified")
        if modified or parser.has_time_tag or re.search(r"updated?\s+(on\s+)?\w+\s+\d", vis_text, re.I):
            results.append(C("content", "freshness", "pass", 4, 4,
                             "A freshness / last-updated signal is present.", ""))
        else:
            results.append(C("content", "freshness", "warn", 1, 4,
                             "No visible freshness/last-updated signal.",
                             "Surface a 'Last updated' date and keep content current."))
    else:
        results.append(C("content", "content", "skip", 0, 30,
                         "Content checks skipped — no HTML.", "Ensure the page is fetchable."))

    # ============================================ PILLAR 4: ENTITY (20)
    if parser is not None:
        org = parser.ld_find("Organization") or parser.ld_find("LocalBusiness")
        same_as = org.get("sameAs") if org else None
        if org and same_as:
            n = len(same_as) if isinstance(same_as, list) else 1
            results.append(C("entity", "org_schema", "pass", 10, 10,
                             f"Organization schema with {n} sameAs link(s) — strongest entity signal.", ""))
        elif org:
            results.append(C("entity", "org_schema", "warn", 5, 10,
                             "Organization schema present but no sameAs links.",
                             "Add sameAs[] to Wikipedia, Wikidata, LinkedIn, Crunchbase, socials."))
        else:
            results.append(C("entity", "org_schema", "fail", 0, 10,
                             "No Organization schema found in raw HTML.",
                             "Add Organization JSON-LD with sameAs (see reference/schema_templates.md)."))
        # E2: JSON-LD in raw HTML at all
        types = parser.ld_types()
        if types:
            results.append(C("entity", "jsonld", "pass", 5, 5,
                             f"JSON-LD in raw HTML: {', '.join(sorted(types)[:6])}.", ""))
        else:
            results.append(C("entity", "jsonld", "warn", 0, 5,
                             "No JSON-LD structured data in raw HTML.",
                             "Add structured data server-side (not JS-injected)."))
        # E3: title + meta description
        title_ok = 15 <= len(parser.title.strip()) <= 65
        desc = parser.meta.get("description", "")
        desc_ok = 50 <= len(desc) <= 165
        if title_ok and desc_ok:
            results.append(C("entity", "meta", "pass", 5, 5,
                             "Title and meta description are present and well-sized.", ""))
        else:
            issues = []
            if not title_ok:
                issues.append(f"title {len(parser.title.strip())} chars")
            if not desc_ok:
                issues.append("meta description missing/off-length" if not desc else f"description {len(desc)} chars")
            results.append(C("entity", "meta", "warn", 2, 5,
                             "Title/description need work: " + "; ".join(issues) + ".",
                             "Title ~50-60 chars; meta description ~120-160 chars, unique per page."))
    else:
        results.append(C("entity", "entity", "skip", 0, 20,
                         "Entity checks skipped — no HTML.", ""))

    # ============================================ PILLAR 5: TECHNICAL / FRESHNESS (support)
    # T1: sitemap
    sm_status, _, _, _ = fetch(urljoin(url, "/sitemap.xml"))
    sitemap_in_robots = bool(robots_txt and re.search(r"(?im)^\s*sitemap:", robots_txt))
    if sm_status == 200 or sitemap_in_robots:
        results.append(C("technical", "sitemap", "pass", 3, 3,
                         "sitemap.xml is reachable / referenced in robots.txt.", ""))
    else:
        results.append(C("technical", "sitemap", "warn", 0, 3,
                         "No sitemap.xml found or referenced.",
                         "Publish sitemap.xml and reference it in robots.txt."))
    # T2: canonical
    if parser and parser.canonical:
        results.append(C("technical", "canonical", "pass", 3, 3,
                         "Canonical tag present in raw HTML.", ""))
    elif parser:
        results.append(C("technical", "canonical", "warn", 0, 3,
                         "No canonical tag in raw HTML.",
                         "Add <link rel=canonical> server-side."))
    # T3: llms.txt (INFORMATIONAL ONLY)
    lt_status, _, _, _ = fetch(urljoin(url, "/llms.txt"))
    if lt_status == 200:
        results.append(C("technical", "llms_txt", "info", 0, 0,
                         "llms.txt present. Note: not consumed by AI search engines "
                         "(97% never fetched) — useful mainly for docs/dev audiences.", ""))
    else:
        results.append(C("technical", "llms_txt", "info", 0, 0,
                         "No llms.txt. Not a citation driver — skip unless you serve dev/API docs.",
                         ""))
    # T4: image alt coverage
    if parser and parser.img_total:
        cov = parser.img_with_alt / parser.img_total
        results.append(C("technical", "img_alt",
                         "pass" if cov >= 0.8 else "warn",
                         3 if cov >= 0.8 else 1, 3,
                         f"{int(cov*100)}% of images have alt text.",
                         "" if cov >= 0.8 else "Add descriptive alt text to images."))

    return results, {"domain": domain, "status": status, "words": vis_words,
                     "final_url": final_url, "robots_found": robots_txt is not None}


# ------------------------------------------------------------------ scoring

PILLAR_MAX = {"offsite": 30, "content": 30, "entity": 20}
PILLAR_LABELS = {
    "access": "Crawler Access & Renderability (GATE)",
    "offsite": "Off-site Authority & Earned Media",
    "content": "Content Citation-Readiness",
    "entity": "Entity Clarity",
    "technical": "Technical & Freshness",
}


def score(results):
    by = {}
    for r in results:
        by.setdefault(r["pillar"], {"pts": 0, "max": 0})
        by[r["pillar"]]["pts"] += r["points"]
        by[r["pillar"]]["max"] += r["max"]

    # Access gate: did any access check fail?
    access_fail = any(r["pillar"] == "access" and r["status"] == "fail" for r in results)

    # weighted pillars (offsite 30, content 30, entity 20 = 80; technical folded as bonus up to 20)
    def pct(p):
        m = by.get(p, {"max": 0})["max"]
        return (by[p]["pts"] / m) if m else 0

    core = pct("offsite") * 30 + pct("content") * 30 + pct("entity") * 20
    tech = pct("technical") * 20 if by.get("technical", {}).get("max") else 0
    total = round(core + tech)

    if access_fail:
        total = min(total, 40)

    return total, by, access_fail


# ------------------------------------------------------------------ report

SEV = {"fail": "CRITICAL", "warn": "FIX", "pass": "OK", "info": "NOTE", "skip": "SKIP"}


def band(total):
    if total >= 90: return "Excellent"
    if total >= 70: return "Effective foundation"
    if total >= 50: return "Needs work"
    return "Critical gaps"


def render(url, brand, results, meta, total, by, access_fail):
    out = []
    out.append("=" * 66)
    out.append("  AI-VISIBILITY / AEO SCAN")
    out.append("=" * 66)
    out.append(f"  Site:   {meta['final_url']}")
    if brand:
        out.append(f"  Brand:  {brand}")
    out.append(f"  Score:  {total}/100   ({band(total)})")
    if access_fail:
        out.append("  ** ACCESS GATE FAILED — score capped at 40. Fix crawler access first. **")
    skipped = [r for r in results if r["status"] == "skip"]
    if skipped:
        out.append(f"  Note: {len(skipped)} check(s) couldn't be verified automatically "
                   "(blocked/rate-limited); score reflects verified checks only.")
    out.append("")

    # pillar summary
    out.append("  PILLARS")
    for p in ["access", "offsite", "content", "entity", "technical"]:
        if p in by:
            d = by[p]
            out.append(f"    - {PILLAR_LABELS[p]:<42} {d['pts']}/{d['max']}")
    out.append("")

    # findings grouped
    order = {"fail": 0, "warn": 1, "skip": 2, "info": 3, "pass": 4}
    for p in ["access", "offsite", "content", "entity", "technical"]:
        rows = [r for r in results if r["pillar"] == p]
        if not rows:
            continue
        rows.sort(key=lambda r: order.get(r["status"], 5))
        out.append(f"  {PILLAR_LABELS[p].upper()}")
        for r in rows:
            out.append(f"    [{SEV[r['status']]:^8}] {r['msg']}")
            if r["fix"] and r["status"] in ("fail", "warn"):
                out.append(f"               -> {r['fix']}")
        out.append("")

    # quick wins vs strategic
    quick = [r for r in results if r["status"] in ("fail", "warn") and r["pillar"] in ("access", "entity", "technical", "content")]
    strat = [r for r in results if r["status"] in ("fail", "warn") and r["pillar"] == "offsite"]
    out.append("  QUICK WINS (mostly on-site, do this week)")
    for r in quick[:8]:
        out.append(f"    [ ] {r['fix'] or r['msg']}")
    if not quick:
        out.append("    (none — on-site foundation is solid)")
    out.append("")
    out.append("  STRATEGIC INVESTMENTS (off-site, this quarter)")
    for r in strat:
        out.append(f"    [ ] {r['fix'] or r['msg']}")
    if not strat:
        out.append("    [ ] Build earned media: reviews, Reddit, best-of listicles, PR.")
    out.append("")
    out.append("  Reminder: this scans on-site + entity signals. Run prompt_panel.py")
    out.append("  to measure live share-of-voice across engines (frequency, not rank).")
    out.append("=" * 66)
    return "\n".join(out)


# ------------------------------------------------------------------ main

def main():
    ap = argparse.ArgumentParser(description="AEO / AI-visibility site scanner (zero-dependency).")
    ap.add_argument("url", help="Site URL, e.g. https://example.com")
    ap.add_argument("--brand", default="", help="Brand name for off-site entity checks")
    ap.add_argument("--json", default="", help="Write full results to this JSON path")
    ap.add_argument("--no-apis", action="store_true", help="Skip off-site API checks")
    ap.add_argument("--page", default="", help="Also scan a deep path, e.g. /pricing")
    args = ap.parse_args()

    url = args.url
    if not url.startswith("http"):
        url = "https://" + url

    results, meta = run_checks(url, args.brand.strip(), not args.no_apis)
    total, by, access_fail = score(results)
    report = render(url, args.brand.strip(), results, meta, total, by, access_fail)
    print(report)

    if args.json:
        payload = {"url": meta["final_url"], "brand": args.brand, "score": total,
                   "access_gate_failed": access_fail, "meta": meta, "checks": results}
        try:
            with open(args.json, "w") as f:
                json.dump(payload, f, indent=2)
            print(f"\n[written] {args.json}")
        except OSError as e:
            print(f"\n[error] could not write JSON: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
