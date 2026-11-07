#!/usr/bin/env python3
"""
Point "Details" at the event's own page when a listing only links to a general what's-on page.

For each listing whose link is a venue's what's-on/events/home page: open that page (once per page per run),
find the link whose text matches the event's name, and switch to it (the old link is kept as "via").
No Claude: plain text matching, so it's free to run daily. Each listing is tried once per link ("dl").

  python3 deep_links.py [--limit N] [--dry]
"""
import json, re, sys, time, html
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

P = "docs/events.json"
UA = "JauntOut-links/0.1 (+https://www.jauntout.com; finds the event's own page on its venue's listing)"
GENERIC = re.compile(r"/(whats-?on|what-s-on|events?|calendar|programme|listings?|diary|shows?|exhibitions?|whatson|gigs|families|kids|learning|visit)/?$", re.I)
TICKETS = re.compile(r"(eventbrite\.|ticketsource\.|tickettailor\.|spektrix|ticketsolve\.|wegottickets\.|skiddle\.|seetickets\.|dice\.fm|universe\.com|ticketweb\.|bookwhen\.)", re.I)
STOP = {"the", "and", "with", "for", "from", "at", "of", "in", "on", "a", "an", "to", "by", "london", "event", "events", "day",
        "tour", "talk", "show", "workshop", "free", "family", "night", "late", "session", "sessions", "club", "2026", "2027"}

def host(u): return urlparse(u).netloc.lower().removeprefix("www.")
def words(s): return [w for w in re.findall(r"[a-z0-9']+", html.unescape(s or "").lower().replace("&", " and ")) if w not in STOP and len(w) > 1]

def generic(e, venue_urls):
    u = e.get("url", "")
    if not u.startswith("http"): return False
    path = urlparse(u).path or "/"
    return u.rstrip("/") in venue_urls or path in ("", "/") or bool(GENERIC.search(path))

def get(url):
    with urlopen(Request(url, headers={"User-Agent": UA, "Accept": "text/html"}), timeout=20) as r:
        return r.geturl(), r.read(900_000).decode("utf-8", "ignore")

def anchors(base, doc):
    doc = re.sub(r"(?is)<(script|style|nav|footer|header).*?</\1>", " ", doc)
    out = []
    for m in re.finditer(r'(?is)<a\b([^>]*)href=["\']([^"\'#]+)["\']([^>]*)>(.*?)</a>', doc):
        href = urljoin(base, html.unescape(m.group(2)).strip())
        if not href.startswith("http"): continue
        attrs = m.group(1) + m.group(3)
        title = " ".join(re.findall(r'(?:title|aria-label)=["\']([^"\']+)', attrs))
        text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", m.group(4))) + " " + title
        alt = " ".join(re.findall(r'alt=["\']([^"\']+)', m.group(4)))
        out.append((href, (text + " " + alt).strip()))
    return out

def best(e, page_url, links):
    want = words(re.sub(r"\(.*?\)", " ", e["name"]))
    if not want: return None
    ph = host(page_url); cands = []
    for href, text in links:
        h = host(href)
        if href.rstrip("/") == page_url.rstrip("/") or GENERIC.search(urlparse(href).path or "/") or (urlparse(href).path or "/") == "/": continue
        if not (h == ph or h.endswith("." + ph) or ph.endswith("." + h) or TICKETS.search(h)): continue
        have = set(words(text)) | set(words(urlparse(href).path.replace("-", " ").replace("_", " ").replace("/", " ")))
        hit = sum(1 for w in want if w in have)
        need = len(want) if len(want) <= 2 else max(2, round(len(want) * 0.75))
        if len(want) == 1 and len(words(text)) > 5: continue          # a one-word name must be most of the link's text
        if hit >= need: cands.append((hit / len(want), -len(href), href))
    if not cands: return None
    cands.sort(reverse=True)
    if len(cands) > 1 and cands[0][0] == cands[1][0] and cands[0][2].split("?")[0] != cands[1][2].split("?")[0]:
        top = [c for c in cands if c[0] == cands[0][0]]           # equally good links to different pages: only if one names it in its address
        named = [c for c in top if all(w in urlparse(c[2]).path.lower() for w in want[:2])]
        return named[0][2] if len(named) == 1 else None
    return cands[0][2]

def main():
    limit = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else 1500
    dry = "--dry" in sys.argv
    data = json.load(open(P)); ev = data["events"]
    venues = json.load(open("venues.json"))["venues"]
    venue_urls = {v["url"].rstrip("/") for v in venues} | {(v.get("feed_url") or "").rstrip("/") for v in venues}
    todo = [e for e in ev if generic(e, venue_urls) and e.get("dl") != e.get("url")][:limit]
    print(f"deep links: {len(todo)} listings link to a general page", file=sys.stderr)
    pages, fixed = {}, 0
    for e in todo:
        u = e["url"]
        if u not in pages:
            try: pages[u] = get(u); time.sleep(0.4)
            except Exception as ex: pages[u] = None; print(f"  · {u[:70]}: {str(ex)[:50]}", file=sys.stderr)
        got = pages[u]
        e["dl"] = u                                              # tried for this link; tried again only if the link changes
        if not got: continue
        final, doc = got
        link = best(e, final, anchors(final, doc))
        if link:
            e.setdefault("via", u); e["url"] = link; e["dl"] = link; fixed += 1
            print(f"  ✓ {e['name'][:40]} → {link[:90]}", file=sys.stderr)
    if not dry: json.dump(data, open(P, "w"), indent=1, ensure_ascii=False)
    print(f"deep links: {fixed} now go to the event's own page ({len(pages)} listing pages read)", file=sys.stderr)

if __name__ == "__main__":
    main()
