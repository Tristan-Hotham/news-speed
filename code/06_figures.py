"""Step 6: figures. Blog (release/blog/b_*.png), paper (release/paper/f_*), page (img/*.png) and the social card
(header.png, 1200 x 630). Numbers from data/results.json and data/papers_events.csv."""
import pandas as pd
import matplotlib.patheffects as pe
from matplotlib.lines import Line2D
from figstyle import *

R = jload(f"{DATA}/results.json")
T = pd.read_csv(f"{DATA}/papers_events.csv", dtype={"lccn": str})
E = T[T.eligible].copy()
BL = os.path.join(ROOT, "release", "blog"); PA = os.path.join(ROOT, "release", "paper"); IM = os.path.join(ROOT, "img")
for d in (BL, PA, IM):
    os.makedirs(d, exist_ok=True)
HALO = [pe.withStroke(linewidth=3, foreground=PAPER)]
BINS = [(0, 1, "next day or sooner", "#7A1D12"), (2, 3, "2 to 3 days", "#B0301F"), (4, 7, "4 to 7 days", "#D9772B"),
        (8, 14, "8 to 14 days", "#D9A21E"), (15, 21, "15 to 21 days", "#8DA66B"), (22, 999, "22 days or more", "#3D6E9E")]
NEVER = "not found in the window"
EVC = {ev: EVENTS[ev]["colour"] for ev in EV}
EVC["pearl1941"] = "#B07A10"
LAB = {"lincoln1865": "Lincoln shot, 1865", "custer1876": "Little Bighorn, 1876", "titanic1912": "Titanic, 1912", "pearl1941": "Pearl Harbor, 1941"}
PHOTO = {"maps"}


def bincol(d):
    if pd.isna(d): return None
    for a, b, _, c in BINS:
        if a <= d <= b: return c


def save(fig, name, page=True):
    if name in PHOTO:
        fig.savefig(f"{WORK}/tmp.png", dpi=200, facecolor=fig.get_facecolor())
        Image.open(f"{WORK}/tmp.png").convert("RGB").save(os.path.join(PA, "f_" + name + ".jpg"), quality=85, optimize=True)
        os.remove(f"{WORK}/tmp.png")
    else:
        fig.savefig(os.path.join(PA, "f_" + name + ".png"), dpi=200, facecolor=fig.get_facecolor())
    fig.savefig(os.path.join(BL, "b_" + name + ".png"), dpi=150, facecolor=fig.get_facecolor())
    if page:
        fig.savefig(os.path.join(IM, name + ".png"), dpi=116.67, facecolor=fig.get_facecolor())
    plt.close(fig)


def title(fig, t, sub=None, y=0.965):
    fig.text(0.03, y, t, fontproperties=DISP, fontsize=24, color=INK, va="top")
    if sub:
        fig.text(0.03, y - 0.055, sub, fontproperties=FELLI, fontsize=15, color=MUT, va="top")


def credit(fig, t="Data: American Stories (Dell et al. 2023) from Chronicling America, Library of Congress · maps.tristanhotham.com/news-speed", y=0.012):
    fig.text(0.97, y, t, fontsize=8.5, color=MUT, ha="right", va="bottom")


def plot_points(ax, d, proj, s=16):
    d = d.sort_values("days", ascending=False, na_position="first")
    nv = d[~d.reported]
    x, y = proj(nv.lon.values, nv.lat.values)
    ax.scatter(x, y, s=s * 0.7, facecolors="#FFFDF6", edgecolors="#8C7B62", linewidths=0.7, zorder=6)
    rp = d[d.reported]
    x, y = proj(rp.lon.values, rp.lat.values)
    ax.scatter(x, y, s=s, c=[bincol(v) for v in rp.days], edgecolors=INK, linewidths=0.4, zorder=7)


def legend(fig, y=0.03, x0=0.03, fs=10.5):
    lax = fig.add_axes([0, 0, 1, 1], zorder=10); lax.set_axis_off(); lax.set_xlim(0, 1); lax.set_ylim(0, 1)
    x = x0
    for a, b, lab, c in BINS:
        lax.scatter([x + 0.006], [y + 0.009], s=70, c=c, edgecolors=INK, linewidths=0.5)
        lax.text(x + 0.016, y, lab, fontsize=fs, color=INK, va="bottom"); x += 0.03 + 0.0072 * len(lab)
    lax.scatter([x + 0.006], [y + 0.009], s=50, facecolors="#FFFDF6", edgecolors="#8C7B62", linewidths=0.8)
    lax.text(x + 0.016, y, NEVER, fontsize=fs, color=INK, va="bottom")


# ---------------------------------------------------------------- 1. four maps
def four_maps(fig, top=0.86, bottom=0.08, insets=True, sub=True):
    W, Hh = 0.47, (top - bottom) / 2 - 0.02
    pos = [(0.02, bottom + Hh + 0.03), (0.51, bottom + Hh + 0.03), (0.02, bottom), (0.51, bottom)]
    for ev, (x0, y0) in zip(EV, pos):
        ax = fig.add_axes([x0, y0, W, Hh])
        usmap(ax)
        d = E[(E.ev == ev) & E.lat.notna()]
        conus = d[(d.lat < 50) & (d.lon > -130)]
        plot_points(ax, conus, albers, s=13)
        sx, sy = albers(*EVENTS[ev]["site"][::-1]) if ev != "titanic1912" and ev != "pearl1941" else (None, None)
        if sx is not None:
            ax.scatter([sx], [sy], marker="*", s=230, c="#FFFDF6", edgecolors=INK, linewidths=1.1, zorder=9)
        s = R["events"][ev]
        ax.text(0.02, 0.97, LAB[ev], transform=ax.transAxes, fontproperties=DISPB, fontsize=15, color=INK, va="top", path_effects=HALO, zorder=12)
        if sub:
            dm = s['daily_median']
            ax.text(0.02, 0.885, f"median {dm:.0f} day{'s' if dm != 1 else ''} for dailies, {s['weekly_median']:.0f} for weeklies",
                    transform=ax.transAxes, fontsize=9.5, color=MUT, va="top", path_effects=HALO, zorder=12)
        if insets:
            for which, rect in (("Alaska", [x0 + 0.005, y0 + 0.005, 0.075, 0.075]), ("Hawaii", [x0 + 0.083, y0 + 0.005, 0.05, 0.04])):
                ia, p = inset(fig, rect, which)
                dd = d[d.state == which]
                if len(dd):
                    plot_points(ia, dd, p, s=10)


fig = plt.figure(figsize=(13, 9.6), facecolor=PAPER)
title(fig, "How fast did the news reach each newspaper?", "Days from the event to the first digitised issue that reports it. Each dot is one newspaper. The star marks where it happened.")
four_maps(fig)
legend(fig)
credit(fig, y=0.003)
save(fig, "maps")

# ---------------------------------------------------------------- 2. cumulative curves
CUM = jload(f"{DATA}/daily.json")
fig = plt.figure(figsize=(12, 6.8), facecolor=PAPER)
title(fig, "Share of newspapers that had printed the news", "Cumulative share of the papers with an issue in the first fortnight, by days after the event")
ax = fig.add_axes([0.07, 0.13, 0.88, 0.67]); ax.set_facecolor(PAPER); spines(ax)
for ev in EV:
    y = CUM[ev][:36]
    ax.plot(range(len(y)), y, color=EVC[ev], lw=2.6, solid_capstyle="round")
    k = 35
    ax.text(k + 0.4, y[k], LAB[ev], color=EVC[ev], fontsize=11.5, va="center", fontweight="bold", path_effects=HALO)
ax.set_xlim(0, 42); ax.set_ylim(0, 100); ax.set_xticks(range(0, 36, 7))
ax.set_xlabel("days after the event"); ax.set_ylabel("% of newspapers")
ax.grid(axis="y", color=RULE, lw=0.8); ax.set_axisbelow(True)
ax.text(0.8, 97, "Most papers were weeklies, so the curves\nclimb in steps as each press day comes round", fontsize=10.5, color=MUT, va="top")
ax.annotate(f"no paper in the sample has Custer\nuntil day {R['events']['custer1876']['first_any_days']}", xy=(R["events"]["custer1876"]["first_any_days"], 1), xytext=(13, 8),
            fontsize=10.5, color=MUT, arrowprops=dict(arrowstyle="-", color=MUT, lw=0.8))
credit(fig)
save(fig, "curves")

# ---------------------------------------------------------------- 3. daily against weekly
fig = plt.figure(figsize=(12, 5.6), facecolor=PAPER)
title(fig, "Dailies had it the next day; weeklies waited for press day", "Median days from the event to the first report, by how often the paper came out")
ax = fig.add_axes([0.2, 0.14, 0.75, 0.62]); ax.set_facecolor(PAPER); spines(ax)
for i, ev in enumerate(EV[::-1]):
    s = R["events"][ev]
    ax.plot([s["daily_median"], s["weekly_median"]], [i, i], color=RULE, lw=6, solid_capstyle="round", zorder=1)
    ax.scatter([s["daily_median"]], [i], s=170, c=EVC[ev], edgecolors=INK, zorder=3)
    ax.scatter([s["weekly_median"]], [i], s=170, c="#FFFDF6", edgecolors=EVC[ev], linewidths=2.2, zorder=3)
    ax.text(s["daily_median"], i + 0.27, f"daily {s['daily_median']:.0f}", ha="center", fontsize=10, color=INK)
    ax.text(s["weekly_median"], i + 0.27, f"weekly {s['weekly_median']:.0f}", ha="center", fontsize=10, color=INK)
ax.set_yticks(range(4)); ax.set_yticklabels([LAB[e] for e in EV[::-1]], fontsize=12)
ax.set_xlim(-1, 21); ax.set_ylim(-0.5, 3.6); ax.set_xlabel("median days after the event")
ax.grid(axis="x", color=RULE, lw=0.8); ax.set_axisbelow(True)
credit(fig)
save(fig, "cadence")

# ---------------------------------------------------------------- 4. distance against delay
fig = plt.figure(figsize=(12, 8.2), facecolor=PAPER)
title(fig, "Distance mattered less than the printing day", "Days to the first report against distance from where the news entered the wires. Filled: dailies; open: weeklies and others.")
for k, ev in enumerate(EV):
    ax = fig.add_axes([0.07 + 0.48 * (k % 2), 0.53 - 0.42 * (k // 2), 0.4, 0.29]); ax.set_facecolor(PAPER); spines(ax)
    d = E[(E.ev == ev) & E.reported & E.dist_hub.notna()]
    dl = d[d.cadence == "daily"]; ot = d[d.cadence != "daily"]
    rng = np.random.default_rng(1)
    ax.scatter(ot.dist_hub, ot.days + rng.uniform(-0.25, 0.25, len(ot)), s=14, facecolors="none", edgecolors=EVC[ev], linewidths=0.8, alpha=0.75)
    ax.scatter(dl.dist_hub, dl.days + rng.uniform(-0.25, 0.25, len(dl)), s=22, c=EVC[ev], edgecolors=INK, linewidths=0.4)
    ax.set_ylim(-1, 42 if ev == "custer1876" else 30); ax.set_xlim(0, 8300)
    ax.set_title(f"{LAB[ev]}: from {R['events'][ev]['hub']}", loc="left", fontsize=12, color=INK, fontweight="bold")
    ax.grid(color=RULE, lw=0.6); ax.set_axisbelow(True)
    if k // 2: ax.set_xlabel("distance, km")
    if k % 2 == 0: ax.set_ylabel("days")
credit(fig)
save(fig, "distance")

# ---------------------------------------------------------------- 5. Lincoln: Union against the former Confederacy
CONF = {"South Carolina", "Georgia", "Louisiana", "Texas", "Mississippi", "Alabama", "Virginia", "North Carolina", "Tennessee", "Arkansas", "Florida"}
d = E[(E.ev == "lincoln1865") & E.reported & (E.state.fillna("") != "")].copy()
d["conf"] = d.state.isin(CONF)
st = d.groupby("state").days.median().sort_values()
fig = plt.figure(figsize=(12, 9), facecolor=PAPER)
title(fig, "Lincoln's death reached the old Confederacy last", "Days from 14 April 1865 to each paper's first report, by state. Red: states of the former Confederacy.")
ax = fig.add_axes([0.22, 0.1, 0.74, 0.74]); ax.set_facecolor(PAPER); spines(ax)
for i, s_ in enumerate(st.index):
    x = d[d.state == s_].days.values
    c = "#A3261B" if s_ in CONF else "#3D6E9E"
    ax.scatter(x, np.full(len(x), i) + np.random.default_rng(i).uniform(-0.18, 0.18, len(x)), s=26, c=c, edgecolors=INK, linewidths=0.4, alpha=0.9)
ax.set_yticks(range(len(st))); ax.set_yticklabels(st.index, fontsize=9.5)
ax.set_xlabel("days after the shooting"); ax.grid(axis="x", color=RULE, lw=0.6); ax.set_axisbelow(True)
ax.set_ylim(-0.7, len(st) - 0.3)
credit(fig)
save(fig, "lincoln")

# ---------------------------------------------------------------- 6. Custer timeline
d = E[(E.ev == "custer1876") & E.reported].copy()
d["rd"] = pd.to_datetime(d.report_date)
fig = plt.figure(figsize=(12, 6.2), facecolor=PAPER)
title(fig, "Custer: eleven days of silence, then the wires carried it everywhere", "First reports of the Little Bighorn by date, coloured by region of the newspaper")
ax = fig.add_axes([0.07, 0.13, 0.9, 0.62]); ax.set_facecolor(PAPER); spines(ax)
REGC = {"Northeast": "#3D6E9E", "South": "#A3261B", "Midwest": "#D9A21E", "West": "#55803A", "": "#9C8656"}
days = pd.date_range("1876-06-25", "1876-08-20")
bottom = np.zeros(len(days))
for reg in ["Northeast", "South", "Midwest", "West", ""]:
    cnt = d[d.region.fillna("") == reg].rd.value_counts().reindex(days, fill_value=0).values
    ax.bar(days, cnt, bottom=bottom, color=REGC[reg], edgecolor=PAPER, lw=0.4, width=0.85, label=reg or "place unknown")
    bottom += cnt
ax.axvline(pd.Timestamp("1876-06-25"), color=INK, lw=1); ax.text(pd.Timestamp("1876-06-25"), bottom.max() * 0.95, " the battle, 25 June", fontsize=10.5, color=INK, va="top")
ax.legend(frameon=False, fontsize=10.5, loc="upper right")
ax.set_ylabel("papers reporting for the first time"); ax.grid(axis="y", color=RULE, lw=0.6); ax.set_axisbelow(True)
import matplotlib.dates as mdates
ax.xaxis.set_major_formatter(mdates.DateFormatter("%-d %b")); ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=0))
credit(fig)
save(fig, "custer")

# ---------------------------------------------------------------- header card
fig = plt.figure(figsize=(12, 6.3), facecolor=PAPER)
fig.text(0.035, 0.93, "How fast did news travel?", fontproperties=DISP, fontsize=40, color=INK, va="top")
fig.text(0.035, 0.80, "Lincoln, Custer, the Titanic and Pearl Harbor in the pages of America's newspapers", fontproperties=FELLI, fontsize=17, color=MUT, va="top")
for k, ev in enumerate(EV):
    ax = fig.add_axes([0.01 + 0.245 * k, 0.12, 0.24, 0.55]); usmap(ax, xlim=(-2400, 2300), ylim=(-1650, 1600), neighbours=False)
    dd = E[(E.ev == ev) & E.lat.notna() & (E.lat < 50) & (E.lon > -130)]
    plot_points(ax, dd, albers, s=7)
    ax.text(0.5, -0.04, LAB[ev], transform=ax.transAxes, ha="center", va="top", fontproperties=DISPB, fontsize=14, color=INK)
fig.text(0.035, 0.035, "Dr Tristan Hotham · maps.tristanhotham.com/news-speed", fontsize=11, color=MUT)
fig.savefig(os.path.join(ROOT, "header.png"), dpi=100, facecolor=PAPER)
plt.close(fig)
print("figures done")
