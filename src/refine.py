# Precision pass (offline, uses cached annotations + gbif cache):
# section-level co-occurrence, SPECIES/GENUS plants only, generic conditions dropped.
import json, os, re, glob
from collections import defaultdict

RAW=os.path.expanduser("~/ethnohack/data/raw")
PROC=os.path.expanduser("~/ethnohack/data/processed")
ANN=os.path.join(RAW,"annotations")
gbif=json.load(open(os.path.join(PROC,"gbif_cache.json")))
corpus={json.loads(l)['pmcid']:json.loads(l) for l in open(os.path.join(RAW,"europepmc_corpus.jsonl")) if json.loads(l).get('pmcid')}

GEN_COND={'disease','diseases','disorder','disorders','illness','illnesses','condition','conditions',
 'symptom','symptoms','ailment','ailments','infection','infections','syndrome','syndromes',
 'health problems','complaints','sickness','pathology','pathologies','abnormalities','ailment/disease'}
def norm(s): return re.sub(r'\s+',' ',s.strip().lower())
def plant_ok(name):
    r=gbif.get(name.strip().lower())
    return r if (r and r.get('rank') in ('SPECIES','GENUS')) else None

edges=defaultdict(lambda:{'arts':set(),'secpairs':set(),'ev':[],'chem':set()})
pmeta={}
for fp in glob.glob(os.path.join(ANN,"*.json")):
    pmcid=os.path.basename(fp)[:-5]
    c=corpus.get(pmcid,{}); doi=c.get('doi'); title=c.get('title')
    anns=json.load(open(fp))
    bysec=defaultdict(lambda:{'plants':{},'conds':{}})
    chems=[norm(a['exact']) for a in anns if a.get('type')=='Chemicals']
    for a in anns:
        sec=(a.get('section') or 'NA').split(' (')[0]
        if a.get('type')=='Organisms':
            r=plant_ok(a['exact'])
            if r: bysec[sec]['plants'][r['accepted']]=r; pmeta[r['accepted']]=r
        elif a.get('type')=='Diseases':
            cond=norm(a['exact'])
            if len(cond)>3 and cond not in GEN_COND:
                bysec[sec]['conds'][cond]=a
    for sec,g in bysec.items():
        for p in g['plants']:
            for cond,a in g['conds'].items():
                e=edges[(p,cond)]
                e['arts'].add(pmcid); e['secpairs'].add((pmcid,sec))
                if len(e['ev'])<3:
                    ctx=(a.get('prefix','')+' ['+a['exact']+'] '+a.get('postfix','')).strip()
                    e['ev'].append({'pmcid':pmcid,'doi':doi,'title':title,'section':sec,'context':ctx})
                for ch in chems[:4]: e['chem'].add(ch)

rows=[]
for (p,cond),e in edges.items():
    arts=len(e['arts'])
    rows.append({'plant':p,'plant_key':pmeta[p].get('key'),'family':pmeta[p].get('family'),
      'rank':pmeta[p].get('rank'),'condition':cond,'support_articles':arts,
      'cooccur_sections':len(e['secpairs']),
      'confidence':round(1-1/(arts+1),3),'evidence':e['ev'],'related_chemicals':sorted(e['chem'])[:6]})
rows.sort(key=lambda r:(-r['support_articles'],-r['cooccur_sections'],r['plant']))
json_all=os.path.join(PROC,"edges_all.jsonl"); json_hc=os.path.join(PROC,"edges_highconf.jsonl")
with open(json_all,"w") as f:
    for r in rows: f.write(json.dumps(r)+"\n")
hc=[r for r in rows if r['support_articles']>=2]
with open(json_hc,"w") as f:
    for r in hc: f.write(json.dumps(r)+"\n")
print(f"ALL edges: {len(rows)} (species/genus, specific conditions, section-level)")
print(f"HIGH-CONF (>=2 articles): {len(hc)} | plants:{len({r['plant'] for r in hc})} conditions:{len({r['condition'] for r in hc})}")
print("\ntop high-confidence species-level associations:")
for r in [x for x in rows if x['rank']=='SPECIES'][:14]:
    print(f"  {r['plant'][:36]:36} -> {r['condition'][:26]:26} arts={r['support_articles']} conf={r['confidence']}")
