from __future__ import annotations

from pathlib import Path
from typing import Any


def generate_phase1_report(
    report_path: Path | str,
    source_summary: dict[str, Any],
    metrics: dict[str, Any],
    quality: dict[str, Any],
    freshness: dict[str, Any],
) -> None:
    """Tạo báo cáo markdown tổng hợp Phase 1 (Baseline Pipeline) và ghi vào report_path."""
    target_path = Path(report_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)

    markdown_content = f"""# Báo Cáo Baseline RAG Pipeline & Evaluation (Phase 1)

Báo cáo này tổng hợp hiệu năng ban đầu của **Baseline RAG Pipeline** trên tập dữ liệu 24 bài báo khoa học sạch và bộ câu hỏi đánh giá cố định (Frozen Evaluation Test Set).

---

## 1. Tóm tắt Dữ liệu Đầu vào (Source & Ingestion Summary)

- **Nguồn dữ liệu**: {source_summary.get("source_api", "Crossref REST API")}
- **Từ khóa truy vấn**: `{source_summary.get("source_query", "N/A")}`
- **Số lượng bản ghi sạch (`clean_records`)**: **{source_summary.get("clean_rows", 24)} bài báo**
- **Đường dẫn dữ liệu sạch**: `data/clean/papers_clean.json`

---

## 2. Bảng Kết quả Đánh giá Baseline (Evaluation Metrics)

| Chỉ số (Metric) | Giá trị (Value) | Mô tả |
| :--- | :--- | :--- |
| **Số mẫu câu hỏi (Test Samples)** | `{metrics.get("samples", 10)}` | Tổng số câu hỏi đóng băng trong `test_set.json` |
| **Retrieval Hit Rate** | **{metrics.get("retrieval_hit_rate", 0.0) * 100:.1f}%** | Tỷ lệ truy xuất thành công đúng bài báo tham chiếu trong Top-4 |
| **Mean Token F1** | **{metrics.get("mean_token_f1", 0.0):.4f}** | Độ trùng khớp từ vựng giữa dự đoán và Ground Truth |
| **LLM Judge Accuracy** | **{metrics.get("judge_accuracy", 0.0) * 100:.1f}%** | Tỷ lệ câu trả lời được LLM Judge đánh giá là ĐÚNG |
| **Mean Judge Score** | **{metrics.get("mean_judge_score", 0.0):.2f} / 5.0** | Điểm số chất lượng trung bình từ LLM Judge (thang 1-5) |

---

## 3. Kiểm tra Chất lượng Dữ liệu & Độ Tươi Mới (Data Quality & Freshness)

- **Trạng thái Quality Check**: `{"PASSED" if quality.get("passed") else "FAILED"}`
- **Tổng số hàng dữ liệu**: `{quality.get("total_rows", 0)}`
- **Paper ID hợp lệ & duy nhất**: `{"Có" if quality.get("checks", {}).get("paper_id_unique") else "Không"}`
- **Tiêu đề không trống**: `{"Có" if quality.get("checks", {}).get("title_not_null") else "Không"}`
- **Độ dài summary >= 100 ký tự**: `{"Có" if quality.get("checks", {}).get("summary_len_ge_100") else "Không"}`
- **Bài báo mới nhất (`latest_published`)**: `{freshness.get("latest_published", "N/A")}`
- **Bài báo cũ nhất (`oldest_published`)**: `{freshness.get("oldest_published", "N/A")}`
- **Số hàng dữ liệu cũ (`stale_rows`)**: `{freshness.get("stale_rows", 0)}`
- **Trạng thái độ tươi mới (`is_fresh`)**: `{"Đạt chuẩn" if freshness.get("is_fresh") else "Cần cập nhật"}`

---

## 4. Kết luận Baseline

Baseline RAG Pipeline hoạt động ổn định trên tập dữ liệu chuẩn. Đây sẽ là mốc điểm cơ sở (benchmark baseline) để đối chiếu hiệu năng khi tiến hành giả lập dữ liệu lỗi (**Corrupted State**) và phục hồi dữ liệu (**Repaired State**) ở các bước tiếp theo.
"""

    with open(target_path, "w", encoding="utf-8") as f:
        f.write(markdown_content)


def generate_corruption_report(
    report_path: Path | str,
    baseline_metrics: dict[str, Any],
    corrupted_metrics: dict[str, Any],
    repaired_metrics: dict[str, Any],
    corrupted_quality: dict[str, Any],
    repaired_quality: dict[str, Any],
    corrupted_freshness: dict[str, Any],
    repaired_freshness: dict[str, Any],
) -> None:
    """Viết markdown report so sánh baseline/corrupted/repaired."""
    target_path = Path(report_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)

    markdown_content = f"""# Báo Cáo So Sánh Hiệu Năng RAG (Baseline vs Corrupted vs Repaired)

Báo cáo so sánh sự biến động điểm số khi dữ liệu bị lỗi và khi dữ liệu được khôi phục.

---

## Bảng So Sánh Chỉ Số (Comparative Metrics)

| Chỉ số (Metric) | Baseline | Corrupted | Repaired |
| :--- | :--- | :--- | :--- |
| **Retrieval Hit Rate** | {baseline_metrics.get("retrieval_hit_rate", 0.0) * 100:.1f}% | {corrupted_metrics.get("retrieval_hit_rate", 0.0) * 100:.1f}% | {repaired_metrics.get("retrieval_hit_rate", 0.0) * 100:.1f}% |
| **Mean Token F1** | {baseline_metrics.get("mean_token_f1", 0.0):.4f} | {corrupted_metrics.get("mean_token_f1", 0.0):.4f} | {repaired_metrics.get("mean_token_f1", 0.0):.4f} |
| **LLM Judge Accuracy** | {baseline_metrics.get("judge_accuracy", 0.0) * 100:.1f}% | {corrupted_metrics.get("judge_accuracy", 0.0) * 100:.1f}% | {repaired_metrics.get("judge_accuracy", 0.0) * 100:.1f}% |
| **Mean Judge Score** | {baseline_metrics.get("mean_judge_score", 0.0):.2f} | {corrupted_metrics.get("mean_judge_score", 0.0):.2f} | {repaired_metrics.get("mean_judge_score", 0.0):.2f} |
"""

    with open(target_path, "w", encoding="utf-8") as f:
        f.write(markdown_content)

