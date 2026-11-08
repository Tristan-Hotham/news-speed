"""Step 2: decide which matched pages really report the event.

A "hit" only means the page contains the name (Lincoln, Custer, Titanic, Pearl Harbor). Lincoln and Custer were in the
news all the time (Lincoln County, Custer City in the Black Hills), and the Titanic was news before she sailed. So a
page counts as reporting the event only when
  (1) it is dated on or after the event's floor date (the earliest day the news could have been printed), and
  (2) its snippet (about 180 characters round the first match) contains a word about the event itself
      (assassination, iceberg, massacre, attack ...), from the event's word list below.
Pages that pass (1) but not (2) are kept as "name only"; they give a looser upper bound used as a sensitivity check.
Hand review (code/review_verdicts.tsv) overrides the rule for individual pages after reading the snippet.
Writes WORK/hits.pkl."""
import pandas as pd
from common import *

pages = pd.read_pickle(f"{WORK}/pages.pkl")

WORDS = {
    "lincoln1865": r"assassin|asassin|assasin|murder|shot|shoot|kill|slain|wound|bullet|pistol|death|died|dead|dying|deceas|"
                   r"funeral|obsequ|mourn|crape|bier|catafalque|remains|grief|sorrow|griev|sad |tragedy|tragic|calamit|martyr|"
                   r"late president|late lamented|lamented|booth|ford'?s|theat|seward|conspira|requiem|eulog|in memoriam|memory of|"
                   r"tolling|bereave|horror|appalling|terrible news|awful|lincoln is dead|nation weeps|national loss|tears|surgeon|physician|"
                   r"bedside|insensible|unconscious|almighty god|taken from|take from|melancholy|sorrowful|shock|dreadful|horrible|"
                   r"successor|johnson|inaugurat|oath of office|lamented|departed|memorial|half.mast|draped|black",
    "custer1876": r"massacr|kill|slain|slaughter|death|dead|died|fell |fall of|fate|annihilat|exterminat|butcher|disaster|defeat|"
                  r"sitting bull|sioux|little horn|big horn|bighorn|little big|rosebud|reno|seventh cavalry|7th cavalry|cavalry|"
                  r"terry|gibbon|battle|fight|engagement|indian|savage|redskin|warrior|widow|memorial|monument|avenge|"
                  r"brave custer|gallant custer|heroic custer|custer's fate|custer'?s command|custer'?s men|custer'?s last|poor custer|"
                  r"intense feeling|sensation|excitement|monroe|his youth|gallant|hero|lamentable|sad|mournful|mourn|scalp|mutilat|"
                  r"crook|yellowstone|montana|bismarck|fort lincoln|lodges|village|charge|troops|soldier|officers",
    "titanic1912": r"iceberg|ice berg|sink|sank|sunk|disaster|wreck|lost|loss|carpathia|surviv|rescu|drown|collision|collid|"
                   r"struck|perish|victim|lifeboat|life boat|life-boat|dead|death|died|mourn|calamit|tragedy|catastroph|"
                   r"went down|bottom|ill.fated|doomed|missing|saved|safe|widow|memorial|inquiry|investigat|wireless|"
                   r"cape race|halifax|mackay.bennett|marconi|bodies|body of|hero|desastre|naufrag|perdida|catastrofe|untergang|katastroph|"
                   r"unglück|unglueck|ungluck|gesunken|katastrof|zatonu|katastrofa",
    "pearl1941": r"attack|bomb|raid|jap|nippon|war|sunk|sink|sank|killed|kill|dead|death|casualt|wound|damage|destroy|"
                 r"strike|struck|assault|surprise|treacher|sneak|infamy|remember|hawaii|honolulu|oahu|navy|naval|fleet|"
                 r"battleship|plane|safe|defen|enemy|fight|missing|survivor|congress|roosevelt|declar|ataque|japon|guerra|incident|disaster|"
                 r"tragedy|victim|sailor|investigat|inquiry",
}
# Phrases that show the name is about something else (checked only where no event word is present, and listed for review)
OTHER = {
    "lincoln1865": r"(?:lincoln county|lincoln co\b|fort lincoln|lincoln,? (?:neb|ill|me|mass|nh)|lincoln street|lincoln township)",
    "custer1876": r"(?:custer city|custer county|custer co\b|custer'?s gulch|from custer|of custer\b|at custer\b|in custer\b)",
    "titanic1912": r"titanic (?:struggle|war|force|effort|task|strength|power|conflict|contest|battle|labou?r|figure|proportion)",
    "pearl1941": r"",
}

V = {}
vf = os.path.join(ROOT, "code", "review_verdicts.tsv")
if os.path.exists(vf):
    for line in open(vf, encoding="utf-8"):
        if line.startswith("#") or not line.strip(): continue
        ev, lccn, date, page, verdict = line.rstrip("\n").split("\t")[:5]
        V[(ev, lccn, date, int(page))] = verdict

rows = []
h = pages[pages.hit == 1].copy()
# word counts over all snippets, to undo the glued line-break "n" for display: "nanother" -> "another" when "another"
# is a far commoner token than "nanother"
from collections import Counter
WC = Counter(w for t in h.snippet.str.lower() for w in re.findall(r"[a-z]+", t))


KEEPN = set("none nice near nearly nearer nearest nor never neither nought nag nail nails nay nod nods nit nought nown neve "
             "neat nil nigh nap nape nell nevermore nonce".split())


def display(t):
    t = re.sub(r"\s+", " ", t)
    def fix(m):
        w = m.group(0); lw = w.lower()
        if lw.startswith("n") and len(lw) > 2 and lw not in KEEPN and WC[lw[1:]] > 1.5 * WC[lw] and WC[lw[1:]] >= 3:
            return w[1:]
        return w
    t = re.sub(r"\b[nN][A-Za-z']+", fix, t)
    t = re.sub(r"(^|\s)n(?=[A-Z0-9'\"(])", r"\1", t)
    t = re.sub(r"(\s+n)+(\s|$)", " ", t)
    # the snippets can straddle the dataset's JSON fields: drop the field names and short values, keep the article text
    t = re.sub(r"[{}]", " ", t)
    t = re.sub(r"^\W*[a-z_]{0,16}\s*[:,]\s*(?=[a-z_]+\s*:)", " ", t)
    t = re.sub(r"(^|[\s,])(?:legibility|full_article_id|reading_order_id|class|image_file_name|object_id|bbox|lccn)\s*:\s*[^,]*,?", " ", t)
    t = re.sub(r"(^|[\s,])raw_text\s*:", " ", t)
    t = re.sub(r"\s*,\s*(?:f|fu|ful|full|full_[a-z_]*|le|leg[a-z]*|rea[a-z_]*|cl|cla|clas|class|raw|raw_[a-z]*)\s*$", "", t)
    return re.sub(r"\s+", " ", t).strip(" ,")
for ev in EV:
    E = EVENTS[ev]
    x = h[h.ev == ev].copy()
    # the snippets mark line breaks with a bare "n" glued to the next word ("nLincoln"); the word lists have no word
    # boundaries, so they are matched on the raw text, and the "n" is only removed for display before capitals or digits
    s = x.snippet.str.replace(r"\s+", " ", regex=True).str.lower()
    x["text"] = x.snippet.map(display)
    x["has_word"] = s.str.contains(WORDS[ev], regex=True)
    x["other"] = s.str.contains(OTHER[ev], regex=True) if OTHER[ev] else False
    x["after_floor"] = x.date >= E["floor"]
    x["rule"] = x.after_floor & x.has_word
    x["verdict"] = [V.get((ev, r.lccn, r.date, r.page), "") for r in x.itertuples()]
    x["event"] = [(v == "yes") if v in ("yes", "no") else r for v, r in zip(x.verdict, x.rule)]
    rows.append(x)
H = pd.concat(rows)
H.to_pickle(f"{WORK}/hits.pkl")
for ev in EV:
    x = H[H.ev == ev]
    pre = x[~x.after_floor]
    print(ev, "hits", len(x), "after floor", int(x.after_floor.sum()), "event", int(x.event.sum()),
          "| before floor", len(pre), "of which rule-words", int(pre.has_word.sum()))
