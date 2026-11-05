#!/usr/bin/env python3
"""
Read the newsletter inbox (IMAP, app password) and add the London events in it to docs/events.json.

  NEWS_IMAP_USER / NEWS_IMAP_PASS  (GitHub secrets)   python3 newsletters.py [--days 10] [--limit 40]

Each email is read once (message ids in news_seen.json). Links in the email are kept with their link text so the
model can give each event its own page (the venue's or organiser's, not the newsletter's). Sign-up confirmation
emails are listed in the log for Raj to click; nothing here clicks links in emails.
"""
import email, email.header, email.utils, html, imaplib, json, os, re, sys, datetime as dt
from email.message import Message
import ingest   # SCHEMA, claude(), valid(), key(), slug(), carry()

P, SEEN = "docs/events.json", "news_seen.json"
DAYS = int(sys.argv[sys.argv.index("--days") + 1]) if "--days" in sys.argv else 10
LIMIT = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else 40
CONFIRM = re.compile(r"confirm (your )?(subscription|email)|verify your email|please confirm|activate your subscription|one more step", re.I)

def dec(s):
    return "".join(t.decode(c or "utf-8", "ignore") if isinstance(t, bytes) else t for t, c in email.header.decode_header(s or ""))

def body_text(msg: Message):
    """Plain text of the email, with links written out as 'text [url]' so they survive."""
    htm = txt = None
    for part in msg.walk():
        ct = part.get_content_type()
        if part.get_content_maintype() == "multipart" or part.get("Content-Disposition", "").startswith("attachment"): continue
        try: data = part.get_payload(decode=True).decode(part.get_content_charset() or "utf-8", "ignore")
        except Exception: continue
        if ct == "text/html" and htm is None: htm = data
        elif ct == "text/plain" and txt is None: txt = data
    if htm:
        h = re.sub(r"(?is)<(script|style|head).*?</\1>", " ", htm)
        def link(m):
            u = html.unescape(m.group(1)); t = re.sub(r"<[^>]+>", " ", m.group(2)); t = re.sub(r"\s+", " ", html.unescape(t)).strip()
            if not u.startswith("http") or re.search(r"unsubscribe|preferences|manage|view in browser|privacy|facebook|twitter|instagram|linkedin|tiktok|youtube", u + " " + t, re.I): return t
            return f"{t} [{u[:220]}]" if t else f"[{u[:220]}]"
        h = re.sub(r'(?is)<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', link, h)
        h = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</tr>|</h\d>|</li>", "\n", h)
        t = html.unescape(re.sub(r"<[^>]+>", " ", h))
    else:
        t = txt or ""
    t = re.sub(r"[ \t ]+", " ", t); t = re.sub(r"\n\s*\n+", "\n", t)
    return t.strip()

def main():
    user, pw = os.environ.get("NEWS_IMAP_USER"), os.environ.get("NEWS_IMAP_PASS")
    if not (user and pw): print("newsletters: no inbox credentials, skipped", file=sys.stderr); return
    seen = json.load(open(SEEN)) if os.path.exists(SEEN) else {}
    today = dt.date.today(); horizon = today + dt.timedelta(days=21)
    M = imaplib.IMAP4_SSL("imap.gmail.com"); M.login(user, pw.replace(" ", ""))
    M.select("INBOX", readonly=True)                       # read-only: nothing is marked, moved or deleted
    since = (today - dt.timedelta(days=DAYS)).strftime("%d-%b-%Y")
    typ, ids = M.search(None, "SINCE", since)
    ids = ids[0].split()[::-1]
    data = json.load(open(P)); events = data.get("events", [])
    existing = {ingest.key(e): e for e in events}
    added, mails, confirms = 0, 0, []
    for i in ids:
        if mails >= LIMIT: break
        typ, hdr = M.fetch(i, "(BODY.PEEK[HEADER.FIELDS (MESSAGE-ID FROM SUBJECT DATE)])")
        h = email.message_from_bytes(hdr[0][1]); mid = (h.get("Message-ID") or "").strip() or f"uid-{i.decode()}"
        if mid in seen: continue
        sender = email.utils.parseaddr(dec(h.get("From")))
        name, addr = (sender[0] or sender[1].split("@")[0]).strip('"'), sender[1].lower()
        subj = dec(h.get("Subject"))
        # the account's own mail (Google security notices, sign-in alerts) is not a newsletter: never read or send it anywhere
        if re.search(r"@(accounts\.)?google\.com$|@googlemail\.com$|no-reply@accounts", addr):
            seen[mid] = {"from": name, "addr": addr, "subject": "(account email, skipped)", "n": 0, "kind": "skip", "day": today.isoformat()}; continue
        typ, raw = M.fetch(i, "(BODY.PEEK[])")
        msg = email.message_from_bytes(raw[0][1])
        text = body_text(msg)
        if CONFIRM.search(subj) or (len(text) < 2500 and CONFIRM.search(text)):
            confirms.append(f"{name} <{addr}>: {subj}"); seen[mid] = {"from": name, "addr": addr, "subject": subj[:120], "n": 0, "kind": "confirm", "day": today.isoformat()}
            continue
        mails += 1
        sent = email.utils.parsedate_to_datetime(h.get("Date")).date().isoformat() if h.get("Date") else today.isoformat()
        prompt = f"""This is a London newsletter email from "{name}", sent {sent}. Today is {today.isoformat()}.
List every event, exhibition, festival, market, show, talk, walk or activity in London that the public can go to
between {today.isoformat()} and {horizon.isoformat()}. Skip adverts for products, restaurant openings with nothing to attend,
competitions, things outside London, online-only things and anything already over.
For "url": use the link in the email that goes to THAT event's own page, preferably the venue's or organiser's site
(links appear as "text [url]"). Use the newsletter's own article link only if nothing better is given. Never invent a URL.
Estimate lat/lon from the venue named. Resolve dates like "this Saturday" from the send date.
{ingest.SCHEMA}
Return ONLY a JSON array (empty if there are no events).
EMAIL SUBJECT: {subj}
EMAIL TEXT:
{text[:14000]}"""
        try: evs = ingest.claude(prompt)
        except Exception as ex: print(f"  {name}: model failed {str(ex)[:80]}", file=sys.stderr); continue
        n = 0
        for e in evs if isinstance(evs, list) else []:
            if not isinstance(e, dict): continue
            e["source"] = f"Newsletter: {name}"
            if not ingest.valid(e, today.isoformat(), horizon.isoformat()): continue
            e["id"] = ingest.slug(e); k = ingest.key(e)
            existing[k] = ingest.carry(existing[k], e) if k in existing else e
            n += 1
        added += n
        seen[mid] = {"from": name, "addr": addr, "subject": subj[:120], "n": n, "day": today.isoformat()}
        print(f"  {name}: “{subj[:60]}” → {n} events", file=sys.stderr)
    M.logout()
    data["events"] = [e for e in existing.values() if (e.get("date") or e.get("to", "")) >= today.isoformat()]
    json.dump(data, open(P, "w"), indent=1, ensure_ascii=False)
    # keep the seen list from growing forever: 120 days is plenty
    cutoff = (today - dt.timedelta(days=120)).isoformat()
    json.dump({k: v for k, v in seen.items() if v.get("day", today.isoformat()) >= cutoff}, open(SEEN, "w"), indent=1, ensure_ascii=False)
    print(f"newsletters: read {mails} emails, {added} events", file=sys.stderr)
    for c in confirms: print(f"  ⚠ needs confirming in the inbox: {c}", file=sys.stderr)

if __name__ == "__main__":
    main()
