#!/usr/bin/env python3
"""
WhatToDo? events ingester, v2: source-first.

For every venue in venues.json (run probe.py first so each has a feed type):
  jsonld   → parse schema.org Event markup from the listing page, plus linked event pages (cap 40)
  ics      → parse the calendar feed
  rss      → feed items → Claude normalises
  html     → page text → Claude normalises (fallback only)
  eventbrite / aggregators → treated as jsonld/html pages like any other

Claude is only called for rss/html sources and for a short "fill the gaps" pass
(indoor/outdoor, age fit, tags, 30-word blurb) on structured events that lack them.

Usage:
  export ANTHROPIC_API_KEY=sk-ant-...
  python3 ingest.py --days 14 --out docs/events.json
  python3 ingest.py --no-llm          # structured sources only, no API spend
"""
import argparse, datetime as dt, json, os, re, sys, time, html
from urllib.parse import urljoin
from urllib.request import Request, urlopen
import meter   # records what each Claude call costs, reported to the dashboard
import eventbrite   # official API when EVENTBRITE_TOKEN is set (Eventbrite's pages block automated reading)

MODEL = os.environ.get("WTD_MODEL", "claude-haiku-5-5")
UA = "WhatToDo-ingest/0.2 (+personal project; summarises in its own words and links back)"
LONDON = dict(lat=(51.25, 51.75), lon=(-0.55, 0.35))
EVENT_TYPES = {"Event","ExhibitionEvent","Festival","MusicEvent","TheaterEvent","ChildrensEvent","EducationEvent","SocialEvent","SportsEvent","VisualArtsEvent","ComedyEvent","ScreeningEvent","FoodEvent","DanceEvent"}

SCHEMA = """Each event is a JSON object:
{"name": str, "area": str (neighbourhood), "lat": float, "lon": float, "in": "in"|"out"|"both",
 "price": "free"|"£"|"££" (£ = under ~£15/adult), "ages": [min,max] (99 = any), "kids": 0-3 (how much children would actually enjoy it, not whether they are allowed; ceremonies, talks and services are 0), "adults": 0-3,
 "dur": hours, "parking": short note only if the venue states it, e.g. "car park on site" / "no parking" (else omit), "tags": [3-5 lowercase words], "blurb": own words, max 35 words, practical,
 "emoji": one emoji for what the thing IS, not where it happens (a space science show → 🚀, a book talk → 📚, a carol concert → 🎄),
 "days": weekday names e.g. ["Sun"] ONLY if it runs on some weekdays but not others, "open"/"close": "HH:MM" opening hours or start/end ONLY if stated,
 "url": the event's own page, then EITHER "date": "YYYY-MM-DD" (+ optional "time") OR "from"/"to": "YYYY-MM-DD".
 If it runs on several separate days rather than every day in a span (e.g. "Sat 14 & Sun 15 Nov, Sat 12 & Sun 13 Dec"), also give
 "dates": every one of those days as "YYYY-MM-DD", including ones further ahead, with "from"/"to" the first and last of them."""

# ---------- fetch ----------
def get(url):
    req = Request(url, headers={"User-Agent": UA, "Accept": "text/html,application/xhtml+xml,text/calendar,*/*"})
    with urlopen(req, timeout=25) as r:
        return r.geturl(), r.read().decode("utf-8", "ignore")

def page_text(doc, base=None):
    """The page's text. With base, links stay in as "text [url]" so each event can get its own page, not the listing."""
    doc = re.sub(r"(?is)<(script|style|nav|footer|header).*?</\1>", " ", doc)
    if base:
        def a(m):
            href = urljoin(base, html.unescape(m.group(1)).strip()); t = re.sub(r"<[^>]+>", " ", m.group(2))
            if not href.startswith("http") or href.rstrip("/") == base.rstrip("/") or len(re.sub(r"\s+", "", t)) < 3: return t
            return f"{t} [{href[:160]}]"
        doc = re.sub(r'(?is)<a\b[^>]*href=["\']([^"\'#]+)["\'][^>]*>(.*?)</a>', a, doc)
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"(?s)<[^>]+>", " ", doc)))[:48000]

# ---------- JSON-LD ----------
def ld_objects(doc):
    for m in re.finditer(r'(?is)<script[^>]+application/ld\+json[^>]*>(.*?)</script>', doc):
        try: data = json.loads(m.group(1))
        except Exception: continue
        stack = [data]
        while stack:
            x = stack.pop()
            if isinstance(x, list): stack += x
            elif isinstance(x, dict):
                yield x
                for k in ("@graph", "itemListElement", "item", "subEvent", "event"):
                    if k in x: stack.append(x[k])

def is_event(x):
    t = x.get("@type"); ts = t if isinstance(t, list) else [t]
    return any(str(v) in EVENT_TYPES for v in ts)

def d10(s):
    return str(s)[:10] if s and re.match(r"\d{4}-\d{2}-\d{2}", str(s)) else None

def tm(s):
    m = re.search(r"T(\d{2}):(\d{2})", str(s or ""));
    if not m: return None
    h, mi = int(m.group(1)), m.group(2)
    return f"{h%12 or 12}{'' if mi=='00' else ':'+mi}{'am' if h<12 else 'pm'}"

def price_band(x):
    offers = x.get("offers") or []
    offers = offers if isinstance(offers, list) else [offers]
    prices = []
    for o in offers:
        if not isinstance(o, dict): continue
        for k in ("price", "lowPrice"):
            try: prices.append(float(str(o.get(k)).replace("£", "")))
            except Exception: pass
    if x.get("isAccessibleForFree") is True or (prices and min(prices) == 0): return "free"
    if not prices: return None
    return "£" if min(prices) < 15 else "££"

def from_ld(x, venue, page_url):
    loc = x.get("location") or {}
    if isinstance(loc, list): loc = loc[0] if loc else {}
    geo = (loc.get("geo") or {}) if isinstance(loc, dict) else {}
    addr = (loc.get("address") or {}) if isinstance(loc, dict) else {}
    start = x.get("startDate"); end = x.get("endDate")
    e = {"name": html.unescape(str(x.get("name", ""))).strip(),
         "area": (addr.get("addressLocality") if isinstance(addr, dict) else None) or venue["area"],
         "lat": float(geo.get("latitude", venue["lat"]) or venue["lat"]), "lon": float(geo.get("longitude", venue["lon"]) or venue["lon"]),
         "url": x.get("url") if str(x.get("url", "")).startswith("http") else page_url,
         "price": price_band(x), "raw_desc": re.sub(r"<[^>]+>", " ", str(x.get("description", "")))[:600],
         "source": venue["name"]}
    s, en = d10(start), d10(end)
    if not s: return None
    if en and en != s: e.update({"from": s, "to": en})
    else: e.update({"date": s, "time": tm(start)})
    return e

def event_links(doc, base, limit=40):
    out = []
    for m in re.finditer(r'(?is)<a\b[^>]*href=["\']([^"\']+)["\']', doc):
        href = urljoin(base, html.unescape(m.group(1)))
        if (re.search(r"/(event|events|whats-on|whatson|exhibition|exhibitions)/[^/?#]+", href) or re.search(r"eventbrite\.[a-z.]+/e/[^/?#]+-\d{6,}", href)) \
                and href not in out and href.rstrip("/") != base.rstrip("/"):
            out.append(href)
        if len(out) >= limit: break
    return out

def harvest_jsonld(venue):
    evs = []
    try: final, doc = get(venue["url"])
    except Exception as ex: print(f"  fetch failed: {ex}", file=sys.stderr); return evs
    pages = [(final, doc)]
    if sum(1 for x in ld_objects(doc) if is_event(x)) < 3:          # listing page is thin: follow links
        for href in event_links(doc, final):
            if eventbrite.enabled() and eventbrite.event_id(href) and "eventbrite." in href:
                e = eventbrite.event(href, default=venue)
                if e: e["source"] = venue["name"]; evs.append(e)
                continue
            try: pages.append(get(href)); time.sleep(1)
            except Exception: pass
    for url, d in pages:
        for x in ld_objects(d):
            if is_event(x):
                e = from_ld(x, venue, url)
                if e: evs.append(e)
    return evs

# ---------- ICS ----------
def harvest_ics(venue):
    url = venue.get("feed_url") or venue["url"]
    try: _, body = get(url.replace("webcal://", "https://"))
    except Exception as ex: print(f"  ics failed: {ex}", file=sys.stderr); return []
    evs = []
    for block in re.findall(r"(?s)BEGIN:VEVENT(.*?)END:VEVENT", body):
        f = dict(re.findall(r"(?m)^([A-Z\-]+)(?:;[^:]*)?:(.*)$", block.replace("\r", "")))
        s, en = d10(re.sub(r"(\d{4})(\d{2})(\d{2}).*", r"\1-\2-\3", f.get("DTSTART", ""))), d10(re.sub(r"(\d{4})(\d{2})(\d{2}).*", r"\1-\2-\3", f.get("DTEND", "")))
        if not s: continue
        e = {"name": f.get("SUMMARY", "").strip(), "area": venue["area"], "lat": venue["lat"], "lon": venue["lon"],
             "url": f.get("URL") or venue["url"], "price": None, "raw_desc": f.get("DESCRIPTION", "")[:600].replace("\\n", " "), "source": venue["name"]}
        if en and en != s and (dt.date.fromisoformat(en) - dt.date.fromisoformat(s)).days > 1: e.update({"from": s, "to": en})
        else: e.update({"date": s})
        evs.append(e)
    return evs

# ---------- Claude ----------
def parse_array(out):
    """Tolerant JSON-array parse: handles trailing prose, truncated output, trailing commas; salvages complete objects."""
    m = re.search(r"\[", out)
    if not m: return []
    text = out[m.start():]
    for cand in (text, text[:text.rfind("]")+1] if "]" in text else text):
        try: return json.loads(cand)
        except Exception: pass
    objs, depth, start = [], 0, None
    for i, ch in enumerate(text):
        if ch == "{":
            if depth == 0: start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start is not None:
                try: objs.append(json.loads(re.sub(r",\s*}", "}", text[start:i+1])))
                except Exception: pass
                start = None
    return objs

_client = None
def claude(prompt, max_tokens=16000):
    global _client
    import anthropic
    _client = _client or anthropic.Anthropic()
    msg = _client.messages.create(model=MODEL, max_tokens=max_tokens, messages=[{"role": "user", "content": prompt}])
    out = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
    return parse_array(out)

def listing_url(venue):
    """The page to read. A site's RSS feed is usually its news/blog (WordPress has one by default), not its events,
    so for "rss" venues read the events page itself unless the feed is clearly an events feed."""
    fu = venue.get("feed_url")
    if venue.get("feed") == "rss" and fu and not re.search(r"event|whats-?on|calendar|programme", fu, re.I): return venue["url"]
    return fu or venue["url"]

# Pages that haven't changed since the last read keep last time's events, so Claude only reads what's new.
CACHE_P, CACHE_DAYS = "ingest_cache.json", 3
CACHE = json.load(open(CACHE_P)) if os.path.exists(CACHE_P) else {}

def harvest_html(venue, horizon, log=None):
    try: final, doc = get(listing_url(venue))
    except Exception as ex: print(f"  fetch failed: {ex}", file=sys.stderr); return []
    text = page_text(doc, final)
    import hashlib
    h = hashlib.sha1(re.sub(r"\d{1,2}:\d{2}(:\d{2})?", "", text).encode()).hexdigest()[:16]
    c = CACHE.get(venue["id"])
    if c and c.get("h") == h and (dt.date.today() - dt.date.fromisoformat(c["day"])).days < CACHE_DAYS:
        if log is not None: log.append(f"  page unchanged since {c['day']}: reused")
        return [dict(e) for e in c["evs"]]
    prompt = f"""Extract things to do in London from this listings page for a weekend-planning app.
Source: {venue['name']} ({final}). Today is {dt.date.today()}; include only events between today and {horizon}.
Skip permanent attractions, online events, anything outside Greater London, anything without a usable date.
Regular sessions the public can join (a weekly class, club, quiz, choir, open studio, baby group) count too: list each ONCE with
"regular": true, "days": the weekday(s) it runs, "time", and "from"/"to" for the term or season (if no end is given, the next 3 months).
If the venue is a single place, use lat {venue['lat']}, lon {venue['lon']}; otherwise estimate the venue's coordinates.
For "url": each event's OWN page. Links in the text appear as "text [url]"; use the one next to that event (its title, "more info",
"book"). Use the listing page {final} only if the event has no link of its own.
Return ONLY a JSON array of at most 40 events, most relevant first.
{SCHEMA}
PAGE TEXT:
{text}"""
    evs = claude(prompt)
    for e in evs: e["source"] = venue["name"]
    CACHE[venue["id"]] = {"h": h, "day": dt.date.today().isoformat(), "evs": [dict(e) for e in evs if isinstance(e, dict)]}
    return evs

def enrich(evs, venue):
    """Fill in/out, ages, kids/adults, tags, dur and a 30-word blurb for structured events, in one call per venue."""
    d = venue.get("defaults", {})
    need = [e for e in evs if "blurb" not in e]
    if not need: return evs
    compact = [{"i": i, "name": e["name"], "desc": e.get("raw_desc", "")[:300], "price": e.get("price")} for i, e in enumerate(need)]
    prompt = f"""For each event below from {venue['name']} (a {venue.get('kind')}), return a JSON array of objects
{{"i": index, "in": "in"|"out"|"both", "price": "free"|"£"|"££" (keep the given price if present; otherwise infer, "free" only if clearly free),
 "ages": [min,max], "kids": 0-3, "adults": 0-3, "dur": hours, "emoji": one emoji for what it IS (a space show → 🚀), "parking": short note only if the venue states it, e.g. "car park on site" / "no parking" (else omit), "tags": [3-5 lowercase words], "days": ["Sun"] only if it runs on some weekdays but not others, "open"/"close": "HH:MM" only if stated, "blurb": your own words, max 30 words, practical}}.
Venue defaults if unsure: {json.dumps(d)}.
EVENTS: {json.dumps(compact, ensure_ascii=False)}"""
    try: fills = {f["i"]: f for f in claude(prompt)}
    except Exception as ex: print(f"  enrich failed: {ex}", file=sys.stderr); fills = {}
    for i, e in enumerate(need):
        f = fills.get(i, {})
        e["in"] = f.get("in") or d.get("in", "both"); e["price"] = e.get("price") or f.get("price") or "£"
        e["ages"] = f.get("ages") or d.get("ages", [0, 99]); e["kids"] = f.get("kids", d.get("kids", 1)); e["adults"] = f.get("adults", d.get("adults", 2))
        e["dur"] = f.get("dur", 2)
        if f.get("parking"): e["parking"] = str(f["parking"])[:40]
        if f.get("emoji") and len(str(f["emoji"])) <= 8: e["emoji"] = str(f["emoji"])
        for k in ("days", "open", "close"):
            if f.get(k) and not e.get(k): e[k] = f[k]
        e["tags"] = (f.get("tags") or d.get("tags", []))[:5]
        e["blurb"] = f.get("blurb") or (e.get("raw_desc", "")[:160] or e["name"])
    return evs

# fields later steps work out (relevance, hours, official link): keep them when an event is re-scraped
CARRY = ("rel", "hrs", "days", "open", "close", "part", "lk", "lk_try", "via", "site", "emoji", "eb", "dl")
def carry(old, new):
    for f in CARRY:
        if f in old and f not in new: new[f] = old[f]
    if old.get("via") and new.get("url") in (old.get("via"), None): new["url"] = old["url"]
    return new

# ---------- validate / merge ----------
def norm_dates(e, today):
    """A list of separate dates becomes the listing's own days: sorted, past ones dropped, from/to set to the first and last."""
    ds = e.get("dates")
    if not isinstance(ds, list): e.pop("dates", None); return
    ds = sorted({str(d)[:10] for d in ds if re.match(r"\d{4}-\d{2}-\d{2}$", str(d)[:10]) and str(d)[:10] >= today.isoformat()})
    if len(ds) < 2:
        e.pop("dates", None)
        if ds and not e.get("date"): e.pop("from", None); e.pop("to", None); e["date"] = ds[0]
        return
    e["dates"] = ds; e.pop("date", None); e["from"], e["to"] = ds[0], ds[-1]

def valid(e, today, horizon):
    try:
        norm_dates(e, today)
        if e.get("regular") and e.get("days") and not (e.get("date") or e.get("to")):     # a regular with no end: the next 3 months
            e.setdefault("from", today.isoformat()); e["to"] = (today + dt.timedelta(days=90)).isoformat()
        if not (LONDON["lat"][0] <= float(e["lat"]) <= LONDON["lat"][1] and LONDON["lon"][0] <= float(e["lon"]) <= LONDON["lon"][1]): return False
        if e.get("in") not in ("in", "out", "both") or e.get("price") not in ("free", "£", "££"): return False
        if not e.get("name") or not e.get("blurb") or not str(e.get("url", "")).startswith("http"): return False
        s = e.get("date") or e.get("from"); en = e.get("date") or e.get("to")
        if not (s and en): return False
        return en >= today.isoformat() and s <= horizon.isoformat()
    except (KeyError, ValueError, TypeError):
        return False

def key(e): return re.sub(r"[^a-z0-9]", "", e["name"].lower())[:40] + (e.get("date") or e.get("from", ""))
def slug(e): return "ev-" + re.sub(r"[^a-z0-9]+", "-", e["name"].lower()).strip("-")[:40] + "-" + (e.get("date") or e.get("from"))[5:]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=14); ap.add_argument("--out", default="events.json")
    ap.add_argument("--venues", default="venues.json"); ap.add_argument("--no-llm", action="store_true"); ap.add_argument("--only")
    a = ap.parse_args()
    today = dt.date.today(); horizon = today + dt.timedelta(days=a.days)
    venues = json.load(open(a.venues))["venues"]
    existing = {}
    if os.path.exists(a.out):
        for e in json.load(open(a.out)).get("events", []): existing[key(e)] = e

    def one(v):
        """One venue: its log lines and its events. Venues are different sites, so several run at once."""
        log = [f"{v['id']} [{v.get('feed', 'html')}]"]
        feed = v.get("feed", "html")
        try:
            if eventbrite.enabled() and eventbrite.organizer_id(v["url"]):          # an Eventbrite organiser: use the API
                evs = eventbrite.organizer_events(v["url"], default=v); [e.__setitem__("source", v["name"]) for e in evs]
            elif feed == "jsonld" or feed == "eventbrite": evs = harvest_jsonld(v)
            elif feed == "ics": evs = harvest_ics(v)
            elif feed in ("rss", "html", "error"): evs = [] if a.no_llm else harvest_html(v, horizon, log)
            else: evs = []
        except Exception as ex:
            log.append(f"  failed: {str(ex)[:120]}"); evs = []
        evs = [e for e in evs if (e.get("date") or e.get("to", "")) >= today.isoformat() and (e.get("date") or e.get("from", "")) <= horizon.isoformat()]
        for e in evs:
            old = existing.get(key(e)) if e.get("name") and (e.get("date") or e.get("from")) else None
            if old and old.get("blurb") and "blurb" not in e:
                for f in ("in", "price", "ages", "kids", "adults", "dur", "tags", "blurb", "emoji"):
                    if f in old and f not in e: e[f] = old[f]
        if evs and not a.no_llm:
            try: evs = enrich(evs, v)
            except Exception as ex: log.append(f"  enrich failed: {str(ex)[:80]}")
        elif evs:                                     # no LLM: venue defaults, description as blurb
            d = v.get("defaults", {})
            for e in evs:
                e.setdefault("in", d.get("in", "both")); e["price"] = e.get("price") or "£"; e.setdefault("ages", d.get("ages", [0, 99]))
                e.setdefault("kids", d.get("kids", 1)); e.setdefault("adults", d.get("adults", 2)); e.setdefault("dur", 2); e.setdefault("tags", d.get("tags", []))
                e["blurb"] = (e.get("raw_desc") or e["name"])[:160]
        for e in evs:
            e.pop("raw_desc", None); e["id"] = slug(e); e["source"] = e.get("source") or v["name"]
        ok = [e for e in evs if valid(e, today, horizon)]
        log.append(f"  {len(ok)} events")
        return log, ok

    from concurrent.futures import ThreadPoolExecutor
    todo = [v for v in venues if not (a.only and v["id"] != a.only)]
    found = []
    with ThreadPoolExecutor(max_workers=int(os.environ.get("INGEST_WORKERS", "6"))) as pool:
        for log, ok in pool.map(one, todo):
            print("\n".join(log), file=sys.stderr); found += ok

    keep = {k: c for k, c in CACHE.items() if (today - dt.date.fromisoformat(c["day"])).days < 14}
    json.dump(keep, open(CACHE_P, "w"), ensure_ascii=False)
    merged = dict(existing)
    for e in found: merged[key(e)] = carry(existing[key(e)], e) if key(e) in existing else e
    events = [e for e in merged.values() if (e.get("date") or e.get("to", "")) >= today.isoformat()]
    events.sort(key=lambda e: e.get("date") or e.get("from"))
    json.dump({"generated": today.isoformat(), "events": events}, open(a.out, "w"), indent=1, ensure_ascii=False)
    print(f"wrote {len(events)} events to {a.out}")

if __name__ == "__main__":
    main()
