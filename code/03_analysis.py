"""Step 3: for every newspaper and event, the first issue after the news could have arrived and the first issue that
reports it; days and issues missed; then the summaries quoted in the text. Writes data/papers_events.csv,
data/points.json (the map), data/daily.json (cumulative curves) and WORK/stats.json (read by 04_results.py)."""
import pandas as pd, numpy as np
from scipy.stats import spearmanr
from common import *

pages = pd.read_pickle(f"{WORK}/pages.pkl")
H = pd.read_pickle(f"{WORK}/hits.pkl")
N = pd.read_csv(f"{DATA}/newspapers.csv", dtype={"lccn": str}).set_index("lccn")
HUB = {"lincoln1865": DC, "custer1876": EVENTS["custer1876"]["site"], "titanic1912": NYC, "pearl1941": DC}
HUB_NAME = {"lincoln1865": "Washington", "custer1876": "the battlefield", "titanic1912": "New York", "pearl1941": "Washington"}
WINDOW = 14     # a paper counts if it has a digitised issue within 14 days of the floor date


def clean(s):
    s = str(s).replace("&#39;", "'").replace("&amp;", "&")
    if "\\u" in s:
        try:
            s = s.encode("latin-1", "backslashreplace").decode("unicode_escape").encode("latin-1").decode("utf-8")
        except Exception:
            s = re.sub(r"\\u[0-9a-f]{4}", "", s)
    return s


rows = []
for ev in EV:
    E = EVENTS[ev]
    d0, fl = pd.Timestamp(E["day0"]), pd.Timestamp(E["floor"])
    P = pages[pages.ev == ev]
    issues = P.groupby("lccn").date.apply(lambda s: sorted(set(s)))
    X = H[(H.ev == ev) & H.event].sort_values(["date", "page"])
    first = X.groupby("lccn").first()
    nev = X.groupby(["lccn", "date"]).size()
    loose = H[(H.ev == ev) & H.after_floor].sort_values(["date", "page"]).groupby("lccn").first()
    for l, ds in issues.items():
        ds = [pd.Timestamp(d) for d in ds]
        after = [d for d in ds if d >= fl]
        if not after:
            continue
        gaps = np.diff([d.toordinal() for d in ds])
        gap = float(np.median(gaps)) if len(gaps) else None
        cad = "daily" if gap is not None and gap <= 2 else ("weekly" if gap is not None and gap >= 5 else ("several a week" if gap else "unknown"))
        rep = pd.Timestamp(first.loc[l, "date"]) if l in first.index else None
        lrep = pd.Timestamp(loose.loc[l, "date"]) if l in loose.index else None
        n = N.loc[l] if l in N.index else None
        lat = n.lat if n is not None and pd.notna(n.lat) else None
        lon = n.lon if n is not None and pd.notna(n.lon) else None
        r = dict(ev=ev, lccn=l, name=clean(n["name"]) if n is not None else "", city=clean(n.city) if n is not None and pd.notna(n.city) else "",
                 state=n.state if n is not None and pd.notna(n.state) else "", region=n.region if n is not None and pd.notna(n.region) else "",
                 lat=lat, lon=lon, geo=n.how if n is not None else "none",
                 n_issues=len(ds), first_issue=after[0].date().isoformat(), eligible=(after[0] - fl).days < WINDOW,
                 cadence=cad, gap=gap, reported=rep is not None,
                 report_date=rep.date().isoformat() if rep is not None else "",
                 days=(rep - d0).days if rep is not None else None,
                 wait=(rep - after[0]).days if rep is not None else None,
                 missed=sum(1 for d in after if rep is not None and d < rep) if rep is not None else sum(1 for d in after),
                 missed_since=sum(1 for d in ds if d > d0 and (rep is None or d < rep)),
                 loose_days=(lrep - d0).days if lrep is not None else None,
                 pages_event=int(nev.loc[l].sum()) if l in nev.index.get_level_values(0) else 0,
                 snippet=clean(first.loc[l, "text"])[:200] if rep is not None else "",
                 page=int(first.loc[l, "page"]) if rep is not None else None,
                 dist_site=round(hav((lat, lon), E["site"])) if lat is not None else None,
                 dist_hub=round(hav((lat, lon), HUB[ev])) if lat is not None else None)
        rows.append(r)
T = pd.DataFrame(rows)
T.to_csv(f"{DATA}/papers_events.csv", index=False)

S = {}
for ev in EV:
    E = EVENTS[ev]
    t = T[T.ev == ev]
    e = t[t.eligible]
    rep = e[e.reported]
    dd = rep.days
    s = dict(papers=int(t.lccn.nunique()), eligible=int(len(e)), reported=int(len(rep)), reported_pct=100 * len(rep) / len(e),
             issues=int(pages[pages.ev == ev].groupby(["lccn", "date"]).ngroups), pages=int(len(pages[pages.ev == ev])),
             hits=int((H.ev == ev).sum()), event_pages=int(H[(H.ev == ev)].event.sum()),
             median_days=float(dd.median()), p25=float(dd.quantile(.25)), p75=float(dd.quantile(.75)),
             first_any=rep.report_date.min(), first_any_days=int(dd.min()),
             daily_n=int((e.cadence == "daily").sum()), weekly_n=int((e.cadence == "weekly").sum()),
             daily_median=float(rep[rep.cadence == "daily"].days.median()) if (rep.cadence == "daily").any() else None,
             weekly_median=float(rep[rep.cadence == "weekly"].days.median()) if (rep.cadence == "weekly").any() else None,
             first_issue_pct=100 * float((rep.missed == 0).mean()),
             daily_first_issue_pct=100 * float((rep[rep.cadence == "daily"].missed == 0).mean()) if (rep.cadence == "daily").any() else None,
             missed_median=float(rep.missed.median()), missed_since_median=float(rep.missed_since.median()),
             weekly_missed_since_median=float(rep[rep.cadence == "weekly"].missed_since.median()),
             daily_missed_since_median=float(rep[rep.cadence == "daily"].missed_since.median()), wait_median=float(rep.wait.median()),
             loose_median=float(e[e.loose_days.notna()].loose_days.median()))
    for k in (0, 1, 2, 3, 5, 7, 10, 14, 21):
        s[f"by{k}"] = 100 * float((e.days <= k).sum()) / len(e)
    # distance and delay among geocoded papers that report it
    g = rep[rep.dist_hub.notna()]
    s["geo_n"] = int(len(g))
    rho, p = spearmanr(g.dist_hub, g.days)
    s["rho"], s["rho_p"] = float(rho), float(p)
    gd = g[g.cadence == "daily"]
    if len(gd) > 8:
        rho, p = spearmanr(gd.dist_hub, gd.days)
        s["rho_daily"], s["rho_daily_p"], s["geo_daily_n"] = float(rho), float(p), int(len(gd))
    bands = [(0, 500), (500, 1000), (1000, 2000), (2000, 3500), (3500, 99999)]
    s["bands"] = {f"{a}-{b}": dict(n=int(((g.dist_hub >= a) & (g.dist_hub < b)).sum()),
                                   median=float(g[(g.dist_hub >= a) & (g.dist_hub < b)].days.median()) if ((g.dist_hub >= a) & (g.dist_hub < b)).sum() else None)
                  for a, b in bands}
    s["regions"] = {r: dict(n=int((rep.region == r).sum()), median=float(rep[rep.region == r].days.median()) if (rep.region == r).any() else None)
                    for r in ("Northeast", "South", "Midwest", "West")}
    s["hub"] = HUB_NAME[ev]
    S[ev] = s
    print(ev, {k: (round(v, 1) if isinstance(v, float) else v) for k, v in s.items() if k not in ("bands", "regions")})
    print("   bands", s["bands"]); print("   regions", s["regions"])

# cumulative share reported by day, for the curves (all eligible papers)
CUM = {}
for ev in EV:
    e = T[(T.ev == ev) & T.eligible]
    mx = 45
    CUM[ev] = [round(100 * float((e.days <= k).sum()) / len(e), 2) for k in range(mx + 1)]
jsave(CUM, f"{DATA}/daily.json")
jsave(S, f"{WORK}/stats.json", indent=1)

# examples: earliest far papers and notable cases
for ev in EV:
    t = T[(T.ev == ev) & T.eligible & T.reported & T.dist_hub.notna()].sort_values(["days", "dist_hub"], ascending=[True, False])
    print("==", ev, "fast and far")
    print(t[["name", "city", "state", "report_date", "days", "cadence", "dist_hub", "missed"]].head(8).to_string())
    print("   slow and near (daily)")
    u = T[(T.ev == ev) & T.eligible & T.reported & (T.cadence == "daily")].sort_values("days", ascending=False)
    print(u[["name", "city", "state", "report_date", "days", "dist_hub", "missed", "first_issue"]].head(6).to_string())
