#!/usr/bin/env python3
"""
Build docs/images.json: one picture per card.

  regulars  → Wikipedia page thumbnail (Wikimedia Commons, CC/public domain; credited on the card)
  events    → the source page's og:image (the venue's own promo image, linked back to its page)

Runs in the daily workflow; safe to re-run (keeps what it already has unless --refresh).
  python3 images.py --events docs/events.json --out docs/images.json
"""
import argparse, json, os, re, sys, time, html
from urllib.parse import quote
from urllib.request import Request, urlopen

UA = "WhatToDo-images/0.1 (+personal project; one thumbnail per venue, credited)"
# regular id → Wikipedia title
WIKI = {
 "horniman":"Horniman Museum","nhm":"Natural History Museum, London","sciencemuseum":"Science Museum, London",
 "crystalpalace":"Crystal Palace Dinosaurs","dulwich":"Dulwich Picture Gallery","greenwichpark":"Royal Observatory, Greenwich",
 "nmm":"National Maritime Museum","cuttysark":"Cutty Sark","tatemodern":"Tate Modern","southbank":"South Bank",
 "docklands":"Museum of London Docklands","va":"Victoria and Albert Museum","youngva":"Young V&A","kew":"Kew Gardens",
 "wetland":"London Wetland Centre","battersea":"Battersea Park","heath":"Parliament Hill, London","richmond":"Richmond Park",
 "eltham":"Eltham Palace","brockwell":"Brockwell Park","beckenham":"Beckenham Place Park","nunhead":"Nunhead Cemetery",
 "borough":"Borough Market","maltby":"Maltby Street Market","skygarden":"20 Fenchurch Street","tower":"Tower of London",
 "postal":"The Postal Museum","ltm":"London Transport Museum","discover":"Discover Children's Story Centre",
 "olympic":"Queen Elizabeth Olympic Park","wellcome":"Wellcome Collection","bm":"British Museum","columbia":"Columbia Road Flower Market",
 "leake":"Leake Street","brixton":"Brixton Market","mudchute":"Mudchute Park and Farm","vauxhallfarm":"Vauxhall City Farm",
 "wwetlands":"Walthamstow Wetlands","epping":"Epping Forest","barrierpark":"Thames Barrier Park","cablecar":"London Cable Car",
 "barbican":"Barbican Centre","boldtendencies":"Bold Tendencies","severndroog":"Severndroog Castle","chislehurst":"Chislehurst Caves",
 "woolwich":"Royal Arsenal, Woolwich","deptford":"Deptford Market","stpauls":"St Paul's Cathedral","mayfield":"Banstead",
}

def get(url, accept="*/*"):
    req = Request(url, headers={"User-Agent": UA, "Accept": accept})
    with urlopen(req, timeout=20) as r:
        return r.geturl(), r.read().decode("utf-8", "ignore")

def wiki_thumb(title):
    _, body = get("https://en.wikipedia.org/api/rest_v1/page/summary/" + quote(title.replace(" ", "_")), "application/json")
    j = json.loads(body)
    src = (j.get("thumbnail") or {}).get("source") or (j.get("originalimage") or {}).get("source")
    if not src: return None
    src = re.sub(r"/(\d+)px-", "/640px-", src)            # bigger thumb
    return {"url": src, "credit": "Photo: Wikimedia Commons", "page": j.get("content_urls", {}).get("desktop", {}).get("page")}

def og_image(url):
    _, doc = get(url, "text/html")
    m = re.search(r'(?is)<meta[^>]+property=["\']og:image(?::secure_url)?["\'][^>]+content=["\']([^"\']+)', doc) or \
        re.search(r'(?is)<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image', doc)
    if not m: return None
    src = html.unescape(m.group(1))
    if not src.startswith("http"): return None
    host = re.sub(r"^https?://(www\.)?", "", url).split("/")[0]
    return {"url": src, "credit": host}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--events", default="docs/events.json"); ap.add_argument("--out", default="docs/images.json")
    ap.add_argument("--refresh", action="store_true"); a = ap.parse_args()
    out = json.load(open(a.out)) if os.path.exists(a.out) and not a.refresh else {}
    for id_, title in WIKI.items():
        if id_ in out: continue
        try:
            t = wiki_thumb(title)
            if t: out[id_] = t; print(f"{id_}: wiki ok", file=sys.stderr)
        except Exception as ex:
            print(f"{id_}: wiki failed {ex}", file=sys.stderr)
        time.sleep(0.5)
    events = json.load(open(a.events)).get("events", []) if os.path.exists(a.events) else []
    for e in events:
        if e["id"] in out or not e.get("url", "").startswith("http"): continue
        if "instagram.com" in e["url"]: continue                 # IG media URLs expire; skip
        try:
            t = og_image(e["url"])
            if t: out[e["id"]] = t; print(f"{e['id']}: og ok", file=sys.stderr)
        except Exception as ex:
            print(f"{e['id']}: og failed {str(ex)[:60]}", file=sys.stderr)
        time.sleep(1)
    live = set(WIKI) | {e["id"] for e in events}
    out = {k: v for k, v in out.items() if k in live}
    json.dump(out, open(a.out, "w"), indent=0, ensure_ascii=False)
    print(f"wrote {len(out)} images to {a.out}")

if __name__ == "__main__":
    main()
