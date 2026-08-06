import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import json
import tempfile
import shutil

from ingestion.crossref import PaperRecord, parse_crossref_payload, fetch_source_records, load_raw_records
from core.config import Settings, Paths

class TestCrossrefIngestion(unittest.TestCase):
    def setUp(self):
        # Tạo thư mục tạm để test việc lưu file
        self.test_dir = Path(tempfile.mkdtemp())
        
        # Tạo settings giả lập
        self.mock_paths = Paths(
            project_dir=self.test_dir,
            workspace_dir=self.test_dir,
            raw_api_response=self.test_dir / "crossref_response.json",
            raw_records_json=self.test_dir / "crossref_records.json",
            clean_csv=self.test_dir / "papers_clean.csv",
            clean_json=self.test_dir / "papers_clean.json",
            chroma_dir=self.test_dir / "chroma",
            embeddings_json=self.test_dir / "papers_embeddings.json",
            corrupted_clean_csv=self.test_dir / "papers_clean_corrupted.csv",
            corrupted_clean_json=self.test_dir / "papers_clean_corrupted.json",
            corrupted_embeddings_json=self.test_dir / "papers_embeddings_corrupted.json",
            repaired_clean_csv=self.test_dir / "papers_clean_repaired.csv",
            repaired_clean_json=self.test_dir / "papers_clean_repaired.json",
            repaired_embeddings_json=self.test_dir / "papers_embeddings_repaired.json",
            eval_testset=self.test_dir / "test_set.json",
            baseline_metrics=self.test_dir / "baseline_metrics.json",
            baseline_answers=self.test_dir / "baseline_answers.json",
            demo_answers=self.test_dir / "agent_demo_answers.json",
            quality_dir=self.test_dir / "quality",
            gx_dir=self.test_dir / "quality" / "gx",
            freshness_report=self.test_dir / "quality" / "freshness_report.json",
            baseline_report=self.test_dir / "reports" / "phase1_report.md",
            corruption_log=self.test_dir / "results" / "corruption_log.json",
            corrupted_metrics=self.test_dir / "results" / "corrupted_metrics.json",
            corrupted_answers=self.test_dir / "results" / "corrupted_answers.json",
            repaired_metrics=self.test_dir / "results" / "repaired_metrics.json",
            repaired_answers=self.test_dir / "results" / "repaired_answers.json",
            comparison_report=self.test_dir / "reports" / "corruption_report.md"
        )
        self.settings = Settings(
            llm_provider="mock",
            model_name="mock",
            google_api_key=None,
            openai_api_key=None,
            anthropic_api_key=None,
            openrouter_api_key=None,
            openrouter_base_url="http://mock",
            ollama_base_url="http://mock",
            custom_llm_api_key=None,
            custom_llm_base_url=None,
            embedding_model="mock",
            baseline_collection_name="mock",
            corrupted_collection_name="mock",
            repaired_collection_name="mock",
            source_api="Crossref REST API",
            source_query="test query",
            source_filter="has-abstract:true",
            max_results=5,
            top_k=2,
            freshness_threshold_days=180,
            refresh_source=True,
            refresh_test_set=True,
            paths=self.mock_paths
        )

    def tearDown(self):
        # Xóa thư mục tạm sau khi test xong
        shutil.rmtree(self.test_dir)

    def test_parse_crossref_payload(self):
        payload = {
            "message": {
                "items": [
                    {
                        "DOI": "10.1001/test.1",
                        "title": ["Test Paper Title"],
                        "abstract": "<p>This is a test abstract with <jats:italic>italic</jats:italic> tag.</p>",
                        "author": [
                            {"given": "John", "family": "Doe"},
                            {"given": "Jane", "family": "Smith"}
                        ],
                        "subject": ["Computer Science", "AI"],
                        "published": {"date-parts": [[2026, 8, 6]]},
                        "indexed": {"date-parts": [[2026, 8, 6]]},
                        "URL": "https://doi.org/10.1001/test.1",
                        "link": [
                            {"URL": "https://test.com/pdf", "content-type": "application/pdf"}
                        ],
                        "publisher": "Test Publisher"
                    },
                    {
                        # bản ghi thiếu abstract -> bị lọc bỏ
                        "DOI": "10.1001/test.2",
                        "title": ["Missing Abstract Title"],
                        "author": [],
                        "subject": []
                    }
                ]
            }
        }
        records = parse_crossref_payload(payload)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].paper_id, "10.1001/test.1")
        self.assertEqual(records[0].title, "Test Paper Title")
        # Giữ nguyên thẻ XML/JATS ở bước Ingestion theo yêu cầu mới nhất
        self.assertEqual(records[0].summary, "<p>This is a test abstract with <jats:italic>italic</jats:italic> tag.</p>")
        self.assertEqual(records[0].authors, ["John Doe", "Jane Smith"])
        self.assertEqual(records[0].categories, ["Computer Science", "AI"])
        self.assertEqual(records[0].primary_category, "Computer Science")
        self.assertEqual(records[0].published, "2026-08-06")
        self.assertEqual(records[0].updated, "2026-08-06")
        self.assertEqual(records[0].abs_url, "https://doi.org/10.1001/test.1")
        self.assertEqual(records[0].pdf_url, "https://test.com/pdf")
        self.assertEqual(records[0].comment, "Test Publisher")

    @patch("ingestion.crossref.requests.get")
    @patch("ingestion.crossref.time.sleep") # mock sleep để chạy test nhanh hơn
    def test_fetch_source_records_retry_and_save(self, mock_sleep, mock_get):
        response_429 = MagicMock()
        response_429.status_code = 429
        
        response_200 = MagicMock()
        response_200.status_code = 200
        payload_data = {
            "message": {
                "items": [
                    {
                        "DOI": "10.1001/test.3",
                        "title": ["Another Test Paper"],
                        "abstract": "Normal Abstract Text",
                        "author": []
                    }
                ]
            }
        }
        response_200.json.return_value = payload_data
        
        # Giả lập lần 1 lỗi 429, lần 2 thành công
        mock_get.side_effect = [response_429, response_200]
        
        records = fetch_source_records(self.settings)
        
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].paper_id, "10.1001/test.3")
        self.assertTrue(self.mock_paths.raw_api_response.exists())
        self.assertTrue(self.mock_paths.raw_records_json.exists())
        
        # Kiểm tra file raw HTTP response
        with open(self.mock_paths.raw_api_response, "r", encoding="utf-8") as f:
            saved_raw = json.load(f)
        self.assertEqual(saved_raw, payload_data)
        
        # Kiểm tra file raw records đã được parse
        loaded_records = load_raw_records(self.mock_paths.raw_records_json)
        self.assertEqual(len(loaded_records), 1)
        self.assertEqual(loaded_records[0].paper_id, "10.1001/test.3")

if __name__ == "__main__":
    unittest.main()
