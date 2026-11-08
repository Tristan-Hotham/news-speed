"""Step 5: index.html from code/page_template.html, filled from data/results.json, with the full-screen snippet.
10.5281/zenodo.24052721, https://doi.org/10.5281/zenodo.24052721 and https://blog.tristanhotham.com/2026/10/31/news-speed/ stay as placeholders for the publisher."""
from common import *

R = jload(f"{DATA}/results.json")
# facts stated in words on the page
assert R["events"]["lincoln1865"]["daily_median"] == 1 == R["events"]["titanic1912"]["daily_median"] == R["events"]["pearl1941"]["daily_median"]
assert R["events"]["custer1876"]["first_any"] == "1876-07-06" and R["ex"]["gold_hill"]["date"] == "1865-04-15"
assert R["ex"]["juneau"]["date"] == "1941-12-07" and R["ex"]["honolulu_titanic"]["date"] == "1912-04-15"
import pandas as pd
T = pd.read_csv(f"{DATA}/papers_events.csv")
tx = T[(T.ev == "lincoln1865") & (T.state == "Texas") & T.reported].days
assert len(tx) and tx.min() >= 19 and tx.max() <= 29   # "three to four weeks"
assert R["lincoln_conf"]["median"] > R["lincoln_conf"]["other_median"]
t = open(os.path.join(ROOT, "code", "page_template.html"), encoding="utf-8").read()
t = t.replace("{{FULLSCREEN}}", open(os.path.join(ROOT, "code", "fullscreen_snippet.html"), encoding="utf-8").read())
t = t.replace("{{REPO}}", REPO).replace("{{AI}}", AI)
t = fill(t, R)
left = set(re.findall(r"\{\{([^}]+)\}\}", t))
assert left <= KEEP, left
check_visible(t)
open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(t)
print("index.html", len(t) // 1024, "KB")
