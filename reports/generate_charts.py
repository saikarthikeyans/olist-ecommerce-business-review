"""Matplotlib chart generation module for Olist Weekly Business Review.

Generates four publication-grade charts from analytical SQL query results:
  1. Monthly revenue trend (Merchandise GMV & Gross Revenue)
  2. Month-over-month revenue growth rate (%)
  3. Top product categories in leading customer states
  4. Delivery delay vs. customer review score (CSAT impact)

Saves output high-resolution PNG images to reports/charts/.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from typing import Any, Dict, List, Optional
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd

from backend.analytics.runner import (
    run_delivery_delay_vs_review,
    run_monthly_revenue_growth,
    run_top_categories_by_state,
)
from backend.config import CHARTS_DIR, setup_logging
from backend.db.connection import get_engine

logger = setup_logging()

# Styling settings
NAVY = "#1E293B"
SLATE = "#475569"
BLUE = "#2563EB"
AMBER = "#D97706"
EMERALD = "#059669"
ROSE = "#E11D48"
GRID_COLOR = "#E2E8F0"

plt.rcParams["font.sans-serif"] = "DejaVu Sans"
plt.rcParams["axes.edgecolor"] = "#CBD5E1"
plt.rcParams["axes.linewidth"] = 0.8


def generate_chart_01_revenue_trend(data: List[Dict[str, Any]], output_dir: Path) -> Path:
    """Chart 1: Monthly Gross Merchandise Value Trend."""
    out_path = output_dir / "01_monthly_revenue_trend.png"
    if not data:
        logger.warning("No data for Chart 1 (Monthly Revenue Trend). Generating placeholder.")
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.text(0.5, 0.5, "Awaiting Pipeline Execution\n(Run python -m backend.pipeline.run)", ha="center", va="center", color=SLATE, fontsize=14)
        ax.set_axis_off()
        fig.savefig(out_path, dpi=300, bbox_inches="tight")
        plt.close(fig)
        return out_path

    df = pd.DataFrame(data)
    df = df.sort_values("year_month")

    fig, ax = plt.subplots(figsize=(11, 5.5))
    x = range(len(df))

    ax.plot(x, df["gross_item_revenue"], marker="o", linewidth=2.2, color=BLUE, label="Gross Item Revenue (Merchandise GMV)")
    ax.plot(x, df["total_gross_revenue"], marker="s", linewidth=1.8, linestyle="--", color=EMERALD, label="Total Billed GMV (Items + Freight)")

    ax.set_title("Olist Marketplace: Monthly Revenue Trajectory (2016 - 2018)", fontsize=13, fontweight="bold", color=NAVY, pad=12)
    ax.set_xlabel("Purchase Month", fontsize=10, fontweight="bold", color=SLATE)
    ax.set_ylabel("Revenue (BRL R$)", fontsize=10, fontweight="bold", color=SLATE)

    ax.set_xticks(x)
    ax.set_xticklabels(df["year_month"], rotation=45, ha="right", fontsize=9)
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda y, _: f"R${y*1e-3:.0f}k" if y >= 1000 else f"R${y:.0f}"))

    ax.grid(True, linestyle=":", color=GRID_COLOR, alpha=0.8)
    ax.legend(frameon=True, facecolor="white", edgecolor="#CBD5E1", fontsize=9.5)
    ax.set_facecolor("#FAFAFA")
    fig.patch.set_facecolor("white")

    fig.tight_layout()
    fig.savefig(out_path, dpi=300)
    plt.close(fig)
    logger.info("Saved: %s", out_path)
    return out_path


def generate_chart_02_revenue_growth(data: List[Dict[str, Any]], output_dir: Path) -> Path:
    """Chart 2: Month-over-Month Revenue Growth Rate (%)."""
    out_path = output_dir / "02_monthly_revenue_growth.png"
    if not data:
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.text(0.5, 0.5, "Awaiting Pipeline Execution", ha="center", va="center", color=SLATE, fontsize=14)
        ax.set_axis_off()
        fig.savefig(out_path, dpi=300, bbox_inches="tight")
        plt.close(fig)
        return out_path

    df = pd.DataFrame(data)
    df = df.dropna(subset=["item_revenue_mom_growth_pct"])
    df = df.sort_values("year_month")

    fig, ax = plt.subplots(figsize=(11, 5.2))
    x = range(len(df))
    growth_vals = df["item_revenue_mom_growth_pct"].tolist()
    colors = [EMERALD if val >= 0 else ROSE for val in growth_vals]

    bars = ax.bar(x, growth_vals, color=colors, width=0.6, edgecolor=NAVY, linewidth=0.5)
    ax.axhline(0, color=SLATE, linewidth=1, linestyle="-")

    ax.set_title("Month-over-Month Merchandise Revenue Growth Rate (%)", fontsize=13, fontweight="bold", color=NAVY, pad=12)
    ax.set_xlabel("Purchase Month", fontsize=10, fontweight="bold", color=SLATE)
    ax.set_ylabel("MoM Growth Rate (%)", fontsize=10, fontweight="bold", color=SLATE)

    ax.set_xticks(x)
    ax.set_xticklabels(df["year_month"], rotation=45, ha="right", fontsize=9)
    ax.yaxis.set_major_formatter(ticker.PercentFormatter())

    # Add data labels
    for bar in bars:
        h = bar.get_height()
        va = "bottom" if h >= 0 else "top"
        ax.annotate(f"{h:+.1f}%", xy=(bar.get_x() + bar.get_width() / 2, h),
                    xytext=(0, 3 if h >= 0 else -8), textcoords="offset points",
                    ha="center", va=va, fontsize=7.5, color=NAVY)

    ax.grid(True, linestyle=":", color=GRID_COLOR, axis="y")
    ax.set_facecolor("#FAFAFA")
    fig.patch.set_facecolor("white")

    fig.tight_layout()
    fig.savefig(out_path, dpi=300)
    plt.close(fig)
    logger.info("Saved: %s", out_path)
    return out_path


def generate_chart_03_top_categories(data: List[Dict[str, Any]], output_dir: Path) -> Path:
    """Chart 3: Top Product Categories in Major States."""
    out_path = output_dir / "03_top_categories_by_state.png"
    if not data:
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.text(0.5, 0.5, "Awaiting Pipeline Execution", ha="center", va="center", color=SLATE, fontsize=14)
        ax.set_axis_off()
        fig.savefig(out_path, dpi=300, bbox_inches="tight")
        plt.close(fig)
        return out_path

    df = pd.DataFrame(data)
    # Focus on top 5 states by overall revenue (e.g. SP, RJ, MG, RS, PR)
    top_states = ["SP", "RJ", "MG", "RS", "PR"]
    filtered_df = df[df["customer_state"].isin(top_states)]

    fig, ax = plt.subplots(figsize=(12, 6))

    # Pivot to state vs rank
    pivot = filtered_df.pivot(index="customer_state", columns="category_rank", values="total_category_revenue")
    categories_pivot = filtered_df.pivot(index="customer_state", columns="category_rank", values="product_category")

    states = top_states
    x = np.arange(len(states))
    width = 0.25

    colors = [BLUE, AMBER, EMERALD]
    for i, rank in enumerate([1, 2, 3]):
        revs = [pivot.loc[s, rank] if (s in pivot.index and rank in pivot.columns) else 0 for s in states]
        cats = [categories_pivot.loc[s, rank] if (s in categories_pivot.index and rank in categories_pivot.columns) else "" for s in states]
        bars = ax.bar(x + (i - 1) * width, revs, width=width, color=colors[i], label=f"Rank {rank}", edgecolor=NAVY, linewidth=0.5)

    ax.set_title("Top 3 Product Category Revenue Across Key Brazilian States (SP, RJ, MG, RS, PR)", fontsize=13, fontweight="bold", color=NAVY, pad=12)
    ax.set_xlabel("Customer State", fontsize=10, fontweight="bold", color=SLATE)
    ax.set_ylabel("Category Revenue (BRL R$)", fontsize=10, fontweight="bold", color=SLATE)
    ax.set_xticks(x)
    ax.set_xticklabels(states, fontsize=10, fontweight="bold")
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda y, _: f"R${y*1e-3:.0f}k"))

    ax.legend(frameon=True, facecolor="white", edgecolor="#CBD5E1")
    ax.grid(True, linestyle=":", color=GRID_COLOR, axis="y")
    ax.set_facecolor("#FAFAFA")
    fig.patch.set_facecolor("white")

    fig.tight_layout()
    fig.savefig(out_path, dpi=300)
    plt.close(fig)
    logger.info("Saved: %s", out_path)
    return out_path


def generate_chart_04_delivery_vs_review(data: List[Dict[str, Any]], output_dir: Path) -> Path:
    """Chart 4: Delivery Delay vs. Review Score (CSAT Impact)."""
    out_path = output_dir / "04_delivery_delay_vs_review.png"
    if not data:
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.text(0.5, 0.5, "Awaiting Pipeline Execution", ha="center", va="center", color=SLATE, fontsize=14)
        ax.set_axis_off()
        fig.savefig(out_path, dpi=300, bbox_inches="tight")
        plt.close(fig)
        return out_path

    df = pd.DataFrame(data)
    review_score_rows = df[df["analysis_dimension"] == "BY_REVIEW_SCORE"].copy()

    if review_score_rows.empty:
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.text(0.5, 0.5, "No review score breakdown data", ha="center", va="center")
        fig.savefig(out_path, dpi=300)
        plt.close(fig)
        return out_path

    fig, ax1 = plt.subplots(figsize=(11, 5.5))
    ax2 = ax1.twinx()

    x = range(len(review_score_rows))
    scores = review_score_rows["segment_label"].tolist()
    delays = review_score_rows["avg_delay_days"].tolist()
    late_pcts = review_score_rows["score_1_dissatisfaction_rate_pct"].tolist()

    bars = ax1.bar([i - 0.18 for i in x], delays, width=0.35, color=AMBER, label="Avg Delivery Delay (Days)", edgecolor=NAVY, linewidth=0.5)
    lines = ax2.plot([i + 0.18 for i in x], late_pcts, marker="o", color=ROSE, linewidth=2.4, label="Late Delivery Rate (%)")

    ax1.set_title("Delivery Punctuality Impact on Customer Ratings (Review Scores 1 - 5)", fontsize=13, fontweight="bold", color=NAVY, pad=12)
    ax1.set_xlabel("Customer Review Score", fontsize=10, fontweight="bold", color=SLATE)
    ax1.set_ylabel("Average Delay in Days (Negative = Early)", color=AMBER, fontsize=10, fontweight="bold")
    ax2.set_ylabel("Late Delivery Proportion (%)", color=ROSE, fontsize=10, fontweight="bold")

    ax1.set_xticks(x)
    ax1.set_xticklabels(scores, fontsize=9.5)
    ax1.axhline(0, color=SLATE, linestyle="--", alpha=0.7)
    ax2.yaxis.set_major_formatter(ticker.PercentFormatter())

    ax1.grid(True, linestyle=":", color=GRID_COLOR, alpha=0.8)
    fig.patch.set_facecolor("white")
    ax1.set_facecolor("#FAFAFA")

    # Combined legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper right", frameon=True, facecolor="white", edgecolor="#CBD5E1")

    fig.tight_layout()
    fig.savefig(out_path, dpi=300)
    plt.close(fig)
    logger.info("Saved: %s", out_path)
    return out_path


def generate_all_charts(output_dir: Optional[Path] = None) -> Dict[str, Path]:
    """Execute all 4 chart generation routines."""
    out_dir = output_dir or CHARTS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Generating analytical charts into: %s", out_dir)

    try:
        rev_data = run_monthly_revenue_growth()
        cat_data = run_top_categories_by_state()
        delivery_data = run_delivery_delay_vs_review()
    except Exception as exc:
        logger.warning("Could not query DB directly for charts: %s. Generating with empty state.", str(exc))
        rev_data, cat_data, delivery_data = [], [], []

    paths = {
        "monthly_revenue_trend": generate_chart_01_revenue_trend(rev_data, out_dir),
        "monthly_revenue_growth": generate_chart_02_revenue_growth(rev_data, out_dir),
        "top_categories_by_state": generate_chart_03_top_categories(cat_data, out_dir),
        "delivery_delay_vs_review": generate_chart_04_delivery_vs_review(delivery_data, out_dir),
    }

    logger.info("Successfully generated %d charts.", len(paths))
    return paths


if __name__ == "__main__":
    generate_all_charts()
