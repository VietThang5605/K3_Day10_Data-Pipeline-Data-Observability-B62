import unittest
from datetime import UTC, datetime
import pandas as pd

from ingestion.crossref import PaperRecord
from ingestion.cleaning import build_clean_dataframe


class TestDataCleaning(unittest.TestCase):
    def test_build_clean_dataframe(self):
        records = [
            # 1. Bản ghi chuẩn có thẻ JATS XML
            PaperRecord(
                paper_id="10.1001/test.1",
                title="<jats:title>Test Title 1</jats:title>",
                summary="<p>This is a sufficiently long abstract test summary that exceeds 100 characters in length to verify that valid abstracts are retained correctly by the cleaning module.</p>",
                authors=["John Doe", "Jane Smith"],
                categories=[],
                primary_category="unknown",
                published="2026-08-01",
                updated="2026-08-01",
                abs_url="https://doi.org/10.1001/test.1",
                pdf_url="",
                comment="Test Publisher"
            ),
            # 2. Bản ghi có tóm tắt quá ngắn (< 100 ký tự) -> phải bị lọc bỏ
            PaperRecord(
                paper_id="10.1001/test.2",
                title="Test Title 2",
                summary="Too short summary.",
                authors=["Alice Brown"],
                categories=["AI"],
                primary_category="AI",
                published="2026-08-01",
                updated="2026-08-01",
                abs_url="https://doi.org/10.1001/test.2",
                pdf_url="",
                comment=""
            ),
            # 3. Bản ghi thiếu tiêu đề -> phải bị lọc bỏ
            PaperRecord(
                paper_id="10.1001/test.3",
                title="",
                summary="<p>This is another long summary but title is missing so it should be filtered out from the final dataset.</p>",
                authors=[],
                categories=[],
                primary_category="unknown",
                published="2026-08-01",
                updated="2026-08-01",
                abs_url="",
                pdf_url="",
                comment=""
            ),
            # 4. Bản ghi có tiêu đề tiếng Nga (phi Latinh) -> phải bị lọc bỏ
            PaperRecord(
                paper_id="10.47576/2949-1894.2026.7.7.023",
                title="Снижение рисков применения LLM (Large Language Model) в сфере экономической безопасности",
                summary="This is a long summary for Russian paper that should be filtered out because the title is in Russian.",
                authors=["И.В. Ермаков"],
                categories=["Finance"],
                primary_category="Finance",
                published="2026-08-01",
                updated="2026-08-01",
                abs_url="",
                pdf_url="",
                comment=""
            )
        ]

        run_date = datetime(2026, 8, 6, tzinfo=UTC)
        df = build_clean_dataframe(records, run_date)

        # Kiểm tra số bản ghi còn lại (chỉ bản ghi 1 hợp lệ)
        self.assertEqual(len(df), 1)
        row = df.iloc[0]

        # Kiểm tra bóc tách XML
        self.assertEqual(row["title"], "Test Title 1")
        self.assertTrue("<p>" not in row["summary"])

        # Kiểm tra gộp authors và categories
        self.assertEqual(row["authors_joined"], "John Doe, Jane Smith")
        self.assertTrue("categories_joined" in row)

        # Kiểm tra tính toán age_days (từ 2026-08-01 đến 2026-08-06 là 5 ngày)
        self.assertEqual(row["age_days"], 5)

        # Kiểm tra trường text_for_embedding
        self.assertTrue("Title: Test Title 1" in row["text_for_embedding"])
        self.assertTrue("Summary:" in row["text_for_embedding"])

        # Kiểm tra report
        report = df.attrs.get("cleaning_report", {})
        self.assertEqual(report["filtered"]["short_summary"], 1)
        self.assertEqual(report["filtered"]["missing_title"], 1)
        self.assertEqual(report["filtered"]["non_english_script"], 1)


if __name__ == "__main__":
    unittest.main()
