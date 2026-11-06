"""
Eventbrite's official API (needs EVENTBRITE_TOKEN, the account's private token). Eventbrite's web pages block
automated reading, so with a token we use the API instead:

  organizer_events(url_or_id)  → upcoming public events for an Eventbrite organiser page (/o/name-12345678901)
  event(url_or_id)             → one event (/e/name-123456789012), with venue, times and price

Both return events in JauntOut's shape (name, date/time or from/to, lat/lon, area, url, price, raw_desc).
Without a token every function returns [] / None and callers carry on as before.
"""
import json, os, re, sys, time, datetime as dt
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError

API = "https://www.eventbriteapi.com/v3"
TOKEN = os.environ.get("EVENTBRITE_TOKEN", "").strip()
_cache = {}

def enabled(): return bool(TOKEN)

def get(path, **params):
    if not TOKEN: return None
    url = f"{API}{path}" + ("?" + urlencode(params) if params else "")
    if url in _cache: return _cache[url]
    for attempt in range(3):
        try:
            req = Request(url, headers={"Authorization": f"Bearer {TOKEN}", "User-Agent": "JauntOut/0.1 (+https://www.jauntout.com)"})
            with urlopen(req, timeout=20) as r: data = json.loads(r.read())
            _cache[url] = data; return data
        except HTTPError as ex:
            if ex.code == 429: time.sleep(5 * (attempt + 1)); continue        # rate limited: back off
            if ex.code in (400, 403, 404): _cache[url] = None; return None
            raise
    return None

def organizer_id(u):
    m = re.search(r"eventbrite\.[a-z.]+/o/(?:[^/?#]*-)?(\d{6,})", str(u)); return m.group(1) if m else (str(u) if str(u).isdigit() else None)

def event_id(u):
    m = re.search(r"eventbrite\.[a-z.]+/e/(?:[^/?#]*-)?(\d{6,})", str(u)); return m.group(1) if m else (str(u) if str(u).isdigit() else None)

def _shape(x, default=None):
    """Eventbrite event JSON → JauntOut event, or None for online-only, cancelled or past ones."""
    if not x or x.get("online_event") or x.get("status") in ("canceled", "cancelled", "draft", "ended", "completed"): return None
    st, en = (x.get("start") or {}).get("local", ""), (x.get("end") or {}).get("local", "")
    if not st: return None
    v = x.get("venue") or {}; a = v.get("address") or {}
    lat, lon = a.get("latitude") or v.get("latitude"), a.get("longitude") or v.get("longitude")
    d = default or {}
    try: lat, lon = float(lat), float(lon)
    except (TypeError, ValueError): lat, lon = d.get("lat"), d.get("lon")
    if lat is None: return None
    e = {"name": ((x.get("name") or {}).get("text") or "").strip(), "url": x.get("url") or "",
         "lat": round(lat, 5), "lon": round(lon, 5),
         "area": d.get("area") or (a.get("city") if a.get("city") and a.get("city").lower() != "london" else None) or "London",
         "raw_desc": ((x.get("summary") or "") or ((x.get("description") or {}).get("text") or ""))[:600]}
    if x.get("is_free"): e["price"] = "free"
    ta = x.get("ticket_availability") or {}
    lo = (ta.get("minimum_ticket_price") or {}).get("major_value")
    if lo not in (None, ""):
        try: e["price"] = "free" if float(lo) == 0 else ("£" if float(lo) < 15 else "££")
        except ValueError: pass
    if v.get("name"): e["venue"] = v["name"]
    s, f = st[:10], en[:10]
    if f and f != s and (dt.date.fromisoformat(f) - dt.date.fromisoformat(s)).days >= 1:
        e.update({"from": s, "to": f})
    else:
        e.update({"date": s, "time": st[11:16]})
    if not e["name"] or not e["url"]: return None
    return e

def event(u, default=None):
    i = event_id(u)
    if not i: return None
    return _shape(get(f"/events/{i}/", expand="venue,ticket_availability"), default)

def organizer_events(u, default=None, limit=60):
    i = organizer_id(u)
    if not i: return []
    out, cont = [], None
    for _ in range(4):                                       # up to 4 pages of 50
        p = {"status": "live", "order_by": "start_asc", "expand": "venue,ticket_availability", "only_public": "true"}
        if cont: p["continuation"] = cont
        data = get(f"/organizers/{i}/events/", **p)
        if not data: break
        for x in data.get("events", []):
            e = _shape(x, default)
            if e: out.append(e)
        pg = data.get("pagination") or {}
        if not pg.get("has_more_items") or len(out) >= limit: break
        cont = pg.get("continuation")
    return out[:limit]

if __name__ == "__main__":       # python3 eventbrite.py <organiser or event url>: quick check that the token works
    if not TOKEN: sys.exit("set EVENTBRITE_TOKEN")
    for u in sys.argv[1:]:
        r = organizer_events(u) if "/o/" in u else [event(u)]
        print(u, "→", len([x for x in r if x])); [print("  ", x.get("date") or x.get("from"), x["name"][:60], x.get("area"), x.get("price")) for x in r[:8] if x]
