from __future__ import annotations

import json
from pathlib import Path
import pandas as pd

from core.config import load_settings
from core.utils import now_utc, read_json, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from ingestion.cleaning import build_clean_dataframe
from ingestion.corruption import corrupt_clean_dataframe
from ingestion.crossref import load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_corruption_report
from retrieval.index import LocalEmbeddingIndex


def main() -> None:
    settings = load_settings()

    print("[1/10] Loading baseline metrics and clean dataset")
    if not settings.paths.baseline_metrics.exists():
        raise FileNotFoundError(f"Baseline metrics not found at {settings.paths.baseline_metrics}. Run phase1 first.")
    
    baseline_metrics = read_json(settings.paths.baseline_metrics)
    
    # Load optional baseline quality/freshness reports
    baseline_quality_path = settings.paths.quality_dir / "baseline_quality_report.json"
    baseline_quality = read_json(baseline_quality_path) if baseline_quality_path.exists() else None
    
    baseline_freshness_path = settings.paths.freshness_report
    baseline_freshness = read_json(baseline_freshness_path) if baseline_freshness_path.exists() else None

    # Load clean dataframe
    if not settings.paths.clean_csv.exists():
        raise FileNotFoundError(f"Clean CSV not found at {settings.paths.clean_csv}.")
    df_clean = pd.read_csv(settings.paths.clean_csv)

    print("[2/10] Creating corrupted dataframe")
    df_corrupted = corrupt_clean_dataframe(df_clean, settings.paths.corruption_log)

    print("[3/10] Saving corrupted artifacts")
    write_csv(df_corrupted, settings.paths.corrupted_clean_csv)
    corrupted_records = json.loads(df_corrupted.to_json(orient="records", date_format="iso"))
    write_json(settings.paths.corrupted_clean_json, corrupted_records)
    # Also save to data/clean/papers_corrupted.csv as requested by user instructions
    user_corrupted_csv = settings.paths.project_dir / "data" / "clean" / "papers_corrupted.csv"
    write_csv(df_corrupted, user_corrupted_csv)
    print(f"Saved corrupted artifacts to {settings.paths.corrupted_clean_csv} and {user_corrupted_csv}")

    print("[4/10] Rebuilding Chroma index for corrupted dataset")
    corrupted_index = LocalEmbeddingIndex.build(
        df_corrupted,
        settings=settings,
        embeddings_output_path=settings.paths.corrupted_embeddings_json,
    )

    print("[5/10] Evaluating corrupted index on frozen test set")
    corrupted_evaluation = evaluate_pipeline(
        settings=settings,
        index=corrupted_index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.corrupted_metrics,
        answers_output_path=settings.paths.corrupted_answers,
    )

    print("[6/10] Running quality and freshness checks on corrupted data")
    corrupted_quality = run_data_quality_checks(df_corrupted, settings, report_name="corrupted")
    corrupted_freshness = build_freshness_report(
        df_corrupted, settings, settings.paths.quality_dir / "corrupted_freshness_report.json"
    )

    print("[7/10] Repairing dataset from raw Crossref records")
    if not settings.paths.raw_records_json.exists():
        raise FileNotFoundError(f"Raw records snapshot not found at {settings.paths.raw_records_json}.")
    raw_records = load_raw_records(settings.paths.raw_records_json)
    df_repaired = build_clean_dataframe(raw_records, run_date=now_utc())

    print("[8/10] Saving repaired artifacts")
    write_csv(df_repaired, settings.paths.repaired_clean_csv)
    repaired_records = json.loads(df_repaired.to_json(orient="records", date_format="iso"))
    write_json(settings.paths.repaired_clean_json, repaired_records)

    print("[9/10] Rebuilding Chroma index for repaired dataset")
    repaired_index = LocalEmbeddingIndex.build(
        df_repaired,
        settings=settings,
        embeddings_output_path=settings.paths.repaired_embeddings_json,
    )
    
    print("[10/10] Evaluating repaired index and generating reports")
    repaired_evaluation = evaluate_pipeline(
        settings=settings,
        index=repaired_index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.repaired_metrics,
        answers_output_path=settings.paths.repaired_answers,
    )
    repaired_quality = run_data_quality_checks(df_repaired, settings, report_name="repaired")
    repaired_freshness = build_freshness_report(
        df_repaired, settings, settings.paths.quality_dir / "repaired_freshness_report.json"
    )

    print("Generating comparison report")
    generate_corruption_report(
        report_path=settings.paths.comparison_report,
        baseline_metrics=baseline_metrics,
        corrupted_metrics=corrupted_evaluation.summary,
        repaired_metrics=repaired_evaluation.summary,
        corrupted_quality=corrupted_quality,
        repaired_quality=repaired_quality,
        corrupted_freshness=corrupted_freshness,
        repaired_freshness=repaired_freshness,
        baseline_quality=baseline_quality,
        baseline_freshness=baseline_freshness,
    )
    print(f"Corruption flow completed. Report saved to: {settings.paths.comparison_report}")

