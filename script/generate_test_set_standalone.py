"""Script standalone - sinh test_set.json KHÔNG cần import metrics.py.

Dùng khi chưa cài đầy đủ dependency (datasets, ragas...).

    python script/generate_test_set_standalone.py
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────
# Inline implementation: không import __init__.py của evaluation
# để tránh kéo datasets/ragas vào khi chưa cài xong
# ──────────────────────────────────────────────────────────────────


def _truncate(text: str, max_chars: int = 300) -> str:
    text = text.strip()
    first_dot = text.find(". ")
    if 0 < first_dot <= max_chars:
        return text[: first_dot + 1].strip()
    return text[:max_chars].rstrip() + ("..." if len(text) > max_chars else "")


def generate(clean_json: Path, output: Path) -> list[dict]:
    with open(clean_json, "r", encoding="utf-8") as f:
        records = json.load(f)

    if len(records) < 5:
        raise ValueError(f"Cần ít nhất 5 records, chỉ có {len(records)}")

    # Sắp xếp ổn định: mới nhất trước
    records_sorted = sorted(records, key=lambda r: (r.get("published", ""), r.get("paper_id", "")), reverse=True)

    n = len(records_sorted)

    def pick(idx_list: list[int]) -> list[dict]:
        return [records_sorted[min(i, n - 1)] for i in idx_list]

    papers_summary    = pick([0, n // 3, 2 * n // 3])
    papers_authors    = pick([1, n // 3 + 1, 2 * n // 3 + 1])
    papers_date       = pick([2, n // 3 + 2, 2 * n // 3 + 2])
    papers_categories = pick([3, n // 3 + 3, min(2 * n // 3 + 3, n - 1)])

    test_set = []
    q_id = 1

    for row in papers_summary:
        gt = _truncate(row["summary"])
        test_set.append({
            "id": f"q{q_id}",
            "question_type": "summary",
            "question": f"What is the main contribution or topic of the paper titled \"{row['title']}\"?",
            "ground_truth": gt,
            "ground_truth_doc_ids": [row["paper_id"]],
        })
        q_id += 1

    for row in papers_authors:
        authors = row.get("authors_joined", "") or ", ".join(row.get("authors", [])) or "Unknown"
        test_set.append({
            "id": f"q{q_id}",
            "question_type": "authors",
            "question": f"Who are the authors of the paper titled \"{row['title']}\"?",
            "ground_truth": authors,
            "ground_truth_doc_ids": [row["paper_id"]],
        })
        q_id += 1

    for row in papers_date:
        test_set.append({
            "id": f"q{q_id}",
            "question_type": "date",
            "question": f"When was the paper titled \"{row['title']}\" published?",
            "ground_truth": row.get("published", ""),
            "ground_truth_doc_ids": [row["paper_id"]],
        })
        q_id += 1

    for row in papers_categories:
        cats = row.get("categories_joined", "") or row.get("primary_category", "unknown")
        test_set.append({
            "id": f"q{q_id}",
            "question_type": "categories",
            "question": f"What are the research topics or categories of the paper titled \"{row['title']}\"?",
            "ground_truth": cats,
            "ground_truth_doc_ids": [row["paper_id"]],
        })
        q_id += 1

    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w", encoding="utf-8") as f:
        json.dump(test_set, f, indent=2, ensure_ascii=False)

    return test_set


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    clean_json   = project_root / "data" / "clean" / "papers_clean.json"
    output       = project_root / "data" / "eval" / "test_set.json"

    logger.info("Đọc clean data: %s", clean_json)
    if not clean_json.exists():
        logger.error("Không tìm thấy file: %s", clean_json)
        sys.exit(1)

    test_set = generate(clean_json, output)

    logger.info("=== %d câu hỏi đã được tạo ===", len(test_set))
    for item in test_set:
        print(f"  [{item['id']}] ({item['question_type']:10s}) {item['question'][:90]}")
    print()
    logger.info("Lưu vào: %s", output)


if __name__ == "__main__":
    main()
