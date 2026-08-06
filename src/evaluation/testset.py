from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import pandas as pd

from core.utils import write_json

logger = logging.getLogger(__name__)

_MIN_DOCS = 5


def _truncate(text: str, max_chars: int = 300) -> str:
    """Rút gọn text dài thành câu đầu tiên, tối đa max_chars ký tự."""
    text = text.strip()
    first_dot = text.find(". ")
    if 0 < first_dot <= max_chars:
        return text[: first_dot + 1].strip()
    return text[:max_chars].rstrip() + ("..." if len(text) > max_chars else "")


def build_test_set(df: pd.DataFrame, output_path) -> list[dict[str, Any]]:
    """Tạo bộ evaluation set cố định (Frozen Evaluation Set) từ cleaned dataframe."""
    output_path = Path(output_path)

    if len(df) < _MIN_DOCS:
        raise ValueError(
            f"Cần ít nhất {_MIN_DOCS} document để tạo test set, chỉ có {len(df)}."
        )

    required_cols = {"paper_id", "title", "summary", "authors_joined",
                     "categories_joined", "primary_category", "published"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"DataFrame thiếu các cột: {missing}")

    df = df.sort_values(["published", "paper_id"], ascending=[False, True]).reset_index(drop=True)
    n = len(df)

    indices_summary    = [0, n // 3, 2 * n // 3]
    indices_authors    = [1, n // 3 + 1, 2 * n // 3 + 1]
    indices_date       = [2, n // 3 + 2, 2 * n // 3 + 2]
    indices_categories = [3, n // 3 + 3, min(2 * n // 3 + 3, n - 1)]

    def _clamp(idx_list: list[int]) -> list[int]:
        return [min(i, n - 1) for i in idx_list]

    indices_summary    = _clamp(indices_summary)
    indices_authors    = _clamp(indices_authors)
    indices_date       = _clamp(indices_date)
    indices_categories = _clamp(indices_categories)

    test_set: list[dict[str, Any]] = []
    q_id = 1

    # 1. Summary questions
    for i in indices_summary:
        row = df.iloc[i]
        test_set.append({
            "id": f"q{q_id}",
            "question_type": "summary",
            "question": f"What is the main contribution or topic of the paper titled \"{row['title']}\"?",
            "ground_truth": _truncate(row["summary"]),
            "ground_truth_doc_ids": [row["paper_id"]],
        })
        q_id += 1

    # 2. Authors questions
    for i in indices_authors:
        row = df.iloc[i]
        authors = row["authors_joined"]
        if not authors or str(authors).strip() == "":
            authors = "Unknown"
        test_set.append({
            "id": f"q{q_id}",
            "question_type": "authors",
            "question": f"Who are the authors of the paper titled \"{row['title']}\"?",
            "ground_truth": str(authors),
            "ground_truth_doc_ids": [row["paper_id"]],
        })
        q_id += 1

    # 3. Date questions
    for i in indices_date:
        row = df.iloc[i]
        test_set.append({
            "id": f"q{q_id}",
            "question_type": "date",
            "question": f"When was the paper titled \"{row['title']}\" published?",
            "ground_truth": str(row["published"]),
            "ground_truth_doc_ids": [row["paper_id"]],
        })
        q_id += 1

    # 4. Categories questions
    for i in indices_categories:
        row = df.iloc[i]
        cats = row["categories_joined"]
        if not cats or str(cats).strip() == "":
            cats = row.get("primary_category", "unknown")
        test_set.append({
            "id": f"q{q_id}",
            "question_type": "categories",
            "question": f"What are the research topics or categories of the paper titled \"{row['title']}\"?",
            "ground_truth": str(cats),
            "ground_truth_doc_ids": [row["paper_id"]],
        })
        q_id += 1

    # Ghi file với ensure_ascii=False để giữ nguyên UTF-8 đọc được
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(test_set, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8"
    )

    logger.info("Đã tạo %d câu hỏi và lưu vào '%s'.", len(test_set), output_path)
    return test_set
