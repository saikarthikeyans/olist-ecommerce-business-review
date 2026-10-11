"""One-stop orchestrator for the complete Olist Weekly Business Review.

Executes:
  1. Pipeline (Extract, Raw Load, Staging Cleanse, Mart Build, Quality Checks)
  2. SQL Analytics Suite (All 5 queries)
  3. Matplotlib Charts (All 4 charts)
  4. ReportLab 5-page PDF Report & VP Executive Memo
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.analytics.runner import run_all_analytics
from backend.pipeline.run import run_pipeline
from reports.generate_charts import generate_all_charts
from reports.generate_pdf import build_pdf_report


def main():
    start_time = time.time()
    print("=" * 80)
    print("OLIST WEEKLY BUSINESS REVIEW — MASTER ORCHESTRATION RUN")
    print("=" * 80)

    # 1. Pipeline Execution
    print("\n>>> STEP 1: Running Idempotent ELT Pipeline...")
    exit_code = run_pipeline()
    if exit_code != 0:
        print(f"\n[FAIL] Pipeline terminated with exit code {exit_code}. Halting review.")
        sys.exit(exit_code)

    # 2. Analytics Execution
    print("\n>>> STEP 2: Running Analytical SQL Suite (Queries 1 to 5)...")
    try:
        analytics = run_all_analytics()
        print(f"[OK] Analytical suite executed successfully.")
        retention = analytics.get("repeat_purchase_rate", {})
        if retention:
            print(f"     - Repeat Purchase Rate: {retention.get('repeat_purchase_rate_pct', 'N/A')}%")
            print(f"     - Distinct Customers:   {retention.get('total_distinct_customers', 'N/A'):,}")
            print(f"     - Repeat Buyers:        {retention.get('repeat_customers', 'N/A'):,}")
    except Exception as e:
        print(f"[WARNING] Analytics query error: {e}")

    # 3. Chart Generation
    print("\n>>> STEP 3: Generating Matplotlib Publication Charts...")
    try:
        charts = generate_all_charts()
        print(f"[OK] Generated {len(charts)} charts in reports/charts/.")
    except Exception as e:
        print(f"[WARNING] Chart generation error: {e}")

    # 4. PDF Compilation
    print("\n>>> STEP 4: Compiling 5-Page ReportLab PDF & VP Memo...")
    try:
        pdf_path = build_pdf_report()
        print(f"[OK] PDF compiled successfully at: {pdf_path}")
    except Exception as e:
        print(f"[WARNING] PDF compilation error: {e}")

    elapsed = time.time() - start_time
    print("\n" + "=" * 80)
    print(f"REVIEW ORCHESTRATION COMPLETE in {elapsed:.2f} seconds.")
    print("=" * 80)


if __name__ == "__main__":
    main()
