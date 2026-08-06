from __future__ import annotations

import json
import os

from core.config import Settings, load_settings
from core.utils import now_utc, read_json, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from evaluation.testset import build_test_set
from ingestion.cleaning import build_clean_dataframe
from ingestion.crossref import fetch_source_records, load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_phase1_report
from retrieval.agent import build_agent, run_agent_question
from retrieval.index import LocalEmbeddingIndex


def _load_source(settings: Settings):
    """Load the reproducible snapshot unless an explicit refresh was requested."""
    if settings.paths.raw_records_json.exists() and not settings.refresh_source:
        records = load_raw_records(settings.paths.raw_records_json)
        mode = "raw snapshot"
    else:
        records = fetch_source_records(settings)
        mode = "Crossref API"
    if not records:
        raise RuntimeError("No raw records were loaded. Refresh the source or inspect the raw snapshot.")
    return records, mode


def _save_clean_artifacts(df, settings: Settings) -> None:
    write_csv(df, settings.paths.clean_csv)
    # Convert pandas/numpy scalars to JSON-native values before using write_json.
    records = json.loads(df.to_json(orient="records", date_format="iso"))
    write_json(settings.paths.clean_json, records)


def _load_or_build_test_set(df, settings: Settings) -> list[dict]:
    if settings.paths.eval_testset.exists() and not settings.refresh_test_set:
        test_set = read_json(settings.paths.eval_testset)
        if not isinstance(test_set, list) or not test_set:
            raise ValueError("The existing evaluation test set must be a non-empty JSON list.")
        return test_set
    test_set = build_test_set(df, settings.paths.eval_testset)
    if not test_set:
        raise RuntimeError("Test-set generation returned no questions.")
    return test_set


def _run_optional_demo(settings: Settings, index: LocalEmbeddingIndex, test_set: list[dict]) -> None:
    """Run a small LLM-agent demo only when requested, so baseline stays reproducible."""
    if os.getenv("RUN_AGENT_DEMO", "").strip().lower() not in {"1", "true", "yes"}:
        write_json(
            settings.paths.demo_answers,
            {"skipped": "Set RUN_AGENT_DEMO=1 to enable the optional LLM-agent demo."},
        )
        return

    try:
        agent = build_agent(settings, index)
        answers = [
            {
                "question": item["question"],
                "answer": run_agent_question(agent, item["question"]),
            }
            for item in test_set[:3]
        ]
        write_json(settings.paths.demo_answers, answers)
    except Exception as exc:
        write_json(
            settings.paths.demo_answers,
            {"error": f"Agent demo unavailable: {type(exc).__name__}"},
        )

def main() -> None:
    """Run ingestion through reporting for the clean baseline corpus.

    Pseudo-code:
    1. Load settings.
    2. Load hoac fetch raw records.
    3. Clean data.
    4. Save clean CSV/JSON.
    5. Build Chroma index.
    6. Tao hoac load evaluation set.
    7. Evaluate.
    8. Run quality checks va freshness report.
    9. Tao markdown report.
    10. Co the demo agent tren vai sample question.
    """
    settings = load_settings()

    print("[1/8] Loading source records")
    raw_records, source_mode = _load_source(settings)

    print("[2/8] Cleaning records and saving clean artifacts")
    clean_df = build_clean_dataframe(raw_records, run_date=now_utc())
    if clean_df.empty:
        raise RuntimeError("Cleaning produced zero records; inspect the cleaning report and raw data.")
    _save_clean_artifacts(clean_df, settings)

    print(f"[3/8] Building Chroma index for {len(clean_df)} records")
    index = LocalEmbeddingIndex.build(
        clean_df,
        settings=settings,
        embeddings_output_path=settings.paths.embeddings_json,
    )

    print("[4/8] Loading or creating the frozen evaluation set")
    test_set = _load_or_build_test_set(clean_df, settings)

    print(f"[5/8] Evaluating {len(test_set)} questions")
    evaluation = evaluate_pipeline(
        settings=settings,
        index=index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.baseline_metrics,
        answers_output_path=settings.paths.baseline_answers,
    )

    print("[6/8] Running data-quality and freshness checks")
    quality = run_data_quality_checks(clean_df, settings, report_name="baseline")
    freshness = build_freshness_report(clean_df, settings, settings.paths.freshness_report)

    source_summary = {
        "source": settings.source_api,
        "load_mode": source_mode,
        "query": settings.source_query,
        "filter": settings.source_filter,
        "raw_records": len(raw_records),
        "clean_records": len(clean_df),
        "cleaning_report": clean_df.attrs.get("cleaning_report", {}),
        "embedding_model": settings.embedding_model,
        "collection": settings.baseline_collection_name,
        "top_k": settings.top_k,
    }
    print("[7/8] Generating the baseline report")
    generate_phase1_report(
        report_path=settings.paths.baseline_report,
        source_summary=source_summary,
        metrics=evaluation.summary,
        quality=quality,
        freshness=freshness,
    )

    print("[8/8] Writing the optional agent-demo artifact")
    _run_optional_demo(settings, index, test_set)
    print(f"Baseline completed: {settings.paths.baseline_report}")
