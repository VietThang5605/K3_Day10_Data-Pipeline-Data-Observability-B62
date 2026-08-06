# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                                                                       |
| ------------------ | ------------------------------------------------------------------------------ |
| Họ và tên       | Kim Duy Hùng                                                                   |
| MSSV               | 01763                                                                          |
| Khóa/Lớp         | K3 / AI-B62                                                                    |
| Tên nhóm         | Nhóm 6 người (B62)                                                             |
| Vai trò chính    | Người 3: Evaluation và Test Set                                                |
| Repository         | [VietThang5605/K3_Day10_Data-Pipeline-Data-Observability-B62](https://github.com/VietThang5605/K3_Day10_Data-Pipeline-Data-Observability-B62) |
| Ngày hoàn thành | 2026-08-06                                                                     |

---

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| ------------------ | --------------------- | ---------------- | ----------------- | -------------------------------------------- |
| Evaluation Set Generator | [`src/evaluation/testset.py`](file:///e:/lab/K3_Day10_Data-Pipeline-Data-Observability-B62/src/evaluation/testset.py)<br>`build_test_set()` | Cleaned DataFrame từ [`data/clean/papers_clean.json`](file:///e:/lab/K3_Day10_Data-Pipeline-Data-Observability-B62/data/clean/papers_clean.json) | [`data/eval/test_set.json`](file:///e:/lab/K3_Day10_Data-Pipeline-Data-Observability-B62/data/eval/test_set.json) (bộ câu hỏi cố định) | Hoàn thành |
| Verification & Metrics Checking | [`src/evaluation/metrics.py`](file:///e:/lab/K3_Day10_Data-Pipeline-Data-Observability-B62/src/evaluation/metrics.py)<br>`evaluate_pipeline()`, `_token_f1()`, `_judge_answer()` | `test_set.json`, ChromaDB Vector Index | [`data/results/baseline_metrics.json`](file:///e:/lab/K3_Day10_Data-Pipeline-Data-Observability-B62/data/results/baseline_metrics.json), `baseline_answers.json` | Hoàn thành |
| Generator Scripts | [`script/generate_test_set.py`](file:///e:/lab/K3_Day10_Data-Pipeline-Data-Observability-B62/script/generate_test_set.py), [`script/generate_test_set_standalone.py`](file:///e:/lab/K3_Day10_Data-Pipeline-Data-Observability-B62/script/generate_test_set_standalone.py) | Settings, `papers_clean.json` | Script sinh test set tự động độc lập | Hoàn thành |
| Technical Module Report | [`evaluation_report.md`](file:///e:/lab/K3_Day10_Data-Pipeline-Data-Observability-B62/evaluation_report.md) | Quá trình triển khai & kết quả testset | Báo cáo chi tiết kỹ thuật C2 cho module Evaluation | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| ------------------------------------ | ------------------------------------ | ---------------------------- |
| Tích hợp luồng Đánh giá RAG End-to-End | Người 5 (`src/pipelines/phase1.py`) | Đảm bảo `evaluate_pipeline()` đọc đúng `test_set.json` và xuất kết quả metrics cho Pha 1 Baseline |
| Đánh giá tác động Data Corruption | Người 6 (`src/pipelines/corruption_flow.py`) | Xác minh bộ `test_set.json` hoạt động chính xác khi đánh giá so sánh trên cả 3 trạng thái Baseline, Corrupted và Repaired |

---

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --------------------------- | ----------------------------- | ------------------------- | ----------------------- |
| Lập trình module sinh test set | [`src/evaluation/testset.py`](file:///e:/lab/K3_Day10_Data-Pipeline-Data-Observability-B62/src/evaluation/testset.py) | Hàm `build_test_set` với logic sắp xếp ổn định, chọn mẫu phân tán và phân loại câu hỏi | `python script/generate_test_set.py` |
| Sinh bộ câu hỏi cố định (Frozen Evaluation Set) | [`data/eval/test_set.json`](file:///e:/lab/K3_Day10_Data-Pipeline-Data-Observability-B62/data/eval/test_set.json) | File JSON chứa các câu hỏi thuộc 4 loại (`summary`, `authors`, `date`, `categories`) với `ground_truth` và `ground_truth_doc_ids` chính xác | Kiểm tra cấu trúc file JSON và validate `ground_truth_doc_ids` |
| Kiểm tra module tính metrics và LLM Judge | [`src/evaluation/metrics.py`](file:///e:/lab/K3_Day10_Data-Pipeline-Data-Observability-B62/src/evaluation/metrics.py) | Đã kiểm tra tính toán Token F1, LLM Judge (1-5), và Retrieval Hit Rate | Chạy `evaluate_pipeline` trên Baseline, Corrupted, Repaired |
| Viết tài liệu báo cáo kỹ thuật C2 | [`evaluation_report.md`](file:///e:/lab/K3_Day10_Data-Pipeline-Data-Observability-B62/evaluation_report.md) | Báo cáo mô tả quy trình sinh test set, chuẩn schema và giải thích nguyên tắc Frozen Eval Set | Khởi tạo file trong repository |

**Output cụ thể do phần việc tạo ra:**
- [`data/eval/test_set.json`](file:///e:/lab/K3_Day10_Data-Pipeline-Data-Observability-B62/data/eval/test_set.json): Bộ câu hỏi cố định chuẩn mực gồm các câu hỏi thực tế được trích xuất trực tiếp từ cleaned data. Bộ test set này được đóng băng và sử dụng nhất quán xuyên suốt cho cả 3 lần đánh giá (Baseline, Corrupted, Repaired), đóng vai trò là thước đo trung lập duy nhất để chứng minh tác động của chất lượng dữ liệu lên hệ thống RAG.

---

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết
Trong một hệ thống RAG Data Pipeline, để đo lường xem dữ liệu bị lỗi (Corrupted Data) ảnh hưởng xấu như thế nào đến khả năng trả lời của Agent và việc sửa lỗi (Repair) có thực sự phục hồi được chất lượng hay không, hệ thống cần một **bộ câu hỏi đánh giá chuẩn và cố định (Frozen Evaluation Set)**. Bộ câu hỏi này phải đảm bảo:
1. Trích xuất từ dữ liệu sạch đáng tin cậy.
2. Bao phủ đa dạng các loại câu hỏi (nội dung bài báo, tác giả, ngày xuất bản, chủ đề).
3. Có `ground_truth` và `ground_truth_doc_ids` rõ ràng để tính toán metric chính xác.

### Cách triển khai
1. **Thuật toán sắp xếp & chọn mẫu (Deterministic Sampling):**
   - Sắp xếp cleaned DataFrame theo ngày xuất bản `published` (mới nhất trước) và `paper_id` để kết quả sinh ra là **hoàn toàn cố định (deterministic)** mỗi lần chạy.
   - Phân chia danh sách thành các khoảng đều nhau (đầu, 1/3, 2/3 danh sách) để chọn các bài báo đại diện cho từng nhóm câu hỏi, tránh thiên vị chủ đề hay thời gian.
2. **Sinh 4 loại câu hỏi chuẩn hóa:**
   - `summary`: *"What is the main contribution or topic of the paper titled ...?"* → Ground truth là câu đầu tiên của bản tóm tắt.
   - `authors`: *"Who are the authors of the paper titled ...?"* → Ground truth là danh sách tác giả ghép chuỗi (`authors_joined`).
   - `date`: *"When was the paper titled ... published?"* → Ground truth là ngày `published` (YYYY-MM-DD).
   - `categories`: *"What are the research topics or categories of the paper titled ...?"* → Ground truth là các chủ đề/thể loại (`categories_joined`).
3. **Mã hóa và kiểm tra:**
   - Ghi file JSON với mã hóa UTF-8 (`ensure_ascii=False`) để giữ nguyên văn bản Tiếng Anh và các ký tự đặc biệt nếu có.
   - Validate để đảm bảo 100% `ground_truth_doc_ids` tồn tại trong dataset gốc.

### Input, output và contract

| Thành phần | Mô tả |
| ------------------------------ | ------------------------------------------- |
| Input | Cleaned DataFrame (`papers_clean.json`) với các cột mandatory: `paper_id`, `title`, `summary`, `authors_joined`, `categories_joined`, `published` |
| Output | `data/eval/test_set.json` (List chứa các dict có `id`, `question_type`, `question`, `ground_truth`, `ground_truth_doc_ids`) |
| Module phụ thuộc | Module `src/ingestion/cleaning.py` (cung cấp cleaned DataFrame) |
| Module sử dụng output | Module `src/evaluation/metrics.py` (hàm `evaluate_pipeline`), `src/pipelines/phase1.py`, `src/pipelines/corruption_flow.py` |
| Điều kiện lỗi cần xử lý | - Số lượng document trong DF < 5 (`ValueError`).<br>- DataFrame thiếu các cột bắt buộc (`ValueError`).<br>- `ground_truth_doc_ids` không khớp với `paper_id` thực tế (Log warning). |

### Cách xác minh

```bash
python script/generate_test_set.py
```

- **Kết quả mong đợi:** Tự động đọc `data/clean/papers_clean.json`, tạo ra bộ câu hỏi chuẩn và ghi thành công vào `data/eval/test_set.json`.
- **Kết quả thực tế:** Log hiển thị `[INFO] evaluation.testset: Đã tạo câu hỏi và lưu vào data/eval/test_set.json`. 
- **Artifact/log:** [`data/eval/test_set.json`](file:///e:/lab/K3_Day10_Data-Pipeline-Data-Observability-B62/data/eval/test_set.json).

---

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Cần quyết định cách thức khởi tạo bộ câu hỏi đánh giá RAG: Sinh bộ câu hỏi động (Dynamic Evaluation) mỗi lần chạy pipeline hay Tạo bộ câu hỏi cố định và đóng băng (Frozen Evaluation Set) từ dữ liệu sạch Baseline?
- **Các phương án đã cân nhắc:**
  1. *Phương án A (Dynamic Set):* Sinh câu hỏi mới ngẫu nhiên mỗi lần chạy pipeline trên dataset hiện tại.
  2. *Phương án B (Frozen Evaluation Set - Đã chọn):* Sinh bộ câu hỏi 1 lần duy nhất từ Cleaned Baseline Data, đóng băng và lưu cố định vào `data/eval/test_set.json` để dùng chung cho cả 3 pha (Baseline, Corrupted, Repaired).
- **Phương án đã chọn:** Phương án B — Frozen Evaluation Set.
- **Lý do:**
  - **Tính so sánh công bằng (Apples-to-Apples):** Đảm bảo cả 3 trạng thái hệ thống được đánh giá trên *cùng một thước đo*. Nếu mỗi pha dùng câu hỏi khác nhau, sự suy giảm metric ở pha Corrupted có thể do câu hỏi khó hơn chứ không phải do dữ liệu lỗi.
  - **Tính tái lặp (Reproducibility):** Cho phép mọi thành viên và giảng viên kiểm tra độc lập kết quả với độ ổn định 100%.
  - **Đo lường chính xác tác động của Data Corruption:** Khi một document bị xóa hoặc làm nhiễu ở pha Corrupted, câu hỏi tương ứng trong test set sẽ bị trượt Retrieval (`retrieval_hit=False`), làm giảm `retrieval_hit_rate` một cách phản ánh đúng thực tế.
- **Bằng chứng quyết định phù hợp:** Kết quả so sánh trên 3 pha: `retrieval_hit_rate` sụt giảm từ **1.0 (Baseline)** xuống **0.9 (Corrupted)** và phục hồi về **1.0 (Repaired)** nhờ sử dụng chung một `test_set.json`.

---

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:**
  1. Lỗi mã hóa ký tự trong JSON: Ký tự Unicode bị mã hóa thành dạng hex `\u0421\u043d...` gây khó đọc.
  2. Lỗi ModuleNotFoundError khi chạy script độc lập: `ModuleNotFoundError: No module named 'langchain_ollama'` và `No module named 'datasets'` khi `testset.py` import gián tiếp qua `evaluation.__init__`.
- **Lệnh hoặc bước tái hiện:**
  ```bash
  python script/generate_test_set.py
  ```
- **Nguyên nhân gốc:**
  - Lỗi 1: Hàm `json.dumps()` mặc định sử dụng `ensure_ascii=True`, tự động escape các ký tự Unicode.
  - Lỗi 2: File `src/evaluation/__init__.py` import `metrics.py`, mà `metrics.py` lại kéo theo các thư viện RAG nặng như `datasets`, `ragas`, `langchain_ollama`. Khi môi trường chưa cài đủ các provider này, script bị dừng.
- **Cách xử lý:**
  - Lỗi 1: Thêm `ensure_ascii=False` và mở file ghi với `encoding="utf-8"`.
  - Lỗi 2: Cài đặt đầy đủ các dependency thiếu (`pip install langchain-ollama langchain-anthropic datasets`), đồng thời tạo script `script/generate_test_set_standalone.py` độc lập không phụ thuộc vào `metrics.py` để sinh test set nhanh khi cần.
- **Cách xác minh sau khi sửa:**
  Chạy lại `python script/generate_test_set.py`, file `data/eval/test_set.json` xuất ra văn bản tiếng Anh thuần túy, đọc được rõ ràng và script chạy hoàn toàn không còn lỗi.
- **Điều học được:** Khi viết module utility hoặc generator, nên tách biệt phần data generation thuần túy khỏi các module chứa heavy dependencies (như LLM/RAG evaluators) để tránh lỗi import dây chuyền.

---

## 7. Hiểu biết về luồng end-to-end

**Câu trả lời:**

1. **Luồng dữ liệu từ Crossref đến Vector Index:**
   - Dữ liệu thô (raw HTTP JSON) được thu thập từ Crossref REST API qua `src/ingestion/crossref.py`, lưu trữ tại `data/raw/crossref_response.json` và `crossref_records.json`.
   - Dữ liệu thô chuyển qua `src/ingestion/cleaning.py` để làm sạch HTML/JATS XML, chuẩn hóa ngày tháng, suy luận danh mục (`primary_category`), tính `age_days` và tạo văn bản đại diện `text_for_embedding`. Kết quả xuất ra `data/clean/papers_clean.csv` và `papers_clean.json`.
   - Cột `text_for_embedding` được đưa vào `src/retrieval/index.py`, sử dụng mô hình embedding `sentence-transformers/all-MiniLM-L6-v2` để biến đổi thành vector 384 chiều, lưu trữ vào cơ sở dữ liệu vector ChromaDB (`data/chroma/`) kèm theo metadata (`paper_id`, `title`, `published`,...).

2. **Vai trò của Evaluation Set và ground-truth document IDs:**
   - Evaluation Set (`test_set.json`) chứa các câu hỏi thử nghiệm và `ground_truth` (câu trả lời mẫu chuẩn).
   - `ground_truth_doc_ids` chứa danh sách ID bài báo chính xác chứa câu trả lời.
   - Khi Agent chạy query, hệ thống so sánh danh sách `retrieved_doc_ids` từ Vector Database với `ground_truth_doc_ids`. Nếu có ít nhất 1 ID trùng khớp, `retrieval_hit` = True. Điều này giúp tính toán chính xác `retrieval_hit_rate` độc lập với chất lượng sinh văn bản của LLM.

3. **Phân biệt Quality Checks và Freshness Monitoring:**
   - **Quality Checks** (`quality.py`): Kiểm tra tính toàn vẹn và cấu trúc dữ liệu tĩnh (Data Contract) như: số lượng dòng, kiểm tra `paper_id` not null & unique, tiêu đề không rỗng, độ dài tóm tắt tối thiểu, định dạng schema.
   - **Freshness Monitoring** (`quality.py`): Kiểm tra tính mới của dữ liệu theo thời gian thực (Data Drift/Staleness) bằng cách so sánh ngày xuất bản `published` với ngày chạy pipeline (`run_date`). Nếu `age_days` > 180 ngày (ngưỡng threshold), dữ liệu bị coi là bị cũ (Stale).

4. **Lý do phải dùng cùng 1 test set cho cả 3 pha (Baseline, Corrupted, Repaired):**
   - Giữ nguyên bộ test set giúp biến bộ câu hỏi thành một **hằng số (constant)**.
   - Nhờ đó, bất kỳ sự thay đổi nào về chỉ số (`retrieval_hit_rate`, `mean_token_f1`, `judge_accuracy`) giữa các pha đều phản ánh **100% nguyên nhân từ chất lượng dữ liệu** (Data Quality), chứ không phải do sự thay đổi độ khó của câu hỏi.

5. **Tiêu chí đánh giá Repair thành công:**
   - Repair được xem là thành công khi các chỉ số khôi phục về xấp xỉ hoặc bằng mức Baseline:
     - `retrieval_hit_rate` phục hồi từ 0.9 lên 1.0.
     - `judge_accuracy` phục hồi từ 0.7 lên 0.9.
     - `mean_judge_score` phục hồi từ 3.7/5.0 lên 4.5/5.0.
     - Trạng thái Quality checks chuyển từ `FAILED` về `PASSED`.
     - Trạng thái Freshness chuyển từ `Stale` về `Fresh`.

---

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| ---------------------- | -------: | --------: | -------: | ------------------------- |
| `retrieval_hit_rate` | **1.00 (100%)** | **0.90 (90%)** | **1.00 (100%)** | Đồ thị sụt giảm ở pha Corrupted do một số bài báo bị drop/lỗi làm Vector Index không tìm thấy, và phục hồi hoàn toàn sau Repair. |
| `mean_token_f1` | **0.582** | **0.460** | **0.579** | Token F1 giảm mạnh ở pha Corrupted do summary bị làm nhiễu/xóa, làm câu trả lời của LLM lệch khỏi ground truth. Sau Repair chỉ số phục hồi về ~0.58. |
| `judge_accuracy` | **0.90 (90%)** | **0.70 (70%)** | **0.90 (90%)** | LLM Judge đánh giá độ chính xác giảm từ 90% xuống 70% khi dữ liệu bị lỗi, và tăng trở lại 90% khi dữ liệu được sửa. |
| `mean_judge_score` | **4.50 / 5.0** | **3.70 / 5.0** | **4.50 / 5.0** | Điểm số chất lượng câu trả lời bị tụt 0.8 điểm do dữ liệu nhiễu/thiếu thông tin, phục hồi lại mức 4.5/5.0 sau khi repair từ raw records. |
| Quality checks | **PASSED** | **FAILED** | **PASSED** | Quality checks phát hiện thành công các lỗi mất summary, title bị truncate và trùng lặp dòng ở pha Corrupted. |
| Freshness status | **Fresh** | **Stale** | **Fresh** | Hệ thống cảnh báo dữ liệu bị cũ khi corruption cố tình lùi ngày xuất bản > 180 ngày và báo Fresh trở lại sau repair. |

### Kết luận từ số liệu

1. **[Data corruption] → [quality/freshness signal thay đổi] → [agent metric thay đổi]:**
   Khi corruption loại bỏ bản tóm tắt (summary) và làm nhiễu tiêu đề → Quality checks báo `FAILED` → `retrieval_hit_rate` giảm từ 100% xuống 90%, `judge_accuracy` tụt từ 90% xuống 70%, và `mean_judge_score` giảm từ 4.5 xuống 3.7.

2. **[Repair action] → [quality/freshness signal phục hồi] → [agent metric phục hồi]:**
   Khi tiến hành Repair khôi phục dữ liệu từ `data/raw/crossref_records.json` → Quality checks báo `PASSED` trở lại → `retrieval_hit_rate` khôi phục về 100%, `judge_accuracy` đạt lại 90%, điểm judge trung bình trở lại mức 4.5/5.0.

**Corruption nào ảnh hưởng rõ nhất và vì sao?**
- Lỗi **xóa rỗng summary (Blank Summary)** và **Truncate Title** ảnh hưởng rõ nhất. Nguyên nhân do `text_for_embedding` phụ thuộc trực tiếp vào Title và Summary. Khi 2 trường này bị rỗng hoặc mất từ khóa, vector embedding bị lệch hoàn toàn trong không gian vector của ChromaDB, dẫn đến việc Vector Search trả về sai document context cho LLM.

**Kết quả nào khác với kỳ vọng ban đầu?**
- `mean_token_f1` ở mức Baseline chỉ đạt ~0.582 (dù `judge_accuracy` đạt 90% và điểm judge là 4.5/5.0). 
- *Giải thích:* Token F1 so sánh chính xác từng từ (exact word overlap) giữa câu trả lời sinh bởi LLM và ground truth. Do LLM sinh câu trả lời tự nhiên theo văn phong diễn đạt dài hơn ground truth trích đoạn, Token F1 bị phạt thấp hơn dù câu trả lời hoàn toàn đúng về mặt ngữ nghĩa (vốn được LLM Judge đánh giá đúng 90%).

---

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. **Về Data Pipeline:** Thấu hiểu tầm quan trọng của nguyên tắc *Immutable Raw Data*. Lưu trữ nguyên bản `raw_response.json` và `raw_records.json` là điều kiện tiên quyết để hệ thống có thể thực hiện cơ chế Data Repair khôi phục pipeline khi data bị hỏng ở các tầng sau.
2. **Về Data Quality/Observability:** Data Quality checks và Freshness monitoring hoạt động như hệ thống cảnh báo sớm (Early Warning System). Phát hiện dữ liệu lỗi ngay ở tầng lưu trữ giúp ngăn chặn việc đưa ngữ cảnh sai vào LLM, tránh gây ra lỗi nhầm lẫn (Hallucination) cho người dùng cuối.
3. **Về ảnh hưởng của Data đến RAG Agent:** "Garbage in, Garbage out". Chất lượng của RAG Agent phụ thuộc trực tiếp 100% vào chất lượng dữ liệu đầu vào. Dữ liệu lỗi làm suy giảm cả khả năng Tìm kiếm (Retrieval Hit Rate) lẫn khả năng Sinh câu trả lời (Generation Quality).

### Nếu có thêm thời gian

- **Cải thiện:** Tích hợp bộ thư viện **Ragas** đầy đủ (`RUN_RAGAS=1`) để tính toán thêm các chỉ số chuyên sâu như *Faithfulness*, *Answer Relevance*, *Context Recall*, và *Context Precision*.
- **Lý do:** Ragas đánh giá sâu hơn về mối quan hệ giữa Context retrieved và Answer của LLM.
- **Cách đo cải thiện:** So sánh bảng điểm Ragas giữa 3 pha Baseline, Corrupted và Repaired để xem chỉ số *Faithfulness* sụt giảm ra sao khi dữ liệu bị nhiễu.

---

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Kim Duy Hùng  
**Ngày xác nhận:** 2026-08-06
