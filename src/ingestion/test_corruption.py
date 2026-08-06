import unittest
import shutil
import tempfile
from pathlib import Path
import pandas as pd

from ingestion.corruption import corrupt_clean_dataframe


class TestDataCorruption(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.log_path = self.test_dir / "corruption_log.json"

        # Đọc dữ liệu sạch thực tế
        self.clean_df = pd.read_json("data/clean/papers_clean.json")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_corrupt_clean_dataframe(self):
        corrupted_df = corrupt_clean_dataframe(self.clean_df, self.log_path)

        # 1. Kiểm tra số lượng dòng tăng lên do duplicate
        self.assertGreater(len(corrupted_df), len(self.clean_df))

        # 2. Kiểm tra file log có được sinh ra không
        self.assertTrue(self.log_path.exists())

        # 3. Kiểm tra kịch bản blank summary cho paper 10.1111/exsy.70341
        blank_row = corrupted_df[corrupted_df["paper_id"].str.lower() == "10.1111/exsy.70341"]
        if not blank_row.empty:
            self.assertEqual(blank_row.iloc[0]["summary"], "")

        # 4. Kiểm tra kịch bản stale date
        stale_rows = corrupted_df[corrupted_df["published"] == "2000-01-01"]
        self.assertGreaterEqual(len(stale_rows), 5)


if __name__ == "__main__":
    unittest.main()
