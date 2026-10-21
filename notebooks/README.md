# Consolidated pipeline (5 notebooks) + two patches

The 12 notebooks are merged into **5**, run strictly in order. All API spend is in
notebooks **1** and **2**; notebooks **3** and **4** are offline. Re-run from `0`.
`src/common.py` and `.env` are unchanged and not included — keep your local copies.

```
0_proxy_overrides   (offline)  = old 00
1_generate_perturb  (LLM)      = old 01 + 02
2_score             (LLM)      = old 03 + 03b + 03c(patched) + 03d + 06   → writes score parquets only
3_tables            (offline)  = old 04 + 08 + table halves of 03c/03d/06/03b
4_figures           (offline)  = old 05 + 07(patched)
```

## Notebook 5 — second-round diagnostics (R3, R4, R6, R7)

`5_diagnostics.ipynb` runs **after 0–2** and adds four independently-toggleable
blocks that answer the second-round review. Each writes its own table/figure.

| Block | Review point | API? | What it does |
|---|---|---|---|
| **D** | **R7** (stale override summary) | no | Recomputes MAD, 80%-band coverage, band-exceedance count, and the floor-sensitivity table **from `with_override.parquet`**, and **overwrites `tab_override_summary.csv`** so the data section + appendix match the override count used in analysis. Paste its printout into the data section and the appendix floor table. |
| **A** | **R3** (why metric drops on P2) | optional | Correlates the P2 proxy-metric drop with characters removed, and (LLM) decomposes it into claim-count (`total`) vs entailment-rate. Shows whether the P2 "metric drop" is a length/claim-count artifact. |
| **C** | **R4** (P4b magnitude) | yes | Repeats the P4b construct test at grade moves of 1/2/3 notches; reports judge drop + `d_z` per magnitude so you can show the result is not an artifact of `CONSTRUCT_NOTCH=2`. |
| **B** | **R6** (run-to-run stability) | yes | Re-generates + re-flips + re-judges a `K_CASES` subsample under several `SEEDS` (OpenAI `seed` param), reporting the P4 `d_z` distribution (mean/sd/range) across seeds. |

Toggles: `RUN_D_FLOOR, RUN_A_P2, RUN_A_LLM, RUN_C_P4B, RUN_B_SEED`. Block D is free
(offline); B is the most expensive (`K_CASES × SEEDS ×` ~4 calls, default 40×5).

> **R7 fix in one step:** run Block D, then copy its `tab_override_summary` numbers
> (MAD, coverage, n_outside) into the data section and its `tab_floor_sensitivity`
> rows into the appendix table, replacing the `(regen.)` placeholders. No manual
> recomputation needed — it reads the current `with_override.parquet`.

## Data flow (parquet checkpoints between notebooks)

```
0 → data/with_override.parquet
1 → data/generated.parquet, data/perturbed.parquet
2 → data/scored.parquet, data/judge_models.parquet,
    data/construct_scored.parquet, data/interjudge.parquet
3 → results/tables/*.csv (+ .tex)
4 → results/figures/*.{png,pdf}, results/tables/tab_decision_impact.csv
```

## The two patches

**Patch 1 — faithfulness metrics (in `2_score`).** Two fixes:
- **Proxy faithfulness is reverted to the paper's ORIGINAL metric** — it scores the
  rationale *alone* (no financial profile passed). Passing the terse numeric
  profile floored it and destroyed its P3 sensitivity; this restores the published
  behaviour (catches P3, blind to P4).
- **Production faithfulness** extracts **only quantitative/factual claims** and
  verifies them against the **financial profile ONLY** (MD&A is *not* used — adding
  it made the verifier rubber-stamp everything, high-flat with no P3 signal). The
  profile lets an injected contradicting number (P3) be caught, while a reversed
  *qualitative* support argument (P4) changes no quantitative claim, so the metric
  stays blind to P4 — the comparison the review asked for. A commented block shows
  how to swap in the `ragas` package instead.

> After the run, check `fig_faith_proxy_vs_rag`: the **proxy** should have range and
> dip on P3; the **production** metric should also dip on P3 and stay flat on P4. If
> the production metric floors again, fall back to reporting the proxy at several
> metric-model tiers (we can wire that in).

**Patch 2 — decision-impact thresholds (in `4_figures`).** The fixed `3.0` gate was
unfair to the faithfulness channel (whose ×5 values sit well below 3), so it
rejected valid outputs wholesale and the production-metric gate was degenerate.
Each channel now uses its **own optimal operating point (Youden's J on validity)**
via `sklearn.metrics.roc_curve`; the sklearn `+inf` sentinel threshold is dropped.
The gates are therefore compared at each channel's best cut, not a shared one.

## API call counts per block (full n=114 override subset)

Notebook 1: generation 228 + edits (P2/P3/P4) 684 = **912 calls**.

Notebook 2 (all blocks on):

| Block | records | calls/record | calls |
|---|---|---|---|
| Block1 judge (informed+blind) | 1,824 perturbed rows (2 conditions × 8 variants × 114) | 2 | 3,648 |
| Block1 proxy faithfulness | 912 **gap_given** rows only | 1 | 912 |
| Block1 production faithfulness | 912 **gap_given** rows only | 2 (extract+verify) | 1,824 |
| Block2 judge-models | 342 (gap_given × {P0,P3,P4}) | 3 models | 1,026 |
| Block3 construct | 456 ({P0,P1,P4,P4b}) | 2 (grade shown/hidden) | 912 |
| Block4 inter-judge | 60 sample | 1 | 60 |
| **Total** | | | **8,382** |

Two speedups are already applied: **(a)** faithfulness is computed only on
`gap_given` rows — the only ones any analysis reads — which removes 2,736 wasted
calls versus scoring both conditions; **(b)** all calls run concurrently across
`MAX_WORKERS` threads (default 8), so wall-clock ≈ total/`MAX_WORKERS`, subject to
your API rate limits. Lower `MAX_WORKERS` if you get 429s; raise it if your tier
allows. Turn off `RUN_PRODUCTION_FAITH` to drop Block1 by 1,824 calls; turn off
`RUN_JUDGE_MODELS` to drop 1,026.

## Cost control (notebook 2)

Toggle the flags at the top of `2_score`:
`RUN_JUDGE_PROXY, RUN_PRODUCTION_FAITH, RUN_JUDGE_MODELS, RUN_CONSTRUCT, RUN_INTERJUDGE`.
`1_generate_perturb` has `MAX_CASES = None` (full 114 override subset) — set an int
for a cheap smoke-test first. `JUDGE_MODELS` defaults to your three `.env` tiers;
`CONSTRUCT_NOTCH = 2`, `INTERJUDGE_N = 60`.

> **Run the full 114 override subset** for the submission. The earlier extra-experiment
> run came back at n≈20–26 (a capped `MAX_CASES`), which underpowers P2/P3 and the
> weak-judge cell. Leave `MAX_CASES = None`.

## Dependencies

```
pip install statsmodels scipy scikit-learn pyarrow
```
(`scikit-learn` is used by `0` and by the new Youden thresholds in `4`.)

## Validation

Notebooks 1→4 were executed end-to-end offline against synthetic data with a
stubbed model client to confirm the merge, the data contracts, the statistics,
and the figure/table code run without error. Run locally with your `.env` and the
real corpus for the actual numbers.
