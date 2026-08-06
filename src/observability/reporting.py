from __future__ import annotations

from datetime import UTC, datetime
import json
import math
from numbers import Real
from pathlib import Path
from typing import Any, Mapping, Sequence

from core.utils import write_text


PRIMARY_METRICS = (
    "retrieval_hit_rate",
    "mean_token_f1",
    "judge_accuracy",
    "mean_judge_score",
)


def _timestamp() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _escape_markdown(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", "<br>")


def _as_number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, Real):
        return None
    number = float(value)
    return number if math.isfinite(number) else None


def _display(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, bool):
        return "pass" if value else "fail"
    number = _as_number(value)
    if number is not None:
        return str(int(number)) if number.is_integer() else f"{number:.4f}"
    if isinstance(value, (dict, list, tuple)):
        return _escape_markdown(json.dumps(value, ensure_ascii=False, default=str, sort_keys=True))
    return _escape_markdown(str(value))


def _delta(later: Any, earlier: Any) -> str:
    later_number = _as_number(later)
    earlier_number = _as_number(earlier)
    if later_number is None or earlier_number is None:
        return "—"
    difference = later_number - earlier_number
    return f"{difference:+.4f}"


def _table(headers: Sequence[str], rows: Sequence[Sequence[Any]]) -> str:
    header_row = "| " + " | ".join(_escape_markdown(header) for header in headers) + " |"
    separator = "| " + " | ".join("---" for _ in headers) + " |"
    body = ["| " + " | ".join(_display(value) for value in row) + " |" for row in rows]
    return "\n".join([header_row, separator, *body])


def _mapping_table(payload: Mapping[str, Any] | None) -> str:
    if not payload:
        return "_Không có dữ liệu được cung cấp._"
    return _table(["Trường", "Giá trị"], [[key, value] for key, value in payload.items()])


def _quality_status(payload: Mapping[str, Any] | None) -> str:
    if not payload:
        return "not supplied"
    value = payload.get("overall_passed")
    if value is None and isinstance(payload.get("summary"), Mapping):
        value = payload["summary"].get("passed")
    if value is True:
        return "pass"
    if value is False:
        return "fail"
    return "unknown"


def _failed_checks(payload: Mapping[str, Any] | None) -> list[str]:
    if not payload:
        return []
    summary = payload.get("summary")
    if isinstance(summary, Mapping) and isinstance(summary.get("failed_checks"), list):
        return [str(value) for value in summary["failed_checks"]]
    checks = payload.get("checks")
    if not isinstance(checks, Mapping):
        return []
    return [str(name) for name, result in checks.items() if isinstance(result, Mapping) and result.get("passed") is False]


def _quality_checks_table(payload: Mapping[str, Any] | None) -> str:
    checks = payload.get("checks") if payload else None
    if not isinstance(checks, Mapping) or not checks:
        return "_Không có chi tiết quality checks được cung cấp._"

    rows: list[list[Any]] = []
    for name, result in checks.items():
        if not isinstance(result, Mapping):
            rows.append([name, "unknown", result, ""])
            continue
        details = {key: value for key, value in result.items() if key not in {"passed", "message"}}
        rows.append([name, result.get("passed"), details, result.get("message", "")])
    return _table(["Check", "Trạng thái", "Số liệu", "Diễn giải"], rows)


def _freshness_status(payload: Mapping[str, Any] | None) -> str:
    if not payload:
        return "not supplied"
    status = payload.get("status")
    if status is not None:
        return str(status)
    is_fresh = payload.get("is_fresh")
    if is_fresh is True:
        return "fresh"
    if is_fresh is False:
        return "stale/unknown"
    return "unknown"


def _freshness_table(payload: Mapping[str, Any] | None) -> str:
    if not payload:
        return "_Không có freshness payload được cung cấp._"
    preferred_keys = (
        "status",
        "is_fresh",
        "freshness_threshold_days",
        "total_rows",
        "fresh_rows",
        "stale_rows",
        "missing_age_days",
        "invalid_age_days",
        "future_dated_rows",
        "latest_published",
        "oldest_published",
        "missing_published",
        "invalid_published",
        "message",
    )
    rows = [[key, payload.get(key)] for key in preferred_keys if key in payload]
    return _table(["Trường", "Giá trị"], rows) if rows else "_Freshness payload không có trường nhận diện._"


def _limits(
    metrics: Mapping[str, Any] | None,
    quality: Mapping[str, Any] | None,
    freshness: Mapping[str, Any] | None,
) -> list[str]:
    limits: list[str] = []
    ragas = metrics.get("ragas") if metrics else None
    if isinstance(ragas, Mapping):
        if ragas.get("skipped"):
            limits.append(f"Ragas chưa chạy: {ragas['skipped']}")
        elif ragas.get("error"):
            limits.append(f"Ragas lỗi: {ragas['error']}")

    failed_checks = _failed_checks(quality)
    if failed_checks:
        limits.append(f"Quality checks chưa đạt: {', '.join(failed_checks)}.")
    if freshness and freshness.get("is_fresh") is not True:
        limits.append(f"Freshness không được xác nhận là fresh (status: {_freshness_status(freshness)}).")
    return limits


def _metric_rows(metrics: Mapping[str, Any] | None) -> list[list[Any]]:
    metrics = metrics or {}
    rows = [[metric, metrics.get(metric)] for metric in PRIMARY_METRICS]
    if "samples" in metrics:
        rows.append(["samples", metrics["samples"]])
    return rows


def generate_phase1_report(
    report_path,
    source_summary: dict[str, Any],
    metrics: dict[str, Any],
    quality: dict[str, Any],
    freshness: dict[str, Any],
) -> None:
    """Generate a Markdown baseline report from pipeline artifact payloads.

    All figures are rendered from the supplied dictionaries.  Missing metrics or
    failed checks remain visible instead of being replaced with optimistic
    defaults, which makes the report safe to use as a baseline artifact.
    """

    source_summary = source_summary or {}
    metrics = metrics or {}
    quality = quality or {}
    freshness = freshness or {}
    limits = _limits(metrics, quality, freshness)

    lines = [
        "# Phase 1 Baseline Report",
        "",
        f"Generated at (UTC): {_timestamp()}",
        "",
        "## Source summary",
        "",
        _mapping_table(source_summary),
        "",
        "## Evaluation metrics",
        "",
        _table(["Metric", "Value"], _metric_rows(metrics)),
        "",
        "## Data quality",
        "",
        _table(
            ["Overall status", "Failed checks", "Rows"],
            [[_quality_status(quality), ", ".join(_failed_checks(quality)) or "none", quality.get("dataset", {}).get("total_rows") if isinstance(quality.get("dataset"), Mapping) else None]],
        ),
        "",
        _quality_checks_table(quality),
        "",
        "## Freshness",
        "",
        _freshness_table(freshness),
        "",
        "## Optional Ragas result",
        "",
        _mapping_table(metrics.get("ragas") if isinstance(metrics.get("ragas"), Mapping) else None),
        "",
        "## Limitations and signals",
        "",
    ]
    if limits:
        lines.extend(f"- {limit}" for limit in limits)
    else:
        lines.append("- Không có lỗi hoặc giới hạn nào được ghi trong các artifact đã cung cấp.")

    write_text(Path(report_path), "\n".join(lines).rstrip() + "\n")


def _comparison_observations(
    baseline_metrics: Mapping[str, Any],
    corrupted_metrics: Mapping[str, Any],
    repaired_metrics: Mapping[str, Any],
    corrupted_quality: Mapping[str, Any] | None,
    repaired_quality: Mapping[str, Any] | None,
    corrupted_freshness: Mapping[str, Any] | None,
    repaired_freshness: Mapping[str, Any] | None,
) -> list[str]:
    observations: list[str] = []
    for metric in PRIMARY_METRICS:
        baseline = _as_number(baseline_metrics.get(metric))
        corrupted = _as_number(corrupted_metrics.get(metric))
        repaired = _as_number(repaired_metrics.get(metric))
        if baseline is None or corrupted is None:
            observations.append(f"`{metric}` thiếu dữ liệu baseline hoặc corrupted nên không thể tính thay đổi.")
            continue
        corruption_delta = corrupted - baseline
        if math.isclose(corruption_delta, 0.0, abs_tol=1e-12):
            observations.append(f"`{metric}` không thay đổi giữa baseline và corrupted.")
        else:
            direction = "giảm" if corruption_delta < 0 else "tăng"
            observations.append(f"`{metric}` {direction} {abs(corruption_delta):.4f} sau corruption (thay đổi quan sát được).")
        if repaired is not None:
            repaired_distance = abs(repaired - baseline)
            corrupted_distance = abs(corrupted - baseline)
            recovery = "gần baseline hơn" if repaired_distance < corrupted_distance else "không gần baseline hơn"
            observations.append(f"`{metric}` repaired {recovery} so với corrupted.")

    observations.append(
        "Các thay đổi trên là đối chiếu artifact; chỉ kết luận quan hệ nhân quả khi corruption log và answers truy vết được cùng xác nhận."
    )
    observations.append(
        f"Quality status: corrupted={_quality_status(corrupted_quality)}, repaired={_quality_status(repaired_quality)}; "
        f"freshness: corrupted={_freshness_status(corrupted_freshness)}, repaired={_freshness_status(repaired_freshness)}."
    )
    return observations


def generate_corruption_report(
    report_path,
    baseline_metrics: dict[str, Any],
    corrupted_metrics: dict[str, Any],
    repaired_metrics: dict[str, Any],
    corrupted_quality: dict[str, Any],
    repaired_quality: dict[str, Any],
    corrupted_freshness: dict[str, Any],
    repaired_freshness: dict[str, Any],
    baseline_quality: dict[str, Any] | None = None,
    baseline_freshness: dict[str, Any] | None = None,
) -> None:
    """Generate a baseline/corrupted/repaired comparison report.

    ``baseline_quality`` and ``baseline_freshness`` are optional trailing
    arguments for backwards compatibility with the starter signature.  Passing
    them lets the report show all three states for data-quality signals; when
    omitted, the report explicitly marks the baseline signal as not supplied.
    """

    baseline_metrics = baseline_metrics or {}
    corrupted_metrics = corrupted_metrics or {}
    repaired_metrics = repaired_metrics or {}
    corrupted_quality = corrupted_quality or {}
    repaired_quality = repaired_quality or {}
    corrupted_freshness = corrupted_freshness or {}
    repaired_freshness = repaired_freshness or {}

    comparison_rows: list[list[Any]] = []
    for metric in PRIMARY_METRICS:
        baseline = baseline_metrics.get(metric)
        corrupted = corrupted_metrics.get(metric)
        repaired = repaired_metrics.get(metric)
        comparison_rows.append(
            [
                metric,
                baseline,
                corrupted,
                repaired,
                _delta(corrupted, baseline),
                _delta(repaired, corrupted),
            ]
        )

    quality_rows = [
        [
            "Quality checks",
            _quality_status(baseline_quality),
            _quality_status(corrupted_quality),
            _quality_status(repaired_quality),
            ", ".join(_failed_checks(corrupted_quality)) or "none",
            ", ".join(_failed_checks(repaired_quality)) or "none",
        ],
        [
            "Freshness",
            _freshness_status(baseline_freshness),
            _freshness_status(corrupted_freshness),
            _freshness_status(repaired_freshness),
            corrupted_freshness.get("stale_rows"),
            repaired_freshness.get("stale_rows"),
        ],
    ]

    observations = _comparison_observations(
        baseline_metrics,
        corrupted_metrics,
        repaired_metrics,
        corrupted_quality,
        repaired_quality,
        corrupted_freshness,
        repaired_freshness,
    )
    lines = [
        "# Corruption and Repair Comparison Report",
        "",
        f"Generated at (UTC): {_timestamp()}",
        "",
        "## Evaluation comparison",
        "",
        _table(
            ["Metric", "Baseline", "Corrupted", "Repaired", "Corruption delta", "Repair delta"],
            comparison_rows,
        ),
        "",
        "## Quality and freshness comparison",
        "",
        _table(
            ["Signal", "Baseline", "Corrupted", "Repaired", "Corrupted detail", "Repaired detail"],
            quality_rows,
        ),
        "",
        "## Corrupted quality details",
        "",
        _quality_checks_table(corrupted_quality),
        "",
        "## Repaired quality details",
        "",
        _quality_checks_table(repaired_quality),
        "",
        "## Corrupted freshness details",
        "",
        _freshness_table(corrupted_freshness),
        "",
        "## Repaired freshness details",
        "",
        _freshness_table(repaired_freshness),
        "",
        "## Evidence-based observations",
        "",
    ]
    lines.extend(f"- {observation}" for observation in observations)
    write_text(Path(report_path), "\n".join(lines).rstrip() + "\n")
