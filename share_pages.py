#!/usr/bin/env python3
"""Write docs/e/<event-id>/index.html: a tiny page per event with its own title, description and photo,
so a link shared on WhatsApp shows a proper preview. The page then hands over to the app (/?e=<id>)."""
import json, os, shutil, html, sys
from urllib.parse import quote
ev = json.load(open("docs/events.json")).get("events", [])
img = json.load(open("docs/images.json")) if os.path.exists("docs/images.json") else {}
root = "docs/e"
os.makedirs(root, exist_ok=True); old = set(os.listdir(root)); live = set()
MON = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
def nice(d): y, m, dd = d.split("-"); return f"{int(dd)} {MON[int(m)-1]}"
n = 0
for e in ev:
    i = e["id"]; live.add(i)
    if "/" in i or ".." in i: continue
    when = (nice(e["date"]) + (" · " + e["time"] if e.get("time") else "")) if e.get("date") else ("until " + nice(e["to"]) if e.get("to") else "")
    title = html.escape(e["name"]); desc = html.escape(" · ".join(x for x in [e.get("area"), when, "Free" if e.get("price") == "free" else ""] if x) + " — " + e.get("blurb", "")[:150])
    pic = (img.get(i) or {}).get("url", "")
    os.makedirs(f"{root}/{i}", exist_ok=True)
    qn = quote(e["name"][:80])          # the name too, so the app can still find it if the listing's id changes
    page = (f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><link rel="icon" href="/icons/icon.svg" type="image/svg+xml"><link rel="icon" href="/icons/favicon-32.png" sizes="32x32" type="image/png"><link rel="apple-touch-icon" href="/icons/apple-touch-icon.png"><link rel="manifest" href="/manifest.webmanifest"><meta name="apple-mobile-web-app-title" content="JauntOut"><title>{title} · JauntOut London</title>
<meta property="og:site_name" content="JauntOut London"><meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}"><meta property="og:url" content="https://www.jauntout.com/e/{i}/">
{f'<meta property="og:image" content="{html.escape(pic)}">' if pic else ''}<meta name="robots" content="noindex">
<script>var q=new URLSearchParams(location.search);location.replace('/?e={i}&n={qn}&s='+(q.get('s')||'link'));</script>
</head><body style="font-family:system-ui;background:#122018;color:#F2EEE3;padding:24px"><p><a href="/?e={i}&n={qn}">Open {title} in JauntOut</a></p><p style="font-size:13px;opacity:.7">Running something? <a href="/submit/">List your event</a></p></body></html>""")
    f = f"{root}/{i}/index.html"
    if os.path.exists(f) and open(f).read() == page: continue      # unchanged: leave it alone
    open(f, "w").write(page)
    n += 1
for i in old - live: shutil.rmtree(f"{root}/{i}", ignore_errors=True)       # over or merged: /404.html still forwards old links
print(f"wrote {n} share pages, removed {len(old - live)}", file=sys.stderr)
