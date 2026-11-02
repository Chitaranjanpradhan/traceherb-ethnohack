# Ensure Europe PMC annotations cached for every corpus PMCID (resumable).
import json, os, time, urllib.request
RAW=os.path.expanduser("~/ethnohack/data/raw"); ANN=os.path.join(RAW,"annotations"); os.makedirs(ANN,exist_ok=True)
ids=[json.loads(l).get('pmcid') for l in open(os.path.join(RAW,"europepmc_corpus.jsonl"))]
ids=[i for i in ids if i]
todo=[i for i in ids if not os.path.exists(os.path.join(ANN,i+".json"))]
print(f"{len(ids)} articles, {len(todo)} to fetch")
for n,pmcid in enumerate(todo,1):
    u=f"https://www.ebi.ac.uk/europepmc/annotations_api/annotationsByArticleIds?articleIds=PMC%3A{pmcid[3:]}&format=JSON"
    try:
        with urllib.request.urlopen(u,timeout=30) as r: d=json.load(r)
        anns=d[0]['annotations'] if d and d[0].get('annotations') else []
    except Exception: anns=[]
    json.dump(anns, open(os.path.join(ANN,pmcid+".json"),"w"))
    if n%50==0: print(f"  cached {n}/{len(todo)}")
    time.sleep(0.2)
print("annotations cache complete")
