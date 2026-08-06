from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
import shutil

import pandas as pd

from core.config import load_settings
from core.utils import read_json
from evaluation.metrics import evaluate_pipeline
from ingestion.cleaning import build_clean_dataframe
from ingestion.crossref import load_raw_records
from ingestion.corruption import corrupt_clean_dataframe
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_corruption_report
from retrieval.index import LocalEmbeddingIndex


def main() -> None:
    """Xây dựng và thực thi Pha 2 Thí nghiệm (Corruption -> Evaluate -> Repair -> Compare)."""
    print("=== Phase 2 Experiment: Corruption, Repair & Comparison Flow ===")
    settings = load_settings()

    # Step 1: Load Baseline Metrics & Clean Data
    if not settings.paths.baseline_metrics.exists():
        raise RuntimeError("Baseline metrics missing. Please run Phase 1 first via script/run_phase1.py.")

    baseline_metrics = read_json(settings.paths.baseline_metrics)
    print(f"Loaded Baseline Metrics: {baseline_metrics}")

    if not settings.paths.clean_json.exists():
        raise RuntimeError("Clean dataset missing.")
    df_clean = pd.read_json(settings.paths.clean_json)

    # Step 2: Corrupt Data
    print("\n--- Step 1: Generating Controlled Corrupted Data ---")
    df_corrupted = corrupt_clean_dataframe(df_clean, settings.paths.corruption_log)
    df_corrupted.to_json(settings.paths.corrupted_clean_json, orient="records", indent=2, force_ascii=False)
    df_corrupted.to_csv(settings.paths.corrupted_clean_csv, index=False)
    print(f"Corrupted dataset created with {len(df_corrupted)} records (Log saved to {settings.paths.corruption_log}).")

    # Step 3: Build Index & Evaluate Corrupted State
    print("\n--- Step 2: Building ChromaDB Vector Index for Corrupted Data ---")
    corrupted_index = LocalEmbeddingIndex.build(
        df=df_corrupted,
        settings=settings,
        embeddings_output_path=settings.paths.corrupted_embeddings_json,
    )
    print("Evaluating Corrupted State (RAG Agent & LLM Judge)...")
    corrupted_bundle = evaluate_pipeline(
        settings=settings,
        index=corrupted_index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.corrupted_metrics,
        answers_output_path=settings.paths.corrupted_answers,
    )
    print(f"Corrupted Metrics Summary: {corrupted_bundle.summary}")

    print("Running Observability Data Quality & Freshness on Corrupted Data...")
    corrupted_quality = run_data_quality_checks(df_corrupted, settings, report_name="corrupted_quality")
    corrupted_freshness_path = settings.paths.quality_dir / "corrupted_freshness_report.json"
    corrupted_freshness = build_freshness_report(df_corrupted, settings, corrupted_freshness_path)

    # Step 4: Repair Data from Raw Snapshot
    print("\n--- Step 3: Repairing Data from Raw Snapshot (crossref_records.json) ---")
    if not settings.paths.raw_records_json.exists():
        raise RuntimeError(f"Raw snapshot file missing at {settings.paths.raw_records_json}")

    raw_records = load_raw_records(settings.paths.raw_records_json)
    df_repaired = build_clean_dataframe(raw_records, run_date=datetime.now(UTC))
    df_repaired.to_json(settings.paths.repaired_clean_json, orient="records", indent=2, force_ascii=False)
    df_repaired.to_csv(settings.paths.repaired_clean_csv, index=False)
    print(f"Data successfully repaired: {len(df_repaired)} clean records recovered.")

    # Step 5: Build Index & Evaluate Repaired State
    print("\n--- Step 4: Building ChromaDB Vector Index for Repaired Data ---")
    repaired_index = LocalEmbeddingIndex.build(
        df=df_repaired,
        settings=settings,
        embeddings_output_path=settings.paths.repaired_embeddings_json,
    )
    print("Evaluating Repaired State (RAG Agent & LLM Judge)...")
    repaired_bundle = evaluate_pipeline(
        settings=settings,
        index=repaired_index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.repaired_metrics,
        answers_output_path=settings.paths.repaired_answers,
    )
    print(f"Repaired Metrics Summary: {repaired_bundle.summary}")

    print("Running Observability Data Quality & Freshness on Repaired Data...")
    repaired_quality = run_data_quality_checks(df_repaired, settings, report_name="repaired_quality")
    repaired_freshness_path = settings.paths.quality_dir / "repaired_freshness_report.json"
    repaired_freshness = build_freshness_report(df_repaired, settings, repaired_freshness_path)

    # Step 6: Generate 3-Column Comparison Report
    print("\n--- Step 5: Generating Comparison Report ---")
    generate_corruption_report(
        report_path=settings.paths.comparison_report,
        baseline_metrics=baseline_metrics,
        corrupted_metrics=corrupted_bundle.summary,
        repaired_metrics=repaired_bundle.summary,
        corrupted_quality=corrupted_quality,
        repaired_quality=repaired_quality,
        corrupted_freshness=corrupted_freshness,
        repaired_freshness=repaired_freshness,
    )

    # Copy to project root
    root_report_path = settings.paths.project_dir / "corruption_report.md"
    shutil.copy(settings.paths.comparison_report, root_report_path)
    print(f"Comparison report saved to {settings.paths.comparison_report} and {root_report_path}.")
    print("\n=== Phase 2 Experiment Completed Successfully! ===")


if __name__ == "__main__":
    main()

