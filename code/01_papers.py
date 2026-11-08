"""Step 1: read the four event files, build one row per newspaper (lccn) with a title, a place and a state, and geocode
it from the city and state in its Library of Congress title, using Wikidata US places (the most populous place of
that name in that state). Writes WORK/pages.pkl (all rows) and data/newspapers.csv."""
import pandas as pd, unicodedata
from common import *

fr = []
for ev in EV:
    d = pd.read_csv(f"{RAW}/news_{ev}.tsv", sep="\t", dtype=str, keep_default_na=False, quoting=3)
    d["ev"] = ev
    fr.append(d)
pages = pd.concat(fr, ignore_index=True)
pages["page"] = pages.page.astype(int)
pages["hit"] = pages.hit.astype(int)
pages.to_pickle(f"{WORK}/pages.pkl")

# ---- Wikidata places
P = pd.read_csv(f"{RAW}/us_places.tsv", sep="\t", dtype=str, keep_default_na=False, quoting=3)
P.columns = ["item", "label", "wkt", "st", "stl", "pop"]
P["label"] = P.label.str.replace(r'^"(.*)"@en$', r"\1", regex=True)
P["stl"] = P.stl.str.replace(r'^"(.*)"@en$', r"\1", regex=True)
P["pop"] = pd.to_numeric(P["pop"], errors="coerce").fillna(0)
xy = P.wkt.str.extract(r"POINT\(([-0-9.eE]+) ([-0-9.eE]+)\)")
P["lon"] = xy[0].astype(float); P["lat"] = xy[1].astype(float)
P = P.dropna(subset=["lat"])


def norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"\bst\.?\s", "saint ", s); s = re.sub(r"\bmt\.?\s", "mount ", s); s = re.sub(r"\bft\.?\s", "fort ", s)
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


P["key"] = P.label.map(norm)
P["id"] = "wikidata:" + P.item.str.strip("<>").str.rsplit("/", n=1).str[-1]
# GeoNames US places with 500 or more people (cities500, CC BY 4.0), because the Wikidata extract lacks some large
# cities (Chicago, for one). Extracted from the geonamescache package by 00_gazetteer.py.
G = pd.read_csv(GN_US, sep="\t", dtype=str, keep_default_na=False, quoting=3)
G = pd.DataFrame(dict(label=G.name, stl=G.state, pop=pd.to_numeric(G.population, errors="coerce").fillna(0),
                      lat=G.lat.astype(float), lon=G.lon.astype(float), id="geonames:" + G.geonameid))
G["key"] = G.label.map(norm)
P = pd.concat([P[["label", "stl", "pop", "lat", "lon", "id", "key"]], G], ignore_index=True)
P = P.sort_values("pop", ascending=False)
IDX = {}
for r in P.itertuples():
    IDX.setdefault((r.stl, r.key), (r.lat, r.lon, r.label, int(r.pop), r.id))
# places Wikidata lists without a state label (Washington, D.C.) or historic names the gazetteer lacks
MANUAL = {("District of Columbia", "washington"): (DC[0], DC[1], "Washington", 0, "wikidata:Q61"),
          ("District of Columbia", "georgetown"): (38.9097, -77.0654, "Georgetown, Washington", 0, "manual")}

# ---- one row per newspaper
ABBR_RE = sorted(STATE_ABBR, key=len, reverse=True)


def state_from(place):
    place = re.sub(r"^\[(.*)\]$", r"\1", place)
    br = re.findall(r"\[(?:i\.e\. )?([^\]]+)\]", place)
    for cand in br[::-1] + [place.split(",")[-1] if "," in place else ""]:
        c = cand.strip().rstrip(". ;")
        c = re.sub(r"\s+Territory$", "", c)
        if c in REGION: return c
        for a in ABBR_RE:
            if c.rstrip(".") == a.rstrip("."): return STATE_ABBR[a]
    return ""


def city_from(place):
    p = place.replace("&#39;", "'").replace("&amp;", "&")
    m = re.match(r"^\[([^\]]+)\]", p)
    if m and "," not in m.group(1) and not p.startswith("[Silver"):
        pass
    p = re.sub(r"^\[([^\]]*)\]", r"\1", p)
    p = re.sub(r"([A-Za-z .]+?) \[i\.e\. ([^\]]+)\]", r"\2", p)
    p = re.sub(r"Washington \[Washington Court House\]", "Washington Court House", p)
    p = re.sub(r"\[(sic|Colony)\]\s*", "", p)
    p = re.sub(r"\[[^\]]*\]", "", p)
    c = p.split(",")[0].strip()
    m = re.match(r"^(.*?)\s+(S\.C\.|La\.)$", c)
    return m.group(1) if m else c


rows = []
for l, x in pages.groupby("lccn"):
    titles = [t for t in x.title.unique() if t]
    withp = [t for t in titles if re.search(r"\([^()]+\)\s*\d{4}", t) or re.search(r"\([^()]+\)\s*$", t)]
    title = (withp or titles or [""])[0]
    sts = x.state[x.state != ""].value_counts()
    st_col = sts.index[0] if len(sts) else ""
    m = re.findall(r"\(([^()]*(?:\[[^\]]*\])?[^()]*)\)", title)
    place = m[-1] if m else ""
    name = re.sub(r"\s*\[volume\]|\s*\[microfilm reel\]", "", title.split(" (")[0]).strip().rstrip(".")
    city, st_t, how = (city_from(place), state_from(place), "title") if place else ("", "", "")
    st = st_col or st_t
    if st_t and st_col and st_t != st_col:
        st = st_t                      # title place wins (e.g. a Chicago paper filed under Pennsylvania)
    if place == "D.C." or (city and st == "District of Columbia"):
        city = "Washington" if city in ("D.C.", "Washington City", "") else city
    rows.append(dict(lccn=l, title=title, name=name, place=place, city=city, state=st, how=how, events=" ".join(sorted(x.ev.unique(), key=EV.index))))
N = pd.DataFrame(rows)

STOP = set("the a an and of daily weekly semi tri evening morning sunday news times star sun press herald journal post record tribune "
           "gazette chronicle democrat republican courier register advertiser enterprise citizen review leader banner union "
           "independent bee era sentinel standard telegraph miner mirror argus examiner bulletin observer state county city "
           "new old free people workingman workingmans advocate globe call express dispatch eagle pioneer messenger reporter "
           "statesman transcript commercial guide future outlook index mail vidette record nugget".split())


# Old or local place names in the titles, looked up under their modern name (renamed towns, villages absorbed into a
# city, and spellings of the time). Each is a documented renaming or merger; papers whose town has vanished and is not in
# either gazetteer stay without a point.
ALIAS = {("Oregon", "saint johns"): "portland", ("Maryland", "leonard town"): "leonardtown",
         ("West Virginia", "charlestown"): "charles town", ("South Carolina", "yorkville"): "york",
         ("Maryland", "mechanicstown"): "thurmont", ("Virginia", "jeffersonville"): "tazewell",
         ("Ohio", "hillsborough"): "hillsboro", ("Pennsylvania", "allentaun"): "allentown", ("Pennsylvania", "laport"): "laporte",
         ("Tennessee", "sequachee"): "sequatchie", ("Maryland", "upper marlborough"): "upper marlboro",
         ("Louisiana", "bayou sara"): "saint francisville", ("Rhode Island", "olneyville"): "providence",
         ("Montana", "benton"): "fort benton", ("District of Columbia", "alexandria"): ("Virginia", "alexandria"), ("Maryland", "port tobacco"): "port tobacco village",
         ("Louisiana", "saint martinsville"): "saint martinville", ("Maryland", "towsontown"): "towson",
         ("Maryland", "frederick city"): "frederick", ("Nevada", "east ely"): "ely", ("Iowa", "new oregon"): "cresco",
         ("Nevada", "gold hill"): "virginia city"}   # Gold Hill adjoins Virginia City on the Comstock Lode, about 2 km apart


def geocode(city, st):
    k = norm(city)
    if (st, k) in ALIAS:
        a = ALIAS[(st, k)]
        if isinstance(a, tuple): st, k = a       # Alexandria, Virginia, part of the District until 1846
        else: k = a
    for kk in (k, re.sub(r" city$", "", k), re.sub(r" court house$| c h$", "", k), k + " city", k.replace("saint ", "st ")):
        if (st, kk) in MANUAL: return MANUAL[(st, kk)]
        if (st, kk) in IDX: return IDX[(st, kk)]
    return None


# Papers whose title gives no place and whose name matched the wrong town, checked against the Library of Congress
# catalogue record (place of publication): lccn -> (city, lat, lon, gazetteer id)
BY_LCCN = {"sn87052181": ("Ste. Genevieve", 37.9814, -90.0418, "wikidata:Q963578"),   # Fair play (Ste. Genevieve, Mo.), not Fair Play, Polk County
           "sn92070146": ("El Centro", 32.7920, -115.5631, "wikidata:Q506345")}      # Imperial Valley press (El Centro, Calif.)

out = []
for r in N.itertuples():
    g, how, city = None, r.how, r.city
    if city and r.state:
        g = geocode(city, r.state)
    st = r.state
    if st == "District of Columbia" and norm(city or "") == "alexandria":
        st = "Virginia"                  # Alexandria, part of the District only until 1846; in Virginia in all four windows
    if r.lccn in BY_LCCN:
        c, la, lo, q = BY_LCCN[r.lccn]
        g, how, city = (la, lo, c, None, q), "catalogue", c
    if g is None and r.state:
        # no place in the title (or no match): look for the longest place name of that state inside the paper's name
        words = norm(r.name).split()
        best = None
        for n in range(min(4, len(words)), 0, -1):
            for i in range(len(words) - n + 1):
                k = " ".join(words[i:i + n])
                if n == 1 and (k in STOP or len(k) < 4): continue
                if all(w in STOP for w in k.split()): continue
                if (r.state, k) in IDX and IDX[(r.state, k)][3] >= 200:
                    best = best or IDX[(r.state, k)]
            if best: break
        if best:
            g, how, city = best, "name", best[2]
    out.append(dict(r._asdict(), city=city, how=how if g else "none", lat=g[0] if g else None, lon=g[1] if g else None,
                    match=g[2] if g else "", qid=g[4] if g else "", pop=g[3] if g else None, state=st, region=REGION.get(st, "")))
N = pd.DataFrame(out).drop(columns=["Index"])
N.to_csv(f"{DATA}/newspapers.csv", index=False)
print(N.how.value_counts().to_dict(), len(N))
