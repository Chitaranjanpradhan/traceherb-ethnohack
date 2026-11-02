# LLM relation extraction, grounded in cited sentences. Pluggable provider.
#   AI_PROVIDER=mock (default, offline, no key) | anthropic | openai
# For each candidate plant×condition edge, classify its evidence sentences:
#   is this a *therapeutic-use* claim? -> {is_use, relation, confidence, quote}
# The model only LABELS sentences that exist in the corpus; the quote must be a
# substring of the input (grounding check) or the output is rejected -> no hallucinated fact.
import json, os, re, sys, urllib.request
PROC=os.path.expanduser("~/ethnohack/data/processed")
PROVIDER=os.environ.get("AI_PROVIDER","mock")

SCHEMA_HINT=('Return ONLY JSON: {"is_use":bool,"relation":"treats|prevents|manages|none",'
 '"confidence":0..1,"quote":"<exact span from the sentence>"}')

def prompt(sent, plant, cond):
    return (f'Sentence: "{sent}"\nPlant: {plant}\nCondition: {cond}\n'
      f'Does the sentence assert that this plant is traditionally or therapeutically '
      f'USED FOR this condition (treat/prevent/manage)? Base the answer only on the sentence. {SCHEMA_HINT}')

CUE=re.compile(r'\b(treat|treating|treatment|treated|remedy|remedies|cure[sd]?|manage[sd]?|management|'
  r'against|therap|medicinal|heal(s|ed|ing)?|relief|relieve|alleviat|used (to|for|against|in)|'
  r'ethnomedicin|traditional(ly)? used|administered for|prescribed for)\b', re.I)
PREVENT=re.compile(r'\b(prevent|prophyla|protect(s|ive)? against)\b',re.I)
MANAGE=re.compile(r'\b(manage|management|control(s|led)?|alleviat|relief|relieve)\b',re.I)
NEG=re.compile(r'\b(no (significant )?effect|not (used|effective|recommended)|ineffective|lack of|'
  r'no evidence|failed to|contraindicat|toxic|adverse|poison)\b',re.I)

def classify_mock(sent, plant, cond):
    s=sent
    if NEG.search(s): return {"is_use":False,"relation":"none","confidence":0.3,"quote":s[:120]}
    if CUE.search(s):
        rel="prevents" if PREVENT.search(s) else ("manages" if MANAGE.search(s) else "treats")
        return {"is_use":True,"relation":rel,"confidence":0.72,"quote":s[:160]}
    return {"is_use":False,"relation":"none","confidence":0.4,"quote":s[:120]}

def call_json(url, headers, body):
    req=urllib.request.Request(url, data=json.dumps(body).encode(), headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=60) as r: return json.load(r)

def classify_anthropic(sent, plant, cond):
    key=os.environ["ANTHROPIC_API_KEY"]
    d=call_json("https://api.anthropic.com/v1/messages",
      {"x-api-key":key,"anthropic-version":"2023-06-01","content-type":"application/json"},
      {"model":os.environ.get("AI_MODEL","claude-3-5-haiku-latest"),"max_tokens":200,
       "messages":[{"role":"user","content":prompt(sent,plant,cond)}]})
    return _parse(d["content"][0]["text"], sent)

def classify_openai(sent, plant, cond):
    key=os.environ["OPENAI_API_KEY"]
    d=call_json("https://api.openai.com/v1/chat/completions",
      {"Authorization":f"Bearer {key}","content-type":"application/json"},
      {"model":os.environ.get("AI_MODEL","gpt-4o-mini"),"temperature":0,
       "messages":[{"role":"user","content":prompt(sent,plant,cond)}]})
    return _parse(d["choices"][0]["message"]["content"], sent)

def _parse(text, sent):
    m=re.search(r'\{.*\}', text, re.S)
    if not m: return {"is_use":False,"relation":"none","confidence":0.0,"quote":""}
    try: o=json.loads(m.group(0))
    except Exception: return {"is_use":False,"relation":"none","confidence":0.0,"quote":""}
    # GROUNDING: quote must be a real span of the sentence, else reject the claim
    q=(o.get("quote") or "").strip().strip('.')
    if q and q.lower() not in sent.lower():
        o["is_use"]=False; o["grounding_failed"]=True
    return o

CLASSIFY={"mock":classify_mock,"anthropic":classify_anthropic,"openai":classify_openai}[PROVIDER]

edges=[json.loads(l) for l in open(os.path.join(PROC,"edges_highconf.jsonl"))]
kept=[]; grounding_rejects=0
for e in edges:
    best=None
    for ev in e["evidence"]:
        sent=re.sub(r'[\[\]]','', ev.get("context",""))
        if not sent.strip(): continue
        r=CLASSIFY(sent, e["plant"], e["condition"])
        if r.get("grounding_failed"): grounding_rejects+=1
        if r.get("is_use") and (best is None or r["confidence"]>best["confidence"]):
            best={**r,"sentence":sent,"doi":ev.get("doi"),"pmcid":ev.get("pmcid")}
    if best:
        e2=dict(e); e2["ai_relation"]=best["relation"]; e2["ai_confidence"]=best["confidence"]
        e2["ai_provider"]=PROVIDER; e2["ai_quote"]=best["sentence"]
        kept.append(e2)
out=os.path.join(PROC,"edges_ai.jsonl")
with open(out,"w") as f:
    for e in kept: f.write(json.dumps(e)+"\n")
# refresh dashboard to the AI-extracted set
graph={"edges":[{"p":e["plant"],"fam":e["family"],"c":e["condition"],"n":e["support_articles"],
  "conf":e["confidence"],"rel":e["ai_relation"],"aiconf":e["ai_confidence"],
  "ev":e["evidence"],"chem":e["related_chemicals"]} for e in kept]}
json.dump(graph, open(os.path.expanduser("~/ethnohack/web/graph.json"),"w"))
from collections import Counter
rels=Counter(e["ai_relation"] for e in kept)
print(f"provider={PROVIDER}  input edges={len(edges)}  AI-asserted use-edges={len(kept)}")
print(f"grounding rejections={grounding_rejects}  relations={dict(rels)}")
print(f"plants={len({e['plant'] for e in kept})} conditions={len({e['condition'] for e in kept})}")
