"""House style for the static figures, in the ink of the Inked World: parchment, iron-gall black, vermilion lettering,
hand-tinted colours; the Albers projection for the United States; Natural Earth outlines."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon as MPoly
from matplotlib.collections import PatchCollection
import numpy as np
from PIL import Image
from common import *

FD = os.path.join(WORK, "fonts"); os.makedirs(FD, exist_ok=True)
if not os.path.exists(f"{FD}/Fraunces-Black.ttf"):
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer
    for w, nm in ((900, "Black"), (700, "Bold")):
        instancer.instantiateVariableFont(TTFont(f"{FONTS}/FrauncesVar.ttf"), {"wght": w, "opsz": 144, "SOFT": 0, "WONK": 0}).save(f"{FD}/Fraunces-Black.ttf" if w == 900 else f"{FD}/Fraunces-Bold.ttf")
DISP = fm.FontProperties(fname=f"{FD}/Fraunces-Black.ttf")
DISPB = fm.FontProperties(fname=f"{FD}/Fraunces-Bold.ttf")
HAND = fm.FontProperties(fname=f"{INKFONTS}/MedievalSharp.ttf")
FELL = fm.FontProperties(fname=f"{INKFONTS}/IMFeENrm28P.ttf")
FELLI = fm.FontProperties(fname=f"{INKFONTS}/IMFeGPit28P.ttf")
SERP = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-Regular.ttf")
for f in ("IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf"):
    fm.fontManager.addfont(f"{FONTS}/{f}")
fm.fontManager.addfont(f"{INKFONTS}/IMFeENrm28P.ttf")
MONO = "IBM Plex Mono"
for f in ("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",):
    if os.path.exists(f):
        fm.fontManager.addfont(f)
plt.rcParams.update({"font.family": [MONO, "Noto Sans CJK JP"], "font.size": 12, "axes.edgecolor": "#6E604E", "axes.labelcolor": "#2B2119",
                     "xtick.color": "#6E604E", "ytick.color": "#6E604E", "text.color": "#2B2119"})
PAPER, PAPER2, INK, MUT, RED, SEA, RULE = "#F6EED8", "#F3E5BF", "#2B2119", "#6E604E", "#A3261B", "#E3EAE6", "#E2D3AE"
LANDC = "#ECD9AC"
SEAC = "#DFE6E1"


def eqearth(lon, lat):
    """Equal Earth projection (Savric, Patterson and Jenny 2018), unit sphere."""
    lon = np.radians(np.asarray(lon, float)); lat = np.radians(np.asarray(lat, float))
    A1, A2, A3, A4 = 1.340264, -0.081106, 0.000893, 0.003796
    M = np.sqrt(3) / 2
    th = np.arcsin(M * np.sin(lat))
    t2 = th * th; t6 = t2 ** 3
    x = 2 * np.sqrt(3) * lon * np.cos(th) / (3 * (9 * A4 * t6 * t2 + 7 * A3 * t6 + 3 * A2 * t2 + A1))
    y = th * (A1 + A2 * t2 + t6 * (A3 + A4 * t2))
    return x, y


def plate(lon, lat, lat0=0):
    return np.asarray(lon, float) * np.cos(np.radians(lat0)), np.asarray(lat, float)


NE = jload(f"{GEO}/ne_50m_admin_0_countries.geojson")
LAND = jload(f"{GEO}/ne_50m_land.geojson")


def rings(geom):
    cs = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    for poly in cs:
        yield np.array(poly[0])


ADM1 = jload(f"{GEO}/ne_10m_admin_1_states_provinces.geojson")
US = [f for f in ADM1["features"] if f["properties"].get("adm0_a3") == "USA"]
CANMEX = [f for f in ADM1["features"] if f["properties"].get("adm0_a3") in ("CAN", "MEX")]


def albers(lon, lat, lon0=-96, lat0=37.5, p1=29.5, p2=45.5):
    """Albers equal-area conic (USA Contiguous Albers parameters), unit sphere, output in km."""
    lon = np.radians(np.asarray(lon, float)); lat = np.radians(np.asarray(lat, float))
    l0, f0, f1, f2 = map(np.radians, (lon0, lat0, p1, p2))
    n = (np.sin(f1) + np.sin(f2)) / 2
    C = np.cos(f1) ** 2 + 2 * n * np.sin(f1)
    r0 = np.sqrt(C - 2 * n * np.sin(f0)) / n
    r = np.sqrt(C - 2 * n * np.sin(lat)) / n
    th = n * (lon - l0)
    return 6371 * r * np.sin(th), 6371 * (r0 - r * np.cos(th))


AK = dict(lon0=-154, lat0=50, p1=55, p2=65)
HI = dict(lon0=-157, lat0=13, p1=8, p2=18)


def states(ax, proj, feats=US, fill=LANDC, lw=0.35, coast=0.7, names=None, keep=None):
    polys = []
    for f in feats:
        if keep and f["properties"].get("name") not in keep:
            continue
        for r in rings(f["geometry"]):
            if len(r) < 4:
                continue
            x, y = proj(r[:, 0], r[:, 1])
            polys.append(MPoly(np.c_[x, y], closed=True))
    ax.add_collection(PatchCollection(polys, facecolor="none", edgecolor="#6C9FD6", lw=4.5, alpha=0.18, zorder=1))
    ax.add_collection(PatchCollection(polys, facecolor=fill, edgecolor=INK, lw=lw, alpha=1, zorder=2))
    return polys


def usmap(ax, xlim=(-2420, 2300), ylim=(-1700, 1650), neighbours=True):
    ax.set_facecolor(SEAC)
    if neighbours:
        states(ax, albers, CANMEX, fill="#EFE3C4", lw=0.2)
    states(ax, albers, [f for f in US if f["properties"].get("name") not in ("Alaska", "Hawaii")])
    ax.set_xlim(*xlim); ax.set_ylim(*ylim); ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)


def inset(fig, rect, which):
    ax = fig.add_axes(rect)
    ax.set_facecolor(SEAC)
    p = (lambda lo, la: albers(lo, la, **AK)) if which == "Alaska" else (lambda lo, la: albers(lo, la, **HI))
    states(ax, p, [f for f in US if f["properties"].get("name") == which], lw=0.4)
    if which == "Alaska":
        x, y = p(np.array([-170, -130]), np.array([51, 71.5]))
    else:
        x, y = p(np.array([-160.4, -154.6]), np.array([18.8, 22.4]))
    ax.set_xlim(x.min(), x.max()); ax.set_ylim(y.min(), y.max()); ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_edgecolor(MUT); s.set_linewidth(0.6)
    return ax, p


def spines(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
