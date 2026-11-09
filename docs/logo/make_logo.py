import math
INK = {"light": "#1c2421", "dark": "#e6ebe5"}
WOOD = {"light": "#eef0e6", "dark": "#1b2220"}
GREEN = {"light": "#5f9a2a", "dark": "#8fc455"}
BARK = {"light": "#fbfbf8", "dark": "#d8dbd4"}

def wobbly(cx, cy, r, ecc=(0.0, 0.0), amp=0.035, ph=0.0, n=96):
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n
        rr = r * (1 + amp * math.sin(3 * t + ph) + amp * 0.6 * math.sin(5 * t + 1.7 * ph) + amp * 0.4 * math.sin(2 * t + 0.4))
        pts.append((cx + ecc[0] * r + rr * math.cos(t), cy + ecc[1] * r + rr * math.sin(t)))
    d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + " Z"
    return d

def rings(mode):
    ink, wood, green = INK[mode], WOOD[mode], GREEN[mode]
    c = (64, 64)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128" width="128" height="128">']
    out.append(f'<path d="{wobbly(*c, 58, amp=0.02, ph=0.3)}" fill="{ink}"/>')
    out.append(f'<path d="{wobbly(*c, 51.5, amp=0.02, ph=0.3)}" fill="{green}"/>')
    out.append(f'<path d="{wobbly(*c, 48, amp=0.02, ph=0.3)}" fill="{wood}"/>')
    for k, r in enumerate((40, 31.5, 23.5, 15.5)):
        f = r / 48
        out.append(f'<path d="{wobbly(c[0] - 6 * (1 - f), c[1] - 7 * (1 - f), r, amp=0.022 + 0.004 * k, ph=0.3 + 0.5 * k)}" fill="none" stroke="{ink}" stroke-width="{2.6 - 0.25 * k:.2f}" stroke-linejoin="round"/>')
    out.append(f'<circle cx="{c[0] - 6:.1f}" cy="{c[1] - 7:.1f}" r="3.2" fill="{ink}"/>')
    out.append("</svg>")
    return "\n".join(out)

def bark_c(mode):
    ink, bark, green = INK[mode], BARK[mode], GREEN[mode]
    cx, cy, R, W = 64, 66, 40, 24
    a0, a1 = math.radians(40), math.radians(320)
    def arc(r, s, e, sweep=1):
        x0, y0 = cx + r * math.cos(s), cy + r * math.sin(s)
        x1, y1 = cx + r * math.cos(e), cy + r * math.sin(e)
        large = 1 if (e - s) % (2 * math.pi) > math.pi else 0
        return x0, y0, x1, y1, large
    ro, ri = R + W / 2, R - W / 2
    x0, y0, x1, y1, lg = arc(ro, a0, a1)
    xi1, yi1, xi0, yi0, _ = arc(ri, a0, a1)
    d = f"M{x0:.1f},{y0:.1f} A{ro},{ro} 0 {lg} 1 {x1:.1f},{y1:.1f} L{xi0:.1f},{yi0:.1f} A{ri},{ri} 0 {lg} 0 {xi1:.1f},{yi1:.1f} Z"
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128" width="128" height="128">']
    out.append(f'<path d="{d}" fill="{bark}" stroke="{ink}" stroke-width="3" stroke-linejoin="round"/>')
    marks = [(70, 0.55, 9), (100, 0.35, 6), (128, 0.62, 11), (160, 0.42, 7), (190, 0.58, 10), (222, 0.38, 6), (250, 0.6, 9), (282, 0.45, 7)]
    for deg, frac, L in marks:
        t = math.radians(deg)
        r = ri + 3 + frac * (W - 6)
        px, py = cx + r * math.cos(t), cy + r * math.sin(t)
        tx, ty = -math.sin(t), math.cos(t)
        out.append(f'<line x1="{px - tx * L / 2:.1f}" y1="{py - ty * L / 2:.1f}" x2="{px + tx * L / 2:.1f}" y2="{py + ty * L / 2:.1f}" stroke="{ink}" stroke-width="3.2" stroke-linecap="round"/>')
    # a birch leaf growing from the upper tip of the C
    tipx, tipy = cx + R * math.cos(a1), cy + R * math.sin(a1)
    out.append(f'<path d="M{tipx + 2:.1f},{tipy - 8:.1f} q8,-16 26,-20 q-2,18 -20,24 z" fill="{green}" stroke="{ink}" stroke-width="2.5" stroke-linejoin="round"/>')
    out.append(f'<path d="M{tipx + 4:.1f},{tipy - 10:.1f} q9,-9 19,-14" fill="none" stroke="{ink}" stroke-width="1.6" stroke-linecap="round"/>')
    out.append("</svg>")
    return "\n".join(out)

def sprout(mode):
    ink, wood, green = INK[mode], WOOD[mode], GREEN[mode]
    c = (64, 80)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128" width="128" height="128">']
    # stem rising from the rings, with one birch leaf
    out.append(f'<path d="M64,44 C64,30 70,20 80,12" fill="none" stroke="{ink}" stroke-width="4" stroke-linecap="round"/>')
    out.append(f'<path d="M70,26 C58,24 48,14 47,4 C60,6 70,14 70,26 Z" fill="{green}" stroke="{ink}" stroke-width="2.6" stroke-linejoin="round"/>')
    out.append(f'<path d="M69,24 C62,18 56,12 51,7" fill="none" stroke="{ink}" stroke-width="1.5" stroke-linecap="round"/>')
    out.append(f'<path d="{wobbly(*c, 42, amp=0.02, ph=1.1)}" fill="{ink}"/>')
    out.append(f'<path d="{wobbly(*c, 36.5, amp=0.02, ph=1.1)}" fill="{green}"/>')
    out.append(f'<path d="{wobbly(*c, 33.5, amp=0.02, ph=1.1)}" fill="{wood}"/>')
    for k, r in enumerate((26, 18, 10.5)):
        f = r / 33.5
        out.append(f'<path d="{wobbly(c[0] - 4 * (1 - f), c[1] - 5 * (1 - f), r, amp=0.025, ph=0.9 + 0.6 * k)}" fill="none" stroke="{ink}" stroke-width="{2.3 - 0.2 * k:.2f}"/>')
    out.append(f'<circle cx="{c[0] - 4:.1f}" cy="{c[1] - 5:.1f}" r="2.6" fill="{ink}"/>')
    out.append("</svg>")
    return "\n".join(out)

for name, fn in (("rings", rings), ("barkc", bark_c), ("sprout", sprout)):
    for mode in ("light", "dark"):
        open(f"logo_{name}_{mode}.svg", "w", encoding="utf-8").write(fn(mode))
print("ok")
