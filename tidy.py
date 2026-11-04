#!/usr/bin/env python3
"""
Tidy docs/events.json after the harvesters run:
  1. merge duplicates (the same event listed by several sources) into the richest copy
  2. days and hours: which weekdays a recurring listing runs, and its opening hours, so a Sunday
     market doesn't show on a Saturday and a morning-only thing doesn't show at 3pm
  3. relevance check: drop things a Londoner can't just turn up to (online-only, members-only,
     trade/B2B, careers/recruitment, private bookings). Judged by Claude on name + description + venue,
     never on the title alone. Each event is checked once; the verdict is cached on the event.
"""
import json, os, re, sys
from urllib.parse import urlparse

P = "docs/events.json"
data = json.load(open(P)); events = data.get("events", [])

# ---------- 1. merge duplicates ----------
STOP = {"the","a","an","and","of","at","in","on","for","with","london","event","events","2026","2027","day",
        "weekly","monthly","every","sunday","saturday","sundays","saturdays","weekend","weekends","mondays","fridays"}
def namekey(e, brackets=True):
    n = e["name"].lower() if brackets else re.sub(r"\(.*?\)", " ", e["name"].lower())   # "(Brixton Library)" can matter on a one-off
    words = [w for w in re.sub(r"[^a-z0-9 ]", " ", n.replace("&", " and ")).split() if w not in STOP]
    words = [w[:-1] if w.endswith("s") and len(w) > 4 else w for w in words]
    return " ".join(sorted(words[:5]))
def key(e):
    # one-off dates must match; date ranges at the same spot (within ~150 m) that overlap are the same listing
    if e.get("date"): return namekey(e) + "|" + e["date"]
    return namekey(e, brackets=False) + "|range|" + f"{round(float(e.get('lat', 0)) / 0.0015)}:{round(float(e.get('lon', 0)) / 0.0022)}"
AGG = re.compile(r"ianvisits|londonist|time ?out|visit ?london|kidrated|hoop|dads in london|aggregator|blog|diamond", re.I)
def richness(e):
    src = e.get("source", "")
    host = urlparse(e.get("url", "")).netloc
    tier = 0 if AGG.search(src) else 1 if re.search(r"council|instagram", src, re.I) else 2   # venue's own listing wins
    return (tier, bool(e.get("time")), e.get("price") not in (None, ""), bool(e.get("parking")), len(e.get("blurb", "")), "instagram" not in host)
groups = {}
for e in events: groups.setdefault(key(e), []).append(e)
merged = []
for g in groups.values():
    g.sort(key=richness, reverse=True); best = dict(g[0])
    for o in g[1:]:
        for f in ("time", "parking", "ages", "to", "from", "days", "open", "close"):
            if not best.get(f) and o.get(f): best[f] = o[f]
        if o.get("from") and best.get("from"): best["from"] = min(best["from"], o["from"])
        if o.get("to") and best.get("to"): best["to"] = max(best["to"], o["to"])
    prices = {o.get("price") for o in g}
    if best.get("price") == "free" and prices & {"£", "££"} and richness(best)[0] < 2:
        best["price"] = "£" if "£" in prices else "££"          # an aggregator says free but someone says ticketed: don't overpromise
    if len(g) > 1: best["also"] = sorted({o.get("source", "") for o in g[1:]} - {best.get("source", "")})[:4]
    merged.append(best)
print(f"merge: {len(events)} → {len(merged)} events", file=sys.stderr)

# ---------- 2. days and hours ----------
DAYN = {"sun": 0, "mon": 1, "tue": 2, "wed": 3, "thu": 4, "fri": 5, "sat": 6}
def hhmm(x):
    m = re.match(r"^\s*(\d{1,2})(?:[:.](\d{2}))?\s*(am|pm)?\s*$", str(x or "").lower())
    if not m: return None
    h, mi, ap = int(m.group(1)), int(m.group(2) or 0), m.group(3)
    if ap == "pm" and h < 12: h += 12
    if ap == "am" and h == 12: h = 0
    return f"{h:02d}:{mi:02d}" if 0 <= h < 24 and mi < 60 else None
def norm_hours(e):
    d = e.get("days")
    if isinstance(d, list):
        d = sorted({DAYN[str(x).strip().lower()[:3]] if not isinstance(x, int) else x for x in d if isinstance(x, int) or str(x).strip().lower()[:3] in DAYN})
        if d and len(d) < 7: e["days"] = d
        else: e.pop("days", None)
    for f in ("open", "close"):
        v = hhmm(e.get(f)) if e.get(f) else None
        if v: e[f] = v
        else: e.pop(f, None)
    if e.get("open") and e.get("close") and e["close"] <= e["open"]: e.pop("close")
for e in merged: norm_hours(e)
todo = [e for e in merged if "hrs" not in e]
if todo and os.environ.get("ANTHROPIC_API_KEY") and "--no-llm" not in sys.argv:
    import anthropic
    client = anthropic.Anthropic()
    for i in range(0, len(todo), 40):
        batch = todo[i:i+40]
        items = [{"i": n, "name": e["name"], "when": e.get("date") or f"{e.get('from')} to {e.get('to')}", "time": e.get("time", ""),
                  "about": e.get("blurb", "")[:260]} for n, e in enumerate(batch)]
        prompt = ("For each London listing below, read the name, time and description and say WHEN on the day it runs.\n"
                  '- "days": weekday names it runs on, e.g. ["Sun"], ONLY if it runs on some weekdays but not others (weekly market, '
                  'Saturday club, weekends only). Omit if every day or a single date.\n'
                  '- "open"/"close": "HH:MM" 24h, ONLY if the text states the hours or a start and end time. A start time alone goes in "open".\n'
                  '- "part": "morning"|"afternoon"|"evening"|"all day", only if clearly implied (e.g. "breakfast club", "late opening").\n'
                  "Never guess: leave a field out when the text doesn't say.\n"
                  'Return ONLY a JSON array: [{"i":0,"days":["Sun"],"open":"10:00","close":"15:00"}]\n' + json.dumps(items, ensure_ascii=False))
        try:
            msg = client.messages.create(model=os.environ.get("WTD_MODEL", "claude-haiku-5-5"), max_tokens=5000, messages=[{"role": "user", "content": prompt}])
            out = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
            m = re.search(r"\[.*\]", out, re.S); got = {v["i"]: v for v in json.loads(m.group(0))} if m else {}
        except Exception as ex:
            print(f"hours batch failed: {str(ex)[:100]}", file=sys.stderr); continue
        for n, e in enumerate(batch):
            v = got.get(n) or {}
            for f in ("days", "open", "close"):
                if v.get(f) and not e.get(f): e[f] = v[f]
            if v.get("part") in ("morning", "afternoon", "evening"): e["part"] = v["part"]
            norm_hours(e); e["hrs"] = 1
    print(f"hours: checked {len(todo)}, days on {sum(1 for e in merged if e.get('days'))}, hours on {sum(1 for e in merged if e.get('close'))}", file=sys.stderr)

# ---------- 3. relevance ----------
todo = [e for e in merged if "rel" not in e]
if todo and os.environ.get("ANTHROPIC_API_KEY") and "--no-llm" not in sys.argv:
    import anthropic
    client = anthropic.Anthropic()
    for i in range(0, len(todo), 40):
        batch = todo[i:i+40]
        items = [{"i": n, "name": e["name"], "venue": e.get("source", ""), "area": e.get("area", ""), "about": e.get("blurb", "")[:240]} for n, e in enumerate(batch)]
        prompt = ("For a London weekend-ideas app, decide for each listing whether an ordinary member of the public could go "
                  "(free or by buying a ticket). Judge on name, description AND venue together: a show at a theatre is a show "
                  "even if its title sounds like a trade fair. Mark keep=false ONLY for: online-only, members/staff/residents-only, "
                  "trade or B2B shows, careers/recruitment/job fairs, council meetings or consultations, private hire, "
                  "multi-week courses needing enrolment, or listings that are adverts rather than events. When unsure, keep=true.\n"
                  'Return ONLY a JSON array: [{"i":0,"keep":true,"why":"two words"}]\n' + json.dumps(items, ensure_ascii=False))
        try:
            msg = client.messages.create(model=os.environ.get("WTD_MODEL", "claude-haiku-5-5"), max_tokens=4000, messages=[{"role": "user", "content": prompt}])
            out = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
            m = re.search(r"\[.*\]", out, re.S); verdicts = {v["i"]: v for v in json.loads(m.group(0))} if m else {}
        except Exception as ex:
            print(f"relevance batch failed: {str(ex)[:100]}", file=sys.stderr); continue
        for n, e in enumerate(batch):
            v = verdicts.get(n)
            if v: e["rel"] = "keep" if v.get("keep", True) else "drop:" + str(v.get("why", ""))[:30]
dropped = [e for e in merged if str(e.get("rel", "")).startswith("drop")]
for e in dropped: print(f"  drop {e['name'][:60]} ({e['rel']})", file=sys.stderr)
keep = [e for e in merged if not str(e.get("rel", "")).startswith("drop")]
keep.sort(key=lambda e: e.get("date") or e.get("from") or "")
data["events"] = keep
data["dropped"] = [{"name": e["name"], "source": e.get("source"), "why": e["rel"][5:]} for e in dropped][:200]
json.dump(data, open(P, "w"), indent=1, ensure_ascii=False)
print(f"tidy: kept {len(keep)}, dropped {len(dropped)}", file=sys.stderr)
