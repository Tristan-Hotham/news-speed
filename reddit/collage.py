"""Reddit collage (r/dataisbeautiful): four maps of the days each newspaper took to print the news, light paper,
labels on paper or sea only. Run from the study root: python3 reddit/collage.py"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "code"))
import pandas as pd
import matplotlib.patheffects as pe
from figstyle import *

R = jload(f"{DATA}/results.json")
T = pd.read_csv(f"{DATA}/papers_events.csv", dtype={"lccn": str})
E = T[T.eligible].copy()
BINS = [(0, 1, "next day or sooner", "#7A1D12"), (2, 3, "2 to 3 days", "#B0301F"), (4, 7, "4 to 7 days", "#D9772B"),
        (8, 14, "8 to 14 days", "#D9A21E"), (15, 21, "15 to 21 days", "#8DA66B"), (22, 999, "22 days or more", "#3D6E9E")]
LAB = {"lincoln1865": "1865 · Lincoln is shot", "custer1876": "1876 · Custer falls at the Little Bighorn", "titanic1912": "1912 · The Titanic sinks", "pearl1941": "1941 · Pearl Harbor is attacked"}
HALO = [pe.withStroke(linewidth=4, foreground=SEAC)]
HALOP = [pe.withStroke(linewidth=4, foreground=PAPER)]


def col(d):
    for a, b, _, c in BINS:
        if a <= d <= b: return c


def pts(ax, d, proj, s):
    d = d.sort_values("days", ascending=False, na_position="first")
    nv = d[~d.reported]; x, y = proj(nv.lon.values, nv.lat.values)
    ax.scatter(x, y, s=s * 0.7, facecolors="#FFFDF6", edgecolors="#8C7B62", linewidths=0.9, zorder=6)
    rp = d[d.reported]; x, y = proj(rp.lon.values, rp.lat.values)
    ax.scatter(x, y, s=s, c=[col(v) for v in rp.days], edgecolors=INK, linewidths=0.5, zorder=7)


NOTE = {"lincoln1865": [(-3900, 380, f"Gold Hill, Nevada:\nthe next day,\n{R['ex']['gold_hill']['dist']:,} km from\nWashington", (R["ex"]["gold_hill"], -119.65, 39.31)),
                        (-3900, -520, f"Old Confederacy:\nmedian {R['lincoln_conf']['median']:.0f} days;\nelsewhere {R['lincoln_conf']['other_median']:.0f}", None)],
        "custer1876": [(-3900, 0, f"No paper had it for\n{R['events']['custer1876']['first_any_days']} days, then\n{R['custer']['first_day_n']} papers in\n{R['custer']['first_day_states']} states on 6 July", None)],
        "titanic1912": [(-3900, 0, f"{R['titanic']['day0_n']} papers in\n{R['titanic']['day0_states']} states printed\nit the day she sank", None)],
        "pearl1941": [(-3900, 0, f"Dailies: median\n{R['events']['pearl1941']['daily_median']:.0f} day; weeklies\n{R['events']['pearl1941']['weekly_median']:.0f} days", None)]}

fig = plt.figure(figsize=(24, 17), facecolor=PAPER)
fig.text(0.03, 0.972, "How fast did news travel?", fontproperties=DISP, fontsize=60, color=INK, va="top")
fig.text(0.03, 0.912, f"Days from each event to the first report in {R['source']['papers']:,} American newspapers. A daily printed Lincoln's death the next morning, just as fast as the Titanic or Pearl Harbor.\nThe weekly press day, not distance, set the pace.",
         fontproperties=FELLI, fontsize=25, color=MUT, va="top", linespacing=1.3)
W, Hh = 0.475, 0.33
pos = [(0.02, 0.458), (0.505, 0.458), (0.02, 0.07), (0.505, 0.07)]
for ev, (x0, y0) in zip(EV, pos):
    s = R["events"][ev]
    fig.text(x0 + 0.005, y0 + Hh + 0.034, LAB[ev], fontproperties=DISPB, fontsize=28, color=INK, va="bottom")
    dm = s["daily_median"]
    fig.text(x0 + 0.006, y0 + Hh + 0.008, f"Median wait: dailies {dm:.0f} day{'s' if dm != 1 else ''}, weeklies {s['weekly_median']:.0f} days", fontsize=16, color=MUT, va="bottom")
    ax = fig.add_axes([x0, y0, W, Hh])
    usmap(ax, xlim=(-4000, 2300), ylim=(-1750, 1600))
    d = E[(E.ev == ev) & E.lat.notna()]
    pts(ax, d[(d.lat < 50) & (d.lon > -130)], albers, 46)
    if ev in ("lincoln1865", "custer1876"):
        sx, sy = albers(EVENTS[ev]["site"][1], EVENTS[ev]["site"][0])
        ax.scatter([sx], [sy], marker="*", s=700, c="#FFFDF6", edgecolors=INK, linewidths=1.6, zorder=9)
    for tx, ty, t, link in NOTE[ev]:
        ax.text(tx, ty, t, fontsize=15, color=INK, va="center", ha="left", path_effects=HALO, zorder=12, linespacing=1.25)
        if link:
            px, py = albers(link[1], link[2])
            ax.plot([tx + 1150, px - 25], [ty + 250, py], color=INK, lw=1.1, zorder=11)
    for which, rect in (("Alaska", [x0 + 0.004, y0 + 0.004, 0.085, 0.08]), ("Hawaii", [x0 + 0.093, y0 + 0.004, 0.06, 0.045])):
        ia, p = inset(fig, rect, which)
        dd = d[d.state == which]
        if len(dd): pts(ia, dd, p, 30)

# legend on paper
lax = fig.add_axes([0, 0, 1, 1], zorder=10); lax.set_axis_off(); lax.set_xlim(0, 1); lax.set_ylim(0, 1)
x = 0.03; y = 0.03
lax.text(x, y + 0.0, "Days to the first report:", fontsize=17, color=INK, va="bottom", fontweight="bold"); x += 0.155
for a, b, lab, c in BINS:
    lax.scatter([x + 0.005], [y + 0.007], s=220, c=c, edgecolors=INK, linewidths=0.8)
    lax.text(x + 0.013, y, lab, fontsize=17, color=INK, va="bottom"); x += 0.024 + 0.0068 * len(lab)
lax.scatter([x + 0.005], [y + 0.007], s=160, facecolors="#FFFDF6", edgecolors="#8C7B62", linewidths=1.2)
lax.text(x + 0.013, y, "no report found", fontsize=17, color=INK, va="bottom")
lax.scatter([0.03 + 0.005], [0.012], marker="*", s=300, c="#FFFDF6", edgecolors=INK, linewidths=1)
lax.text(0.043, 0.006, "where it happened", fontsize=14, color=MUT, va="bottom")
fig.text(0.975, 0.006, "Data: American Stories (Dell et al. 2023, CC BY 4.0) from Chronicling America, Library of Congress; places Wikidata, GeoNames · Dr Tristan Hotham · maps.tristanhotham.com/news-speed",
         fontsize=13, color=MUT, ha="right", va="bottom")
out = os.path.join(ROOT, "reddit", "news_speed_collage.png")
fig.savefig(out, dpi=110, facecolor=PAPER)
print(out, Image.open(out).size)
