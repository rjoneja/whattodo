#!/usr/bin/env python3
"""
Tidy docs/events.json after the harvesters run:
  1. merge duplicates (the same event listed by several sources) into the richest copy
  2. relevance check: drop things a Londoner can't just turn up to (online-only, members-only,
     trade/B2B, careers/recruitment, private bookings). Judged by Claude on name + description + venue,
     never on the title alone. Each event is checked once; the verdict is cached on the event.
"""
import json, os, re, sys
from urllib.parse import urlparse

P = "docs/events.json"
data = json.load(open(P)); events = data.get("events", [])

# ---------- 1. merge duplicates ----------
STOP = {"the","a","an","and","of","at","in","on","for","with","london","event","events","2026","2027","day"}
def key(e):
    words = [w for w in re.sub(r"[^a-z0-9 ]", " ", e["name"].lower().replace("&", " and ")).split() if w not in STOP]
    words = [w[:-1] if w.endswith("s") and len(w) > 4 else w for w in words]
    return " ".join(sorted(words[:5])) + "|" + (e.get("date") or e.get("from") or "")
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
        for f in ("time", "parking", "ages", "to", "from"):
            if not best.get(f) and o.get(f): best[f] = o[f]
    prices = {o.get("price") for o in g}
    if best.get("price") == "free" and prices & {"£", "££"} and richness(best)[0] < 2:
        best["price"] = "£" if "£" in prices else "££"          # an aggregator says free but someone says ticketed: don't overpromise
    if len(g) > 1: best["also"] = sorted({o.get("source", "") for o in g[1:]} - {best.get("source", "")})[:4]
    merged.append(best)
print(f"merge: {len(events)} → {len(merged)} events", file=sys.stderr)

# ---------- 2. relevance ----------
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
