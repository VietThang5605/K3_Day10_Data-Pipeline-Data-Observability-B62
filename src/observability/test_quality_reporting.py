from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest

import pandas as pd

from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_corruption_report, generate_phase1_report


def _settings(root: Path) -> SimpleNamespace:
    return SimpleNamespace(
        max_results=24,
        freshness_threshold_days=180,
        paths=SimpleNamespace(quality_dir=root / "quality"),
    )


def _clean_dataframe() -> pd.DataFrame:
    summary = "This abstract contains enough text to be valid for the evaluation dataset."
    return pd.DataFrame(
        {
            "paper_id": ["doi-1", "doi-2", "doi-3", "doi-4"],
            "title": ["Paper one", "Paper two", "Paper three", "Paper four"],
            "summary": [summary] * 4,
            "published": ["2026-08-01", "2026-08-02", "2026-08-03", "2026-08-04"],
            "age_days": [5, 4, 3, 2],
        }
    )


class TestQualityAndReporting(unittest.TestCase):
    def test_quality_and_freshness_reports_record_valid_and_invalid_data(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            settings = _settings(root)
            clean_df = _clean_dataframe()

            quality = run_data_quality_checks(clean_df, settings, "baseline")
            freshness = build_freshness_report(clean_df, settings, root / "freshness.json")

            self.assertTrue(quality["overall_passed"])
            self.assertEqual(quality["summary"]["failed_checks"], [])
            self.assertTrue((root / "quality" / "baseline_quality_report.json").exists())
            self.assertTrue(freshness["is_fresh"])
            self.assertEqual(freshness["latest_published"], "2026-08-04")
            self.assertEqual(freshness["oldest_published"], "2026-08-01")

            corrupted_df = clean_df.copy()
            corrupted_df.loc[0, "summary"] = ""
            corrupted_df.loc[1, "age_days"] = 500
            corrupted_df.loc[3, "paper_id"] = "doi-3"
            corrupted_quality = run_data_quality_checks(corrupted_df, settings, "corrupted")
            corrupted_freshness = build_freshness_report(corrupted_df, settings, root / "corrupted_freshness.json")

            self.assertFalse(corrupted_quality["overall_passed"])
            self.assertIn("paper_id_unique", corrupted_quality["summary"]["failed_checks"])
            self.assertIn("summary_length", corrupted_quality["summary"]["failed_checks"])
            self.assertFalse(corrupted_freshness["is_fresh"])
            self.assertEqual(corrupted_freshness["stale_rows"], 1)

    def test_markdown_reports_render_real_payload_values(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            settings = _settings(root)
            clean_df = _clean_dataframe()
            quality = run_data_quality_checks(clean_df, settings, "baseline")
            freshness = build_freshness_report(clean_df, settings, root / "freshness.json")
            metrics = {
                "samples": 4,
                "retrieval_hit_rate": 1.0,
                "mean_token_f1": 0.8,
                "judge_accuracy": 0.75,
                "mean_judge_score": 4.0,
                "ragas": {"skipped": "RUN_RAGAS is disabled"},
            }

            phase1_path = root / "phase1_report.md"
            generate_phase1_report(
                phase1_path,
                {"source_api": "Crossref", "records": 4},
                metrics,
                quality,
                freshness,
            )
            phase1_text = phase1_path.read_text(encoding="utf-8")
            self.assertIn("retrieval_hit_rate", phase1_text)
            self.assertIn("RUN_RAGAS is disabled", phase1_text)
            self.assertIn("latest_published", phase1_text)

            corrupted_metrics = {**metrics, "retrieval_hit_rate": 0.5, "mean_token_f1": 0.4}
            comparison_path = root / "corruption_report.md"
            generate_corruption_report(
                comparison_path,
                metrics,
                corrupted_metrics,
                metrics,
                quality,
                quality,
                freshness,
                freshness,
                baseline_quality=quality,
                baseline_freshness=freshness,
            )
            comparison_text = comparison_path.read_text(encoding="utf-8")
            self.assertIn("Corruption delta", comparison_text)
            self.assertIn("-0.5000", comparison_text)
            self.assertIn("Quality and freshness comparison", comparison_text)


if __name__ == "__main__":
    unittest.main()
