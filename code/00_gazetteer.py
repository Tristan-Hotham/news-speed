"""Step 0: US places with 500 or more people from GeoNames cities500 (CC BY 4.0, https://www.geonames.org/), as shipped
in the geonamescache 3.0.2 package on PyPI. Writes GN_US (a small TSV) and deletes the download."""
import subprocess, zipfile, glob, shutil
from common import *

tmp = os.path.join(WORK, "gnc")
os.makedirs(tmp, exist_ok=True)
subprocess.run(["pip", "download", "geonamescache==3.0.2", "--no-deps", "-d", tmp], check=True)
z = zipfile.ZipFile(glob.glob(f"{tmp}/geonamescache-*.whl")[0])
c = json.loads(z.read("geonamescache/data/cities500.json"))
st = {k: v["name"] for k, v in json.loads(z.read("geonamescache/data/us_states.json")).items()}
with open(GN_US, "w", encoding="utf-8") as f:
    f.write("geonameid\tname\talternatenames\tlat\tlon\tstate\tpopulation\n")
    for v in c.values():
        if v["countrycode"] == "US":
            f.write("\t".join(map(str, [v["geonameid"], v["name"], "|".join(v.get("alternatenames") or [])[:300], v["latitude"], v["longitude"],
                                        st.get(v["admin1code"], v["admin1code"]), v["population"]])) + "\n")
shutil.rmtree(tmp)
print("written", GN_US)
