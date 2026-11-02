# 🌿 TraceHerb — evidence-grounded ethnopharmacology knowledge graph

**EthnoHack 2026 · Track 1 (Traditional knowledge)**

TraceHerb mines open-access scientific literature to build a knowledge graph of
**plant → traditional/therapeutic use → condition** associations, where **every
edge traces back to the exact sentence and DOI it came from**, carries a
confidence score, and is only asserted when the source text actually expresses a
*use* — not a mere co-mention. The goal: make traditional-medicine knowledge
computable and auditable without ever presenting an unvalidated co-occurrence as
an established medical fact.

## Problem

Ethnobotanical and ethnopharmacological knowledge is scattered across thousands
of papers as free text. Existing structured databases are small, hand-curated,
and slow to update. Automated extraction tends to over-generate noisy links and
strip provenance — the opposite of what scientific use requires. TraceHerb tackles
**scale + provenance + honesty about uncertainty** together.

## Pipeline

```
Europe PMC (open-access ethnobotany/ethnopharmacology corpus)
  → Europe PMC Annotations API (Organisms / Diseases / Chemicals, with section)
  → section-level co-occurrence of plant × condition
  → GBIF species name resolution (keep SPECIES/GENUS, kingdom Plantae)
  → LLM relation extraction (pluggable: mock | anthropic | openai), grounded
  → confidence = f(distinct papers supporting the pair) + AI relation type
  → evidence-cited edge list  →  self-contained explorer dashboard
```

### AI / NLP layers (what does the work, and where)

| Layer | Technique | Where |
|---|---|---|
| **Named-entity recognition** | Europe PMC biomedical text-mining (Organisms/Diseases/Chemicals + section) | annotations API |
| **Name normalization** | GBIF fuzzy + taxonomic name matching → accepted species | `refine.py` |
| **Relation extraction** | LLM classifies each co-mention sentence → `{is_use, relation∈treats/prevents/manages, confidence, quote}`; pluggable provider, mock offline default | `ai_extract.py` |
| **Grounding / anti-hallucination** | the model's quote must be a verbatim span of the input sentence or the edge is rejected | `ai_extract.py:_parse` |
| **Confidence** | statistical aggregation across distinct supporting papers | `refine.py` |

The LLM only **labels sentences that already exist in the corpus** — it never
generates facts, and every asserted edge keeps its source sentence + DOI.
`AI_PROVIDER=mock` (rule+negation classifier) runs with no key so the demo always
works; set `AI_PROVIDER=anthropic|openai` with a key for the full model pass.

Design principle (shared with the "evidence-first" idea in the brief): **nothing
is asserted unless it traces to a recorded data point.** Each edge stores its
supporting PMCIDs/DOIs, the sentence context, the section, and a confidence.

## Tiers (precision / recall trade-off, reported honestly)

| Tier | Rule | Use |
|---|---|---|
| `edges_all` | species/genus + specific condition, section co-occurrence | recall-oriented exploration |
| `edges_highconf` | ≥ 2 distinct supporting papers | balanced |
| `edges_curated` | high-conf **and** a therapeutic-use cue in the cited sentence | precision-oriented (dashboard default) |

See `data/processed/validation.json` for the precision-proxy and recall-vs-gold
numbers and the stated limitations.

## Setup

**Requirements:** Python ≥ 3.8 only. **No pip installs** — every script uses the
standard library (`json`, `urllib`, `re`, `collections`). Network is needed for
the fetch/resolve steps (Europe PMC + GBIF public REST APIs, no keys); once the
corpus and annotations are cached the graph builds fully offline.

```bash
git clone <repo> && cd ethnohack
python3 --version        # 3.8+
```

## Run it (end to end)

```bash
# 1. fetch the literature corpus (no API key)
python3 src/fetch_corpus.py            # ~200 papers
#    or the larger corpus used in our results:
python3 src/fetch_corpus_1k.py         # ~1000 papers

# 2. cache Europe PMC entity annotations (resumable; re-run to resume)
python3 src/cache_annotations.py

# 3. build the graph  (GBIF name resolution cached in data/processed/gbif_cache.json)
python3 src/refine.py                  # -> edges_all.jsonl, edges_highconf.jsonl, edges_curated.jsonl

# 4. LLM relation extraction  (default mock = offline, no key)
python3 src/ai_extract.py              # -> edges_ai.jsonl (+ refreshes web/graph.json)
#    full model pass (optional):
#    AI_PROVIDER=anthropic ANTHROPIC_API_KEY=sk-ant-... python3 src/ai_extract.py
#    AI_PROVIDER=openai    OPENAI_API_KEY=sk-...        python3 src/ai_extract.py

# 5. validate  (precision proxy + recall vs curated gold set, seed=42)
python3 src/validate.py                # -> data/processed/validation.json

# 6. explore the graph
cd web && python3 -m http.server 8900  # open http://127.0.0.1:8900  (loopback only)
```

Steps 1–2 are already cached in the repo, so a judge can run **4 → 6** immediately
and reproduce the graph and dashboard offline.

## Results (1,000-paper corpus)

| Tier | Edges | Precision proxy | Recall vs 15 gold pairs |
|---|---|---|---|
| Recall (`edges_highconf`, ≥2 papers) | 7,113 | 0.43 | **0.93** (14/15) |
| Precision (`edges_ai`, LLM use-asserted) | 3,040 | **1.00** | 0.67 (10/15) |

516 plant species · 227 conditions · relations: 2,554 treats / 462 manages / 24
prevents · 0 grounding rejections. Full numbers + limitations in
`data/processed/validation.json`.

## Data sources & licences

| Source | Used for | Access | Licence / attribution |
|---|---|---|---|
| **Europe PMC** | corpus + entity annotations | REST API (`ebi.ac.uk/europepmc`), no key | Open-access subset; cite each article DOI. Europe PMC © EMBL-EBI |
| **GBIF** | plant name → accepted species resolution | REST API (`api.gbif.org/v1/species/match`) | GBIF Backbone Taxonomy, CC BY 4.0 — attribute GBIF |
| **Dr. Duke's Phytochemical & Ethnobotanical DB** | optional compound/activity enrichment | USDA | Public domain (U.S. Government work) |
| **LOTUS / NPASS / COCONUT** | optional natural-product↔target depth | bulk TSV/SDF | CC0 / CC BY (per dataset) |

## Responsible-research notes

- Associations are **literature co-occurrences with a use-cue**, not verified
  causal, clinical, or safety claims. The UI states this prominently.
- No personal or patient data is used.
- Traditional-knowledge attribution: edges cite the source literature; this tool
  surfaces published knowledge and does not claim ownership of it.
- Computational predictions are presented with confidence and provenance, never
  as established medical fact.

## Repo layout

```
src/        fetch_corpus.py · cache_annotations.py · refine.py · validate.py
data/raw/   europepmc_corpus.jsonl · annotations/ (cached per article)
data/processed/  edges_all|highconf|curated.jsonl · gbif_cache.json · validation.json
web/        index.html · graph.json   (self-contained explorer)
docs/       slides, architecture
```
