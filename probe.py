#!/usr/bin/env python3
"""
Probe every venue in venues.json and record what structured feed it offers.

  python3 probe.py                 # updates venues.json in place (adds "feed", "feed_url", "probed")
  python3 probe.py --discover      # also harvests candidate venue URLs from the aggregator pages
                                   # into candidates.csv for you to review and add

Feed detection order: JSON-LD Event markup → ICS link → RSS/Atom link → Eventbrite organiser → html.
"""
import argparse, csv, datetime as dt, json, re, sys, time, html
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

UA = "WhatToDo-probe/0.1 (+personal project; checks for public event feeds)"
EVENT_TYPES = {"Event","ExhibitionEvent","Festival","MusicEvent","TheaterEvent","ChildrensEvent","EducationEvent","SocialEvent","SportsEvent","VisualArtsEvent","ComedyEvent","ScreeningEvent","FoodEvent","DanceEvent"}

def get(url):
    req = Request(url, headers={"User-Agent": UA, "Accept": "text/html,application/xhtml+xml,*/*"})
    with urlopen(req, timeout=25) as r:
        return r.geturl(), r.read().decode("utf-8", "ignore")

def jsonld_events(doc):
    n = 0
    for m in re.finditer(r'(?is)<script[^>]+application/ld\+json[^>]*>(.*?)</script>', doc):
        try:
            data = json.loads(m.group(1))
        except Exception:
            continue
        stack = [data]
        while stack:
            x = stack.pop()
            if isinstance(x, list):
                stack += x
            elif isinstance(x, dict):
                t = x.get("@type")
                ts = t if isinstance(t, list) else [t]
                if any(str(v) in EVENT_TYPES for v in ts):
                    n += 1
                for k in ("@graph", "itemListElement", "item", "subEvent", "event"):
                    if k in x:
                        stack.append(x[k])
    return n

def find_links(doc, base):
    out = {"ics": None, "rss": None, "eventbrite": None}
    for m in re.finditer(r'(?is)<(?:a|link)\b[^>]*?(?:href)=["\']([^"\']+)["\'][^>]*>', doc):
        href = urljoin(base, html.unescape(m.group(1)))
        tag = m.group(0).lower()
        if not out["ics"] and (href.lower().endswith(".ics") or "webcal://" in href or "format=ical" in href.lower()):
            out["ics"] = href
        if not out["rss"] and ("application/rss+xml" in tag or "application/atom+xml" in tag or re.search(r"/(feed|rss)(/|\.xml|$)", href.lower())):
            out["rss"] = href
        if not out["eventbrite"] and re.search(r"eventbrite\.[a-z.]+/o/", href.lower()):
            out["eventbrite"] = href
    return out

LISTING = re.compile(r"/(whats-on|what-s-on|whatson|events?|things-to-do|calendar|programme)(/|$|\?)", re.I)

def find_listing(url):
    """URL 404s or redirects badly: open the site's home page and follow its what's-on/events link."""
    root = re.match(r"https?://[^/]+", url).group(0) + "/"
    final, doc = get(root)
    best = None
    for m in re.finditer(r'(?is)<a\b[^>]*href=["\']([^"\'#]+)["\'][^>]*>(.*?)</a>', doc):
        href = urljoin(final, html.unescape(m.group(1))); text = re.sub(r"<[^>]+>", "", m.group(2)).strip().lower()
        if urlparse(href).netloc.replace("www.", "") != urlparse(final).netloc.replace("www.", ""): continue
        if LISTING.search(urlparse(href).path) or text in ("what's on", "whats on", "events", "what’s on"):
            if best is None or len(href) < len(best): best = href
    return best

def probe(v):
    rec = {"probed": dt.date.today().isoformat()}
    try:
        final, doc = get(v["url"])
    except Exception as ex:
        code = getattr(ex, "code", None)
        if code in (404, 307, 308, 301, 302) or "redirect" in str(ex):
            try:
                alt = find_listing(v["url"])
                if alt:
                    final, doc = get(alt); rec["url"] = alt; rec["was"] = v["url"]
                else:
                    rec.update(feed="error", error=str(ex)[:120]); return rec
            except Exception as ex2:
                rec.update(feed="error", error=str(ex2)[:120]); return rec
        else:
            rec.update(feed="blocked" if code in (403, 405, 429) else "error", error=str(ex)[:120]); return rec
    n = jsonld_events(doc)
    links = find_links(doc, final)
    if n:
        rec.update(feed="jsonld", feed_url=final, jsonld_events=n)
    elif links["ics"]:
        rec.update(feed="ics", feed_url=links["ics"])
    elif links["rss"]:
        rec.update(feed="rss", feed_url=links["rss"])
    elif links["eventbrite"]:
        rec.update(feed="eventbrite", feed_url=links["eventbrite"])
    else:
        rec.update(feed="html", feed_url=final)
    for k in ("ics", "rss", "eventbrite"):
        if links[k]: rec["has_" + k] = links[k]
    return rec

def discover(venues):
    known = {urlparse(v["url"]).netloc.replace("www.", "") for v in venues}
    seen = {}
    for v in venues:
        if v.get("kind") != "aggregator": continue
        try:
            final, doc = get(v["url"])
        except Exception:
            continue
        for m in re.finditer(r'(?is)<a\b[^>]*href=["\'](https?://[^"\']+)["\'][^>]*>(.*?)</a>', doc):
            href, text = m.group(1), re.sub(r"<[^>]+>", "", m.group(2)).strip()
            host = urlparse(href).netloc.replace("www.", "")
            if host in known or host == urlparse(final).netloc.replace("www.", ""): continue
            if any(b in host for b in ("facebook.", "instagram.", "twitter.", "x.com", "tiktok.", "youtube.", "google.", "apple.", "amazon.", "wikipedia.")): continue
            seen.setdefault(host, {"host": host, "example_url": href, "text": text[:60], "found_on": v["id"]})
        time.sleep(2)
    with open("candidates.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["host", "example_url", "text", "found_on"]); w.writeheader()
        for row in seen.values(): w.writerow(row)
    print(f"{len(seen)} candidate hosts written to candidates.csv")

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--discover", action="store_true"); ap.add_argument("--only")
    a = ap.parse_args()
    reg = json.load(open("venues.json")); venues = reg["venues"]
    for v in venues:
        if a.only and v["id"] != a.only: continue
        if v.get("feed") == "skip": continue
        for k in ("error", "was"): v.pop(k, None)
        v.update(probe(v))
        print(f'{v["id"]:22} {v.get("feed","?"):10} {v.get("jsonld_events","")} {("-> " + v["url"]) if v.get("was") else ""} {v.get("error","")[:50]}', file=sys.stderr)
        time.sleep(1.5)
    json.dump(reg, open("venues.json", "w"), indent=1, ensure_ascii=False)
    counts = {}
    for v in venues: counts[v.get("feed")] = counts.get(v.get("feed"), 0) + 1
    print("feed types:", counts)
    if a.discover: discover(venues)

if __name__ == "__main__":
    main()
