#!/usr/bin/env python3
"""
Three-way merge of one conflicted JSON file during `git rebase` (used by .github/push.sh).

  base  = :1:<file>  (common ancestor)
  main  = :2:<file>  (what's on main now: someone else's commit, e.g. Raj's hand edits)
  bot   = :3:<file>  (this workflow's freshly generated version)

Merged entry by entry: dicts by key, lists of records by their "id" / "handle" (or "url"). Changes on both
sides are kept; where both changed the same field, the bot's newer value wins. Exits 1 if the file
isn't mergeable JSON, and push.sh then keeps the bot's version.
"""
import json, subprocess, sys

def stage(n, f):
    r = subprocess.run(["git", "show", f":{n}:{f}"], capture_output=True, text=True)
    return json.loads(r.stdout) if r.returncode == 0 and r.stdout.strip() else None

MISSING = object()
KEYS = ("id", "handle", "url")

def keyed(lst):
    if not isinstance(lst, list) or not lst or not all(isinstance(x, dict) for x in lst): return None
    for k in KEYS:
        if all(k in x for x in lst) and len({json.dumps(x[k]) for x in lst}) == len(lst): return k
    return None

def merge(base, main, bot):
    if main == bot: return main
    if base == main: return bot          # only the bot changed it
    if base == bot: return main          # only main changed it
    if isinstance(main, dict) and isinstance(bot, dict):
        b = base if isinstance(base, dict) else {}
        out = {}
        for k in list(main) + [k for k in bot if k not in main]:
            v = merge(b.get(k, MISSING), main.get(k, MISSING), bot.get(k, MISSING))
            if v is not MISSING: out[k] = v
        return out
    if isinstance(main, list) and isinstance(bot, list):
        k = keyed(main) or keyed(bot)
        if k and (keyed(main) in (k, None)) and (keyed(bot) in (k, None)):
            bl = base if isinstance(base, list) else []
            B = {json.dumps(x.get(k)): x for x in bl if isinstance(x, dict)}
            M = {json.dumps(x[k]): x for x in main}; T = {json.dumps(x[k]): x for x in bot}
            order = [i for i in T] + [i for i in M if i not in T]   # bot's order (it sorts), then main-only extras
            out = []
            for i in order:
                v = merge(B.get(i, MISSING), M.get(i, MISSING), T.get(i, MISSING))
                if v is not MISSING: out.append(v)
            return out
    return bot                            # both changed a plain value: the bot's is newer

def main():
    f = sys.argv[1]
    try: base, main_, bot = stage(1, f), stage(2, f), stage(3, f)
    except Exception as ex: print(f"merge_json: {f}: {ex}", file=sys.stderr); sys.exit(1)
    if main_ is None or bot is None: sys.exit(1)
    out = merge(base if base is not None else MISSING, main_, bot)
    with open(f, "w") as fh: json.dump(out, fh, indent=1, ensure_ascii=False)
    print(f"merge_json: merged {f}", file=sys.stderr)

if __name__ == "__main__":
    main()
