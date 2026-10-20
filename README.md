# Fuzzing the Verification Layer of AI Governance

*Anonymous repository for double-blind peer review.*
*Authors and affiliations are withheld. Manuscript under review at an anonymous venue.*

---

## Overview

This repository accompanies a study that applies **metamorphic / fuzzing-style
perturbations to the *verification layer* of AI governance** — the automated
methods that decide whether an AI-generated judgment passes review. Using
automated corporate credit assessment (AAA–D letter ratings with written
rationales) as the empirical testbed, it shows that reference-free technical
metrics (RAG-faithfulness style) are structurally insensitive to
reasoning-validity defects that a governance framework's "verification"
requirement is meant to catch, whereas an LLM judge detects them — and it
diagnoses, with a generation × judging ablation, when apparent robustness is an
artifact of the test design rather than a property of the verifier.

The empirical corpus pairs public financial ratios and agency ratings with the
firm's actual 10-K **Management's Discussion and Analysis (MD&A)** text, so the
evaluated rationales are grounded in genuine disclosures rather than only in
model-generated text.

## Method in brief

A quantitative stand-alone-credit-profile proxy with an 80% predictive interval
yields a signed **notch gap** and isolates a **qualitative-override** subset.
Each override's generated (rating, rationale) is subjected to five controlled
perturbations, and every variant is scored on two channels — an **LLM judge**
(qualitative-adequacy axis) and an **input-grounded faithfulness metric** —
whose signed, paired, Holm-corrected difference is the metric–judgment
divergence. A 2×2 generation × judging ablation separates what the judge
detects on its own from what the data-generating protocol handed it.

| Code | Perturbation | A sound judge should… |
|------|--------------|------------------------|
| P1 | rating–rationale inconsistency | drop |
| P2 | remove qualitative justification | drop (but see the circularity ablation) |
| P3 | factual error | the **metric** is the better detector here |
| P4 | direction flip | drop — the central, robust signal |
| P5 | verbosity padding | stay robust (surface form only) |

## Suggested repository name

`governance-verification-fuzzing` (neutral, descriptive, reveals no author
identity). Alternatives: `verifier-robustness-credit`, `fuzzing-ai-governance`.

## Repository layout

```
.
├── data/                # inputs & intermediates (NOT committed — see below)
├── notebooks/           # single-cell notebooks, run in numeric order
│   ├── 00_proxy_override.ipynb     # SACP proxy, notch gap, override subset
│   ├── 01_generation.ipynb         # rating+rationale generation (gap-given/blind)
│   ├── 02_perturbation.ipynb       # controlled defects P1–P5
│   ├── 03_judge_metric.ipynb       # LLM judge + input-grounded faithfulness
│   ├── 04_ablation.ipynb           # divergence tests, 2×2 ablation, agreement
│   └── 05_figures_tables.ipynb     # final grayscale figures & tables
├── src/
│   └── common.py        # shared paths, .env loader, grayscale plotting, savers
├── results/
│   ├── figures/         # PNG + PDF at 600 dpi (no captions)
│   └── tables/          # CSV + LaTeX
├── requirements.txt
├── .env.example
└── .gitignore
```

## Setup

```bash
python -m venv .venv && source .venv/bin/activate   # or conda
pip install -r requirements.txt
cp .env.example .env            # then fill in your OpenAI key
```

Create a `.env` file at the repository root (used by every notebook):

```
OPENAI_API_KEY=<your key>
LLM_MODEL_WEAK=<small model>
LLM_MODEL_MID=<mid model>
LLM_MODEL_STRONG=<strong model>
```

`.env` is git-ignored and must never be committed.

## Running

Open the notebooks in `notebooks/` and run them in order (00 → 05). Each is a
**single cell** with all code and English comments; each reads its inputs from
`data/` and writes intermediates back to `data/`, and figures/tables to
`results/`. Notebooks 01–03 call the LLM API — start with the small `MAX_CASES`
cap in `01` to check cost, then raise it to the full override subset.

### Pipeline inputs/outputs

| Notebook | reads | writes |
|----------|-------|--------|
| 00 | `data/corpus_main.parquet` | `data/with_override.parquet`, override figure/table |
| 01 | `data/with_override.parquet` | `data/generated.parquet` |
| 02 | `data/generated.parquet` | `data/perturbed.parquet` |
| 03 | `data/perturbed.parquet` | `data/scored.parquet` |
| 04 | `data/scored.parquet` | divergence & ablation tables |
| 05 | `data/scored.parquet`, tables | publication figures |

## Data availability

Raw and intermediate data are **not** redistributed in this repository
(`data/` is git-ignored) for licensing and size reasons. All inputs are public
and reconstructible:

- **Financial ratios + agency ratings** — a public corporate-rating dataset
  (financial ratios keyed by ticker, agency, and rating date).
- **MD&A narrative text** — the `edgar-corpus` collection of SEC 10-K filings,
  section 7 (MD&A). Fetched per year as JSON Lines and joined to the ratings on
  (CIK, fiscal year); CIK is resolved from the ticker via the SEC
  `company_tickers.json` mapping.

A build step assembles `data/corpus_main.parquet` (financials + rating + MD&A).
MD&A entries below a length floor (incorporation-by-reference stubs) are flagged
and excluded from the main corpus; a sensitivity check confirms the exclusion
does not materially change the sector composition.

## Methodological notes

- **Leakage control.** The same firm appears in several rows (multiple rating
  dates/agencies). The proxy is fit with a **firm-grouped** cross-validation
  split (GroupKFold on the firm identifier) so it predicts genuinely unseen
  firms; a plain shuffled split collapses the residual scale and erases the
  override subset.
- **Override floor.** The override floor scales to the realized residual spread
  rather than using a fixed notch cutoff, so the predictive-band criterion is
  not starved when the proxy is accurate.

## Figures

All figures are produced with seaborn in **grayscale**, **without captions**
(captions live in the manuscript), at **600 dpi**, and saved as both **PNG and
PDF** via `src/common.save_fig`.

## Reproducibility

A fixed random seed governs the proxy's cross-validation folds. LLM calls use
temperature 0 for judging/metric and low temperature for generation; LLM outputs
are not bit-for-bit deterministic across API versions, so exact score magnitudes
may vary while the effect **directions** and the **divergence structure** are
the reported findings. To reproduce end-to-end, reconstruct
`data/corpus_main.parquet` as described above and run the notebooks in order.

## License

Code released under the MIT License (see `LICENSE`). Third-party data are
subject to their own licenses.
