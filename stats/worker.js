// JauntOut stats: the app posts small batches of events here; the private dashboard reads totals with a key.
const ORIGINS = ["https://www.jauntout.com", "https://jauntout.com"];
const TYPES = new Set(["visit", "share", "share_open", "swipe", "setup_done", "trip_open", "trip_pick", "map_action", "save", "undo"]);
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
  const [daily, firsts, types, swipes, who, modes, shareWho, opens, topSaved, topShared, returning, total] = await Promise.all([
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
  ]);
  return json(req, { days, since, daily, firsts, types, swipes, who, modes, shareWho, opens, topSaved, topShared,
                     returning: returning[0]?.n || 0, phones: total[0]?.phones || 0 });
}

export default {
  async fetch(req, env) {
    const url = new URL(req.url);
    if (req.method === "OPTIONS") return new Response(null, { headers: cors(req) });
    if (url.pathname === "/e" && req.method === "POST") return ingest(req, env);
    if (url.pathname === "/summary" && req.method === "GET") return summary(req, env);
    return new Response("JauntOut stats", { headers: cors(req) });
  },
};
