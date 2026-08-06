# Báo Cáo Baseline RAG Pipeline & Evaluation (Phase 1)

Báo cáo này tổng hợp hiệu năng ban đầu của **Baseline RAG Pipeline** trên tập dữ liệu 23 bài báo khoa học sạch (đã qua lọc ngôn ngữ phi Latinh) và bộ câu hỏi đánh giá cố định (Frozen Evaluation Test Set).

---

## 1. Tóm tắt Dữ liệu Đầu vào (Source & Ingestion Summary)

- **Nguồn dữ liệu**: Crossref REST API
- **Từ khóa truy vấn**: `agentic retrieval augmented generation large language model`
- **Số lượng bản ghi sạch (`clean_records`)**: **23 bài báo (100% Tiếng Anh chuẩn)**
- **Đường dẫn dữ liệu sạch**: [papers_clean.json](file:///Users/nguyenvietthang/Coding/VinUni/Lab/K3_Day10_Data-Pipeline-Data-Observability-B62/data/clean/papers_clean.json)

---

## 2. Bảng Kết quả Đánh giá Baseline (Baseline Evaluation Metrics)

| Chỉ số (Metric) | Giá trị (Value) | Mô tả |
| :--- | :--- | :--- |
| **Số mẫu câu hỏi (Test Samples)** | `10` | Tổng số câu hỏi đóng băng trong `test_set.json` |
| **Retrieval Hit Rate** | **100.0%** | Tỷ lệ truy xuất thành công đúng bài báo tham chiếu trong Top-4 |
| **Mean Token F1** | **0.5824** | Độ trùng khớp từ vựng giữa dự đoán và Ground Truth |
| **LLM Judge Accuracy** | **90.0%** | Tỷ lệ câu trả lời được LLM Judge đánh giá là ĐÚNG (9/10 câu) |
| **Mean Judge Score** | **4.50 / 5.0** | Điểm số chất lượng trung bình từ LLM Judge (thang 1-5) |

---

## 3. Bảng Cải Tiến Hiệu Năng khi Tối Ưu Hóa Data Cleaning (Improvement Metrics)

Việc bổ sung quy tắc **lọc bỏ dữ liệu phi Tiếng Anh (Non-Latin Script Filtering)** ở bước Data Cleaning giúp loại bỏ các ký tự rác Tiếng Nga (Cyrillic), tăng cường độ sạch của dữ liệu đầu vào và đem lại sự gia tăng rõ rệt về hiệu năng RAG:

| Chỉ số (Metric) | Trước khi lọc bài Tiếng Nga (24 bài) | Sau khi lọc bài Tiếng Nga (23 bài) | Mức độ cải thiện |
| :--- | :--- | :--- | :--- |
| **Retrieval Hit Rate** | `100.0%` | **100.0%** | Giữ vững 100% |
| **Mean Token F1** | `0.5748` | **0.5824** | ⬆️ **+0.0076** |
| **LLM Judge Accuracy** | `80.0%` | **90.0%** | ⬆️ **+10.0%** (9/10 câu đúng) |
| **Mean Judge Score** | `4.40 / 5.0` | **4.50 / 5.0** | ⬆️ **+0.10 điểm** |

---

## 4. Kiểm tra Chất lượng Dữ liệu & Độ Tươi Mới (Data Quality & Freshness)

- **Trạng thái Quality Check**: `PASSED`
- **Tổng số hàng dữ liệu**: `23`
- **Paper ID hợp lệ & duy nhất**: `Có`
- **Tiêu đề không trống & Tiếng Anh chuẩn**: `Có`
- **Độ dài summary >= 100 ký tự**: `Có`
- **Bài báo mới nhất (`latest_published`)**: `2026-08-01`
- **Bài báo cũ nhất (`oldest_published`)**: `2026-02-12`
- **Số hàng dữ liệu cũ (`stale_rows`)**: `0`
- **Trạng thái độ tươi mới (`is_fresh`)**: `Đạt chuẩn`

---

## 5. Kết luận Baseline

Baseline RAG Pipeline hoạt động cực kỳ ấn tượng trên tập dữ liệu chuẩn 23 bài báo sạch với độ chính xác LLM Judge đạt **90%** và điểm số trung bình **4.5/5.0**. Đây sẽ là mốc điểm cơ sở (benchmark baseline) để đối chiếu hiệu năng khi tiến hành giả lập dữ liệu lỗi (**Corrupted State**) và phục hồi dữ liệu (**Repaired State**) ở các bước tiếp theo.
