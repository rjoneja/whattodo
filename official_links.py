#!/usr/bin/env python3
"""
Point "Details" at the venue's or organiser's own page, not a middleman.

For each event whose link is a listings site (Londonist, IanVisits, Skiddle, a blog, an Instagram post,
or a council what's-on page for someone else's event):
  1. open that page (for Instagram, the account's own website) and collect the links going out to other sites,
  2. ask Claude which one is the official page for THIS event (venue or organiser), if any,
  3. check that page loads and mentions the event, then swap it in. The old link is kept as "via".
Anything that can't be verified keeps its current link. Each event is checked once ("lk" marker).

  python3 official_links.py [--limit N] [--dry]
"""
import json, os, re, sys, time, html
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

P = "docs/events.json"
UA = "JauntOut-links/0.1 (+https://www.jauntout.com; finds the official page for a listing)"
MODEL = os.environ.get("WTD_MODEL", "claude-haiku-5-5")
MIDDLEMEN = re.compile(r"(^|\.)(londonist\.com|ianvisits\.co\.uk|skiddle\.com|timeout\.com|visitlondon\.com|secretldn\.com|kidrated\.com|"
                       r"dadsinlondon\.com|hoop\.co\.uk|designmynight\.com|allevents\.in|fatsoma\.com|blogspot\.com|wordpress\.com|"
                       r"instagram\.com|londonxlondon\.com|sohotheatre\.com\.ignored)$")
COUNCIL = re.compile(r"(\.gov\.uk|enjoyroyalgreenwich\.org\.uk)$")
SKIP_OUT = re.compile(r"(facebook|twitter|x\.com|instagram|youtube|youtu\.be|tiktok|linkedin|pinterest|whatsapp|threads\.net|"
                      r"google\.[a-z.]+/maps|maps\.google|goo\.gl|maps\.apple|bit\.ly/share|addtoany|sharethis|mailchimp|list-manage|"
                      r"doubleclick|googletagmanager|gravatar|wp\.com|cloudfront|cdn\.|apple\.com/app|play\.google|tfl\.gov\.uk/plan|"
                      r"simpleview|wordpress\.org|wix\.com|squarespace\.com|jadu|granicus|govdelivery|cookiebot|onetrust|"
                      r"gov\.uk/(?!.*event)|nhs\.uk|police\.uk)", re.I)
STOP = {"london", "event", "events", "family", "festival", "with", "from", "the", "and", "for", "day", "night", "show", "tour", "talk",
        "workshop", "free", "2026", "2027", "november", "december", "october", "saturday", "sunday"}

def host(u): return urlparse(u).netloc.lower().removeprefix("www.")

def get(url, n=600_000):
    req = Request(url, headers={"User-Agent": UA, "Accept": "text/html,application/xhtml+xml"})
    with urlopen(req, timeout=20) as r:
        if r.status >= 400: raise IOError(r.status)
        return r.geturl(), r.read(n).decode("utf-8", "ignore")

def outbound(page_url, doc):
    """Links leaving the listing site, with their anchor text and a little surrounding text."""
    base = host(page_url); out, seen = [], set()
    for m in re.finditer(r'(?is)<a\b[^>]*href=["\']([^"\'#]+)["\'][^>]*>(.*?)</a>', doc):
        u = urljoin(page_url, html.unescape(m.group(1)).strip())
        if not u.startswith("http") or SKIP_OUT.search(u): continue
        h = host(u)
        if not h or h == base or h.endswith("." + base) or base.endswith("." + h): continue
        if u in seen: continue
        seen.add(u)
        text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html.unescape(m.group(2)))).strip()[:80]
        ctx = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html.unescape(doc[max(0, m.start() - 300):m.start()]))).strip()[-140:]
        out.append({"url": u[:300], "text": text, "before": ctx})
        if len(out) >= 60: break
    return out

def words(s): return {w for w in re.findall(r"[a-z]{5,}", (s or "").lower()) if w not in STOP}

def mentions(doc, e):
    """The page talks about this event: shares at least two distinctive name words (or one, for short names)."""
    want = words(e["name"])
    if not want: return True
    text = re.sub(r"<[^>]+>", " ", doc).lower()
    hits = sum(1 for w in want if w in text)
    return hits >= min(2, len(want))

_client = None
def choose(e, page_url, links):
    global _client
    import anthropic
    _client = _client or anthropic.Anthropic()
    items = [{"i": n, **l} for n, l in enumerate(links)]
    prompt = (f"A London listings app shows this event and wants to link to its OFFICIAL page: the venue's or the organiser's own "
              f"website (a ticketing page on the organiser's own site, or their Eventbrite page, is fine).\n"
              f"Event: {e['name']}\nWhere: {e.get('area','')}\nAbout: {e.get('blurb','')[:200]}\nListed on: {page_url}\n\n"
              "Below are the links leaving that listing page, each with its link text and the text just before it. "
              "Pick the one that is the official page for THIS event. If the page lists many events, only pick a link that sits "
              "next to this event. Prefer the event's own page; otherwise the venue's or organiser's what's-on page. "
              "Never pick another listings/aggregator site, a news article, a map, social media, or a link about a different event.\n"
              'Reply ONLY with JSON: {"i": <index or null>, "kind": "event"|"venue"|"organiser"}\n' + json.dumps(items, ensure_ascii=False))
    try:
        msg = _client.messages.create(model=MODEL, max_tokens=200, thinking={"type": "disabled"}, messages=[{"role": "user", "content": prompt}])
    except Exception as ex:
        if "thinking" not in str(ex).lower(): raise
        msg = _client.messages.create(model=MODEL, max_tokens=2000, messages=[{"role": "user", "content": prompt}])
    txt = "".join(getattr(b, "text", "") for b in msg.content if getattr(b, "type", "") == "text")
    i0 = txt.find("{")
    if i0 < 0: return None, None
    v, _ = json.JSONDecoder().raw_decode(txt[i0:])          # first JSON object only, ignore anything after it
    i = v.get("i")
    return (links[i]["url"], v.get("kind")) if isinstance(i, int) and 0 <= i < len(links) else (None, None)

def main():
    limit = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else 400
    dry = "--dry" in sys.argv
    if not os.environ.get("ANTHROPIC_API_KEY"): print("official links: no API key, skipped", file=sys.stderr); return
    data = json.load(open(P)); ev = data["events"]
    todo = []
    for e in ev:
        if e.get("lk"): continue
        h = host(e.get("url", ""))
        if MIDDLEMEN.search(h) or COUNCIL.search(h): todo.append(e)
    print(f"official links: {len(todo)} listings to check", file=sys.stderr)
    # Instagram posts from before account websites were recorded: use the matching venue's own site
    venues = json.load(open("venues.json"))["venues"] if os.path.exists("venues.json") else []
    def venue_site(e):
        acct = re.sub(r"^Instagram @", "", e.get("source", ""))
        for v in venues:
            near = abs(float(v.get("lat", 0)) - float(e.get("lat", 0))) < 0.002 and abs(float(v.get("lon", 0)) - float(e.get("lon", 0))) < 0.003
            if near and (words(v["name"]) & (words(acct) | words(e.get("area", ""))) or near) and not MIDDLEMEN.search(host(v.get("url", ""))) and v.get("kind") not in ("aggregator", "blog", "ticketing", "council"):
                return v["url"]
        return None
    pages, changed, kept = {}, 0, 0
    for e in todo[:limit]:
        start = (e.get("site") or venue_site(e)) if "instagram.com" in e.get("url", "") else e["url"]
        if not start: kept += 1; continue                     # no website known yet: try again once Instagram tells us
        e.setdefault("site", start) if "instagram.com" in e["url"] else None
        e["lk"] = 1
        try:
            if start not in pages: pages[start] = get(start)
            final, doc = pages[start]
            links = outbound(final, doc)
            if "instagram.com" in e["url"]:                       # the account's own site: its own pages count too
                links = [{"url": urljoin(final, m.group(1))[:300], "text": re.sub(r"<[^>]+>", " ", m.group(2)).strip()[:80], "before": ""}
                         for m in re.finditer(r'(?is)<a\b[^>]*href=["\']([^"\'#]+)["\'][^>]*>(.*?)</a>', doc)
                         if host(urljoin(final, m.group(1))) == host(final)][:60] + links
            if not links: kept += 1; continue
            url, kind = choose(e, final, links)
            if not url or MIDDLEMEN.search(host(url)): kept += 1; continue
            got, page = get(url)
            # an event page must mention the event; a venue/organiser page just has to load (and isn't someone's homepage spam)
            if kind == "event" and not mentions(page, e): kept += 1; print(f"  ✗ {e['name'][:40]}: {url[:70]} doesn't mention it", file=sys.stderr); continue
            if "instagram.com" in e["url"] and kind != "event" and not mentions(page, e):
                url = e.get("site") or url                          # fall back to the account's homepage, still official
            elif kind != "event" and not mentions(page, e) and not (words(e.get("area", "")) & words(re.sub(r"<[^>]+>", " ", page))):
                kept += 1; print(f"  ✗ {e['name'][:40]}: {url[:70]} mentions neither the event nor {e.get('area','')}", file=sys.stderr); continue
            e["via"] = e["url"]; e["url"] = got if host(got) == host(url) else url; changed += 1
            print(f"  ✓ {e['name'][:40]}: {host(e['via'])} → {e['url'][:80]} ({kind})", file=sys.stderr)
        except Exception as ex:
            kept += 1; print(f"  · {e['name'][:40]}: {str(ex)[:60]}", file=sys.stderr)
            e["lk_try"] = e.get("lk_try", 0) + 1
            if e["lk_try"] < 3: e.pop("lk", None)                # a passing error: try again another day
        time.sleep(0.3)
    if not dry: json.dump(data, open(P, "w"), indent=1, ensure_ascii=False)
    print(f"official links: {changed} now go to the venue/organiser, {kept} kept as they were", file=sys.stderr)

if __name__ == "__main__":
    main()
