from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from core.config import Settings
from core.utils import safe_slug, write_json


# The evaluation set must cover four question types.  When the source is
# configured to return fewer records, use the configured limit instead.
MIN_ROWS_FOR_EVALUATION = 4
MIN_SUMMARY_CHARS = 30
REQUIRED_COLUMNS = ("paper_id", "title", "summary", "published", "age_days")
_MISSING_TEXT_MARKERS = frozenset({"", "nan", "none", "null", "<na>"})


def _timestamp() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _blank_mask(series: pd.Series) -> pd.Series:
    """Return a boolean mask for null-like or whitespace-only values."""

    normalized = series.astype("string").fillna("").str.strip().str.casefold()
    return normalized.isin(_MISSING_TEXT_MARKERS)


def _count(mask: pd.Series) -> int:
    return int(mask.fillna(False).sum())


def _coerce_age_days(df: pd.DataFrame) -> tuple[pd.Series | None, pd.Series | None]:
    """Return numeric age values and the mask of missing source values."""

    if "age_days" not in df.columns:
        return None, None
    raw_age_days = df["age_days"]
    return pd.to_numeric(raw_age_days, errors="coerce"), _blank_mask(raw_age_days)


def _freshness_stats(df: pd.DataFrame, threshold_days: int) -> dict[str, Any]:
    """Build freshness counts from the pipeline's age_days contract.

    The cleaning step calculates age_days against its run date.  Recomputing it
    from the wall-clock date here would make snapshot runs non-reproducible, so
    observability treats age_days as the source of truth and reports invalid
    values explicitly.
    """

    total_rows = int(len(df))
    age_days, missing_mask = _coerce_age_days(df)
    if age_days is None or missing_mask is None:
        return {
            "age_days_column_present": False,
            "total_rows": total_rows,
            "fresh_rows": 0,
            "stale_rows": 0,
            "missing_age_days": total_rows,
            "invalid_age_days": 0,
            "future_dated_rows": 0,
            "is_fresh": False,
            "status": "unknown",
            "message": "Cột age_days bắt buộc bị thiếu.",
        }

    invalid_mask = age_days.isna() & ~missing_mask
    future_mask = age_days.notna() & age_days.lt(0)
    stale_mask = age_days.notna() & age_days.gt(threshold_days)
    fresh_mask = age_days.notna() & age_days.ge(0) & age_days.le(threshold_days)

    missing_age_days = _count(missing_mask)
    invalid_age_days = _count(invalid_mask)
    future_dated_rows = _count(future_mask)
    stale_rows = _count(stale_mask)
    fresh_rows = _count(fresh_mask)
    is_fresh = (
        total_rows > 0
        and missing_age_days == 0
        and invalid_age_days == 0
        and future_dated_rows == 0
        and stale_rows == 0
    )

    if is_fresh:
        status = "fresh"
        message = "Tất cả các hàng có giá trị age_days hợp lệ nằm trong ngưỡng cấu hình."
    elif stale_rows:
        status = "stale"
        message = "Một hoặc nhiều hàng cũ hơn ngưỡng freshness được cấu hình."
    else:
        status = "unknown"
        message = "Không thể xác định độ tươi mới vì tập dữ liệu trống hoặc có giá trị age_days không hợp lệ."

    return {
        "age_days_column_present": True,
        "total_rows": total_rows,
        "fresh_rows": fresh_rows,
        "stale_rows": stale_rows,
        "missing_age_days": missing_age_days,
        "invalid_age_days": invalid_age_days,
        "future_dated_rows": future_dated_rows,
        "is_fresh": is_fresh,
        "status": status,
        "message": message,
    }


def _published_stats(df: pd.DataFrame) -> dict[str, Any]:
    """Return parseability and date bounds without inventing missing dates."""

    total_rows = int(len(df))
    if "published" not in df.columns:
        return {
            "published_column_present": False,
            "missing_published": total_rows,
            "invalid_published": 0,
            "latest_published": None,
            "oldest_published": None,
        }

    raw_published = df["published"]
    missing_mask = _blank_mask(raw_published)
    parsed = pd.to_datetime(raw_published, errors="coerce", utc=True)
    invalid_mask = parsed.isna() & ~missing_mask
    valid_dates = parsed.dropna()

    def format_date(value: pd.Timestamp | pd.NaT) -> str | None:
        if pd.isna(value):
            return None
        return value.date().isoformat()

    return {
        "published_column_present": True,
        "missing_published": _count(missing_mask),
        "invalid_published": _count(invalid_mask),
        "latest_published": format_date(valid_dates.max()) if not valid_dates.empty else None,
        "oldest_published": format_date(valid_dates.min()) if not valid_dates.empty else None,
    }


def _check(passed: bool, message: str, **details: Any) -> dict[str, Any]:
    return {"passed": bool(passed), **details, "message": message}


def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    """Run deterministic checks against a clean/corrupted/repaired dataframe.

    The returned JSON contains each check's observed count and threshold, and is
    written to ``settings.paths.quality_dir`` as
    ``<report_name>_quality_report.json``.  Missing required columns are
    reported as failed checks rather than raising, so a corrupted artifact still
    leaves useful diagnostic evidence.
    """

    report_slug = safe_slug(report_name)
    total_rows = int(len(df))
    minimum_rows = min(MIN_ROWS_FOR_EVALUATION, max(1, int(settings.max_results)))
    threshold_days = int(settings.freshness_threshold_days)
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in df.columns]

    checks: dict[str, dict[str, Any]] = {
        "minimum_row_count": _check(
            total_rows >= minimum_rows,
            "Tập dữ liệu có đủ số hàng cho phạm vi đánh giá yêu cầu."
            if total_rows >= minimum_rows
            else "Tập dữ liệu có ít hàng hơn mức tối thiểu yêu cầu cho phạm vi đánh giá.",
            actual=total_rows,
            minimum=minimum_rows,
        ),
        "required_columns": _check(
            not missing_columns,
            "Tất cả các cột bắt buộc đều hiển thị."
            if not missing_columns
            else "Các cột bắt buộc bị thiếu khỏi dataframe.",
            missing_columns=missing_columns,
        ),
    }

    if "paper_id" in df.columns:
        blank_paper_ids = _count(_blank_mask(df["paper_id"]))
        duplicate_paper_ids = _count(
            df["paper_id"].astype("string").fillna("").str.strip().duplicated(keep="first")
            & ~_blank_mask(df["paper_id"])
        )
        checks["paper_id_not_null"] = _check(
            blank_paper_ids == 0,
            "Mọi hàng đều có paper_id không trống."
            if blank_paper_ids == 0
            else "Một hoặc nhiều hàng có paper_id bị trống.",
            blank_rows=blank_paper_ids,
        )
        checks["paper_id_unique"] = _check(
            duplicate_paper_ids == 0,
            "Các giá trị paper_id là duy nhất."
            if duplicate_paper_ids == 0
            else "Tìm thấy các giá trị paper_id không trống bị trùng lặp.",
            duplicate_rows=duplicate_paper_ids,
        )
    else:
        checks["paper_id_not_null"] = _check(False, "Cột paper_id bị thiếu.", blank_rows=None)
        checks["paper_id_unique"] = _check(False, "Cột paper_id bị thiếu.", duplicate_rows=None)

    if "title" in df.columns:
        blank_titles = _count(_blank_mask(df["title"]))
        checks["title_not_blank"] = _check(
            blank_titles == 0,
            "Mọi hàng đều có tiêu đề không trống."
            if blank_titles == 0
            else "Một hoặc nhiều hàng có tiêu đề bị trống.",
            blank_rows=blank_titles,
        )
    else:
        checks["title_not_blank"] = _check(False, "Cột title bị thiếu.", blank_rows=None)

    if "summary" in df.columns:
        summaries = df["summary"].astype("string").fillna("").str.strip()
        blank_summaries = _count(summaries.eq(""))
        short_summaries = _count(summaries.str.len().lt(MIN_SUMMARY_CHARS) & summaries.ne(""))
        invalid_summaries = blank_summaries + short_summaries
        checks["summary_length"] = _check(
            invalid_summaries == 0,
            "Tất cả tóm tắt đáp ứng độ dài tối thiểu."
            if invalid_summaries == 0
            else "Một hoặc nhiều tóm tắt bị trống hoặc ngắn hơn độ dài tối thiểu.",
            minimum_chars=MIN_SUMMARY_CHARS,
            blank_rows=blank_summaries,
            too_short_rows=short_summaries,
        )
    else:
        checks["summary_length"] = _check(
            False,
            "Cột summary bị thiếu.",
            minimum_chars=MIN_SUMMARY_CHARS,
            blank_rows=None,
            too_short_rows=None,
        )

    published = _published_stats(df)
    published_invalid_rows = published["missing_published"] + published["invalid_published"]
    checks["published_date_valid"] = _check(
        published["published_column_present"] and published_invalid_rows == 0,
        "Tất cả các giá trị published đều là ngày hợp lệ."
        if published["published_column_present"] and published_invalid_rows == 0
        else "Cột published bị thiếu hoặc chứa ngày bị thiếu/không hợp lệ.",
        missing_rows=published["missing_published"],
        invalid_rows=published["invalid_published"],
    )

    freshness = _freshness_stats(df, threshold_days)
    checks["freshness"] = _check(
        freshness["is_fresh"],
        freshness["message"],
        freshness_threshold_days=threshold_days,
        stale_rows=freshness["stale_rows"],
        missing_age_days=freshness["missing_age_days"],
        invalid_age_days=freshness["invalid_age_days"],
        future_dated_rows=freshness["future_dated_rows"],
    )

    failed_checks = [name for name, result in checks.items() if not result["passed"]]
    payload = {
        "report_name": report_slug,
        "generated_at": _timestamp(),
        "dataset": {
            "total_rows": total_rows,
            "columns": list(df.columns),
        },
        "thresholds": {
            "minimum_rows": minimum_rows,
            "minimum_summary_chars": MIN_SUMMARY_CHARS,
            "freshness_threshold_days": threshold_days,
        },
        "checks": checks,
        "overall_passed": not failed_checks,
        "summary": {
            "passed": not failed_checks,
            "checks_total": len(checks),
            "checks_passed": len(checks) - len(failed_checks),
            "checks_failed": len(failed_checks),
            "failed_checks": failed_checks,
        },
    }
    output_path = Path(settings.paths.quality_dir) / f"{report_slug}_quality_report.json"
    write_json(output_path, payload)
    return payload


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path) -> dict[str, Any]:
    """Write a freshness report based on age_days and published metadata.

    ``age_days`` is assessed against ``settings.freshness_threshold_days``;
    published dates are used only for the oldest/latest evidence in the report.
    Invalid or missing values are surfaced explicitly and never converted to a
    synthetic age.
    """

    threshold_days = int(settings.freshness_threshold_days)
    freshness = _freshness_stats(df, threshold_days)
    published = _published_stats(df)
    payload = {
        "generated_at": _timestamp(),
        "freshness_threshold_days": threshold_days,
        "age_days_column": "age_days",
        "latest_published": published["latest_published"],
        "oldest_published": published["oldest_published"],
        "missing_published": published["missing_published"],
        "invalid_published": published["invalid_published"],
        **freshness,
    }
    write_json(Path(report_path), payload)
    return payload
