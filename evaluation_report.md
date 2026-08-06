# Báo Cáo Tổng Hợp Module Evaluation & Test Set

Tài liệu này tổng hợp toàn bộ công việc đã thực hiện, kết quả đạt được và các lưu ý kỹ thuật đối với module **Evaluation** (xây dựng bộ câu hỏi đánh giá cố định và kiểm tra metrics) thuộc dự án RAG Data Pipeline & Observability.

---

## 1. Các công việc đã thực hiện

### 1.1. Xây dựng Frozen Evaluation Set — `build_test_set()`

Triển khai hàm `build_test_set` trong [testset.py](file:///e:/lab/K3_Day10_Data-Pipeline-Data-Observability-B62/src/evaluation/testset.py):

- **Validation đầu vào**: Kiểm tra DataFrame có ít nhất 5 document và đủ các cột bắt buộc (`paper_id`, `title`, `summary`, `authors_joined`, `categories_joined`, `published`). Raise `ValueError` rõ ràng nếu thiếu.
- **Stable sort**: Sắp xếp theo `published` mới nhất trước, sau đó theo `paper_id` — đảm bảo kết quả **deterministic** mỗi lần chạy lại trên cùng dữ liệu.
- **Chọn papers đại diện**: Lấy 3 vị trí phân tán (đầu / 1/3 / 2/3 danh sách) cho mỗi loại câu hỏi, tránh thiên vị về chủ đề hay thời gian xuất bản.
- **Sinh 4 loại câu hỏi** (3 câu mỗi loại, tổng 12 câu):

  | Loại | Pattern câu hỏi | Ground truth |
  |------|----------------|--------------|
  | `summary` | *"What is the main contribution or topic of the paper titled ...?"* | Câu đầu của field `summary` |
  | `authors` | *"Who are the authors of the paper titled ...?"* | `authors_joined` |
  | `date` | *"When was the paper titled ... published?"* | `published` (YYYY-MM-DD) |
  | `categories` | *"What are the research topics or categories of the paper titled ...?"* | `categories_joined` |

- **Validate doc_ids**: Log cảnh báo nếu `ground_truth_doc_id` không tồn tại trong DataFrame hiện tại.
- **Lưu artifact**: Ghi bộ câu hỏi vào `data/eval/test_set.json` bằng `write_json()` (UTF-8, indent 2).

### 1.2. Đúng chuẩn Schema Yêu Cầu

Mỗi sample trong `test_set.json` tuân thủ đúng schema:

```json
{
  "id": "q1",
  "question_type": "summary",
  "question": "What is the main contribution or topic of the paper titled \"...\"?",
  "ground_truth": "Câu trả lời chuẩn trích từ clean data.",
  "ground_truth_doc_ids": ["10.xxxx/paper_doi"]
}
```

### 1.3. Script tiện ích sinh Test Set

Viết hai script hỗ trợ chạy độc lập không cần pipeline đầy đủ:

- [generate_test_set.py](file:///e:/lab/K3_Day10_Data-Pipeline-Data-Observability-B62/script/generate_test_set.py): Dùng `core.config.load_settings()` để tự động resolve đường dẫn, import `build_test_set` từ module chính.
- [generate_test_set_standalone.py](file:///e:/lab/K3_Day10_Data-Pipeline-Data-Observability-B62/script/generate_test_set_standalone.py): Phiên bản standalone không phụ thuộc vào `datasets`/`ragas` — chạy được ngay kể cả khi chưa cài đầy đủ dependency nặng.

### 1.4. Kiểm tra `metrics.py`

Đọc và xác nhận toàn bộ logic của [metrics.py](file:///e:/lab/K3_Day10_Data-Pipeline-Data-Observability-B62/src/evaluation/metrics.py):

- `_token_f1`: Tính F1 dựa trên token overlap — không cần LLM, dùng làm fallback.
- `_judge_answer`: Gọi LLM với structured output (`JudgeVerdict`) để chấm điểm 1–5 và phân loại `correct`. Có fallback về heuristic khi LLM không khả dụng.
- `evaluate_pipeline`: Hàm chính — load test set, chạy `answer_question` cho từng câu, tính `retrieval_hit`, `token_f1`, `judge`, tổng hợp summary metrics, ghi hai artifact `baseline_metrics.json` và `baseline_answers.json`.
- Xác nhận **không cần sửa** `metrics.py` — module đã hoàn chỉnh, sẵn sàng nhận `test_set.json` đúng schema.

---

## 2. Kết quả đạt được

### 2.1. Artifact `data/eval/test_set.json`

File đã được tạo và xác nhận nội dung với **12 câu hỏi** đa dạng, trích xuất trực tiếp từ `papers_clean.json`:

```text
q1  (summary)    SafeRAG — Oil and Gas Safety Report Generation
q2  (summary)    Снижение рисков LLM+RAG (tiếng Nga + tiếng Anh)
q3  (summary)    Speculative RAG for Cost-Efficient LLM Inference
q4  (authors)    Hi‐RAG: Hierarchical RAG for Tool Selection
q5  (authors)    RAG, Generative AI & Agentic AI Governance
q6  (authors)    Agentic RAG for Mental Health Language Models
q7  (date)       JADE-Plus: Multimodal Agentic RAG for Jawbone Lesions
q8  (date)       Operationalizing Reliability Gaps in LLMs
q9  (date)       RAG LLM Agents for Scientific Literature Review
q10 (categories) RAG for Cross-Market Equity Analysis
q11 (categories) Hallucination in LLMs and RAG
q12 (categories) RAG for Medical LLM Factual Accuracy
```

### 2.2. Phân bố câu hỏi theo loại

```text
summary    3 câu — đo khả năng retrieve và tóm tắt nội dung
authors    3 câu — đo khả năng retrieve thông tin metadata tác giả
date       3 câu — đo khả năng retrieve thông tin thời gian
categories 3 câu — đo khả năng retrieve và phân loại chủ đề
```

### 2.3. Độ bao phủ theo primary_category

```text
Retrieval-Augmented Generation    6 câu
Agentic AI                        3 câu
Healthcare AI                     2 câu
Finance                           1 câu
```

---

## 3. Các lưu ý kỹ thuật quan trọng (Notes & Observations)

1. **Tại sao phải đóng băng Eval Set trước khi đánh giá**:
   Ba trạng thái hệ thống (baseline → corrupted → repaired) phải được đánh giá trên **cùng bộ câu hỏi và cùng ground truth**. Nếu câu hỏi thay đổi giữa các lần chạy, chênh lệch metric có thể do câu hỏi dễ/khó hơn, không phải do chất lượng dữ liệu thay đổi.

2. **Xử lý khi `ground_truth_doc_ids` bị thiếu ở pha sau**:
   Khi một bài báo trong `ground_truth_doc_ids` bị drop ra khỏi index ở corruption flow, **không xóa câu hỏi** khỏi eval set. Logic trong `metrics.py` tự động xử lý:
   ```python
   retrieval_hit = any(doc_id in item["ground_truth_doc_ids"]
                       for doc_id in result.retrieved_doc_ids)
   # → False vì doc bị drop khỏi ChromaDB index
   ```
   Chỉ số `retrieval_hit_rate` giảm chính là **bằng chứng đo được impact của data corruption** — đây là mục tiêu cốt lõi của bài lab.

3. **Ground truth trích từ clean data gốc**:
   Tất cả `ground_truth` trong `test_set.json` được trích xuất trực tiếp từ `papers_clean.json` (dữ liệu baseline sạch), không phụ thuộc vào LLM hay bất kỳ bước sinh câu trả lời nào — đảm bảo tính xác thực.

4. **Câu hỏi dạng `summary` dùng câu đầu tiên**:
   Hàm `_truncate()` lấy câu đầu tiên của field `summary` (kết thúc bằng `. `) với tối đa 300 ký tự. Câu đầu tiên thường mang thông tin cô đọng nhất về đóng góp của bài báo, phù hợp làm ground truth cho factual QA.

5. **Một record có summary tiếng Nga**:
   Paper `10.47576/...` có `summary` song ngữ Nga-Anh. Ground truth được lấy từ phần tiếng Nga (câu đầu) vì đó là câu đầu tiên trong field. Điều này sẽ làm khó hơn cho RAG agent nhưng là dữ liệu thực tế từ Crossref API.
