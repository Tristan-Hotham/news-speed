"""Step 7: the paper. Fills code/paper_template.tex from data/results.json, adds tables and compiles with xelatex.
Output: release/paper/Hotham_News_Speed.pdf and .tex, beside the f_* figures. The DOI stays as a placeholder."""
import subprocess
import pandas as pd
from common import *

R = jload(f"{DATA}/results.json")
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_News_Speed"
tex = lambda s: str(s).replace("\\", "").replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#").replace("$", "\\$")
T = pd.read_csv(f"{DATA}/papers_events.csv", dtype={"lccn": str})
# statements made in words in the paper
e = T[T.eligible & T.reported]
assert e[(e.ev == "lincoln1865") & (e.name.str.contains("Nashville daily union"))].report_date.iloc[0] == "1865-04-15"
assert e[(e.ev == "lincoln1865") & (e.name == "Richmond Whig")].report_date.iloc[0] == "1865-04-17"
assert R["events"]["lincoln1865"]["missed_since_median"] == R["events"]["titanic1912"]["missed_since_median"] == R["events"]["pearl1941"]["missed_since_median"]
assert abs(R["events"]["lincoln1865"]["loose_median"] - R["events"]["lincoln1865"]["median_days"]) <= 1

LAB = {"lincoln1865": "Lincoln shot, 1865", "custer1876": "Little Bighorn, 1876", "titanic1912": "Titanic, 1912", "pearl1941": "Pearl Harbor, 1941"}
rows = ""
for ev in EV:
    s = R["events"][ev]
    rows += (f"{LAB[ev]} & {s['papers']:,} & {s['eligible']:,} & {s['reported_pct']:.0f} & {s['median_days']:.0f} & {s['daily_median']:.0f} ({s['daily_n']}) & "
             f"{s['weekly_median']:.0f} ({s['weekly_n']}) & {s['first_issue_pct']:.0f} & {s['by7']:.0f}\\\\\n")
TE = ("\\begin{table}[tbp]\\centering\\footnotesize\\caption{The four events. Papers: with any digitised issue in the window; counted: with an issue within 14 days of the floor date. "
      "Reported: share of counted papers with a report in the window. Medians in days from the event, among reporting papers (in brackets, the number of counted daily or weekly papers). First issue: share of reporting papers that reported in their first issue after the floor date. By day 7: share of counted papers that had reported by day 7.}\\label{tab:events}"
      "\\begin{tabular}{lrrrrrrrr}\\toprule Event & Papers & Counted & Reported \\% & Median & Daily & Weekly & First issue \\% & By day 7 \\%\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
rows = ""
for ev in EV:
    x = e[(e.ev == ev) & e.dist_hub.notna()].sort_values(["days", "dist_hub"], ascending=[True, False]).head(6)
    for r in x.itertuples():
        rows += f"{LAB[ev]} & {tex(r.name)} & {tex(r.city)}, {tex(r.state)} & {r.report_date} & {int(r.days)} & {int(r.dist_hub):,}\\\\\n"
    rows += "\\midrule\n"
TA = ("{\\footnotesize\\begin{longtable}{p{2.6cm}p{4.6cm}p{3.6cm}lrr}\\caption{The six earliest reports of each event, the farthest first among papers reporting on the same day. Distance in km from the news hub.}\\\\"
      "\\toprule Event & Paper & Place & Date & Days & km\\\\\\midrule\\endfirsthead\\toprule Event & Paper & Place & Date & Days & km\\\\\\midrule\\endhead\n" + rows.rstrip("\\midrule\n") + "\\\\\\bottomrule\\end{longtable}}")
t = open(os.path.join(ROOT, "code", "paper_template.tex"), encoding="utf-8").read()
t = t.replace("\\usepackage{graphicx,booktabs,float,caption,array,xcolor}", "\\usepackage{graphicx,booktabs,float,caption,array,xcolor,longtable}")
t = t.replace("{{PAGE}}", "\\url{%s}" % PAGE).replace("{{REPO}}", "\\url{%s}" % REPO).replace("{{AI}}", AI)
t = t.replace("{{TABLE_EVENTS}}", TE).replace("{{TABLE_EARLY}}", TA)
t = re.sub(r"\{\{(?!DOI)([^}|]+)(\|(\w+))?\}\}", lambda m: fmt(get(R, m.group(1)), m.group(3)), t)
assert "{{" not in t and "--" not in t and "\u2014" not in t and "\u2013" not in t, re.findall(r"\{\{[^}]*\}\}", t)[:4]
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w", encoding="utf-8").write(t)
for _ in range(3):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
log = open(os.path.join(OUT, NAME + ".log"), encoding="utf-8", errors="ignore").read()
print([l for l in log.splitlines() if "Missing character" in l or "undefined" in l.lower() or "Overfull" in l or l.startswith("!")][:12])
for ext in (".aux", ".log", ".out", ".bbl", ".blg"):
    q = os.path.join(OUT, NAME + ext)
    if os.path.exists(q): os.remove(q)
txt = subprocess.run(["pdftotext", os.path.join(OUT, NAME + ".pdf"), "-"], capture_output=True, text=True).stdout
pages = subprocess.run(["pdfinfo", os.path.join(OUT, NAME + ".pdf")], capture_output=True, text=True).stdout
print("paper", r.returncode, len(txt.split()), "words;", [l for l in pages.splitlines() if l.startswith("Pages")], "dashes:", txt.count("\u2014") + txt.count("\u2013") + txt.count("--"))
