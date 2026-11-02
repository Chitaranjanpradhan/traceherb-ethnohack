# Pull an ethnobotany corpus from Europe PMC (abstracts + OA full-text IDs). No API key.
import json, time, urllib.parse, urllib.request, os
BASE="https://www.ebi.ac.uk/europepmc/webservices/rest/search"
Q='(ethnobotany OR ethnopharmacology OR "traditional medicine") AND (medicinal plant) AND OPEN_ACCESS:y'
out=os.path.expanduser("~/ethnohack/data/raw/europepmc_corpus.jsonl")
def get(url):
    with urllib.request.urlopen(url, timeout=30) as r: return json.load(r)
cursor="*"; n=0
with open(out,"w") as f:
    for _ in range(40):  # ~1000 records (25/page)
        u=f"{BASE}?query={urllib.parse.quote(Q)}&format=json&pageSize=25&cursorMark={urllib.parse.quote(cursor)}&resultType=core"
        d=get(u); res=d["resultList"]["result"]
        for x in res:
            f.write(json.dumps({"id":x.get("id"),"source":x.get("source"),"pmcid":x.get("pmcid"),
                "title":x.get("title"),"abstract":x.get("abstractText"),"year":x.get("pubYear"),
                "journal":x.get("journalTitle"),"isOA":x.get("isOpenAccess"),"doi":x.get("doi")})+"\n")
            n+=1
        nc=d.get("nextCursorMark")
        if not nc or nc==cursor: break
        cursor=nc; time.sleep(0.3)
print(f"wrote {n} records -> {out}")
