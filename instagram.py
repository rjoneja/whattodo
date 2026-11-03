#!/usr/bin/env python3
"""
Instagram → events.json, via Meta's official Business Discovery API (no scraping).

What it does
  1. For each handle in accounts.json, fetch that account's recent posts (caption, image, permalink, time).
  2. Skip posts already processed (state in ig_seen.json) and posts older than --days.
  3. Send the new posts to Claude: captions as text, poster images as images, so dates on flyers are read too.
  4. Normalise into the app schema, validate, merge into events.json (same rules as ingest.py).

One-time setup (10 minutes, free)
  a. Make an Instagram account professional: Settings → Account type → Switch to professional (Creator is fine).
  b. developers.facebook.com → My Apps → Create app → add the "Instagram" product → "API setup with Instagram login".
     Add your Instagram account as a tester and generate a token with scope instagram_business_basic.
  c. GET https://graph.instagram.com/me?fields=user_id,username&access_token=TOKEN  → note user_id.
  d. export IG_TOKEN=... IG_USER_ID=... ANTHROPIC_API_KEY=...
     If Meta set your app up with Facebook Login instead, export IG_HOST=graph.facebook.com and use the
     Instagram Business account id from your Facebook Page.

Tokens last 60 days: run `python3 instagram.py --refresh-token` monthly (prints the new token; the
GitHub Action in the README stores it back as a secret).

Usage
  python3 instagram.py --days 21 --out docs/events.json
  python3 instagram.py --check            # validate handles only, no model calls
"""
import argparse, datetime as dt, json, os, re, sys, time
from urllib.parse import quote
from urllib.request import Request, urlopen

HOST = os.environ.get("IG_HOST", "graph.instagram.com")
VER = os.environ.get("IG_API_VERSION", "v22.0")
MODEL = os.environ.get("WTD_MODEL", "claude-haiku-5-5")
MEDIA_FIELDS = "id,caption,media_type,media_url,thumbnail_url,permalink,timestamp,children{media_url,media_type}"

def api(path, params):
    params = dict(params, access_token=os.environ["IG_TOKEN"])
    url = f"https://{HOST}/{VER}/{path}?" + "&".join(f"{k}={quote(str(v), safe='(){},.')}" for k, v in params.items())
    from urllib.error import HTTPError
    try:
        with urlopen(Request(url, headers={"User-Agent": "WhatToDo-ig/0.1"}), timeout=30) as r:
            return json.loads(r.read().decode())
    except HTTPError as ex:
        body = ex.read().decode("utf-8", "ignore")
        try: body = json.loads(body).get("error", {}).get("message", body)
        except Exception: pass
        raise RuntimeError(f"HTTP {ex.code}: {body[:200]}")

def discover(handle, limit=25):
    fields = f"business_discovery.username({handle}){{username,name,media.limit({limit}){{{MEDIA_FIELDS}}}}}"
    data = api(os.environ["IG_USER_ID"], {"fields": fields})
    return data.get("business_discovery", {})

def refresh_token():
    if HOST == "graph.facebook.com":
        # Facebook-login tokens: extend with app id + secret (or use Graph API Explorer > Access Token Tool > Extend)
        url = (f"https://graph.facebook.com/{VER}/oauth/access_token?grant_type=fb_exchange_token"
               f"&client_id={os.environ['FB_APP_ID']}&client_secret={os.environ['FB_APP_SECRET']}&fb_exchange_token={os.environ['IG_TOKEN']}")
    else:
        url = f"https://{HOST}/refresh_access_token?grant_type=ig_refresh_token&access_token={os.environ['IG_TOKEN']}"
    with urlopen(url, timeout=30) as r:
        print(json.loads(r.read().decode())["access_token"])

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

def extract(account, posts, today, horizon):
    import anthropic
    client = anthropic.Anthropic()
    content = []
    for p in posts:
        when = p["timestamp"][:10]
        content.append({"type": "text", "text": f"\n--- POST {p['id']} posted {when} {p['permalink']}\n{(p.get('caption') or '').strip()[:1500]}"})
        img = p.get("media_url") if p.get("media_type") in ("IMAGE", "CAROUSEL_ALBUM") else p.get("thumbnail_url")
        if img and looks_like_poster(p):
            content.append({"type": "image", "source": {"type": "url", "url": img}})
    content.append({"type": "text", "text": f"""
These are recent Instagram posts from {account['name']} (@{account['handle']}), {account['area']}, London.
Today is {today}. Extract every specific, dated thing to do between today and {horizon} that a Londoner could turn up to:
events, workshops, markets, late openings, festivals, exhibitions with an end date, free days, open days.
Resolve relative dates ("this Saturday", "next weekend") from the post date. Skip giveaways, job ads, recaps of past
events, online-only things, and anything without a resolvable date. Prefer dates/prices printed on a poster image.
Default location: lat {account['lat']}, lon {account['lon']}; if the post names another venue, estimate its coordinates.
Return ONLY a JSON array of objects:
{{"post_id": str, "name": str, "area": str, "lat": float, "lon": float, "in": "in"|"out"|"both",
 "price": "free"|"£"|"££", "ages": [min,max], "kids": 0-3, "adults": 0-3, "dur": hours, "tags": [3-5 lowercase words],
 "blurb": your own words, max 30 words, practical, then EITHER "date": "YYYY-MM-DD" (+ optional "time") OR "from"/"to"}}
Return [] if there is nothing."""})
    msg = client.messages.create(model=MODEL, max_tokens=12000, messages=[{"role": "user", "content": content}])
    out = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
    return parse_array(out)

DATE_WORDS = re.compile(r"\b(\d{1,2}(st|nd|rd|th)?\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)|(mon|tues|wednes|thurs|fri|satur|sun)day|this weekend|next week|\d{1,2}[./]\d{1,2}|tonight|tomorrow)", re.I)
def looks_like_poster(p):
    cap = (p.get("caption") or "")
    return len(cap) < 400 or not DATE_WORDS.search(cap)       # short/undated caption → the picture probably carries the detail

# ---------- merge (same rules as ingest.py) ----------
LONDON = dict(lat=(51.25, 51.75), lon=(-0.55, 0.35))
def valid(e, today, horizon):
    try:
        if not (LONDON["lat"][0] <= float(e["lat"]) <= LONDON["lat"][1] and LONDON["lon"][0] <= float(e["lon"]) <= LONDON["lon"][1]): return False
        if e.get("in") not in ("in", "out", "both") or e.get("price") not in ("free", "£", "££"): return False
        if not e.get("name") or not e.get("blurb"): return False
        s = e.get("date") or e.get("from"); en = e.get("date") or e.get("to")
        return bool(s and en) and en >= today and s <= horizon
    except (KeyError, ValueError, TypeError):
        return False
def key(e): return re.sub(r"[^a-z0-9]", "", e["name"].lower())[:40] + (e.get("date") or e.get("from", ""))
def slug(e): return "ev-ig-" + re.sub(r"[^a-z0-9]+", "-", e["name"].lower()).strip("-")[:40] + "-" + (e.get("date") or e.get("from"))[5:]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=21, help="look back this many days of posts")
    ap.add_argument("--horizon", type=int, default=28, help="keep events up to this many days ahead")
    ap.add_argument("--out", default="events.json"); ap.add_argument("--accounts", default="accounts.json")
    ap.add_argument("--state", default="ig_seen.json"); ap.add_argument("--check", action="store_true")
    ap.add_argument("--refresh-token", action="store_true"); ap.add_argument("--only")
    ap.add_argument("--selftest", action="store_true"); ap.add_argument("--probe", help="comma-separated handles to test")
    a = ap.parse_args()
    if a.refresh_token: return refresh_token()
    if a.probe:
        for h in a.probe.split(","):
            try:
                bd = discover(h.strip(), 1); print("OK  ", h, "|", bd.get("name"), "|", bd.get("username"))
            except Exception as ex: print("no  ", h, str(ex)[:60])
        return
    if a.selftest:
        try: print("me:", api(os.environ["IG_USER_ID"], {"fields": "username,name"}))
        except Exception as ex: print("me failed:", ex)
        for h in ["instagram", "natgeo", "britishmuseum", "tate", "hornimanmuseum", "barbicancentre", "kewgardens", "southbankcentre"]:
            try:
                bd = discover(h, 1); m = bd.get("media", {}).get("data", [])
                print("discovery ok:", h, "| posts:", len(m), "|", (m[0].get("caption") or "")[:60].replace("\n", " ") if m else "")
            except Exception as ex: print("discovery failed:", h, ex)
        return
    for k in ("IG_TOKEN", "IG_USER_ID"):
        if not os.environ.get(k): sys.exit(f"set {k} (see the header of this file)")

    today = dt.date.today(); horizon = today + dt.timedelta(days=a.horizon)
    since = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=a.days)).isoformat()
    reg = json.load(open(a.accounts)); accounts = reg["accounts"]
    # validate up to 40 queued candidate handles per run; promote the ones Meta can see
    if reg.get("candidates") and not a.only:
        keep, promoted = [], 0
        for i, c in enumerate(reg["candidates"]):
            if i >= 40: keep.append(c); continue
            try:
                bd = discover(c["handle"], 1)
                c.pop("group", None); c["name"] = bd.get("name") or c["name"]
                accounts.append(c); promoted += 1
            except Exception as ex:
                if "request limit" in str(ex): keep.append(c); continue
                reg.setdefault("rejected", []).append({"handle": c["handle"], "why": str(ex)[:60]})
        reg["candidates"] = keep
        json.dump(reg, open(a.accounts, "w"), indent=1, ensure_ascii=False)
        print(f"candidates: {promoted} promoted, {len(keep)} still queued, {len(reg.get('rejected', []))} rejected in total", file=sys.stderr)
    seen = set(json.load(open(a.state))) if os.path.exists(a.state) else set()
    existing = {}
    if os.path.exists(a.out):
        for e in json.load(open(a.out)).get("events", []): existing[key(e)] = e

    found, missing = [], []
    for acc in accounts:
        if a.only and acc["handle"] != a.only: continue
        try:
            bd = discover(acc["handle"])
        except Exception as ex:
            msg = str(ex)
            missing.append(acc["handle"]); print(f"@{acc['handle']}: not found or not a professional account ({msg[:80]})", file=sys.stderr); continue
        posts = [p for p in bd.get("media", {}).get("data", []) if p.get("timestamp", "") >= since and p["id"] not in seen]
        print(f"@{acc['handle']}: {len(posts)} new posts", file=sys.stderr)
        if a.check or not posts: continue
        try:
            evs = extract(acc, posts, today.isoformat(), horizon.isoformat())
        except Exception as ex:
            print(f"  model failed: {ex}", file=sys.stderr); continue
        by_id = {p["id"]: p for p in posts}
        for e in evs:
            p = by_id.get(str(e.pop("post_id", "")), posts[0])
            e["url"] = p["permalink"]; e["source"] = f"Instagram @{acc['handle']}"
            e["id"] = slug(e); e["tags"] = [t.lower() for t in e.get("tags", [])][:5]
        ok = [e for e in evs if valid(e, today.isoformat(), horizon.isoformat())]
        print(f"  {len(ok)} events", file=sys.stderr)
        found += ok
        seen.update(p["id"] for p in posts)
        time.sleep(1)

    if a.check:
        print("handles Meta could not find:", missing or "none"); return
    merged = dict(existing)
    for e in found: merged[key(e)] = e
    events = [e for e in merged.values() if (e.get("date") or e.get("to", "")) >= today.isoformat()]
    events.sort(key=lambda e: e.get("date") or e.get("from"))
    json.dump({"generated": today.isoformat(), "events": events}, open(a.out, "w"), indent=1, ensure_ascii=False)
    json.dump(sorted(seen)[-5000:], open(a.state, "w"))
    print(f"wrote {len(events)} events to {a.out} ({len(found)} from Instagram this run); unknown handles: {missing or 'none'}")

if __name__ == "__main__":
    main()
