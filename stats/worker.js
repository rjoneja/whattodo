// JauntOut stats + event submissions.
//  - the app posts small batches of usage events; the private dashboard reads totals with a key
//  - organisers submit events; a GitHub job writes them up; Raj approves each by email (signed links)
const ORIGINS = ["https://www.jauntout.com", "https://jauntout.com", "https://jauntout.pages.dev"];
const TYPES = new Set(["visit", "share", "share_open", "swipe", "setup_done", "trip_open", "trip_pick", "map_action", "save", "undo", "search"]);
const clip = (x, n = 60) => (x == null ? null : String(x).slice(0, n));
const londonDay = ms => new Date(ms).toLocaleDateString("en-CA", { timeZone: "Europe/London" });

function cors(req) {
  const o = req.headers.get("Origin") || "";
  return { "Access-Control-Allow-Origin": ORIGINS.includes(o) ? o : ORIGINS[0], "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
           "Access-Control-Allow-Headers": "authorization,content-type", "Vary": "Origin" };
}
const json = (req, body, status = 200) => new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json", ...cors(req) } });

async function ingest(req, env) {
  const o = req.headers.get("Origin") || "";
  if (o && !ORIGINS.includes(o)) return new Response(null, { status: 403 });
  const text = await req.text();
  if (text.length > 16000) return new Response(null, { status: 413 });
  let body; try { body = JSON.parse(text); } catch { return new Response(null, { status: 400 }); }
  const dev = clip(body.d, 40); if (!dev || !/^[a-z0-9-]{8,40}$/i.test(dev)) return new Response(null, { status: 400 });
  const now = Date.now(), day = londonDay(now);
  const rows = (Array.isArray(body.e) ? body.e : []).slice(0, 60).filter(x => x && TYPES.has(x.t));
  if (rows.length) {
    const st = env.DB.prepare("INSERT INTO ev (day, ts, dev, t, a, b, id) VALUES (?, ?, ?, ?, ?, ?, ?)");
    await env.DB.batch(rows.map(x => st.bind(day, now, dev, x.t, clip(x.a), clip(x.b), clip(x.id, 80))));
  }
  return new Response(null, { status: 204, headers: cors(req) });
}

async function summary(req, env) {
  const key = (req.headers.get("authorization") || "").replace(/^Bearer\s+/i, "");
  if (!env.DASH_KEY || key !== env.DASH_KEY) return json(req, { error: "wrong key" }, 401);
  const days = Math.min(90, Math.max(7, +new URL(req.url).searchParams.get("days") || 30));
  const since = londonDay(Date.now() - (days - 1) * 864e5);
  const q = (sql, ...p) => env.DB.prepare(sql).bind(...p).all().then(r => r.results);
  const [daily, firsts, types, swipes, who, modes, shareWho, opens, topSaved, topShared, returning, total, searches, misses] = await Promise.all([
    q("SELECT day, COUNT(DISTINCT dev) AS phones, SUM(t='visit') AS visits, SUM(t='share') AS shares, SUM(t='share_open') AS opens FROM ev WHERE day >= ? GROUP BY day ORDER BY day", since),
    q("SELECT first AS day, COUNT(*) AS n FROM (SELECT dev, MIN(day) AS first FROM ev GROUP BY dev) WHERE first >= ? GROUP BY first", since),
    q("SELECT t, COUNT(*) AS n FROM ev WHERE day >= ? GROUP BY t ORDER BY n DESC", since),
    q("SELECT a AS kind, COUNT(*) AS n FROM ev WHERE day >= ? AND t='swipe' GROUP BY a ORDER BY n DESC", since),
    q("SELECT a AS who, COUNT(DISTINCT dev) AS phones FROM ev WHERE day >= ? AND t='setup_done' GROUP BY a ORDER BY phones DESC", since),
    q("SELECT b AS modes, COUNT(DISTINCT dev) AS phones FROM ev WHERE day >= ? AND t='setup_done' GROUP BY b ORDER BY phones DESC", since),
    q("SELECT a AS who, COUNT(*) AS n FROM ev WHERE day >= ? AND t='share' GROUP BY a ORDER BY n DESC", since),
    q("SELECT a AS via, COUNT(*) AS n FROM ev WHERE day >= ? AND t='share_open' GROUP BY a ORDER BY n DESC", since),
    q("SELECT id, COUNT(*) AS n FROM ev WHERE day >= ? AND t='swipe' AND a IN ('saved','again') AND id IS NOT NULL GROUP BY id ORDER BY n DESC LIMIT 15", since),
    q("SELECT id, COUNT(*) AS n FROM ev WHERE day >= ? AND t='share' AND id IS NOT NULL GROUP BY id ORDER BY n DESC LIMIT 10", since),
    q("SELECT COUNT(*) AS n FROM (SELECT dev FROM ev WHERE day >= ? GROUP BY dev HAVING COUNT(DISTINCT day) > 1)", since),
    q("SELECT COUNT(DISTINCT dev) AS phones FROM ev WHERE day >= ?", since),
    q("SELECT a AS q, COUNT(*) AS n FROM ev WHERE day >= ? AND t='search' AND b <> '0' GROUP BY a ORDER BY n DESC LIMIT 15", since),
    q("SELECT a AS q, COUNT(*) AS n, MAX(id) AS followed FROM ev WHERE day >= ? AND t='search' AND b = '0' GROUP BY a ORDER BY n DESC LIMIT 15", since),
  ]);
  return json(req, { days, since, daily, firsts, types, swipes, who, modes, shareWho, opens, topSaved, topShared, searches, misses,
                     returning: returning[0]?.n || 0, phones: total[0]?.phones || 0 });
}

// ---------- submissions ----------
const authed = (req, env) => env.DASH_KEY && (req.headers.get("authorization") || "").replace(/^Bearer\s+/i, "") === env.DASH_KEY;
async function sign(env, text) {
  const k = await crypto.subtle.importKey("raw", new TextEncoder().encode(env.DASH_KEY), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  const b = new Uint8Array(await crypto.subtle.sign("HMAC", k, new TextEncoder().encode(text)));
  return [...b].slice(0, 16).map(x => x.toString(16).padStart(2, "0")).join("");
}
const esc = x => String(x ?? "").replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);

async function submit(req, env) {
  const o = req.headers.get("Origin") || "";
  if (o && !ORIGINS.includes(o)) return new Response(null, { status: 403 });
  let b; try { b = JSON.parse((await req.text()).slice(0, 8000)); } catch { return json(req, { error: "bad form" }, 400); }
  if (b.website) return json(req, { ok: true });                                   // honeypot: bots fill every box
  const url = clip(b.url, 400), name = clip(b.name, 120), details = clip(b.details, 1200);
  if (url && !/^https?:\/\/[^\s]+\.[^\s]+/i.test(url)) return json(req, { error: "That link doesn't look right." }, 400);
  if (!url && !(name && details)) return json(req, { error: "Add a link, or the event's name and a few details." }, 400);
  if (!b.ok) return json(req, { error: "Please confirm you're the organiser or have their permission." }, 400);
  const recent = await env.DB.prepare("SELECT COUNT(*) AS n FROM sub WHERE ts > ?").bind(Date.now() - 3600e3).first();
  if ((recent?.n || 0) > 40) return json(req, { error: "Lots of submissions right now. Please try again in an hour." }, 429);
  const id = crypto.randomUUID().slice(0, 12);
  await env.DB.prepare("INSERT INTO sub (id, ts, status, url, name, dates, venue, details, contact) VALUES (?, ?, 'new', ?, ?, ?, ?, ?, ?)")
    .bind(id, Date.now(), url, name, clip(b.dates, 120), clip(b.venue, 160), details, clip(b.contact, 120)).run();
  return json(req, { ok: true, id });
}

async function prepared(req, env) {
  if (!authed(req, env)) return json(req, { error: "wrong key" }, 401);
  const b = await req.json(); const row = await env.DB.prepare("SELECT * FROM sub WHERE id = ?").bind(b.id).first();
  if (!row) return json(req, { error: "no such submission" }, 404);
  await env.DB.prepare("UPDATE sub SET status = 'review', event = ?, verdict = ? WHERE id = ?").bind(JSON.stringify(b.event || null), clip(b.verdict, 300), b.id).run();
  const e = b.event || {}, base = new URL(req.url).origin;
  const link = async a => `${base}/review?id=${row.id}&a=${a}&sig=${await sign(env, row.id + ":" + a)}`;
  const when = e.date ? e.date + (e.time ? " · " + e.time : "") : e.from ? `${e.from} to ${e.to}` : "date unclear";
  const body = `<!doctype html><html><body style="margin:0;background:#122018;font-family:Helvetica,Arial,sans-serif;color:#F2EEE3">
<div style="max-width:520px;margin:0 auto;padding:24px 16px">
<p style="margin:0 0 6px;font-size:12px;letter-spacing:.12em;color:#86938A">JAUNTOUT · NEW EVENT TO APPROVE</p>
<div style="background:#1A2C22;border:1px solid #2A3D31;border-radius:14px;padding:18px">
${b.image ? `<img src="${esc(b.image)}" alt="" style="width:100%;border-radius:10px;margin-bottom:12px">` : ""}
<p style="margin:0;font-size:12px;letter-spacing:.1em;color:#86938A">${esc((e.area || row.venue || "").toUpperCase())}</p>
<h2 style="margin:4px 0 8px;font-family:Georgia,serif;font-weight:400;font-size:24px">${esc(e.name || row.name || "(no name)")}</h2>
<p style="margin:0 0 8px;color:#C2C8BE;font-size:14px">${esc(when)} · ${esc(e.price === "free" ? "Free" : e.price || "price?")}</p>
<p style="margin:0 0 12px;font-size:15px;line-height:1.45">${esc(e.blurb || row.details || "")}</p>
<p style="margin:0;font-size:13px;color:#C2C8BE">Link: ${row.url ? `<a style="color:#EE6A3F" href="${esc(e.url || row.url)}">${esc((e.url || row.url).slice(0, 80))}</a>` : "none given"}</p>
${row.contact ? `<p style="margin:6px 0 0;font-size:13px;color:#C2C8BE">Submitted by: ${esc(row.contact)}</p>` : ""}
<p style="margin:12px 0 0;font-size:13px;color:${/fine|ok|good/i.test(b.verdict || "") ? "#5DB58A" : "#E0A43A"}">Check: ${esc(b.verdict || "no verdict")}</p>
</div>
<p style="margin:18px 0"><a href="${await link("approve")}" style="display:inline-block;background:#5DB58A;color:#122018;text-decoration:none;font-weight:bold;padding:12px 20px;border-radius:12px;margin-right:8px">Approve</a>
<a href="${await link("reject")}" style="display:inline-block;background:#1A2C22;color:#F2EEE3;border:1px solid #2A3D31;text-decoration:none;padding:12px 20px;border-radius:12px">Reject</a></p>
<p style="font-size:12px;color:#86938A">Approved events go live at the next hourly update.</p></div></body></html>`;
  const subj = "Approve? " + (e.name || row.name || "new event").slice(0, 70);
  const raw = [`From: JauntOut <events@jauntout.com>`, `To: ${env.NOTIFY_TO}`, `Subject: ${subj.replace(/[\r\n]/g, " ")}`,
    `Message-ID: <${row.id}.${Date.now()}@jauntout.com>`, `Date: ${new Date().toUTCString()}`, "MIME-Version: 1.0",
    'Content-Type: text/html; charset="utf-8"', "Content-Transfer-Encoding: 8bit", "", body].join("\r\n");
  try { const { EmailMessage } = await import("cloudflare:email"); await env.MAIL.send(new EmailMessage("events@jauntout.com", env.NOTIFY_TO, raw)); }
  catch (ex) {   // couldn't email Raj: put it back in the queue so the next hourly run tries again
    await env.DB.prepare("UPDATE sub SET status = 'new' WHERE id = ?").bind(row.id).run();
    return json(req, { ok: false, emailed: false, error: String(ex).slice(0, 200) }, 502);
  }
  return json(req, { ok: true, emailed: true });
}

async function review(req, env) {
  const u = new URL(req.url), id = u.searchParams.get("id"), a = u.searchParams.get("a");
  const page = (title, msg) => new Response(`<!doctype html><meta name=viewport content="width=device-width,initial-scale=1"><title>${title}</title><body style="margin:0;background:#122018;color:#F2EEE3;font-family:Helvetica,Arial,sans-serif;display:grid;place-items:center;min-height:100vh;text-align:center;padding:24px"><div><h1 style="font-family:Georgia,serif;font-weight:400">${title}</h1><p style="color:#C2C8BE">${msg}</p></div>`, { headers: { "content-type": "text/html; charset=utf-8" } });
  if (!id || !["approve", "reject"].includes(a) || u.searchParams.get("sig") !== await sign(env, id + ":" + a)) return page("Link not valid", "This approval link is wrong or has been changed.");
  const row = await env.DB.prepare("SELECT status, name, event FROM sub WHERE id = ?").bind(id).first();
  if (!row) return page("Not found", "That submission doesn't exist any more.");
  if (["published", "approved", "rejected"].includes(row.status)) return page("Already done", `This one is already ${row.status}.`);
  await env.DB.prepare("UPDATE sub SET status = ? WHERE id = ?").bind(a === "approve" ? "approved" : "rejected", id).run();
  const nm = esc((JSON.parse(row.event || "{}").name) || row.name || "The event");
  return a === "approve" ? page("Approved", `${nm} goes live at the next hourly update.`) : page("Rejected", `${nm} won't be listed.`);
}

async function subList(req, env, status) {
  if (!authed(req, env)) return json(req, { error: "wrong key" }, 401);
  const r = await env.DB.prepare("SELECT * FROM sub WHERE status = ? ORDER BY ts LIMIT 30").bind(status).all();
  return json(req, { items: r.results });
}
async function published(req, env) {
  if (!authed(req, env)) return json(req, { error: "wrong key" }, 401);
  const b = await req.json();
  for (const id of (b.ids || []).slice(0, 50)) await env.DB.prepare("UPDATE sub SET status = 'published' WHERE id = ? AND status = 'approved'").bind(id).run();
  return json(req, { ok: true });
}

export default {
  async fetch(req, env) {
    const url = new URL(req.url);
    if (req.method === "OPTIONS") return new Response(null, { headers: cors(req) });
    if (url.pathname === "/submit" && req.method === "POST") return submit(req, env);
    if (url.pathname === "/pending" && req.method === "GET") return subList(req, env, "new");
    if (url.pathname === "/approved" && req.method === "GET") return subList(req, env, "approved");
    if (url.pathname === "/prepared" && req.method === "POST") return prepared(req, env);
    if (url.pathname === "/published" && req.method === "POST") return published(req, env);
    if (url.pathname === "/review" && req.method === "GET") return review(req, env);
    if (url.pathname === "/e" && req.method === "POST") return ingest(req, env);
    if (url.pathname === "/summary" && req.method === "GET") return summary(req, env);
    return new Response("JauntOut stats", { headers: cors(req) });
  },
};
