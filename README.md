# How fast did news travel?

Four American stories, Lincoln's assassination (1865), Custer at the Little Bighorn (1876), the Titanic (1912) and Pearl Harbor (1941), followed through 13,233 digitised issues of 936 newspapers: how many days each paper took to print the news.

Dr Tristan Hotham · Independent researcher · 2026

- Interactive map: https://maps.tristanhotham.com/news-speed/
- Paper: https://doi.org/10.5281/zenodo.24052721
- Blog post: https://blog.tristanhotham.com/2026/10/31/news-speed/
- Code and data: https://github.com/Tristan-Hotham/news-speed

## Headline results

| Event | Papers counted | Reported | Median days, dailies | Median days, weeklies | First report in sample |
|:-|:-|:-|:-|:-|:-|
| Lincoln is shot (1865) | 145 | 93% | 1 | 7 | 1865-04-15 |
| Custer falls at the Little Bighorn (1876) | 216 | 86% | 12 | 18 | 1876-07-06 |
| The Titanic sinks (1912) | 566 | 88% | 1 | 4 | 1912-04-15 |
| Pearl Harbor is attacked (1941) | 69 | 62% | 1 | 5 | 1941-12-07 |

- Dailies printed Lincoln's death, the Titanic and Pearl Harbor with the same median delay of one day: the telegraph had already removed distance as a cause of delay by 1865.
- Weeklies waited for their press day; most papers missed no issue.
- In 1865 papers in the former Confederacy took a median of 11 days, against 6 elsewhere.
- No paper in the sample printed Custer's defeat for 11 days; on 6 July 1876 12 papers in 9 states printed it at once.
- Far did not mean late: Gold Hill, Nevada printed Lincoln's death on 15 April 1865 (3,643 km from Washington); two Honolulu dailies printed the Titanic on 15 April 1912.

## Files

| Path | What |
|:-|:-|
| `index.html`, `js/`, `fonts/`, `data/points.json` | the interactive page (Inked World map style) |
| `data/papers_events.csv` | one row per newspaper and event: place, rhythm, first issue, first report, days, issues missed, snippet |
| `data/newspapers.csv` | the 936 newspapers with their geocoded place and how it was found |
| `data/daily.json` | cumulative share of papers reporting, by day |
| `data/results.json` | every number quoted anywhere |
| `code/` | numbered scripts 00 to 09, `review_verdicts.tsv` (hand review), templates, `qa.js` |
| `release/paper/` | the paper (PDF and LaTeX) and figures |
| `release/blog/` | blog post (WordPress markup), figures and meta |
| `release/zenodo/` | paper, data and code zip, Zenodo metadata |
| `reddit/` | collage, its script and the post |

## Method

A page counts as reporting an event if it is dated on or after the earliest day the news could have been printed and the snippet round the event's name contains a word about the event (word lists in `code/02_classify.py`). 290 early or doubtful first reports were read by hand (9 rejected); in a random check of 60 others, 59 were plainly about the event. Delay is calendar days from the event to a paper's first report; a paper counts if it has a digitised issue within 14 days. Papers are placed at the town in their Library of Congress title (850 of 936).

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

Hotham, T. (2026) How fast did news travel? Four American stories in digitised newspapers, 1865 to 1941. Zenodo. https://doi.org/10.5281/zenodo.24052721

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
