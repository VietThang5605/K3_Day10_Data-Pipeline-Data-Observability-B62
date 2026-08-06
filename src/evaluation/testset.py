from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import pandas as pd

from core.utils import write_json

logger = logging.getLogger(__name__)

# Số lượng câu hỏi tối thiểu mỗi loại
_MIN_DOCS = 5
_QUESTIONS_PER_TYPE = 3


def _truncate(text: str, max_chars: int = 300) -> str:
    """Rút gọn text dài thành câu đầu tiên, tối đa max_chars ký tự."""
    text = text.strip()
    # Lấy câu đầu tiên (kết thúc bằng dấu chấm)
    first_dot = text.find(". ")
    if 0 < first_dot <= max_chars:
        return text[: first_dot + 1].strip()
    return text[:max_chars].rstrip() + ("..." if len(text) > max_chars else "")


def build_test_set(df: pd.DataFrame, output_path) -> list[dict[str, Any]]:
    """Tạo bộ evaluation set cố định (Frozen Evaluation Set) từ cleaned dataframe.

    Quy trình:
    1. Kiểm tra số lượng document tối thiểu.
    2. Chọn các paper đại diện theo từng loại câu hỏi:
       - summary   : câu hỏi về nội dung / đóng góp chính của bài báo
       - authors   : câu hỏi về tác giả
       - date      : câu hỏi về ngày xuất bản
       - categories: câu hỏi về chủ đề / lĩnh vực
    3. Mỗi sample tuân thủ schema:
       {id, question_type, question, ground_truth, ground_truth_doc_ids}
    4. Ghi file JSON vào output_path.

    Tham số:
        df          : DataFrame đã clean (papers_clean.json đã được load).
        output_path : đường dẫn lưu test_set.json (str hoặc Path).

    Trả về:
        List[dict] — danh sách các sample câu hỏi.
    """
    output_path = Path(output_path)

    # ── 1. Kiểm tra số lượng document ────────────────────────────────────────
    if len(df) < _MIN_DOCS:
        raise ValueError(
            f"Cần ít nhất {_MIN_DOCS} document để tạo test set, "
            f"nhưng chỉ có {len(df)}."
        )

    # Đảm bảo các cột cần thiết tồn tại
    required_cols = {"paper_id", "title", "summary", "authors_joined",
                     "categories_joined", "primary_category", "published"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"DataFrame thiếu các cột: {missing}")

    # Sắp xếp ổn định: mới nhất trước, sau đó theo paper_id
    df = df.sort_values(["published", "paper_id"], ascending=[False, True]).reset_index(drop=True)

    # ── 2. Chọn papers đại diện cho từng loại câu hỏi ────────────────────────
    # Chọn phân tán theo vị trí trong danh sách để bao phủ nhiều chủ đề
    n = len(df)
    # Lấy 3 vị trí: đầu / giữa / 3/4 danh sách
    indices_summary    = [0, n // 3, 2 * n // 3]
    indices_authors    = [1, n // 3 + 1, 2 * n // 3 + 1]
    indices_date       = [2, n // 3 + 2, 2 * n // 3 + 2]
    indices_categories = [3, n // 3 + 3, min(2 * n // 3 + 3, n - 1)]

    # Clamp để không vượt bounds
    def _clamp(idx_list: list[int]) -> list[int]:
        return [min(i, n - 1) for i in idx_list]

    indices_summary    = _clamp(indices_summary)
    indices_authors    = _clamp(indices_authors)
    indices_date       = _clamp(indices_date)
    indices_categories = _clamp(indices_categories)

    test_set: list[dict[str, Any]] = []
    q_id = 1

    # ── 3a. Summary questions ─────────────────────────────────────────────────
    for i in indices_summary:
        row = df.iloc[i]
        ground_truth = _truncate(row["summary"])
        test_set.append({
            "id": f"q{q_id}",
            "question_type": "summary",
            "question": f"What is the main contribution or topic of the paper titled \"{row['title']}\"?",
            "ground_truth": ground_truth,
            "ground_truth_doc_ids": [row["paper_id"]],
        })
        q_id += 1

    # ── 3b. Authors questions ─────────────────────────────────────────────────
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

    # ── 3c. Date questions ────────────────────────────────────────────────────
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

    # ── 3d. Categories questions ──────────────────────────────────────────────
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

    # ── 4. Validate tất cả các sample đều có doc_id tồn tại trong df ─────────
    valid_ids = set(df["paper_id"].tolist())
    for sample in test_set:
        for doc_id in sample["ground_truth_doc_ids"]:
            if doc_id not in valid_ids:
                logger.warning(
                    "ground_truth_doc_id '%s' (câu hỏi %s) không tồn tại trong DataFrame.",
                    doc_id, sample["id"],
                )

    # ── 5. Ghi file JSON ──────────────────────────────────────────────────────
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(output_path, test_set)

    logger.info(
        "Đã tạo %d câu hỏi và lưu vào '%s'.", len(test_set), output_path
    )
    return test_set
