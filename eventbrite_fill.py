#!/usr/bin/env python3
"""
Fill in listings that point at an Eventbrite event (found on venue pages, in newsletters, on Instagram) from
Eventbrite's API: exact date and time, the venue's location and the price band. Runs daily, no Claude.
Each listing is checked once ("eb": 1 done, -1 not found / online / over); needs EVENTBRITE_TOKEN.
"""
import json, sys, datetime as dt
import eventbrite

P = "docs/events.json"
def main():
    if not eventbrite.enabled(): print("eventbrite fill: no EVENTBRITE_TOKEN, skipped", file=sys.stderr); return
    data = json.load(open(P)); ev = data["events"]; today = dt.date.today().isoformat()
    done = gone = 0
    for e in ev:
        if e.get("eb") or "eventbrite." not in e.get("url", "") or not eventbrite.event_id(e["url"]): continue
        r = eventbrite.event(e["url"], default=e)
        if not r: e["eb"] = -1; gone += 1; continue
        for k in ("date", "time", "from", "to"): e.pop(k, None)
        for k in ("date", "time", "from", "to", "lat", "lon", "price"):
            if r.get(k) not in (None, ""): e[k] = r[k]
        if r.get("venue") and not e.get("venue"): e["venue"] = r["venue"]
        e["eb"] = 1; done += 1
    data["events"] = [e for e in ev if e.get("eb") != -1 or (e.get("date") or e.get("to", "")) >= today]
    json.dump(data, open(P, "w"), indent=1, ensure_ascii=False)
    print(f"eventbrite fill: {done} listings updated from Eventbrite, {gone} not found or no longer on", file=sys.stderr)

if __name__ == "__main__":
    main()
