"""Step 4: data/results.json, holding every number quoted on the page, in the paper, blog, README, collage and Reddit
post, with asserts for every fact stated in words. Also data/points.json for the map."""
import pandas as pd, numpy as np
from common import *

S = jload(f"{WORK}/stats.json")
T = pd.read_csv(f"{DATA}/papers_events.csv", dtype={"lccn": str})
N = pd.read_csv(f"{DATA}/newspapers.csv", dtype={"lccn": str})
pages = pd.read_pickle(f"{WORK}/pages.pkl")
H = pd.read_pickle(f"{WORK}/hits.pkl")
V = [l.rstrip("\n").split("\t") for l in open(os.path.join(ROOT, "code", "review_verdicts.tsv"), encoding="utf-8") if l.strip() and not l.startswith("#")]

R = {"events": {}}
R["source"] = dict(papers=int(N.lccn.nunique()), pages=int(len(pages)), hits=int((pages.hit == 1).sum()),
                   issues=int(pages.groupby(["ev", "lccn", "date"]).ngroups),
                   geocoded=int((N.how != "none").sum()), geocoded_pct=100 * float((N.how != "none").mean()),
                   geo_title=int((N.how == "title").sum()), geo_name=int(N.how.isin(["name", "catalogue"]).sum()), geo_catalogue=int((N.how == "catalogue").sum()), geo_none=int((N.how == "none").sum()),
                   
                   states=int(N.state[N.state != ""].nunique()))
R["review"] = dict(reviewed=len(V), rejected=sum(1 for v in V if v[4] == "no"), sample=60, sample_ok=59, sample_ambiguous=1)
for ev in EV:
    s = S[ev]
    s["year"] = EVENTS[ev]["year"]
    R["events"][ev] = s

L, C, Ti, P = (R["events"][e] for e in EV)
e = T[T.eligible & T.reported]


def ex(ev, lccn):
    r = e[(e.ev == ev) & (e.lccn == lccn)].iloc[0]
    return dict(name=r["name"], city=r.city, state=r.state, days=int(r.days), date=r.report_date, dist=int(r.dist_hub), cadence=r.cadence)


R["ex"] = dict(gold_hill=ex("lincoln1865", "sn84022046"), honolulu_titanic=ex("titanic1912", "sn82015415"),
               juneau=ex("pearl1941", "sn83045499"), benton=ex("custer1876", "sn84038126"), helena=ex("custer1876", "sn84036143"),
               bozeman=ex("custer1876", "sn84038123"), ny_sun_custer=ex("custer1876", "sn83030272"),
               marshall_tx=ex("lincoln1865", "sn84022871") if ((e.ev == "lincoln1865") & (e.lccn == "sn84022871")).any() else None,
               honolulu_lincoln=ex("lincoln1865", "sn82015418") if ((e.ev == "lincoln1865") & (e.lccn == "sn82015418")).any() else None)
# Lincoln in the old Confederacy against the Union states
conf = {"South Carolina", "Georgia", "Louisiana", "Texas", "Mississippi", "Alabama", "Virginia", "North Carolina", "Tennessee", "Arkansas", "Florida"}
lin = e[e.ev == "lincoln1865"]
R["lincoln_conf"] = dict(n=int(lin.state.isin(conf).sum()), median=float(lin[lin.state.isin(conf)].days.median()),
                         other_n=int((~lin.state.isin(conf) & (lin.state != "")).sum()),
                         other_median=float(lin[~lin.state.isin(conf) & (lin.state != "")].days.median()),
                         sc_n=int((lin.state == "South Carolina").sum()), sc_median=float(lin[lin.state == "South Carolina"].days.median()))
cu = e[e.ev == "custer1876"]
first_day = cu[cu.days == C["first_any_days"]]
east = {"New York", "District of Columbia", "Virginia", "Delaware", "West Virginia", "Ohio", "Indiana", "Wisconsin"}
R["custer"] = dict(first_day_n=int(len(first_day)), first_day_east=int(first_day.state.isin(east).sum()), first_day_states=int(first_day[first_day.state != "District of Columbia"].state.nunique()),
                   montana_n=int((cu.state == "Montana").sum()), montana_median=float(cu[cu.state == "Montana"].days.median()),
                   ny_days=int(C["first_any_days"]))
ti = e[e.ev == "titanic1912"]
R["titanic"] = dict(day0_n=int((ti.days == 0).sum()), day0_states=int(ti[ti.days == 0].state.nunique()),
                    west_day0=int(((ti.days == 0) & (ti.region == "West")).sum()))
# weekly cycle: median days for weeklies, all events
R["weekly_median"] = {ev: R["events"][ev]["weekly_median"] for ev in EV}
R["daily_median"] = {ev: R["events"][ev]["daily_median"] for ev in EV}
R["total_reported"] = int(sum(R["events"][ev]["reported"] for ev in EV))
R["total_eligible"] = int(sum(R["events"][ev]["eligible"] for ev in EV))

# ---- facts stated in words
assert L["daily_median"] == 1 and Ti["daily_median"] == 1 and P["daily_median"] == 1 and C["daily_median"] >= 10
assert C["first_any_days"] >= 10 and C["by10"] == 0
assert L["weekly_median"] > Ti["weekly_median"] and C["weekly_median"] > L["weekly_median"]
assert R["lincoln_conf"]["median"] > R["lincoln_conf"]["other_median"]
assert R["ex"]["gold_hill"]["days"] == 1 and R["ex"]["honolulu_titanic"]["days"] == 0 and R["ex"]["juneau"]["days"] == 0
assert R["ex"]["benton"]["days"] > R["ex"]["ny_sun_custer"]["days"] and R["custer"]["montana_median"] > C["median_days"]
assert abs(L["rho_daily"]) < 0.3 and L["rho_daily_p"] > 0.05 and Ti["rho_daily_p"] > 0.05
assert R["custer"]["first_day_east"] >= R["custer"]["first_day_n"] - 3
jsave(R, f"{DATA}/results.json", indent=1)

# ---- points for the map: one record per geocoded paper and event
pts = []
g = T[T.lat.notna()]
for r in g.itertuples():
    pts.append([round(r.lon, 4), round(r.lat, 4), EV.index(r.ev), int(r.days) if r.reported else -1, int(r.missed) if r.reported else -1,
                r.name if isinstance(r.name, str) else "", r.city if isinstance(r.city, str) else "", r.state if isinstance(r.state, str) else "",
                r.cadence, r.first_issue, r.report_date if isinstance(r.report_date, str) else "", r.lccn,
                int(r.page) if r.reported else 0, r.snippet if isinstance(r.snippet, str) else "", int(r.dist_hub), 1 if r.eligible else 0,
                1 if r.geo == "name" else 0, int(r.missed_since)])
ev_meta = {ev: dict(name=EVENTS[ev]["name"], short=EVENTS[ev]["short"], year=EVENTS[ev]["year"], day0=EVENTS[ev]["day0"], floor=EVENTS[ev]["floor"],
                    site=EVENTS[ev]["site"], site_name=EVENTS[ev]["site_name"], what=EVENTS[ev]["what"], age=EVENTS[ev]["age"],
                    hub=S[ev]["hub"], median=S[ev]["median_days"], daily_median=S[ev]["daily_median"], weekly_median=S[ev]["weekly_median"],
                    eligible=S[ev]["eligible"], reported=S[ev]["reported"]) for ev in EV}
jsave(dict(ev=EV, meta=ev_meta, p=pts, cum=jload(f"{DATA}/daily.json")), f"{DATA}/points.json")
print("results.json and points.json:", len(pts), "points")
