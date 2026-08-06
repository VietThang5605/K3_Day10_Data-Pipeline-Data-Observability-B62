from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
import shutil

import pandas as pd

from core.config import load_settings
from evaluation.metrics import evaluate_pipeline
from evaluation.testset import build_test_set
from ingestion.cleaning import build_clean_dataframe
from ingestion.crossref import fetch_source_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_phase1_report
from retrieval.index import LocalEmbeddingIndex


def main() -> None:
    """Xây dựng và thực thi Baseline RAG Pipeline end-to-end (Phase 1)."""
    print("=== Step 1: Loading Settings & Environment ===")
    settings = load_settings()

    # Step 2: Ensure clean data exists
    if not settings.paths.clean_json.exists():
        print("Clean data missing. Ingesting and cleaning Crossref papers...")
        raw_records = fetch_source_records(settings)
        df_clean = build_clean_dataframe(raw_records, run_date=datetime.now(UTC))
        df_clean.to_json(settings.paths.clean_json, orient="records", indent=2, force_ascii=False)
        df_clean.to_csv(settings.paths.clean_csv, index=False)
    else:
        print(f"Loading cleaned data from {settings.paths.clean_json}...")
        df_clean = pd.read_json(settings.paths.clean_json)

    # Step 3: Build Chroma Vector Index
    print("=== Step 2: Building ChromaDB Vector Index ===")
    index = LocalEmbeddingIndex.build(
        df=df_clean,
        settings=settings,
        embeddings_output_path=settings.paths.embeddings_json,
    )
    print(f"Vector index built with collection '{settings.baseline_collection_name}'.")

    # Step 4: Ensure Frozen Evaluation Test Set exists
    print("=== Step 3: Preparing Evaluation Test Set ===")
    if not settings.paths.eval_testset.exists() or settings.refresh_test_set:
        print("Building new test set...")
        build_test_set(df_clean, settings.paths.eval_testset)
    print(f"Test set loaded from {settings.paths.eval_testset}.")

    # Step 5: Evaluate Baseline RAG Pipeline
    print("=== Step 4: Running Baseline Evaluation (Agent & LLM Judge) ===")
    bundle = evaluate_pipeline(
        settings=settings,
        index=index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.baseline_metrics,
        answers_output_path=settings.paths.baseline_answers,
    )
    print(f"Baseline Evaluation Summary: {bundle.summary}")

    # Step 6: Run Data Quality & Freshness Checks
    print("=== Step 5: Running Data Quality & Freshness Observability ===")
    quality_result = run_data_quality_checks(df_clean, settings, report_name="baseline_quality")
    freshness_result = build_freshness_report(df_clean, settings, settings.paths.freshness_report)

    # Step 7: Generate Markdown Report
    print("=== Step 6: Generating Phase 1 Report ===")
    source_summary = {
        "source_api": settings.source_api,
        "source_query": settings.source_query,
        "clean_rows": len(df_clean),
    }
    generate_phase1_report(
        report_path=settings.paths.baseline_report,
        source_summary=source_summary,
        metrics=bundle.summary,
        quality=quality_result,
        freshness=freshness_result,
    )

    # Also copy report to project root for convenience
    root_report_path = settings.paths.project_dir / "phase1_report.md"
    shutil.copy(settings.paths.baseline_report, root_report_path)
    print(f"Phase 1 report saved to {settings.paths.baseline_report} and {root_report_path}.")
    print("=== Baseline Pipeline Completed Successfully! ===")


if __name__ == "__main__":
    main()
