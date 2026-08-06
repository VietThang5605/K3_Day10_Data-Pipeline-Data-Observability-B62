import unittest
import json
import tempfile
import shutil
from pathlib import Path
import pandas as pd

from evaluation.testset import build_test_set


class TestEvaluationTestSet(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.output_path = self.test_dir / "test_set.json"

        # Đọc dữ liệu sạch thực tế để kiểm tra
        self.clean_df = pd.read_json("data/clean/papers_clean.json")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_build_test_set_success(self):
        samples = build_test_set(self.clean_df, self.output_path)

        # 1. Kiểm tra số lượng câu hỏi
        self.assertEqual(len(samples), 10)

        # 2. Kiểm tra file output thực tế có được sinh ra không
        self.assertTrue(self.output_path.exists())

        # 3. Kiểm tra schema của từng câu hỏi
        required_keys = {"id", "question_type", "question", "ground_truth", "ground_truth_doc_ids"}
        question_types = set()

        for sample in samples:
            self.assertTrue(required_keys.issubset(sample.keys()))
            self.assertTrue(len(sample["ground_truth_doc_ids"]) > 0)
            question_types.add(sample["question_type"])

        # 4. Kiểm tra phân bổ đủ 5 question_type
        expected_types = {"factual", "metadata", "summary", "application", "comparative"}
        self.assertEqual(question_types, expected_types)

        # 5. Mỗi type phải có đúng 2 câu hỏi
        type_counts = {}
        for s in samples:
            t = s["question_type"]
            type_counts[t] = type_counts.get(t, 0) + 1
        for t in expected_types:
            self.assertEqual(type_counts[t], 2)


if __name__ == "__main__":
    unittest.main()
