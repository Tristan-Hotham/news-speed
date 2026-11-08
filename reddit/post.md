# Reddit post

**Title:** [OC] How fast did news travel? A US daily paper printed Lincoln's death in 1865 the next morning, exactly as fast as the Titanic in 1912 or Pearl Harbor in 1941 (median 1 day, 936 newspapers)

**Image:** news_speed_collage.png

**Body:**

I followed four big stories through 13,233 digitised issues of 936 American newspapers and found the first day each paper printed the news. Each dot is a paper, coloured by how many days it took.

- Dailies: a median of 1 day for Lincoln (1865), the Titanic (1912) and Pearl Harbor (1941). The telegraph had already done the job by 1865.
- Weeklies waited for press day: 7, 4 and 5 days.
- Custer's defeat at the Little Bighorn (1876) was fought far from a telegraph office: no paper in the sample had it for 11 days, then 12 papers in 9 states printed it on the same day.
- In 1865 papers in the old Confederacy took a median of 11 days, against 6 elsewhere.

Caveats: digitised papers are a sample (lots of small weeklies, few for 1941), and OCR misses words, so delays are upper bounds.

Interactive map with a day-by-day slider: https://maps.tristanhotham.com/news-speed/

**Source comment:**

Data: American Stories (Dell et al. 2023, Harvard; CC BY 4.0), structured OCR of the Library of Congress's Chronicling America scans. A page counts as a report if it names the event after the earliest possible date and the text round the name is about the event; I hand-checked 290 early or doubtful first reports. Papers placed from their Library of Congress title via Wikidata and GeoNames. Tools: Python (pandas, matplotlib). Paper, data and code: https://github.com/Tristan-Hotham/news-speed
