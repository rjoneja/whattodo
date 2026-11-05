#!/usr/bin/env python3
"""Write docs/sources/index.html: Raj's private (unlinked, noindex) list of every source, grouped by
category, with live idea counts and feed health. Rebuilt on every content run."""
import json, os, html, datetime, collections, re

V = json.load(open("venues.json"))["venues"]
ACC = json.load(open("accounts.json"))
A = ACC.get("accounts", [])
EV = json.load(open("docs/events.json")).get("events", [])

count = collections.Counter()
for e in EV:
    for s in {e.get("source", "")} | set(e.get("also") or []):
        count[s] += 1

VENUE_GROUPS = [
    ("Museums & galleries", {"museum", "gallery"}),
    ("Theatre, music & talks", {"theatre", "arts", "cinema", "talks", "arena", "festival"}),
    ("Heritage & historic places", {"heritage"}),
    ("Parks, gardens & nature", {"park", "gardens", "nature", "farm", "zoo"}),
    ("Attractions, markets & kids", {"attraction", "market", "kids"}),
]
CATS = [("boroughs", "Boroughs", "Council what's-on listings, one per borough.",
         [v for v in V if v.get("kind") == "council"])]
CATS.append(("instagram", "Instagram", "Public accounts we follow for pop-ups, one-offs and things that never make a listings site.", None))
CATS.append(("newsletters", "Newsletters", "Emails sent to the JauntOut inbox, read each morning. Confirmation emails waiting to be clicked are flagged.", None))
CATS.append(("blogs", "Blogs", "Independent London writers who find the odd and wonderful.",
             [v for v in V if v.get("kind") == "blog"]))
CATS.append(("listings", "Listings & ticketing", "Aggregators and ticket sites. We prefer the venue's own listing when both have it.",
             [v for v in V if v.get("kind") in {"aggregator", "ticketing"}]))
known = {"council", "blog", "aggregator", "ticketing"} | set().union(*[g for _, g in VENUE_GROUPS])
LOCAL = [v for v in V if v.get("local")]
NL = [v for v in V if not v.get("local")]
venue_sub = [(t, [v for v in NL if v.get("kind") in g]) for t, g in VENUE_GROUPS]
other = [v for v in NL if v.get("kind") not in known]
if other: venue_sub.append(("Other venues", other))
CATS.insert(1, ("venues", "Venue websites", "Straight from the source: the venues' own what's-on pages.", venue_sub))
by_b = collections.defaultdict(list)
for v in LOCAL: by_b[v.get("borough") or "Other"].append(v)
CATS.insert(1, ("local", "Local & neighbourhood", "Community centres, pubs, churches, libraries, small theatres and societies: the things on people's doorsteps.",
                sorted(by_b.items())))

# names of everything we follow, for the app's search ("we follow X, but nothing's listed right now")
_fol = [{"n": v["name"], "a": v.get("area") or ""} for v in V if v.get("kind") not in ("aggregator", "ticketing", "blog")] + \
       [{"n": a.get("name") or a["handle"], "a": a.get("area") or ""} for a in A if isinstance(a, dict) and a.get("handle")]
json.dump(_fol, open("docs/followed.json", "w"), ensure_ascii=False, separators=(",", ":"))

def esc(s): return html.escape(str(s or ""))
def site(url):
    m = re.match(r"https?://(www\.)?([^/]+)", url or ""); return m.group(2) if m else ""

HEALTH = {"blocked": ("bad", "blocks bots"), "error": ("bad", "broken"), "skip": ("off", "switched off")}
def row(name, url, sub, n, feed=None):
    st, word = HEALTH.get(feed, ("", ""))
    if not st and not n: st, word = "quiet", "nothing live"
    badge = f'<span class="n">{n}</span>' if n else '<span class="n z">–</span>'
    flag = f'<em class="{st}">{word}</em>' if word else ""
    return (f'<li data-q="{esc((name + " " + sub).lower())}" data-st="{st or "ok"}"><a href="{esc(url)}" rel="noopener" target="_blank">'
            f'<b>{esc(name)}</b><small>{esc(sub)}</small></a>{flag}{badge}</li>')

def venue_rows(vs):
    vs = sorted(vs, key=lambda v: (-count[v["name"]], v["name"].lower()))
    return "".join(row(re.sub(r"\s*\((aggregator|blog)\)$", "", v["name"]), v.get("url"),
                       " · ".join(x for x in [v.get("area"), site(v.get("url")), v.get("feed")] if x), count[v["name"]], v.get("feed")) for v in vs)

sections, nav, total = [], [], 0
for key, title, blurb, items in CATS:
    if key == "instagram":
        accs = sorted(A, key=lambda a: (-count[f"Instagram @{a['handle']}"], a["name"].lower()))
        body = "<ul>" + "".join(row(a["name"], f"https://www.instagram.com/{a['handle']}/",
                                    " · ".join(x for x in ["@" + a["handle"], a.get("area")] if x),
                                    count[f"Instagram @{a['handle']}"]) for a in accs) + "</ul>"
        n = len(accs)
    elif key == "newsletters":
        NS = json.load(open("news_seen.json")) if os.path.exists("news_seen.json") else {}
        by = {}
        for m in [m for m in NS.values() if m.get("kind") != "skip"]:
            b = by.setdefault(m.get("addr") or m.get("from"), {"name": m.get("from", ""), "addr": m.get("addr", ""), "mails": 0, "confirm": False, "last": ""})
            if m.get("kind") == "confirm": b["confirm"] = True
            else: b["mails"] += 1; b["last"] = max(b["last"], m.get("day", ""))
        rows = []
        for b in sorted(by.values(), key=lambda b: (-count[f"Newsletter: {b['name']}"], b["name"].lower())):
            n_ev = count[f"Newsletter: {b['name']}"]
            sub = " · ".join(x for x in [b["addr"], f"{b['mails']} email{'s' if b['mails'] != 1 else ''} read" if b["mails"] else "", "confirm in inbox" if b["confirm"] and not b["mails"] else ""] if x)
            st = "bad" if b["confirm"] and not b["mails"] else ("" if n_ev else "quiet")
            badge = f'<span class="n">{n_ev}</span>' if n_ev else '<span class="n z">–</span>'
            flag = '<em class="bad">confirm</em>' if st == "bad" else ('<em class="quiet">nothing live</em>' if st == "quiet" else "")
            rows.append(f'<li data-q="{esc((b["name"] + " " + b["addr"]).lower())}" data-st="{st or "ok"}"><a><b>{esc(b["name"])}</b><small>{esc(sub)}</small></a>{flag}{badge}</li>')
        body = "<ul>" + ("".join(rows) or '<li data-q="" data-st="ok"><a><b>No emails read yet</b><small>the reader runs each morning</small></a></li>') + "</ul>"
        n = len(by)
    elif key in ("venues", "local"):
        body = "".join(f'<h3>{esc(t)}</h3><ul>{venue_rows(vs)}</ul>' for t, vs in items if vs)
        n = sum(len(vs) for _, vs in items)
    else:
        body = f"<ul>{venue_rows(items)}</ul>"; n = len(items)
    total += n
    nav.append(f'<a href="#{key}">{esc(title)} <span>{n}</span></a>')
    sections.append(f'<section id="{key}"><h2>{esc(title)} <span>{n}</span></h2><p class="sub">{esc(blurb)}</p>{body}</section>')

def plain(lst, title, blurb):
    if not lst: return ""
    li = "".join(f'<li data-q="{esc((a.get("name","")+" "+a["handle"]).lower())}" data-st="off"><a href="https://www.instagram.com/{esc(a["handle"])}/" target="_blank" rel="noopener"><b>{esc(a.get("name") or "@"+a["handle"])}</b><small>@{esc(a["handle"])}{" · "+esc(a.get("why") or a.get("reason")) if (a.get("why") or a.get("reason")) else ""}</small></a></li>' for a in lst if isinstance(a, dict) and a.get("handle"))
    return f'<h3>{esc(title)} · {len(lst)}</h3><p class="sub">{esc(blurb)}</p><ul>{li}</ul>'
extra = plain(ACC.get("parked", []), "Parked", "Handles that didn't resolve or aren't business accounts. Check these.") + \
        plain(ACC.get("rejected", []), "Rejected", "Checked and turned down (personal accounts, off-topic, inactive).")
if extra: sections[[i for i, s in enumerate(sections) if 'id="instagram"' in s][0]] = sections[[i for i, s in enumerate(sections) if 'id="instagram"' in s][0]].replace("</section>", extra + "</section>")
bad = sum(1 for v in V if v.get("feed") in ("blocked", "error"))
quiet = sum(1 for v in V if v.get("feed") not in ("blocked", "error", "skip") and not count[v["name"]]) + sum(1 for a in A if not count[f"Instagram @{a['handle']}"])

today = datetime.date.today()
updated = f"{today.day} {today.strftime('%B %Y')}"
PIN = '<svg class="pin" viewBox="0 0 60 84" aria-hidden="true"><path fill-rule="evenodd" d="M30 83 C30 83 3 53 3 30 A27 27 0 1 1 57 30 C57 53 30 83 30 83 Z M40 30 A10 10 0 1 0 20 30 A10 10 0 1 0 40 30 Z"/></svg>'

page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sources · JauntOut London</title>
<meta name="robots" content="noindex,nofollow">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Young+Serif&family=Jost:wght@500;600&family=IBM+Plex+Sans:wght@400;500;600&display=swap">
<style>
:root{{--paper:#F2EEE3;--paper-2:#E8E2D3;--ink:#1E3F2B;--ink-2:#4F6357;--ink-3:#8C9890;--verm:#E2582E;--moss:#2F7D5B;--moss-soft:#E1EFE6;--line:#DCD5C4;--card:#FBF9F3;
--brand:"Young Serif",Georgia,serif;--display:"Jost",system-ui,sans-serif;--body:"IBM Plex Sans",system-ui,sans-serif;color-scheme:light}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--paper:#122018;--paper-2:#1A2C22;--ink:#F2EEE3;--ink-2:#C2C8BE;--ink-3:#86938A;--verm:#EE6A3F;--moss:#5DB58A;--moss-soft:#1C3527;--line:#2A3D31;--card:#1A2C22;color-scheme:dark}}}}
:root[data-theme="dark"]{{--paper:#122018;--paper-2:#1A2C22;--ink:#F2EEE3;--ink-2:#C2C8BE;--ink-3:#86938A;--verm:#EE6A3F;--moss:#5DB58A;--moss-soft:#1C3527;--line:#2A3D31;--card:#1A2C22;color-scheme:dark}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--paper);color:var(--ink);font-family:var(--body);font-size:16px;line-height:1.45;-webkit-font-smoothing:antialiased}}
.wrap{{max-width:760px;margin:0 auto;padding:20px 16px 64px}}
a{{color:inherit;text-decoration:none}}
.logo{{font-family:var(--brand);font-size:28px;letter-spacing:-.03em;line-height:1;display:inline-flex;align-items:baseline;white-space:nowrap}}
.logo .pin{{height:.62em;width:.45em;align-self:center;margin:0 .01em 0 .02em;fill:var(--verm)}}
.logo .city{{font-family:var(--display);font-weight:600;font-size:10px;letter-spacing:.24em;color:var(--ink-2);margin-left:6px;align-self:flex-end;transform:translateY(2px)}}
header{{display:flex;justify-content:space-between;align-items:center;gap:12px}}
header .back{{font-family:var(--display);font-weight:600;font-size:14px;color:var(--verm)}}
h1{{font-family:var(--brand);font-weight:400;font-size:clamp(34px,8vw,48px);letter-spacing:-.02em;line-height:1.05;margin:36px 0 10px}}
.lede{{color:var(--ink-2);margin:0 0 6px;max-width:56ch}}
.meta{{font-size:13px;color:var(--ink-3);margin:0 0 22px}}
.nav{{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:14px}}
.nav a{{font-family:var(--display);font-weight:600;font-size:14px;padding:7px 12px;border:1px solid var(--line);border-radius:999px;background:var(--card)}}
.nav a span,h2 span{{color:var(--ink-3);font-weight:500}}
.find{{width:100%;font:inherit;font-size:16px;padding:11px 14px;border:1px solid var(--line);border-radius:12px;background:var(--card);color:var(--ink);margin-bottom:8px}}
.find:focus{{outline:2px solid var(--verm);outline-offset:1px}}
section{{padding-top:22px;scroll-margin-top:12px}}
h2{{font-family:var(--brand);font-weight:400;font-size:28px;letter-spacing:-.015em;margin:12px 0 4px}}
h2 span{{font-family:var(--display);font-size:16px;margin-left:4px}}
h3{{font-family:var(--display);font-weight:600;font-size:13px;letter-spacing:.1em;text-transform:uppercase;color:var(--ink-3);margin:20px 0 6px}}
.sub{{color:var(--ink-2);font-size:14px;margin:0 0 10px}}
ul{{list-style:none;margin:0;padding:0;border:1px solid var(--line);border-radius:14px;background:var(--card);overflow:hidden}}
li{{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:10px 14px;border-top:1px solid var(--line)}}
li:first-child{{border-top:0}}
li a{{min-width:0;flex:1}}
li a:hover b{{color:var(--verm)}}
li b{{display:block;font-weight:500;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
li small{{display:block;font-size:13px;color:var(--ink-3);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.n{{flex:none;font-family:var(--display);font-weight:600;font-size:13px;min-width:34px;text-align:center;padding:3px 8px;border-radius:999px;background:var(--moss-soft);color:var(--moss)}}
.n.z{{background:transparent;color:var(--ink-3)}}
.key{{font-size:13px;color:var(--ink-3);margin:0 0 4px}}
.key .n{{display:inline-block;min-width:0;margin-right:4px}}
[hidden]{{display:none!important}}
li em{{flex:none;font-style:normal;font-family:var(--display);font-weight:600;font-size:12px;padding:2px 8px;border-radius:999px;border:1px solid var(--line);color:var(--ink-3)}}
li em.bad{{color:var(--verm);border-color:var(--verm)}}
.nav a.on{{background:var(--ink);color:var(--paper);border-color:var(--ink)}}
header .back{{color:var(--ink-3)!important}}
.none{{color:var(--ink-3);padding:16px 0}}
footer{{margin-top:40px;font-size:13px;color:var(--ink-3)}}
footer a{{color:var(--verm)}}
</style></head><body><div class="wrap">
<header><a class="logo" href="/" aria-label="JauntOut London home">jaunt{PIN}ut<span class="city">LONDON</span></a><span class="back">Private · not linked</span></header>
<h1>Sources</h1>
<p class="meta">{total} sources · {len(EV)} ideas live · {bad} broken or blocked · {quiet} with nothing live · updated {updated}</p>
<nav class="nav">{''.join(nav)}</nav>
<input class="find" id="find" type="search" placeholder="Find a source…" aria-label="Find a source">
<div class="nav" id="st"><a href="#" data-st="" class="on">All</a><a href="#" data-st="bad">Broken / blocked <span>{bad}</span></a><a href="#" data-st="quiet">Nothing live <span>{quiet}</span></a></div>
<p class="key"><span class="n">12</span> ideas from that source in the deck right now</p>
<p class="none" id="none" hidden>No source matches that.</p>
{''.join(sections)}
<footer>Rebuilt every morning from venues.json and accounts.json. Counts include events where the source was a duplicate that got merged.</footer>
</div>
<script>
const f=document.getElementById('find');
let st='';document.querySelectorAll('#st a').forEach(a=>a.addEventListener('click',e=>{{e.preventDefault();st=a.dataset.st;document.querySelectorAll('#st a').forEach(b=>b.classList.toggle('on',b===a));run()}}));
f.addEventListener('input',run);
function run(){{const q=f.value.trim().toLowerCase();let any=false;
document.querySelectorAll('li').forEach(li=>{{const on=(!q||li.dataset.q.includes(q))&&(!st||li.dataset.st===st);li.hidden=!on;any=any||on}});
document.querySelectorAll('ul').forEach(u=>{{const v=[...u.children].some(li=>!li.hidden);u.hidden=!v;const h=u.previousElementSibling;if(h&&h.tagName==='H3')h.hidden=!v}});
document.querySelectorAll('section').forEach(s=>{{s.hidden=![...s.querySelectorAll('li')].some(li=>!li.hidden)}});
document.getElementById('none').hidden=any;}}
</script></body></html>"""
os.makedirs("docs/sources", exist_ok=True)
open("docs/sources/index.html", "w").write(page)
print(f"sources page: {total} sources, {len(EV)} events")
