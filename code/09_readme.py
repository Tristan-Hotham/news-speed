"""Step 9: README.md from data/results.json."""
from common import *

R = jload(f"{DATA}/results.json"); E = R["events"]; S = R["source"]
rows = "\n".join(f"| {EVENTS[ev]['name']} ({EVENTS[ev]['year']}) | {E[ev]['eligible']:,} | {E[ev]['reported_pct']:.0f}% | {E[ev]['daily_median']:.0f} | {E[ev]['weekly_median']:.0f} | {E[ev]['first_any']} |" for ev in EV)
md = f"""# How fast did news travel?

Four American stories, Lincoln's assassination (1865), Custer at the Little Bighorn (1876), the Titanic (1912) and Pearl Harbor (1941), followed through {S['issues']:,} digitised issues of {S['papers']:,} newspapers: how many days each paper took to print the news.

Dr Tristan Hotham · Independent researcher · 2026

- Interactive map: {PAGE}
- Paper: {{https://doi.org/10.5281/zenodo.24052721}}
- Blog post: {{https://blog.tristanhotham.com/2026/10/31/news-speed/}}
- Code and data: {REPO}

## Headline results

| Event | Papers counted | Reported | Median days, dailies | Median days, weeklies | First report in sample |
|:-|:-|:-|:-|:-|:-|
{rows}

- Dailies printed Lincoln's death, the Titanic and Pearl Harbor with the same median delay of one day: the telegraph had already removed distance as a cause of delay by 1865.
- Weeklies waited for their press day; most papers missed no issue.
- In 1865 papers in the former Confederacy took a median of {R['lincoln_conf']['median']:.0f} days, against {R['lincoln_conf']['other_median']:.0f} elsewhere.
- No paper in the sample printed Custer's defeat for {E['custer1876']['first_any_days']} days; on 6 July 1876 {R['custer']['first_day_n']} papers in {R['custer']['first_day_states']} states printed it at once.
- Far did not mean late: Gold Hill, Nevada printed Lincoln's death on 15 April 1865 ({R['ex']['gold_hill']['dist']:,} km from Washington); two Honolulu dailies printed the Titanic on 15 April 1912.

## Files

| Path | What |
|:-|:-|
| `index.html`, `js/`, `fonts/`, `data/points.json` | the interactive page (Inked World map style) |
| `data/papers_events.csv` | one row per newspaper and event: place, rhythm, first issue, first report, days, issues missed, snippet |
| `data/newspapers.csv` | the {S['papers']:,} newspapers with their geocoded place and how it was found |
| `data/daily.json` | cumulative share of papers reporting, by day |
| `data/results.json` | every number quoted anywhere |
| `code/` | numbered scripts 00 to 09, `review_verdicts.tsv` (hand review), templates, `qa.js` |
| `release/paper/` | the paper (PDF and LaTeX) and figures |
| `release/blog/` | blog post (WordPress markup), figures and meta |
| `release/zenodo/` | paper, data and code zip, Zenodo metadata |
| `reddit/` | collage, its script and the post |

## Method

A page counts as reporting an event if it is dated on or after the earliest day the news could have been printed and the snippet round the event's name contains a word about the event (word lists in `code/02_classify.py`). {R['review']['reviewed']} early or doubtful first reports were read by hand ({R['review']['rejected']} rejected); in a random check of {R['review']['sample']} others, {R['review']['sample_ok']} were plainly about the event. Delay is calendar days from the event to a paper's first report; a paper counts if it has a digitised issue within 14 days. Papers are placed at the town in their Library of Congress title ({S['geocoded']:,} of {S['papers']:,}).

Caveats: the digitised papers are a sample; OCR and layout detection miss text, so delays are upper bounds; only the snippet round the first name match on each page is read; Pearl Harbor was often reported without its name.

## Sources and licences

- American Stories: Dell, M. et al. (2023) arXiv:2308.12477, CC BY 4.0, from Chronicling America (Library of Congress).
- Places: Wikidata (CC0) and GeoNames cities500 (CC BY 4.0, via the geonamescache package). State outlines: Natural Earth (public domain).
- Map: OpenStreetMap contributors (ODbL) via OpenFreeMap; the Inked World style (MIT) and its data.
- Code MIT; text, figures and derived data CC BY 4.0. See LICENSE.

## Rerun

```
cd code
python3 00_gazetteer.py && python3 01_papers.py && python3 02_classify.py && python3 03_analysis.py && python3 04_results.py
python3 05_build_site.py && python3 06_figures.py && python3 07_paper.py && python3 ../reddit/collage.py && python3 09_readme.py && python3 08_release.py
node qa.js
```
Raw inputs are listed in `code/common.py`.

## Citation

Hotham, T. (2026) How fast did news travel? Four American stories in digitised newspapers, 1865 to 1941. Zenodo. {{https://doi.org/10.5281/zenodo.24052721}}

{AI}
"""
for bad in ("—", "–", "--", "DSIT", "DCMS"):
    assert bad not in md.replace("```", ""), bad
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(md)
print("README", len(md))
