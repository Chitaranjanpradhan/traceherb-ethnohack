# Reproducible validation of TraceHerb edges: precision proxy + recall vs curated gold set.
import json, os, re, random
PROC=os.path.expanduser("~/ethnohack/data/processed")
edges=[json.loads(l) for l in open(os.path.join(PROC,"edges_highconf.jsonl"))]
random.seed(42)

# --- (1) PRECISION PROXY: sample edges, check cited sentences for a therapeutic-use cue ---
CUES=re.compile(r'\b(treat|treating|treatment|treated|remedy|remedies|cure[sd]?|manage|management|'
  r'against|therap|medicinal|heal(s|ed|ing)?|relief|relieve|alleviat|used (to|for|against|in)|'
  r'for the treatment|efficacy|ethnomedicin|traditional(ly)? used)\b', re.I)
sample=random.sample(edges, min(60, len(edges)))
hits=0; detail=[]
for e in sample:
    cued=any(CUES.search(ev.get('context','')) for ev in e['evidence'])
    hits+=cued
    detail.append({'plant':e['plant'],'condition':e['condition'],'support':e['support_articles'],
                   'therapeutic_cue':cued,
                   'sample_sentence':(e['evidence'][0]['context'] if e['evidence'] else '')})
precision_proxy=round(hits/len(sample),3)

# --- (2) RECALL vs curated gold set (well-established ethnopharmacology associations) ---
GOLD=[("Zingiber","nausea|digestive|gastro"),("Allium sativum","hypertension|blood pressure|cholesterol"),
 ("Curcuma","inflammation|arthriti|anti-inflammator"),("Artemisia","malaria|fever"),
 ("Aloe","skin|burn|wound"),("Cassia|Senna","constipation|laxative"),
 ("Azadirachta","skin|infection|antimicrobial|gastro"),("Psidium guajava","diarrh|gastro"),
 ("Ocimum","respiratory|cough|cold|fever"),("Withania","stress|anxiety|sleep|immun"),
 ("Camellia sinensis","antioxidant|cardio|cholesterol"),("Moringa","diabetes|nutrition|inflammation"),
 ("Hibiscus","hypertension|blood pressure"),("Mentha","digestive|gastro|nausea"),
 ("Glycyrrhiza|Licorice","cough|respiratory|gastro|ulcer")]
def covered(genus_pat, cond_pat):
    gp=re.compile(genus_pat,re.I); cp=re.compile(cond_pat,re.I)
    return any(gp.search(e['plant']) and cp.search(e['condition']) for e in edges)
gold_res=[(g,c,covered(g,c)) for g,c in GOLD]
recall=round(sum(1 for *_,ok in gold_res if ok)/len(GOLD),3)

report={
 "corpus":"Europe PMC open-access ethnobotany/ethnopharmacology (200 articles)",
 "edges_total":len(edges),
 "precision_proxy":{"sampled":len(sample),"with_therapeutic_cue":hits,"rate":precision_proxy,
   "method":"fraction of sampled edges whose cited sentence contains an explicit use/treatment cue (rule-based, reproducible, seed=42)"},
 "recall_vs_gold":{"gold_pairs":len(GOLD),"recovered":sum(1 for *_,ok in gold_res if ok),"rate":recall,
   "detail":[{"plant_pattern":g,"condition_pattern":c,"recovered":ok} for g,c,ok in gold_res]},
 "limitations":[
   "Associations are literature CO-OCCURRENCES within a section, not verified causal/clinical facts.",
   "Section-level co-occurrence can still capture incidental mentions; precision proxy measures only presence of a use-cue sentence.",
   "Corpus limited to 200 OA articles; coverage skews to well-studied taxa and English literature.",
   "GBIF match accepted at species/genus; homonyms and vernacular names may mis-resolve."]}
json.dump(report, open(os.path.join(PROC,"validation.json"),"w"), indent=2)
json.dump(detail, open(os.path.join(PROC,"validation_sample.json"),"w"), indent=2)
print(f"PRECISION PROXY: {hits}/{len(sample)} = {precision_proxy} (edges whose cited sentence has a use/treatment cue)")
print(f"RECALL vs gold: {report['recall_vs_gold']['recovered']}/{len(GOLD)} = {recall}")
print("missed gold pairs:")
for g,c,ok in gold_res:
    if not ok: print("  -",g,"→",c)
