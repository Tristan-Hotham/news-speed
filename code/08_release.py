"""Step 8: blog post and meta (release/blog), Zenodo files and metadata (release/zenodo).
10.5281/zenodo.24052721, https://doi.org/10.5281/zenodo.24052721 and https://blog.tristanhotham.com/2026/10/31/news-speed/ stay as placeholders for the publisher."""
import json as _json, shutil, zipfile
import pandas as pd
from common import *

R = jload(f"{DATA}/results.json")
REL = os.path.join(ROOT, "release"); NAME = "Hotham_News_Speed"
T = pd.read_csv(f"{DATA}/papers_events.csv", dtype={"lccn": str})
e = T[T.eligible & T.reported]
# facts in words in the blog and alt text
assert {"Cleveland", "Nashville", "Indianapolis", "New York"} <= set(e[(e.ev == "lincoln1865") & (e.report_date == "1865-04-15")].city)
assert e[(e.ev == "lincoln1865") & (e.state == "North Carolina")].days.max() >= 50
assert R["lincoln_conf"]["sc_median"] > 7
assert 55 <= R["events"]["lincoln1865"]["by7"] <= 65 and 60 <= R["events"]["titanic1912"]["by7"] <= 66
assert R["events"]["custer1876"]["by10"] == 0 and R["events"]["custer1876"]["daily_median"] == 12 and R["events"]["custer1876"]["weekly_median"] == 18

post = open(os.path.join(ROOT, "code", "blog_template.html"), encoding="utf-8").read()
post = fill(post, R)
used = re.findall(r"\{\{IMG\|([^|]+)\|", post)
assert 5 <= len(used) <= 8, len(used)
assert all(re.search(r"^\{\{IMG\|" + re.escape(u_), post, re.M) for u_ in used) and "wp:image" not in post
for img in used:
    assert os.path.exists(f"{REL}/blog/{img}"), img
for fn in os.listdir(f"{REL}/blog"):
    if fn.startswith("b_") and fn not in used:
        os.remove(f"{REL}/blog/{fn}")
assert set(re.findall(r"\{\{([^|}]+)\}\}", post)) <= KEEP
vis = re.sub(r"<!--.*?-->", "", post, flags=re.S)
for bad in ("\u2014", "\u2013", "--", "DSIT", "DCMS"):
    assert bad not in vis, bad
open(f"{REL}/blog/post.html", "w", encoding="utf-8").write(post)
words = len(re.sub(r"<[^>]+>|\{\{IMG\|[^}]*\}\}", " ", vis).split())
S = R["source"]
meta = {"title": "How fast did news travel? Lincoln, Custer, the Titanic and Pearl Harbor in America's newspapers",
        "slug": "news-speed",
        "excerpt": f"I followed four great stories through {S['issues']:,} digitised issues of {S['papers']:,} American newspapers. A daily printed Lincoln's death the next morning, just as fast as the Titanic or Pearl Harbor. What held news back was the weekly press day.",
        "seo_description": f"How many days did Lincoln's death, Custer, the Titanic and Pearl Harbor take to reach {S['papers']:,} American newspapers? Mapped day by day.",
        "tags": ["maps", "history", "newspapers", "telegraph", "Chronicling America", "data visualisation", "American history", "media history"],
        "header_alt": "Title card reading 'How fast did news travel?' on parchment above four small maps of the United States for Lincoln 1865, Little Bighorn 1876, Titanic 1912 and Pearl Harbor 1941, each covered in dots coloured from dark red for the next day to blue for three weeks or more."}
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
jsave(meta, f"{REL}/blog/meta.json", indent=2)

# Zenodo
Z = f"{REL}/zenodo"; os.makedirs(Z, exist_ok=True)
for fn in os.listdir(Z):
    os.remove(os.path.join(Z, fn))
shutil.copy(f"{REL}/paper/{NAME}.pdf", f"{Z}/{NAME}.pdf")
zp = f"{Z}/{SLUG}_data_and_code.zip"
OWN = ["papers_events.csv", "newspapers.csv", "daily.json", "results.json", "points.json"]
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for fn in sorted(os.listdir(os.path.join(ROOT, "code"))):
        if fn.endswith(".pyc") or fn == "__pycache__" or fn.endswith(".png"):
            continue
        z.write(os.path.join(ROOT, "code", fn), f"{SLUG}/code/{fn}")
    for fn in OWN:
        z.write(os.path.join(DATA, fn), f"{SLUG}/data/{fn}")
    for fn in ("README.md", "LICENSE", "index.html"):
        z.write(os.path.join(ROOT, fn), f"{SLUG}/{fn}")
    z.write(os.path.join(ROOT, "reddit", "collage.py"), f"{SLUG}/reddit/collage.py")
tex = open(f"{REL}/paper/{NAME}.tex", encoding="utf-8").read()
ab = re.search(r"\\begin\{center\}\\textbf\{Abstract\}\\end\{center\}\n(.*?)\n\n\\textbf\{Keywords", tex, re.S).group(1)
ab = ab.replace("\\%", "%").replace("\\&", "&").replace("``", "\u201c").replace("''", "\u201d")
ab = re.sub(r"\\textit\{([^}]*)\}", r"\1", ab)
zmeta = {"title": "How Fast Did News Travel? Four American Stories in Digitised Newspapers, 1865 to 1941",
         "upload_type": "publication", "publication_type": "workingpaper",
         "description": f"<p>{ab}</p><p>Interactive version: <a href=\"{PAGE}\">{PAGE}</a>. Data and code: <a href=\"{REPO}\">{REPO}</a>. Blog post: {{https://blog.tristanhotham.com/2026/10/31/news-speed/}}.</p><p>Sources: American Stories (Dell et al. 2023, CC BY 4.0) from Chronicling America, Library of Congress; Wikidata (CC0); GeoNames (CC BY 4.0); Natural Earth (public domain). Derived data and text CC BY 4.0, code MIT.</p>",
         "creators": [{"name": "Hotham, Tristan", "affiliation": "Independent researcher", "orcid": "0000-0003-4931-9349"}],
         "keywords": ["history of news", "telegraph", "newspapers", "Chronicling America", "American Stories", "diffusion of information", "digital history", "maps"],
         "license": "cc-by-4.0", "language": "eng",
         "related_identifiers": [{"identifier": REPO, "relation": "isSupplementedBy", "resource_type": "software"},
                                 {"identifier": PAGE, "relation": "isSupplementedBy", "resource_type": "other"},
                                 {"identifier": "arXiv:2308.12477", "relation": "isDerivedFrom", "resource_type": "dataset"},
                                 {"identifier": "https://chroniclingamerica.loc.gov/", "relation": "isDerivedFrom", "resource_type": "dataset"}],
         "files": sorted(os.listdir(Z))}
sj = _json.dumps(zmeta, ensure_ascii=False) + _json.dumps(meta, ensure_ascii=False)
assert "\u2014" not in sj and "\u2013" not in sj and "--" not in sj
jsave(zmeta, f"{Z}/metadata.json", indent=2)
print("blog words", words, "figures", len(used), "; zenodo", sorted(os.listdir(Z)), os.path.getsize(zp) // 1024, "KB zip")
