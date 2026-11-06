#!/usr/bin/env python3
"""Write docs/about/index.html: the public About page. What JauntOut is, where listings come from (every source,
credited), photos, money (affiliate disclosure), privacy and contact. Rebuilt on every content run."""
import json, html, os, collections, datetime

V = json.load(open("venues.json"))["venues"]
ACC = json.load(open("accounts.json"))
A = [a for a in ACC.get("accounts", []) if isinstance(a, dict) and a.get("handle")]
NS = json.load(open("news_seen.json")) if os.path.exists("news_seen.json") else {}
EV = json.load(open("docs/events.json")).get("events", [])
esc = lambda s: html.escape(str(s or ""))

GROUPS = [("Local and neighbourhood", lambda v: v.get("local")),
          ("Museums, galleries and heritage", lambda v: v.get("kind") in {"museum", "gallery", "heritage"}),
          ("Theatre, music, film and talks", lambda v: v.get("kind") in {"theatre", "arts", "cinema", "talks", "arena", "festival", "music"}),
          ("Parks, gardens, farms and nature", lambda v: v.get("kind") in {"park", "gardens", "nature", "farm", "zoo"}),
          ("Attractions, markets and things for kids", lambda v: v.get("kind") in {"attraction", "market", "kids"}),
          ("Borough councils", lambda v: v.get("kind") == "council"),
          ("Writers, listings and ticket sites", lambda v: v.get("kind") in {"blog", "aggregator", "ticketing"})]
used, sections = set(), []
for title, f in GROUPS:
    items = sorted([v for v in V if v["id"] not in used and f(v)], key=lambda v: v["name"].lower())
    used |= {v["id"] for v in items}
    if items: sections.append((title, items))
rest = sorted([v for v in V if v["id"] not in used], key=lambda v: v["name"].lower())
if rest: sections.append(("Other venues and organisers", rest))
letters = sorted({m.get("from") for m in NS.values() if m.get("kind") not in ("skip", "confirm") and m.get("from")}, key=str.lower)

def site_list(items):
    return "".join(f'<li><a href="{esc(v["url"])}" rel="noopener" target="_blank">{esc(v["name"])}</a>{" <small>" + esc(v.get("area")) + "</small>" if v.get("area") and v.get("local") else ""}</li>' for v in items)

n_sites, n_local, n_ig = len(V), sum(1 for v in V if v.get("local")), len(A)
updated = datetime.date.today().strftime("%-d %B %Y")
src_html = "".join(f'<details><summary>{esc(t)} <span>{len(items)}</span></summary><ul class="src">{site_list(items)}</ul></details>' for t, items in sections)
src_html += f'<details><summary>Instagram accounts <span>{n_ig}</span></summary><ul class="src">' + "".join(
    f'<li><a href="https://www.instagram.com/{esc(a["handle"])}/" rel="noopener" target="_blank">{esc(a.get("name") or "@" + a["handle"])}</a></li>' for a in sorted(A, key=lambda a: (a.get("name") or a["handle"]).lower())) + "</ul></details>"
if letters:
    src_html += f'<details><summary>Newsletters <span>{len(letters)}</span></summary><ul class="src">' + "".join(f"<li>{esc(n)}</li>" for n in letters) + "</ul></details>"

ICONS = '<link rel="icon" href="/icons/icon.svg" type="image/svg+xml"><link rel="icon" href="/icons/favicon-32.png" sizes="32x32" type="image/png"><link rel="apple-touch-icon" href="/icons/apple-touch-icon.png"><link rel="manifest" href="/manifest.webmanifest">'
PIN = '<svg viewBox="0 0 60 84" aria-hidden="true"><path fill-rule="evenodd" d="M30 83 C30 83 3 53 3 30 A27 27 0 1 1 57 30 C57 53 30 83 30 83 Z M40 30 A10 10 0 1 0 20 30 A10 10 0 1 0 40 30 Z"/></svg>'
page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="dark"><meta name="theme-color" content="#122018">{ICONS}
<title>About · JauntOut London</title><meta name="description" content="What JauntOut is, where its listings come from, how it makes money and what it does with your data.">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Young+Serif&family=Jost:wght@500;600;700&family=IBM+Plex+Sans:wght@400;500;600&display=swap">
<style>
:root{{--paper:#122018;--card:#1A2C22;--ink:#F2EEE3;--ink-2:#C2C8BE;--ink-3:#86938A;--line:#2A3D31;--verm:#EE6A3F;--moss:#5DB58A;--sky:#7FA9CC;
  --brand:"Young Serif",Georgia,serif;--display:"Jost",system-ui,sans-serif;--body:"IBM Plex Sans",system-ui,sans-serif;color-scheme:dark}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--paper);color:var(--ink);font:16px/1.55 var(--body);-webkit-font-smoothing:antialiased}}
.wrap{{max-width:640px;margin:0 auto;padding:20px 16px 64px}}
.top{{display:flex;align-items:center;gap:12px}}
.back{{display:inline-flex;align-items:center;justify-content:center;width:40px;height:40px;flex:none;border-radius:999px;border:1px solid var(--line);background:var(--card);color:var(--ink)}}
.back svg{{width:20px;height:20px}}
.logo{{font-family:var(--brand);font-size:28px;letter-spacing:-.03em;display:inline-flex;align-items:baseline;color:var(--ink);text-decoration:none}}
.logo svg{{height:.62em;width:.45em;align-self:center;margin:0 .01em 0 .02em;fill:var(--verm)}}
.logo small{{font-family:var(--display);font-weight:600;font-size:10px;letter-spacing:.24em;color:var(--ink-2);margin-left:6px}}
h1{{font-family:var(--brand);font-weight:400;font-size:36px;line-height:1.08;margin:28px 0 10px;letter-spacing:-.02em}}
h2{{font-family:var(--display);font-weight:700;font-size:19px;margin:30px 0 6px}}
p{{margin:0 0 12px;color:var(--ink-2)}}p b{{color:var(--ink);font-weight:600}}
a{{color:var(--sky)}}
.lede{{font-size:18px;color:var(--ink)}}
details{{border:1px solid var(--line);border-radius:12px;background:var(--card);margin:8px 0;padding:10px 14px}}
summary{{cursor:pointer;font-family:var(--display);font-weight:600}}summary span{{color:var(--ink-3);font-weight:500;margin-left:4px}}
ul.src{{columns:2;column-gap:20px;padding:8px 0 0 18px;margin:0;font-size:14px}}ul.src li{{break-inside:avoid;margin:0 0 4px}}ul.src small{{color:var(--ink-3)}}
@media(max-width:480px){{ul.src{{columns:1}}}}
.fine{{font-size:13px;color:var(--ink-3);margin-top:30px}}
</style></head><body><div class="wrap">
<div class="top"><a class="back" id="back" href="/" aria-label="Back to JauntOut"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M15 5l-7 7 7 7"/></svg></a>
<a class="logo" href="/">jaunt{PIN}ut<small>LONDON</small></a></div>
<h1>About JauntOut</h1>
<p class="lede">JauntOut helps you decide what to do near you in London. Tell it your postcode and who's going, and it suggests things one card at a time, starting with what's walkable or a short trip away.</p>

<h2>Where the listings come from</h2>
<p>Every day or two JauntOut reads the what's-on pages of <b>{n_sites} venues, organisers and councils</b> across London ({n_local} of them small local places like community centres, pubs, churches, libraries and societies), plus <b>{n_ig} Instagram accounts</b>, a set of London newsletters, and events organisers send us. Right now that's about <b>{len(EV):,} things to do</b>.</p>
<p>Descriptions are written in our own words, and <b>Details</b> takes you to the venue's or organiser's own page wherever we can find it, so you always book with them. Dates and prices can change, so check there before you go. Thank you to every one of these sources:</p>
{src_html}

<h2>Pictures</h2>
<p>The drawings are JauntOut's own. Where a card shows a photo, it's of that exact place or thing, from the venue's own page or from Wikimedia Commons under its licence, and credited on the photo.</p>

<h2>How JauntOut makes money</h2>
<p>JauntOut is free to use, and listing an event is free. <b>Some ticket links are affiliate links</b>: if you buy a ticket after following one, we may earn a small commission from the ticket seller, at no extra cost to you. We only use them where that seller is the event's own ticket seller, and they never affect what we suggest or the order you see things in.</p>

<h2>Your privacy</h2>
<p>There are no accounts and no advertising cookies. Your postcode, saved ideas and choices stay on your phone. To improve JauntOut we count things anonymously: which screens are used and for how long, which ideas are saved or shared, what's searched for, and the <b>postcode district</b> people search from (for example "SE4", never your full postcode). We don't store IP addresses or anything that identifies you.</p>
<p>Weather comes from Open-Meteo, journey times from Transport for London, postcode lookups from postcodes.io and fonts from Google Fonts. Your phone asks them directly, so they see the request like any website would.</p>

<h2>Venues and organisers</h2>
<p>Running something people can turn up to? <a href="/submit/">List your event</a>, free. If we've got something wrong about your venue or event, or you'd rather we didn't list you, email <a href="mailto:hello@jauntout.com">hello@jauntout.com</a> and we'll sort it quickly.</p>

<h2>Contact</h2>
<p><a href="mailto:hello@jauntout.com">hello@jauntout.com</a></p>
<p class="fine">Updated {updated}.</p>
</div>
<script>document.getElementById('back').addEventListener('click',e=>{{ if(document.referrer&&new URL(document.referrer).origin===location.origin&&history.length>1){{ e.preventDefault(); history.back(); }} }});</script>
</body></html>"""
os.makedirs("docs/about", exist_ok=True)
open("docs/about/index.html", "w").write(page)
print(f"about page: {n_sites} sites, {n_ig} instagram, {len(letters)} newsletters")
