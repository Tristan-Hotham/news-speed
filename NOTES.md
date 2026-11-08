# news-speed working notes

- Data: raw_new8/news_*.tsv (American Stories). Pages per issue are incomplete (only pages with OCR text in the dataset); some issues have only 1 or 2 pages. Caveat in all copy.
- Geocoding: us_places.tsv (Wikidata) lacks big cities (no Chicago); added GeoNames cities500 US rows (via geonamescache 3.0.2 wheel, 00_gazetteer.py) as fallback. 772 papers from title place, 78 from a town name inside the paper's name (flagged "name"), 86 none.
- Classification: hit + floor date + event word list in snippet; hand review in code/review_verdicts.tsv of every first report that was early (floor day or next), flagged as other use, or lacked a strong word (about 290 rows; 9 rejected). Precision sample of 60 unreviewed first reports: 59 clearly about the event, 1 ambiguous.
- Key results (03_analysis): daily papers median days to first report: 1865 1, 1876 12, 1912 1, 1941 1. Weekly: 7, 18, 4, 5. Custer first in sample 6 July (11 days), East coast dailies first; Montana weeklies slow (Helena weekly 25 d, Benton 40 d).
- Lincoln: South Carolina and Texas late (war), Gold Hill NV daily next day (aliased to Virginia City coords, adjoining).
- Status: COMPLETE. All deliverables built (index, figures, paper 9pp, blog, zenodo, collage, README). QA screenshots in qa/ (only expected offline errors: Google Fonts, site-nav.js).
