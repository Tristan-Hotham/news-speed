"""Shared paths, events and helpers for the news-speed study ("How fast did news travel?").

Raw inputs (read in place, never modified):
  NEWS  /home/claude/newdata/raw_new8/news_<event>.tsv  for event in lincoln1865, custer1876, titanic1912, pearl1941.
        Built from the American Stories dataset (Dell et al. 2023, Harvard; structured OCR text of the Library of
        Congress Chronicling America page scans, CC BY 4.0). Every digitised page in a window after each event.
        Columns: lccn, title (usually ends "(City, State) years"), state, date, page, hit (1 when the page text matched
        the event's name pattern: Lincoln, Custer, Titanic, Pearl Harbor), snippet (about 180 characters around the
        first match). Pages without a hit are collapsed to one row per newspaper and date.
  PLACES /home/claude/newdata/raw_new8/us_places.tsv  Wikidata US cities, towns and villages (item, label, WKT point,
        state, state label, population), CC0. Used to geocode each newspaper from the city and state in its title.
  GN_US US rows of GeoNames cities500 (CC BY 4.0), taken from the geonamescache 3.0.2 package on PyPI by
        00_gazetteer.py; a fallback gazetteer for cities the Wikidata extract lacks.
  GEO   /home/claude/newdata/raw/geo/  Natural Earth (public domain) for the static figures.
  FONTS /home/claude/ref/fonts (Fraunces, Source Serif 4, IBM Plex Mono); the Inked World lettering fonts in fonts/ttf
"""
import json, gzip, os, re, math

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.environ.get("NS_RAW", "/home/claude/newdata/raw_new8")
GN_US = os.environ.get("NS_GN", "/home/claude/work/new8/news-speed/work/geonames_us_cities500.tsv")
GEO = os.environ.get("NS_GEO", "/home/claude/newdata/raw/geo")
FONTS = os.environ.get("NS_FONTS", "/home/claude/ref/fonts")
INKFONTS = os.path.join(ROOT, "fonts", "ttf")
DATA = os.path.join(ROOT, "data")
WORK = os.environ.get("NS_WORK", "/home/claude/work/new8/news-speed/work")   # intermediates, not in the repo
for d in (DATA, WORK):
    os.makedirs(d, exist_ok=True)

SLUG = "news-speed"
PAGE = f"https://maps.tristanhotham.com/{SLUG}/"
REPO = f"https://github.com/Tristan-Hotham/{SLUG}"
TITLE = "How fast did news travel?"
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")
CA_PAGE = "https://chroniclingamerica.loc.gov/lccn/{lccn}/{date}/ed-1/seq-{page}/"

# The four events. day0 is the calendar date of the event itself; "days" everywhere are calendar days after day0.
# floor: the first date on which a newspaper could possibly have printed the news (earlier "hits" are other stories).
# site: where it happened (lat, lon). Washington, D.C. is also the news hub for 1865 and 1941.
EVENTS = {
    "lincoln1865": dict(name="Lincoln is shot", short="Lincoln", year=1865, day0="1865-04-14", floor="1865-04-15",
                        site=(38.8967, -77.0257), site_name="Ford's Theatre, Washington", colour="#2B2119",
                        what="President Abraham Lincoln was shot at Ford's Theatre in Washington on the evening of 14 April 1865 and died the next morning.",
                        age="Telegraph era"),
    "custer1876": dict(name="Custer falls at the Little Bighorn", short="Little Bighorn", year=1876, day0="1876-06-25",
                       floor="1876-07-03", site=(45.5703, -107.4276), site_name="Little Bighorn battlefield, Montana Territory", colour="#A3261B",
                       what="Lieutenant Colonel George Armstrong Custer and about 260 men of the 7th Cavalry were killed at the Little Bighorn on 25 June 1876, in Montana Territory, far from any telegraph.",
                       age="Telegraph era, frontier"),
    "titanic1912": dict(name="The Titanic sinks", short="Titanic", year=1912, day0="1912-04-15", floor="1912-04-15",
                        site=(41.7325, -49.9469), site_name="Titanic wreck site, North Atlantic", colour="#3D6E9E",
                        what="RMS Titanic struck an iceberg late on 14 April 1912 and sank in the early hours of 15 April; news came ashore by wireless.",
                        age="Wireless and wire services"),
    "pearl1941": dict(name="Pearl Harbor is attacked", short="Pearl Harbor", year=1941, day0="1941-12-07", floor="1941-12-07",
                      site=(21.3649, -157.9507), site_name="Pearl Harbor, Oahu, Territory of Hawaii", colour="#D9A21E",
                      what="Japanese aircraft attacked the US Pacific Fleet at Pearl Harbor on the morning of Sunday 7 December 1941; the news was broadcast on radio that afternoon.",
                      age="Radio era"),
}
EV = list(EVENTS)
DC = (38.8951, -77.0364)
NYC = (40.7128, -74.0060)

STATE_ABBR = {
    "Ala": "Alabama", "Ariz": "Arizona", "Ark": "Arkansas", "Cal": "California", "Calif": "California", "Colo": "Colorado",
    "Conn": "Connecticut", "Del": "Delaware", "D.C": "District of Columbia", "DC": "District of Columbia", "Fla": "Florida",
    "Ga": "Georgia", "Ill": "Illinois", "Ind": "Indiana", "Kan": "Kansas", "Kans": "Kansas", "Ky": "Kentucky", "La": "Louisiana",
    "Me": "Maine", "Md": "Maryland", "Mass": "Massachusetts", "Mich": "Michigan", "Minn": "Minnesota", "Miss": "Mississippi",
    "Mo": "Missouri", "Mont": "Montana", "Neb": "Nebraska", "Nebr": "Nebraska", "Nev": "Nevada", "N.H": "New Hampshire",
    "N.J": "New Jersey", "N.M": "New Mexico", "N. M": "New Mexico", "N.Y": "New York", "N.C": "North Carolina",
    "N.D": "North Dakota", "Okla": "Oklahoma", "Or": "Oregon", "Ore": "Oregon", "Oregon": "Oregon", "Pa": "Pennsylvania",
    "R.I": "Rhode Island", "S.C": "South Carolina", "S.D": "South Dakota", "Tenn": "Tennessee", "Tex": "Texas",
    "Vt": "Vermont", "Va": "Virginia", "Wash": "Washington", "W. Va": "West Virginia", "W.Va": "West Virginia",
    "Wis": "Wisconsin", "Wyo": "Wyoming", "Wyo. Terr": "Wyoming", "Utah": "Utah", "Idaho": "Idaho", "Iowa": "Iowa",
    "Ohio": "Ohio", "Hawaii": "Hawaii", "Alaska": "Alaska", "Oahu": "Hawaii",
}

# US Census regions, used to summarise delays
REGION = {}
for r, ss in {
    "Northeast": "Connecticut Maine Massachusetts New_Hampshire Rhode_Island Vermont New_Jersey New_York Pennsylvania",
    "Midwest": "Illinois Indiana Michigan Ohio Wisconsin Iowa Kansas Minnesota Missouri Nebraska North_Dakota South_Dakota",
    "South": "Delaware District_of_Columbia Florida Georgia Maryland North_Carolina South_Carolina Virginia West_Virginia Alabama Kentucky Mississippi Tennessee Arkansas Louisiana Oklahoma Texas",
    "West": "Arizona Colorado Idaho Montana Nevada New_Mexico Utah Wyoming Alaska California Hawaii Oregon Washington",
}.items():
    for s in ss.split():
        REGION[s.replace("_", " ")] = r


def hav(a, b):
    """Great-circle distance in km between (lat, lon) pairs."""
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * 6371.0 * math.asin(min(1, math.sqrt(h)))


def jload(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def nonan(v):
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return None
    if isinstance(v, dict):
        return {k: nonan(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [nonan(x) for x in v]
    if hasattr(v, "item"):
        return nonan(v.item())
    return v


def jsave(obj, path, indent=None):
    obj = nonan(obj)
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "wt", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=indent, separators=None if indent else (",", ":"))


def get(R, path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f=None):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(float(v)):,}"
    if f == "pc": return f"{round(float(v))}%"
    if f == "pc1": return f"{float(v):.1f}%"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    if f == "word": return NUMWORD.get(int(v), f"{int(v):,}")
    raise ValueError(f)


NUMWORD = {0: "no", 1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine", 10: "ten",
           11: "eleven", 12: "twelve"}
KEEP = {"DOI_URL", "BLOG_URL", "DOI"}


def fill(t, R):
    t = re.sub(r"\{\{([^}|]+)(\|(\w+))?\}\}", lambda m: m.group(0) if m.group(1) in KEEP or m.group(1).startswith("IMG") else fmt(get(R, m.group(1)), m.group(3)), t)
    return t


def check_visible(t):
    vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", t, flags=re.S)
    for bad in ("—", "–", "--", "DSIT", "DCMS", "civil serv", "Civil Serv"):
        assert bad not in vis, bad
