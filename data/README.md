# `data/` — how to reconstruct the corpus

This folder is intentionally empty in version control. The raw and intermediate
data are **not** redistributed (public but subject to third-party licenses and
too large to commit). Everything here is reconstructible from public sources.
Place the files below in this folder before running the notebooks.

## Files the pipeline expects

| File | Produced by | Description |
|------|-------------|-------------|
| `corpus_main.parquet` | reconstruction (below) | financials + agency rating + MD&A text; the analysis input for notebook `00` |
| `with_override.parquet` | notebook `00` | adds notch gap, predictive band, override flag |
| `generated.parquet` | notebook `01` | generated (rating, rationale) per override case |
| `perturbed.parquet` | notebook `02` | controlled variants P1–P5 |
| `scored.parquet` | notebook `03` | LLM-judge and faithfulness scores |

Only `corpus_main.parquet` must be built by hand; `00`–`03` write the rest.

## Reconstructing `corpus_main.parquet`

Three public layers, joined on firm identity and fiscal year:

1. **Financial ratios + agency ratings** — a public corporate-rating dataset
   with financial ratios keyed by **ticker**, **rating agency**, and
   **rating date**.
2. **MD&A narrative text** — the `edgar-corpus` collection of SEC 10-K filings.
   Each filing is split into sections; **section 7** is the Management's
   Discussion and Analysis (MD&A). Fetch per year as JSON Lines.
3. **Ticker → CIK mapping** — the SEC `company_tickers.json` file, used to
   resolve each ticker to the CIK that keys `edgar-corpus`.

Join procedure:

- Resolve each rating row's ticker to a CIK via `company_tickers.json`.
- A 10-K covers the prior fiscal year, so for a rating in year *Y* match the
  filing for year *Y* or *Y−1*, keeping the longer MD&A on ties.
- Drop MD&A entries below a length floor (incorporation-by-reference stubs);
  a sensitivity check confirms this does not materially shift sector mix.

The result is `corpus_main.parquet` with the financial ratio columns, the
agency rating, the firm identifier (CIK), the fiscal year, and the MD&A text.

## Notes

- Keep this folder's real contents out of version control (see the repo
  `.gitignore`); only this `README.md` and a `.gitkeep` are tracked.
- Exact row counts depend on the ticker→CIK match rate and the MD&A length
  floor; the reported findings are the effect **directions** and the
  **divergence structure**, which are robust to these choices.
