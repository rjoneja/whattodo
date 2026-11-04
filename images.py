#!/usr/bin/env python3
"""
Build docs/images.json: one picture per card.

  regulars  → Wikipedia page thumbnail (Wikimedia Commons, CC/public domain; credited on the card)
  events    → a picture of what the event is ABOUT: the event page's own photo if it shows the subject
              (Diwali lights, the performers, the artwork), else a Wikimedia Commons photo of the subject,
              and only as a last resort the venue or neighbourhood

Runs in the daily workflow; safe to re-run (keeps what it already has unless --refresh).
  python3 images.py --events docs/events.json --out docs/images.json
"""
import argparse, json, os, re, sys, time, html
from urllib.parse import quote, urljoin
from urllib.request import Request, urlopen

UA = "JauntOut-images/0.2 (https://www.jauntout.com; one credited thumbnail per venue)"
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
    from urllib.error import HTTPError
    for attempt in range(4):
        try:
            req = Request(url, headers={"User-Agent": UA, "Accept": accept})
            with urlopen(req, timeout=20) as r:
                return r.geturl(), r.read().decode("utf-8", "ignore")
        except HTTPError as ex:
            if ex.code == 429 and attempt < 3:
                time.sleep(int(ex.headers.get("Retry-After") or 0) or 5 * (attempt + 1)); continue
            raise

def wiki_thumb(title):
    _, body = get("https://en.wikipedia.org/api/rest_v1/page/summary/" + quote(title.replace(" ", "_")), "application/json")
    j = json.loads(body)
    src = (j.get("thumbnail") or {}).get("source") or (j.get("originalimage") or {}).get("source")
    if not src: return None
    src = re.sub(r"/(\d+)px-", "/960px-", src)            # Wikimedia only serves standard sizes (…500, 960, 1280)
    return {"url": src, "credit": "Photo: Wikimedia Commons", "page": j.get("content_urls", {}).get("desktop", {}).get("page")}

BAD_WORDS = re.compile(r"(logo|crest|favicon|icon|sprite|placeholder|default|share[-_]?image|social[-_]?share|brand|badge|avatar|blank)", re.I)

def candidates(url):
    """Every plausible picture on an event page: og/twitter image, then large <img>s in the content."""
    final, doc = get(url, "text/html")
    out = []
    for pat in (r'(?is)<meta[^>]+(?:property|name)=["\'](?:og:image(?::secure_url)?|twitter:image)["\'][^>]+content=["\']([^"\']+)',
                r'(?is)<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name)=["\'](?:og:image|twitter:image)'):
        out += re.findall(pat, doc)
    for m in re.finditer(r'(?is)<img\b[^>]*>', doc):
        tag = m.group(0)
        src = re.search(r'(?:data-src|src)=["\']([^"\']+)', tag)
        if not src: continue
        w = re.search(r'width=["\']?(\d+)', tag)
        if w and int(w.group(1)) < 500: continue
        out.append(src.group(1))
    seen, res = set(), []
    for u in out:
        u = urljoin(final, html.unescape(u))
        if not u.startswith("http") or u in seen or BAD_WORDS.search(u) or u.lower().endswith((".svg", ".gif")): continue
        seen.add(u); res.append(u)
    return res[:6]

def image_size(u):
    """Width/height from the first bytes of a JPEG/PNG/WebP, without downloading the whole file."""
    req = Request(u, headers={"User-Agent": UA, "Range": "bytes=0-65535"})
    with urlopen(req, timeout=15) as r:
        b = r.read(65536); total = r.headers.get("Content-Range", "") or r.headers.get("Content-Length", "")
    if b[:8] == b"\x89PNG\r\n\x1a\n": return int.from_bytes(b[16:20], "big"), int.from_bytes(b[20:24], "big"), "png"
    if b[:4] == b"RIFF" and b[8:12] == b"WEBP":
        if b[12:16] == b"VP8X": return 1 + int.from_bytes(b[24:27], "little"), 1 + int.from_bytes(b[27:30], "little"), "webp"
        if b[12:16] == b"VP8 ": return int.from_bytes(b[26:28], "little") & 0x3fff, int.from_bytes(b[28:30], "little") & 0x3fff, "webp"
        return None
    if b[:2] == b"\xff\xd8":
        i = 2
        while i < len(b) - 9:
            if b[i] != 0xFF: i += 1; continue
            mk = b[i+1]
            if mk in (0xC0, 0xC1, 0xC2): return int.from_bytes(b[i+7:i+9], "big"), int.from_bytes(b[i+5:i+7], "big"), "jpg"
            i += 2 + int.from_bytes(b[i+2:i+4], "big")
    return None

_client = None
def ask(content, max_tokens=60):
    """One short-answer call. Thinking is switched off so the answer isn't crowded out; if the API won't
    take that, fall back to a roomy token budget instead."""
    global _client
    import anthropic
    _client = _client or anthropic.Anthropic()
    model = os.environ.get("WTD_MODEL", "claude-haiku-5-5")
    try:
        msg = _client.messages.create(model=model, max_tokens=max_tokens, thinking={"type": "disabled"}, messages=[{"role": "user", "content": content}])
    except Exception as ex:
        if "thinking" not in str(ex).lower(): raise
        msg = _client.messages.create(model=model, max_tokens=max(max_tokens, 2000), messages=[{"role": "user", "content": content}])
    return "".join(getattr(b, "text", "") for b in msg.content if getattr(b, "type", "") == "text"), getattr(msg, "stop_reason", "")

def shrink(data, limit=1568):
    """Downscale big images so Claude accepts them (and costs less)."""
    try:
        from PIL import Image
        import io
        im = Image.open(io.BytesIO(data))
        if max(im.size) <= limit: return data, None
        im.thumbnail((limit, limit)); buf = io.BytesIO()
        im.convert("RGB").save(buf, "JPEG", quality=85)
        return buf.getvalue(), "image/jpeg"
    except Exception:
        return data, None

VETS = {"n": 0}
MAX_VETS = int(os.environ.get("IMG_MAX_VETS", "1500"))       # spending cap per run
def relevance(u, name, subject):
    """0-3: how well this picture shows what the event is about. 3 = clearly the subject, 2 = good fit,
    1 = only the venue/room/generic scene, 0 = logo, text, poster, map, screenshot."""
    if not os.environ.get("ANTHROPIC_API_KEY"): return 2
    if VETS["n"] >= MAX_VETS: return -1
    global _client
    import anthropic, base64
    _client = _client or anthropic.Anthropic()
    try:
        with urlopen(Request(u, headers={"User-Agent": UA}), timeout=20) as r:
            data = r.read(6_000_000); ctype = (r.headers.get("Content-Type") or "").split(";")[0].strip()
        if len(data) >= 6_000_000: return 0
        data, ct2 = shrink(data, 512)
        if ctype not in ("image/jpeg", "image/png", "image/webp", "image/gif"):
            ctype = "image/png" if data[:4] == b"\x89PNG" else "image/webp" if data[8:12] == b"WEBP" else "image/jpeg"
        if ct2: ctype = ct2
        VETS["n"] += 1
        txt, stop = ask([
            {"type": "image", "source": {"type": "base64", "media_type": ctype, "data": base64.b64encode(data).decode()}},
            {"type": "text", "text": f"A listings app needs a photo for '{name}', which is about: {subject}.\n"
             "Score this image 0-3. 3 = an appealing photo that clearly shows the subject (e.g. Diwali lights and dancers for a Diwali event, "
             "the performers, the artwork, the activity). 2 = an appealing photo that fits well. 1 = only the venue, building, room or a generic scene "
             "that doesn't show the subject. 0 = a logo, icon, text, a flyer that is mostly words, a map, a screenshot, or unappealing.\n"
             "Answer in the form SCORE: <digit>"}])
        if VETS["n"] <= 4: print(f"    raw reply: {txt[:60]!r} stop={stop}", file=sys.stderr)
        m = re.search(r"SCORE:\s*([0-3])", txt, re.I) or re.search(r"\b([0-3])\b", txt)
        return int(m.group(1)) if m else 0
    except Exception as ex:
        print(f"  vet failed {u[:60]}: {str(ex)[:80]}", file=sys.stderr)
        return 0

def looks_like_photo(u, name):
    """Ask Claude (cheap model) whether this is a real photo of the event/place, not a logo, crest, poster text or stock icon."""
    if not os.environ.get("ANTHROPIC_API_KEY"): return True
    global _client
    import anthropic
    _client = _client or anthropic.Anthropic()
    try:
        import base64
        with urlopen(Request(u, headers={"User-Agent": UA}), timeout=20) as r:
            data = r.read(4_500_000); ctype = (r.headers.get("Content-Type") or "").split(";")[0].strip()
        if len(data) >= 4_500_000: return False
        data, ct2 = shrink(data)
        if ctype not in ("image/jpeg", "image/png", "image/webp", "image/gif"):
            ctype = "image/png" if data[:4] == b"\x89PNG" else "image/webp" if data[8:12] == b"WEBP" else "image/jpeg"
        if ct2: ctype = ct2
        txt, _ = ask([
            {"type": "image", "source": {"type": "base64", "media_type": ctype, "data": base64.b64encode(data).decode()}},
            {"type": "text", "text": f"This image is for a listing called '{name}'. Answer YES if it is an appealing photograph (people, a place, an activity, an exhibit or artwork) that would make someone want to go. Answer NO if it is a logo, coat of arms, icon, plain text, a flyer that is mostly words, a map, a screenshot or a generic graphic. One word."}])
        return "YES" in txt.upper()
    except Exception as ex:
        print(f"  vet failed {u[:60]}: {str(ex)[:80]}", file=sys.stderr)
        return False

def subjects(events):
    """One cheap text call per 40 events: what each is visually about, and a 1-3 word photo search."""
    out = {}
    if not os.environ.get("ANTHROPIC_API_KEY"): return out
    global _client
    import anthropic
    _client = _client or anthropic.Anthropic()
    for i in range(0, len(events), 40):
        b = events[i:i+40]
        items = [{"i": n, "name": e["name"], "at": e.get("source", ""), "about": e.get("blurb", "")[:200]} for n, e in enumerate(b)]
        prompt = ("For each London listing, say what a photo for it should SHOW: the thing people go for, not the venue it happens in "
                  "(a Diwali celebration in a sports hall → Diwali; a model railway show at a school → model railway). If the place itself "
                  "is the point (a palace tour, a park, a late opening of a museum) the place is the subject.\n"
                  'Return ONLY a JSON array: [{"i":0,"subject":"Diwali celebration with lights and dance","q":"Diwali"}] where q is a 1-3 word '
                  "photo search term.\n" + json.dumps(items, ensure_ascii=False))
        try:
            msg = _client.messages.create(model=os.environ.get("WTD_MODEL", "claude-haiku-5-5"), max_tokens=6000, messages=[{"role": "user", "content": prompt}])
            txt = "".join(getattr(x, "text", "") for x in msg.content); m = re.search(r"\[.*\]", txt, re.S)
            for v in (json.loads(m.group(0)) if m else []):
                if isinstance(v, dict) and v.get("i") is not None and v["i"] < len(b): out[b[v["i"]]["id"]] = {"subject": str(v.get("subject", ""))[:90], "q": str(v.get("q", ""))[:40]}
        except Exception as ex:
            print(f"subjects batch failed: {str(ex)[:80]}", file=sys.stderr)
    return out

def strip_html(x): return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", html.unescape(x or ""))).strip()
_commons = {}
def commons(q):
    """Wikimedia Commons photos for a subject, largest-licence-safe first."""
    if not q: return []
    if q in _commons: return _commons[q]
    u = ("https://commons.wikimedia.org/w/api.php?action=query&format=json&generator=search&gsrnamespace=6&gsrlimit=10"
         "&gsrsearch=" + quote("filetype:bitmap " + q) + "&prop=imageinfo&iiprop=url|size|extmetadata&iiurlwidth=960")
    res = []
    try:
        _, body = get(u, "application/json")
        pages = sorted((json.loads(body).get("query") or {}).get("pages", {}).values(), key=lambda p: p.get("index", 99))
        for p in pages:
            ii = (p.get("imageinfo") or [{}])[0]; md = ii.get("extmetadata") or {}
            lic = strip_html((md.get("LicenseShortName") or {}).get("value", ""))
            w, h = ii.get("width", 0), ii.get("height", 0)
            if not ii.get("thumburl") or w < 900 or not (0.6 < w / max(h, 1) < 2.2): continue
            if not re.search(r"CC|Public domain|PD", lic, re.I) or re.search(r"\bNC\b|ND", lic): continue
            artist = strip_html((md.get("Artist") or {}).get("value", ""))[:40] or "Wikimedia Commons"
            res.append({"url": ii["thumburl"], "credit": f"Photo: {artist} · {lic}", "page": ii.get("descriptionurl")})
    except Exception as ex:
        print(f"  commons failed {q}: {str(ex)[:60]}", file=sys.stderr)
    _commons[q] = res
    return res

def best_for(e, used, subj):
    """Event page photo if it shows the subject; else a Commons photo of the subject; else the venue shot (score 1)."""
    name, subject, q = e["name"], (subj or {}).get("subject") or e["name"], (subj or {}).get("q") or ""
    host = re.sub(r"^https?://(www\.)?", "", e["url"]).split("/")[0]
    fallback = None
    if "instagram.com" not in e["url"]:
        try: cands = candidates(e["url"])
        except Exception: cands = []
        for u in cands[:3]:
            if used.get(u, 0) >= 1: continue
            try: sz = image_size(u)
            except Exception: sz = None
            if not sz: continue
            w, h, kind = sz
            if w < 600 or h < 300 or w / max(h, 1) > 2.6 or w / max(h, 1) < 0.6: continue
            sc = relevance(u, name, subject); print(f"    page {sc} {u[:70]}", file=sys.stderr)
            if sc >= 2: return {"url": u, "credit": host, "fit": sc}
            if sc == 1 and not fallback: fallback = {"url": u, "credit": host, "fit": 1}
    cs = commons(q); print(f"    commons '{q}': {len(cs)}", file=sys.stderr)
    for c in [c for c in cs if used.get(c["url"], 0) == 0][:3]:
        sc = relevance(c["url"], name, subject); print(f"    commons {sc} {c['url'][-50:]}", file=sys.stderr)
        if sc >= 2: return dict(c, fit=sc)
    return fallback

def pick(e, used):
    for u in candidates(e["url"]):
        if used.get(u, 0) >= 1: continue                          # same picture on another listing = a site-wide default
        try: sz = image_size(u)
        except Exception: sz = None
        if not sz: continue
        w, h, kind = sz
        if w < 600 or h < 300 or w / max(h, 1) > 2.6 or w / max(h, 1) < 0.6: continue
        if not looks_like_photo(u, e["name"]): continue
        host = re.sub(r"^https?://(www\.)?", "", e["url"]).split("/")[0]
        return {"url": u, "credit": host}
    return None

_area_cache = {}
def wiki_area(area, name):
    """Fallback: Wikipedia's lead photo of the neighbourhood (e.g. 'Blackheath, London'), vetted like any other picture."""
    if not area or area.lower() in ("london-wide", "london", "central"): return None
    if area not in _area_cache:
        t = None
        for title in (f"{area}, London", area):
            try:
                t = wiki_thumb(title)
                if t and not BAD_WORDS.search(t["url"]) and ".svg" not in t["url"].lower(): break
                t = None
            except Exception: t = None
        _area_cache[area] = t
    t = _area_cache[area]
    if t and looks_like_photo(t["url"], f"{name} (in {area})"): return dict(t)
    return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--events", default="docs/events.json"); ap.add_argument("--out", default="docs/images.json")
    ap.add_argument("--refresh", action="store_true"); ap.add_argument("--recheck", action="store_true", help="re-vet existing event pictures")
    a = ap.parse_args()
    out = json.load(open(a.out)) if os.path.exists(a.out) and not a.refresh else {}
    out.pop("_tried", None); tried = out.pop("_tried4", {})      # attempts under the subject-aware picker only
    out = {k: v for k, v in out.items() if "/640px-" not in v.get("url", "")}   # old non-standard size: refetch
    for id_, title in WIKI.items():
        if id_ in out: continue
        try:
            t = wiki_thumb(title)
            if t: out[id_] = t; print(f"{id_}: wiki ok", file=sys.stderr)
        except Exception as ex:
            print(f"{id_}: wiki failed {ex}", file=sys.stderr)
        time.sleep(1.5)
    events = json.load(open(a.events)).get("events", []) if os.path.exists(a.events) else []
    for k, v in out.items():
        if v.get("checked") == 2 and "Wikimedia" not in v.get("credit", ""): v["checked"] = 3
    if a.recheck:
        for e in events:
            if e["id"] in out and (out[e["id"]].get("checked") != 3): out.pop(e["id"])
    used = {}
    for k, v in out.items(): used[v["url"]] = used.get(v["url"], 0) + 1
    today = time.strftime("%Y-%m-%d")
    week_ago = time.strftime("%Y-%m-%d", time.gmtime(time.time() - 7 * 86400))
    # events needing a (better) picture: none yet, or one chosen before relevance scoring (checked < 4)
    need = [e for e in events if e.get("url", "").startswith("http") and (e["id"] not in out or out[e["id"]].get("checked", 0) < 4)
            and not (tried.get(e["id"]) and tried[e["id"]] >= week_ago and e["id"] not in out)]
    subj = subjects(need)
    print(f"pictures: {len(need)} to check, {len(subj)} subjects", file=sys.stderr)
    for e in need:
        if VETS["n"] >= MAX_VETS: print("vet budget reached; the rest wait for tomorrow", file=sys.stderr); break
        old = out.get(e["id"]); print(f"{e['id']}: about '{(subj.get(e['id']) or {}).get('subject','?')}'", file=sys.stderr)
        if old: used[old["url"]] = max(0, used.get(old["url"], 1) - 1)
        t = None
        try: t = best_for(e, used, subj.get(e["id"]))
        except Exception as ex: print(f"{e['id']}: pick failed {str(ex)[:60]}", file=sys.stderr)
        if not t or t.get("fit", 0) < 2:
            if old and old.get("checked", 0) >= 3 and (not t or t.get("fit", 0) <= 1): t = dict(old, fit=1)   # keep a vetted old picture over a mere venue shot
            elif not t:
                try: t = wiki_area(e.get("area"), e["name"])
                except Exception: t = None
                if t: t["fit"] = 1
        tried[e["id"]] = today
        if t:
            t["checked"] = 4; out[e["id"]] = t; used[t["url"]] = used.get(t["url"], 0) + 1
            print(f"{e['id']}: fit {t.get('fit')} {'commons' if 'commons' in t.get('page','') or '·' in t.get('credit','') else 'page' if t['credit'] and 'Wikimedia' not in t['credit'] else 'area'}", file=sys.stderr)
        time.sleep(0.3)
    live = set(WIKI) | {e["id"] for e in events}
    out = {k: v for k, v in out.items() if k in live}
    out["_tried4"] = {k: v for k, v in tried.items() if k in live and k not in out}
    json.dump(out, open(a.out, "w"), indent=0, ensure_ascii=False)
    print(f"wrote {len(out)} images to {a.out}")

if __name__ == "__main__":
    main()
