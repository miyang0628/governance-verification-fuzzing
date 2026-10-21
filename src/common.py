# -*- coding: utf-8 -*-
"""
common.py — shared helpers for all notebooks.

Centralizes: project paths, .env loading (OpenAI config), a grayscale seaborn
plotting style, and a figure saver that writes both PNG and PDF at 600 dpi
WITHOUT captions (titles/axis labels only; captions belong in the manuscript).

All notebooks import from here so that style and paths stay identical across
the pipeline and the results are reproducible.
"""

from __future__ import annotations

import os
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import seaborn as sns


# --------------------------------------------------------------------- paths
# This file lives in <project>/src/common.py, so the project root is its parent's parent.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
NOTEBOOKS_DIR = PROJECT_ROOT / "notebooks"
RESULTS_DIR = PROJECT_ROOT / "results"
FIGURES_DIR = RESULTS_DIR / "figures"
TABLES_DIR = RESULTS_DIR / "tables"

for _d in (DATA_DIR, FIGURES_DIR, TABLES_DIR):
    _d.mkdir(parents=True, exist_ok=True)


# ----------------------------------------------------------------- env / llm
def load_env():
    """Load .env from the project root and return the LLM config as a dict.

    Expected .env (placed at the project root, NOT committed):
        OPENAI_API_KEY=...
        LLM_MODEL_WEAK=gpt-4o-mini
        LLM_MODEL_MID=gpt-5.4-mini
        LLM_MODEL_STRONG=gpt-5.4
    """
    try:
        from dotenv import load_dotenv
        load_dotenv(PROJECT_ROOT / ".env")
    except Exception:
        # python-dotenv not installed: fall back to the ambient environment.
        pass
    return {
        "api_key": os.getenv("OPENAI_API_KEY"),
        "weak": os.getenv("LLM_MODEL_WEAK", "gpt-4o-mini"),
        "mid": os.getenv("LLM_MODEL_MID", "gpt-5.4-mini"),
        "strong": os.getenv("LLM_MODEL_STRONG", "gpt-5.4"),
    }


# ------------------------------------------------------------------ plotting
def set_grayscale_style():
    """Apply a consistent grayscale, publication-style seaborn theme."""
    sns.set_theme(style="whitegrid", context="paper")
    # Grayscale palette (dark -> light) reused for categorical series.
    gray = ["#1a1a1a", "#4d4d4d", "#808080", "#b3b3b3", "#d9d9d9"]
    sns.set_palette(gray)
    mpl.rcParams.update({
        "figure.dpi": 150,              # on-screen; saved figures use save dpi below
        "savefig.dpi": 600,
        "savefig.bbox": "tight",
        "font.family": "serif",
        "axes.edgecolor": "#333333",
        "axes.grid": True,
        "grid.color": "#dddddd",
        "grid.linewidth": 0.5,
        "image.cmap": "Greys",
        "axes.prop_cycle": mpl.cycler(color=gray),
    })
    return gray


def _rel(p: Path) -> str:
    """Path relative to the project root, so absolute local paths are never
    printed (keeps logs anonymous for double-blind review)."""
    try:
        return str(Path(p).resolve().relative_to(PROJECT_ROOT))
    except Exception:
        return Path(p).name


def require_input(path, hint: str = ""):
    """Return `path` if it exists; otherwise raise with a SHORT, anonymous
    message (no absolute local path) instead of a full traceback path."""
    p = Path(path)
    if not p.exists():
        msg = f"Missing input: {_rel(p)}."
        if hint:
            msg += f" {hint}"
        raise FileNotFoundError(msg)
    return p


def save_fig(fig, name: str, dpi: int = 600):
    """Save a figure as both PNG and PDF at `dpi` into results/figures.

    No caption is drawn; the manuscript supplies captions. `name` is a stem
    without extension, e.g. "fig_perturbation_contrast". Only relative paths
    are printed.
    """
    png = FIGURES_DIR / f"{name}.png"
    pdf = FIGURES_DIR / f"{name}.pdf"
    fig.savefig(png, dpi=dpi, bbox_inches="tight")
    fig.savefig(pdf, dpi=dpi, bbox_inches="tight")
    print(f"[saved] {_rel(png)}")
    print(f"[saved] {_rel(pdf)}")
    return png, pdf


def save_table(df, name: str, float_fmt: str = "%.3f"):
    """Save a DataFrame as both CSV and LaTeX into results/tables.

    `name` is a stem, e.g. "tab_divergence". Only relative paths are printed.
    """
    csv = TABLES_DIR / f"{name}.csv"
    tex = TABLES_DIR / f"{name}.tex"
    df.to_csv(csv, index=False, encoding="utf-8")
    try:
        df.to_latex(tex, index=False, float_format=lambda x: float_fmt % x
                    if isinstance(x, float) else str(x), escape=False)
    except Exception as e:
        print(f"[warn] LaTeX export skipped: {type(e).__name__}")
    print(f"[saved] {_rel(csv)}")
    if tex.exists():
        print(f"[saved] {_rel(tex)}")
    return csv, tex


# ------------------------------------------------------------------- misc
RANDOM_SEED = 42
