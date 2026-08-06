from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from core.config import Settings
from core.utils import write_json


def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    """Thực hiện Data Quality Checks trên cleaned dataframe và lưu file JSON."""
    total_rows = len(df)
    if total_rows == 0:
        results = {
            "report_name": report_name,
            "passed": False,
            "total_rows": 0,
            "checks": {"non_empty": False},
        }
        output_path = settings.paths.quality_dir / f"{report_name}.json"
        write_json(output_path, results)
        return results

    paper_id_not_null = bool(df["paper_id"].notnull().all())
    paper_id_unique = bool(df["paper_id"].is_unique)
    title_not_null = bool(df["title"].notnull().all())
    summary_valid = bool((df["summary"].str.len() >= 100).all())
    stale_count = int((df["age_days"] > settings.freshness_threshold_days).sum())

    passed = paper_id_not_null and paper_id_unique and title_not_null and summary_valid and (stale_count == 0)

    results = {
        "report_name": report_name,
        "passed": passed,
        "total_rows": total_rows,
        "checks": {
            "paper_id_not_null": paper_id_not_null,
            "paper_id_unique": paper_id_unique,
            "title_not_null": title_not_null,
            "summary_len_ge_100": summary_valid,
            "stale_rows_count": stale_count,
            "is_fresh": stale_count == 0,
        },
    }

    settings.paths.quality_dir.mkdir(parents=True, exist_ok=True)
    output_path = settings.paths.quality_dir / f"{report_name}.json"
    write_json(output_path, results)
    return results


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path: Path | str) -> dict[str, Any]:
    """Tổng hợp Freshness Report từ dataframe và lưu vào file JSON."""
    if df.empty:
        report = {
            "latest_published": None,
            "oldest_published": None,
            "stale_rows": 0,
            "total_rows": 0,
            "is_fresh": False,
        }
    else:
        stale_rows = int((df["age_days"] > settings.freshness_threshold_days).sum())
        total_rows = len(df)
        report = {
            "latest_published": str(df["published"].max()),
            "oldest_published": str(df["published"].min()),
            "stale_rows": stale_rows,
            "total_rows": total_rows,
            "is_fresh": stale_rows == 0,
        }

    target_path = Path(report_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(target_path, report)
    return report

