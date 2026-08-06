"""Script tạo test_set.json từ papers_clean.json đã có sẵn.

Chạy:
    uv run python script/generate_test_set.py
    # hoặc
    python script/generate_test_set.py
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

# Thêm src/ vào sys.path để import các module trong project
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd

from core.config import load_settings
from evaluation.testset import build_test_set

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    settings = load_settings()
    clean_json_path = settings.paths.clean_json
    testset_path = settings.paths.eval_testset

    logger.info("Đọc dữ liệu sạch từ: %s", clean_json_path)
    if not clean_json_path.exists():
        logger.error("File không tồn tại: %s", clean_json_path)
        sys.exit(1)

    with open(clean_json_path, "r", encoding="utf-8") as f:
        records = json.load(f)

    df = pd.DataFrame(records)
    logger.info("Số lượng records: %d", len(df))

    test_set = build_test_set(df, testset_path)

    logger.info("=== TEST SET ĐÃ TẠO (%d câu hỏi) ===", len(test_set))
    for item in test_set:
        logger.info(
            "[%s] (%s) %s", item["id"], item["question_type"], item["question"][:80]
        )

    logger.info("Đã lưu test_set.json vào: %s", testset_path)


if __name__ == "__main__":
    main()
