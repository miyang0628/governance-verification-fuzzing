# Fuzzing the Verification Layer of AI-Based Decision Support

Reproducibility repository for the paper **"Fuzzing the Verification Layer of
AI-Based Decision Support: Reasoning-Validity Defects that Reference-Free Metrics
Miss in Automated Credit Assessment."**

> **Anonymized for double-blind review.** Author, affiliation, and funding details
> are intentionally omitted and will be restored in the camera-ready version.

---

## Overview

AI governance regimes (the EU AI Act, the NIST AI RMF, Korea's AI Framework Act)
require high-stakes AI systems to be verified for accuracy, robustness, and
reliability. In practice that verification is often discharged with **reference-free
technical metrics** (RAG-style faithfulness), which score whether an output is
consistent with its inputs but set aside whether the resulting *judgment* is valid.

This repository **fuzzes the verification layer itself.** Using automated corporate
credit assessment as a decision-support testbed, it applies controlled
metamorphic/fuzzing-style perturbations to two parallel scoring channels — an **LLM
judge** and an **input-grounded faithfulness metric** — and measures which defects
each channel fails to register.

### Key findings

- **Reasoning-validity blind spot.** Reversing an override rationale's support
  direction (P4) collapses the LLM judge (drop **1.79**, paired **d_z ≈ 1.24**,
  Holm-corrected **p < 10⁻⁷**) while the input-grounded faithfulness metric barely
  moves (**0.30**).
- **Complementarity, not supremacy.** On a purely factual error (P3) the metric is
  the stronger detector (drop **1.08** vs. judge 0.19; Holm **p < 0.001**) — the two
  channels catch *different* defects.
- **Not just grade inconsistency.** The P4 effect survives when the grade is hidden
  from the judge, and an internally-consistent "wrong-direction" variant (P4b) is
  penalized just as hard — the judge reacts to the *direction of the reasoning*, not
  a grade–rationale mismatch.
- **Robust.** The effect replicates across three judge models (d_z 0.46 / 0.71 /
  1.26, weak→strong), is stable across five generation seeds (d_z 1.34–1.62), and
  its bootstrap CI excludes zero.
- **Circularity diagnostic.** A generation×judging ablation separates the judge's
  own competence from artifacts of how the audited outputs were produced.
- **Governance mapping.** Each defect is mapped to the accuracy/robustness/
  verification clauses of the three regimes; only **NIST MEASURE 2.13** explicitly
  requires the verification *method itself* to be verified.

---

## Repository structure

```
.
├── README.md
├── requirements.txt
├── .env.example
├── src/
│   └── common.py              # shared paths, .env loader, grayscale plotting, savers
├── notebooks/
│   ├── 0_proxy_overrides.ipynb   # stand-alone proxy, notch gap, override subset
│   ├── 1_generate_perturb.ipynb  # (LLM) rating+rationale generation, P1–P5 perturbations
│   ├── 2_score.ipynb             # (LLM) judge + faithfulness + judge-models + construct + inter-judge
│   ├── 3_tables.ipynb            # (offline) all statistics and tables
│   ├── 4_figures.ipynb           # (offline) all figures + decision-impact simulation
│   └── 5_diagnostics.ipynb       # (offline/LLM) override floor, P2 metric, P4b magnitude, seed stability
├── paper/                    # LaTeX source (Elsevier elsarticle)
│   ├── main.tex
│   ├── appendix.tex
│   ├── sections/
│   ├── figures/
│   └── references.bib
├── data/                     # NOT redistributed — reconstructed from public sources (see below)
└── results/
    ├── figures/              # grayscale 600-dpi PNG + PDF
    └── tables/               # CSV + LaTeX
```

---

## Pipeline

All API spend is in notebooks **1** and **2**; notebooks **3**, **4**, and the
offline blocks of **5** need no API. Run strictly in order:

```
0_proxy_overrides → 1_generate_perturb → 2_score → 3_tables → 4_figures → 5_diagnostics
```

Parquet checkpoints connect the notebooks:

```
0 → data/with_override.parquet
1 → data/generated.parquet, data/perturbed.parquet
2 → data/scored.parquet, data/judge_models.parquet,
    data/construct_scored.parquet, data/interjudge.parquet
3 → results/tables/*.csv (+ .tex)
4 → results/figures/*.{png,pdf}, results/tables/tab_decision_impact.csv
5 → results/tables/{tab_floor_sensitivity, tab_p2_metric_diagnosis,
    tab_p4b_notch_sensitivity, tab_multiseed_p4, tab_override_summary}
```

The five perturbations (P1–P5) each corrupt one aspect of a generated
`(rating, rationale)` pair while holding the rest fixed:

| Code | Name | Manipulation |
|---|---|---|
| P1 | rating–rationale inconsistency | shift the grade by *k* notches, keep the text |
| P2 | remove qualitative justification | delete the support clause(s), keep the grade |
| P3 | factual error | inject a quantitative claim contradicting the input |
| P4 | direction flip | reverse the support polarity, keep the grade |
| P5 | verbosity control | pad with repetition; content unchanged |

---

## Data

The corpus pairs three **public** layers; raw and intermediate data are **not
redistributed** but are fully reconstructible:

1. **Quantitative** — standardized financial ratios with agency ratings from a
   public corporate-rating dataset (keyed by ticker, agency, rating date).
2. **Narrative** — each firm's actual 10-K MD&A (Item 7) from the **EDGAR-CORPUS**
   collection of SEC filings (keyed by CIK and fiscal year).
3. **Linkage** — tickers resolved to CIKs via the SEC `company_tickers.json`
   mapping; a rating in year *Y* is matched to the filing for year *Y* or *Y−1*.

After excluding incorporation-by-reference MD&A stubs, the analysis corpus holds
**1,219 (firm × rating date) instances across 361 firms**. The qualitative-override
subset (outside the 80% predictive band **and** |notch gap| ≥ 1.5×MAD = 1.45) is
**114 instances (9.4%)**; paired tests average same-firm-year instances, giving
**99 unique override firm-years**.

Place the reconstructed join at `data/corpus_main.parquet` before running
notebook 0 (see the notebook header for the exact schema).

---

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env     # then fill in your keys/model tiers
```

`.env`:

```
OPENAI_API_KEY=sk-...
LLM_MODEL_WEAK=gpt-4o-mini
LLM_MODEL_MID=gpt-5.4-mini
LLM_MODEL_STRONG=gpt-5.4
```

`requirements.txt`: `numpy`, `pandas`, `pyarrow`, `scikit-learn`, `scipy`,
`statsmodels`, `matplotlib`, `seaborn`, `openai`, `python-dotenv`.

---

## Running

Open the notebooks in order (Jupyter / VS Code) and run each top-to-bottom.
Cost controls live at the top of each LLM notebook:

- `1_generate_perturb`: `MAX_CASES = None` (full 114 override subset) — set an int
  for a cheap smoke-test first.
- `2_score`: toggle `RUN_JUDGE_PROXY`, `RUN_PRODUCTION_FAITH`, `RUN_JUDGE_MODELS`,
  `RUN_CONSTRUCT`, `RUN_INTERJUDGE`; `MAX_WORKERS` sets API concurrency.
- Faithfulness is computed only on the `gap_given` outputs any analysis consumes,
  and calls run concurrently, so a full run is ≈ 8.4k API calls.

### Reproducibility notes

- Temperatures are fixed (0 for judging and the metric, low for generation) and
  the model configuration is read from `.env`; the OpenAI `seed` parameter is used
  where supported.
- LLM scores are **not** bit-for-bit reproducible across provider API versions, so
  the effect **directions** and the divergence structure — not point magnitudes —
  are the findings we stand behind. Notebook 5 quantifies run-to-run stability.

---

## Building the paper

```bash
cd paper
pdflatex main.tex && bibtex main && pdflatex main.tex && pdflatex main.tex
```

Elsevier `elsarticle` class; references in the numbered Elsevier style.

---

## License & citation

Code released for reproduction. A citation entry and license will be added with the
camera-ready version.

```bibtex
@article{anonymous_fuzzing_verification,
  title   = {Fuzzing the Verification Layer of AI-Based Decision Support:
             Reasoning-Validity Defects that Reference-Free Metrics Miss in
             Automated Credit Assessment},
  author  = {Anonymous},
  journal = {under review},
  year    = {2026}
}
```
