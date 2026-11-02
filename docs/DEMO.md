# TraceHerb — pitch & demo script (~7 min)

Read the **"SAY"** lines; do the **[DO]** actions on screen. Have the dashboard
open at http://127.0.0.1:8900 before recording.

---

## 0 · Intro (20s)
**SAY:** "Hi, I'm Chitaranjan. My project is **TraceHerb** — for EthnoHack Track 1,
traditional knowledge. It turns thousands of research papers into an
evidence-grounded knowledge graph of which plants are traditionally used for
which conditions — where every single link traces back to the exact sentence and
paper it came from."

## 1 · The problem (40s)
**SAY:** "Traditional-medicine knowledge is scattered across thousands of papers
as free text. The structured databases we have are small and hand-curated, so
they're slow and incomplete. And when people try to automate extraction, they
over-generate noisy links and throw away the source — which makes the result
useless for real science, because you can't check it. So I set out to solve three
things at once: **scale, provenance, and honesty about uncertainty.**"

## 2 · The product — open the dashboard (40s)
**[DO]** Show the dashboard; point at the KPI strip.
**SAY:** "This is built from **1,000 open-access papers**. From them the pipeline
produced about **7,000 candidate plant–condition links**, and **3,040** that pass
AI use-verification — across **516 plant species and 227 conditions.** Let me show
you how it works from a user's point of view."

## 3 · Search a plant (50s)
**[DO]** Type **Zingiber officinale** (ginger); click it.
**SAY:** "I search for ginger. Instantly I get its associated conditions —
diabetes, digestive disorders, malaria, hypertension — each ranked by how many
papers support it, with a confidence score, and a **relation type**: does the
literature say this plant *treats*, *manages*, or *prevents* the condition. These
aren't guesses."

## 4 · The evidence trace — the key moment (50s)
**[DO]** Point at the cited sentence + DOI under an edge; click the DOI.
**SAY:** "Here's what makes TraceHerb different. Every link shows the **actual
sentence** it was extracted from — 'ginger is used to manage hypertension' — and a
**clickable DOI** to the source paper. Nothing is asserted unless it traces to a
real, recorded data point. A hallucinated fact literally cannot enter this graph —
I'll come back to how I guarantee that."

## 5 · Flip the direction (30s)
**[DO]** Toggle **By condition**; pick **diabetes**.
**SAY:** "It works both ways. Start from a condition — diabetes — and see which
plants the literature associates with it, ranked and evidence-cited. This is how a
researcher generates hypotheses for drug discovery."

## 6 · How it works (90s)
**SAY:** "Under the hood, four layers. **One** — I pull an open-access corpus from
**Europe PMC** and run its biomedical text-mining to tag organisms, diseases and
chemicals in every paper. **Two** — I resolve every messy plant name to an
accepted species through **GBIF**, so synonyms and misspellings collapse to one
node. **Three** — for each sentence where a plant and a condition co-occur, an
**LLM classifies whether it's actually a therapeutic-use claim**, and extracts the
relation. It's a pluggable provider — it runs offline with a rule-based default so
the demo needs no API key, and plugs into a real model with one environment
variable. **Four**, and this is the guarantee: the model's answer must quote a
**verbatim span of the source sentence**, or the edge is **rejected** — that's the
grounding check that makes hallucination impossible."

## 7 · Rigor — the differentiator (60s)
**[DO]** Show `data/processed/validation.json`.
**SAY:** "I measured my own error, with a fixed seed so it's reproducible. I report
**two tiers.** The recall tier recovers **93% of a gold set of textbook
plant–use associations** — 14 of 15. The precision tier, which only keeps links
the model verifies as a genuine use, is **100% use-cited** on a random sample. I
state the trade-off and the limitations openly: these are literature
co-occurrences with a use-cue, **not** verified clinical facts — and the interface
says so."

## 8 · Impact & future (40s)
**SAY:** "The impact: traditional knowledge becomes **computable and auditable** —
researchers can generate drug-discovery leads in minutes with full provenance,
instead of reading thousands of papers by hand. Next steps: scale from a thousand
papers to the full corpus, add a compound-to-target layer using LOTUS and NPASS,
and let the real LLM pass replace the offline default. Everything's open source,
runs with one command, and every claim is traceable. Thank you."

---

### Numbers cheat-sheet (say confidently)
- 1,000 open-access papers · ~7,113 candidate links · **3,040** AI use-verified
- **516** plant species · **227** conditions · relations 2,554 treats / 462 manages / 24 prevents
- Recall tier: **0.93** recall (14/15 gold) · Precision tier: **1.00** precision proxy
- Stack: pure-Python stdlib · Europe PMC + GBIF APIs · pluggable LLM · one-command run
