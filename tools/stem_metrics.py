"""The Birch Stem Tracer's measurements in Python, line for line from
tools/birch-stem-tracer.html (rdp, metrics, describe, summarize), so model
stems can be measured exactly like the hand traces.

    python tools/stem_metrics.py [reference/stem_traces.json] [bend_deg]
"""
import json
import math
import sys
from pathlib import Path

SIMPLIFY_FRAC = 0.004


def rdp(pts, eps):
    n = len(pts)
    if n < 3:
        return list(range(n))
    keep = [False] * n
    keep[0] = keep[n - 1] = True
    stack = [(0, n - 1)]
    while stack:
        a, b = stack.pop()
        ax, ay = pts[a]
        dx, dy = pts[b][0] - ax, pts[b][1] - ay
        ln = math.hypot(dx, dy) or 1
        max_d, idx = -1, -1
        for i in range(a + 1, b):
            d = abs((pts[i][0] - ax) * dy - (pts[i][1] - ay) * dx) / ln
            if d > max_d:
                max_d, idx = d, i
        if idx > 0 and max_d > eps:
            keep[idx] = True
            stack += [(a, idx), (idx, b)]
    return [j for j in range(n) if keep[j]]


def metrics(raw, bend):
    if not raw or len(raw) < 2:
        return None
    pts = list(raw)
    if pts[0][1] < pts[-1][1]:
        pts = pts[::-1]                      # base = lowest point in the image
    b, t = pts[0], pts[-1]
    cx, cy = t[0] - b[0], t[1] - b[1]
    L = math.hypot(cx, cy)
    if L < 1:
        return None
    S = sum(math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]) for i in range(1, len(pts)))
    max_dev = 0.0
    for p in pts:
        d = ((p[0] - b[0]) * cy - (p[1] - b[1]) * cx) / L
        if abs(d) > abs(max_dev):
            max_dev = d
    sp = [pts[k] for k in rdp(pts, max(SIMPLIFY_FRAC * L, 1))]
    turns = []
    for i in range(1, len(sp) - 1):
        v1x, v1y = sp[i][0] - sp[i - 1][0], sp[i][1] - sp[i - 1][1]
        v2x, v2y = sp[i + 1][0] - sp[i][0], sp[i + 1][1] - sp[i][1]
        turns.append(math.degrees(math.atan2(v1x * v2y - v1y * v2x, v1x * v2x + v1y * v2y)))
    bends = [a for a in turns if abs(a) >= bend]
    rev = sum(1 for i in range(1, len(bends)) if math.copysign(1, bends[i]) != math.copysign(1, bends[i - 1]))
    angles = [abs(a) for a in bends]
    return {
        "points": len(raw), "chord_px": L, "path_px": S,
        "max_offline_pct": abs(max_dev) / L * 100,
        "extra_length_pct": (S / L - 1) * 100,
        "total_turning_deg": sum(abs(a) for a in turns),
        "bends": len(bends), "bend_angles_deg": angles,
        "mean_bend_deg": sum(angles) / len(angles) if angles else None,
        "reversals": rev,
        "lean_deg": math.degrees(math.atan2(cx, -cy)),
    }


def quant(v, q):
    pos = (len(v) - 1) * q
    lo, hi = math.floor(pos), math.ceil(pos)
    return v[lo] + (v[hi] - v[lo]) * (pos - lo)


def describe(vals):
    v = sorted(x for x in vals if x is not None and math.isfinite(x))
    if not v:
        return None
    return {"median": quant(v, 0.5), "q1": quant(v, 0.25), "q3": quant(v, 0.75), "n": len(v)}


def summarize(rows):
    """rows: metrics dicts with a 'forked' flag (the tool's summarize, given its rows)."""
    col = lambda f: describe([f(m) for m in rows])  # noqa: E731
    return {
        "trunks": len(rows),
        "max_offline_pct": col(lambda m: m["max_offline_pct"]),
        "extra_length_pct": col(lambda m: m["extra_length_pct"]),
        "total_turning_deg": col(lambda m: m["total_turning_deg"]),
        "bends": col(lambda m: m["bends"]),
        "mean_bend_deg": col(lambda m: m["mean_bend_deg"]),
        "reversals": col(lambda m: m["reversals"]),
        "abs_lean_deg": col(lambda m: abs(m["lean_deg"])),
        "forked_share": (sum(1 for m in rows if m["forked"]) / len(rows)) if rows else None,
    }


def table(summ, label):
    def c(key, d):
        x = summ[key]
        return f"{x['median']:.{d}f} ({x['q1']:.{d}f}-{x['q3']:.{d}f})" if x else "-"
    print(f"{label}: {summ['trunks']} trunks")
    for name, key, d in (("Max off-line, % of length", "max_offline_pct", 1), ("Extra length, %", "extra_length_pct", 2),
                         ("Total turning, deg", "total_turning_deg", 0), ("Bends per trunk", "bends", 1),
                         ("Mean bend, deg", "mean_bend_deg", 1), ("S-curve reversals", "reversals", 1),
                         ("Lean from vertical, deg", "abs_lean_deg", 1)):
        print(f"  {name:28s} {c(key, d)}")
    if summ["forked_share"] is not None:
        print(f"  {'Forked':28s} {summ['forked_share'] * 100:.0f} %")


if __name__ == "__main__":
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / "reference" / "stem_traces.json"
    store = json.loads(path.read_text(encoding="utf-8"))
    bend = int((store.get("settings") or {}).get("bendDeg") or (sys.argv[2] if len(sys.argv) > 2 else 4))
    by_src = {}
    for key, rec in store["images"].items():
        rows = []
        for t in rec.get("trunks", []):
            m = metrics(t["pts"], bend)
            if m:
                m["forked"] = bool(t.get("forked"))
                rows.append(m)
        if rows:
            by_src.setdefault(rec.get("source", "photo"), []).extend(rows)
            print(f"{rec['name']} ({rec.get('source')}): {len(rows)} trunks")
    for src, rows in by_src.items():
        table(summarize(rows), f"{src}, bend threshold {bend} deg")
