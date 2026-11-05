#!/usr/bin/env python3
"""
docs/weather.json: the 16-day hourly forecast (8am–8pm) for a 3×3 grid across London, fetched once
every few hours so phones read one small file instead of each calling Open-Meteo.
The app picks the nearest point; weather barely changes across ~15 km.
"""
import json, sys, time, datetime as dt
from urllib.request import Request, urlopen

LATS, LONS = [51.35, 51.49, 51.63], [-0.37, -0.10, 0.17]
VARS = ["temperature_2m", "precipitation_probability", "precipitation", "cloud_cover", "wind_gusts_10m", "weather_code"]
UA = "JauntOut-weather/0.1 (+https://www.jauntout.com)"

def fetch(lat, lon):
    u = (f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly={','.join(VARS)}"
         "&timezone=Europe%2FLondon&forecast_days=16")
    for attempt in range(3):
        try:
            with urlopen(Request(u, headers={"User-Agent": UA}), timeout=30) as r: return json.loads(r.read())
        except Exception as ex:
            if attempt == 2: raise
            time.sleep(5 * (attempt + 1))

cells, times = [], None
for lat in LATS:
    for lon in LONS:
        j = fetch(lat, lon)["hourly"]
        keep = [i for i, t in enumerate(j["time"]) if 8 <= int(t[11:13]) <= 20]
        if times is None: times = [j["time"][i] for i in keep]
        short = {"temperature_2m": "t", "precipitation_probability": "p", "precipitation": "mm", "cloud_cover": "c", "wind_gusts_10m": "g", "weather_code": "code"}
        cells.append({"lat": lat, "lon": lon, **{short[v]: [j[v][i] for i in keep] for v in VARS}})
        time.sleep(0.5)
out = {"updated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="minutes"), "time": times, "cells": cells}
json.dump(out, open("docs/weather.json", "w"), separators=(",", ":"))
print(f"weather: {len(cells)} points × {len(times)} hours", file=sys.stderr)
