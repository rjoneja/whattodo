"""
Meter every Claude call a job makes and report the spend to the stats Worker when the job ends.

  import meter   # first thing in any script that calls Claude; nothing else to change

It wraps the Anthropic SDK's messages.create, adds up the token counts the API returns for each
call, prices them at the model's published rates, and on exit POSTs one row per model to
<stats Worker>/usage (needs DASH_KEY). Without DASH_KEY or the Worker address it just prints the total.
Prices are USD per million tokens; prompts over 100k input tokens pay the higher Haiku 5.5 rate.
"""
import atexit, json, os, sys
from urllib.request import Request, urlopen

PRICES = {   # model prefix: (input, output, cache read, cache write 5m) per million tokens, then the >100k-prompt set
    "claude-haiku-5-5": ((0.10, 0.50, 0.01, 0.125), (0.50, 2.50, 0.05, 0.625)),
}
DEFAULT = PRICES["claude-haiku-5-5"]
JOB = os.environ.get("METER_JOB") or os.environ.get("GITHUB_WORKFLOW", "local") + ":" + os.path.basename(sys.argv[0]).removesuffix(".py")
TOTAL = {}   # model -> {calls, in, out, cr, cw, usd}

def _price(model):
    for k, v in PRICES.items():
        if model.startswith(k): return v
    return DEFAULT

def record(model, u):
    if u is None: return
    get = (lambda k: getattr(u, k, None) or 0) if not isinstance(u, dict) else (lambda k: u.get(k) or 0)
    tin, tout, cr, cw = get("input_tokens"), get("output_tokens"), get("cache_read_input_tokens"), get("cache_creation_input_tokens")
    low, high = _price(model)
    p = high if tin + cr + cw > 100_000 else low
    usd = (tin * p[0] + tout * p[1] + cr * p[2] + cw * p[3]) / 1e6
    t = TOTAL.setdefault(model, {"calls": 0, "in": 0, "out": 0, "cr": 0, "cw": 0, "usd": 0.0})
    t["calls"] += 1; t["in"] += tin; t["out"] += tout; t["cr"] += cr; t["cw"] += cw; t["usd"] += usd

def _patch():
    try:
        from anthropic.resources.messages import Messages
    except Exception:
        return
    if getattr(Messages.create, "_metered", False): return
    orig = Messages.create
    def create(self, *a, **k):
        r = orig(self, *a, **k)
        try: record(getattr(r, "model", None) or k.get("model", ""), getattr(r, "usage", None))
        except Exception: pass
        return r
    create._metered = True
    Messages.create = create

def _report():
    if not TOTAL: return
    usd = sum(t["usd"] for t in TOTAL.values()); calls = sum(t["calls"] for t in TOTAL.values())
    print(f"meter: {JOB} made {calls} Claude calls, about ${usd:.4f}", file=sys.stderr)
    key = os.environ.get("DASH_KEY")
    try: base = json.load(open("docs/stats.json"))["url"].rstrip("/")
    except Exception: base = None
    if not (key and base): return
    rows = [{"job": JOB, "model": m, **{k: (round(v, 6) if k == "usd" else v) for k, v in t.items()}} for m, t in TOTAL.items()]
    try:
        req = Request(base + "/usage", data=json.dumps({"rows": rows}).encode(),
                      headers={"authorization": "Bearer " + key, "content-type": "application/json", "User-Agent": "JauntOut-meter/0.1"})
        urlopen(req, timeout=15).read()
    except Exception as ex:
        print(f"meter: couldn't report spend ({str(ex)[:60]})", file=sys.stderr)

_patch()
atexit.register(_report)
