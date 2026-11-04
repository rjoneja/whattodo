#!/usr/bin/env python3
"""Write docs/e/<event-id>/index.html: a tiny page per event with its own title, description and photo,
so a link shared on WhatsApp shows a proper preview. The page then hands over to the app (/?e=<id>)."""
import json, os, shutil, html, sys
ev = json.load(open("docs/events.json")).get("events", [])
img = json.load(open("docs/images.json")) if os.path.exists("docs/images.json") else {}
root = "docs/e"
shutil.rmtree(root, ignore_errors=True); os.makedirs(root)
MON = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
def nice(d): y, m, dd = d.split("-"); return f"{int(dd)} {MON[int(m)-1]}"
n = 0
for e in ev:
    i = e["id"]
    if "/" in i or ".." in i: continue
    when = (nice(e["date"]) + (" · " + e["time"] if e.get("time") else "")) if e.get("date") else ("until " + nice(e["to"]) if e.get("to") else "")
    title = html.escape(e["name"]); desc = html.escape(" · ".join(x for x in [e.get("area"), when, "Free" if e.get("price") == "free" else ""] if x) + " — " + e.get("blurb", "")[:150])
    pic = (img.get(i) or {}).get("url", "")
    if os.path.exists(f"{root}/{i}"): continue
    os.makedirs(f"{root}/{i}")
    open(f"{root}/{i}/index.html", "w").write(f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{title} · JauntOut London</title>
<meta property="og:site_name" content="JauntOut London"><meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}"><meta property="og:url" content="https://www.jauntout.com/e/{i}/">
{f'<meta property="og:image" content="{html.escape(pic)}">' if pic else ''}<meta name="robots" content="noindex">
<script>var q=new URLSearchParams(location.search);location.replace('/?e={i}&s='+(q.get('s')||'link'));</script>
</head><body style="font-family:system-ui;background:#F2EEE3;color:#1E3F2B;padding:24px"><p><a href="/?e={i}">Open {title} in JauntOut</a></p></body></html>""")
    n += 1
print(f"wrote {n} share pages", file=sys.stderr)
