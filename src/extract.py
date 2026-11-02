# TraceHerb extraction: Europe PMC annotations -> plant×condition edges, GBIF-resolved, evidence-cited.
import json, os, re, time, urllib.parse, urllib.request
from collections import defaultdict

RAW=os.path.expanduser("~/ethnohack/data/raw")
PROC=os.path.expanduser("~/ethnohack/data/processed")
os.makedirs(PROC, exist_ok=True)
ANN_CACHE=os.path.join(RAW,"annotations"); os.makedirs(ANN_CACHE, exist_ok=True)
GBIF_CACHE=os.path.join(PROC,"gbif_cache.json")
gbif=json.load(open(GBIF_CACHE)) if os.path.exists(GBIF_CACHE) else {}

def get(url):
    for _ in range(3):
        try:
            with urllib.request.urlopen(url, timeout=30) as r: return json.load(r)
        except Exception: time.sleep(1)
    return None

def fetch_ann(pmcid):
    fp=os.path.join(ANN_CACHE, pmcid+".json")
    if os.path.exists(fp): return json.load(open(fp))
    u=f"https://www.ebi.ac.uk/europepmc/annotations_api/annotationsByArticleIds?articleIds=PMC%3A{pmcid[3:]}&format=JSON"
    d=get(u) or []
    anns=d[0]['annotations'] if d and d[0].get('annotations') else []
    json.dump(anns, open(fp,"w")); time.sleep(0.25); return anns

GENERIC={'plant','plants','animal','animals','bacteria','human','humans','species','tree','trees','herb','herbs','fungi','fungus','mammals','seed','seeds','flower','leaf','leaves','root','roots'}
def resolve_plant(name):
    key=name.strip().lower()
    if key in gbif: return gbif[key]
    if key in GENERIC or len(key)<4 or not re.match(r'^[A-Za-z][A-Za-z .\-]+$', name):
        gbif[key]=None; return None
    d=get("https://api.gbif.org/v1/species/match?name="+urllib.parse.quote(name)) or {}
    res=None
    if d.get('kingdom')=='Plantae' and d.get('rank') in ('SPECIES','GENUS','FAMILY') and d.get('matchType')!='NONE':
        res={'accepted':d.get('scientificName'),'rank':d.get('rank'),'key':d.get('usageKey'),
             'family':d.get('family'),'genus':d.get('genus')}
    gbif[key]=res; json.dump(gbif, open(GBIF_CACHE,"w")); time.sleep(0.1); return res

def norm_cond(s):
    s=s.strip().lower()
    return re.sub(r'\s+',' ', s)

corpus=[json.loads(l) for l in open(os.path.join(RAW,"europepmc_corpus.jsonl"))]
corpus=[c for c in corpus if c.get('pmcid')]
print(f"articles with PMCID: {len(corpus)}")

edges=defaultdict(lambda: {'support':set(),'sentences':[],'chemicals':set()})
plant_meta={}
for i,c in enumerate(corpus):
    pmcid=c['pmcid']; doi=c.get('doi'); 
    anns=fetch_ann(pmcid)
    orgs=[a for a in anns if a.get('type')=='Organisms']
    diss=[a for a in anns if a.get('type')=='Diseases']
    chems=[a['exact'].lower() for a in anns if a.get('type')=='Chemicals']
    # resolve plants present in this article
    plants={}
    for a in orgs:
        r=resolve_plant(a['exact'])
        if r: plants[r['accepted']]=r; plant_meta[r['accepted']]=r
    conds={norm_cond(a['exact']) for a in diss if len(a['exact'])>3}
    conds={c for c in conds if c not in ('disease','diseases','disorder','disorders','infection','infections','syndrome')}
    # article-level co-occurrence = candidate ethnopharmacological association
    for p in plants:
        for cond in conds:
            e=edges[(p,cond)]
            e['support'].add(pmcid)
            if doi and len(e['sentences'])<3:
                e['sentences'].append({'pmcid':pmcid,'doi':doi,'title':c.get('title')})
            for ch in chems[:5]: e['chemicals'].add(ch)
    if (i+1)%25==0: print(f"  processed {i+1}/{len(corpus)} ...")

# write edges with confidence
out=os.path.join(PROC,"edges.jsonl")
rows=[]
for (p,cond),e in edges.items():
    sup=len(e['support'])
    conf=round(1-1/(sup+1),3)  # more supporting articles -> higher confidence
    rows.append({'plant':p,'plant_key':plant_meta[p].get('key'),'family':plant_meta[p].get('family'),
        'rank':plant_meta[p].get('rank'),'condition':cond,'support_articles':sup,
        'confidence':conf,'evidence':e['sentences'],'related_chemicals':sorted(e['chemicals'])[:8]})
rows.sort(key=lambda r:(-r['support_articles'], r['plant']))
with open(out,"w") as f:
    for r in rows: f.write(json.dumps(r)+"\n")
plants_n=len({r['plant'] for r in rows}); conds_n=len({r['condition'] for r in rows})
print(f"\nEDGES: {len(rows)} | plants: {plants_n} | conditions: {conds_n} | gbif-resolved names: {sum(1 for v in gbif.values() if v)}")
print("top edges by support:")
for r in rows[:12]:
    print(f"  {r['plant'][:34]:34} -> {r['condition'][:28]:28} support={r['support_articles']} conf={r['confidence']}")
