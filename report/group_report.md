# Group Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin bài nộp

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Khóa/Lớp         | K3 / AI-B62               |
| Tên nhóm         | Nhóm 6 người (B62)        |
| Repository         | [VietThang5605/K3_Day10_Data-Pipeline-Data-Observability-B62](https://github.com/VietThang5605/K3_Day10_Data-Pipeline-Data-Observability-B62) |
| Ngày hoàn thành | 2026-08-06                |

### Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò chính | Module/deliverable sở hữu |
| --: | --- | --- | --- | --- |
| 1 | Nguyễn Việt Thắng | 2A202601321 | Ingestion từ Crossref | `src/ingestion/crossref.py`, `data/raw/crossref_response.json`, `data/raw/crossref_records.json` |
| 2 | Nguyễn Đức Thiện | 2A2026014015 | Cleaning và data modeling | `src/ingestion/cleaning.py`, `data/clean/papers_clean.csv`, `data/clean/papers_clean.json` |
| 3 | Kim Duy Hưng | 01763 | Evaluation và test set | `src/evaluation/testset.py`, `src/evaluation/metrics.py`, `data/eval/test_set.json` |
| 4 | Lê Hồng Đức | 2A202601313 | Data observability | `src/observability/quality.py`, `src/observability/reporting.py`, `data/quality/*` |
| 5 | Vũ Minh Đức | 22022587 | Retrieval và baseline pipeline | `src/pipelines/phase1.py`, `src/retrieval/qa.py`, `data/results/baseline_metrics.json` |
| 6 | Nguyễn Hữu Kiên | 2A202601033 | Corruption, repair và comparison | `src/ingestion/corruption.py`, `src/pipelines/corruption_flow.py`, `corruption_report.md` |

## 2. Tóm tắt kết quả

Nhóm đã xây dựng hoàn chỉnh hệ thống Data Pipeline & Data Observability cho RAG Agent theo chuẩn 2 pha end-to-end. 

Ở Phase 1 (Baseline Pipeline), hệ thống thu thập 24 bản ghi thô từ Crossref REST API qua cơ chế exponential backoff, lưu snapshot bất biến `crossref_records.json`. Tầng Cleaning chuẩn hóa XML, lọc 1 bản ghi tiếng Nga non-Latin và suy luận danh mục, thu được 23 bản ghi sạch. Tập dữ liệu này được index vào ChromaDB qua model `all-MiniLM-L6-v2` và đánh giá bằng bộ câu hỏi đóng băng (`test_set.json`, 10 mẫu). Kết quả Baseline đạt *Retrieval Hit Rate* 100.0%, *LLM Judge Accuracy* 90.0%, *Mean Judge Score* 4.5/5.0 và *Mean Token F1* 0.5824, với 8/8 Data Quality checks PASSED và trạng thái Freshness FRESH (0 stale row).

Ở Phase 2 (Controlled Corruption & Repair Flow), 4 kịch bản gây lỗi (Blank Summary, Semantic Poisoning nông nghiệp/ẩm thực cổ đại, Stale Date năm 2000, Duplicates & Missing ID) được tiêm vào pipeline. Corruption khiến *Retrieval Hit Rate* sụt giảm xuống 90.0%, *Judge Accuracy* còn 70.0%, *Mean Judge Score* tụt xuống 3.7/5.0 và vi phạm 3/8 kiểm tra Observability (Duplicate ID, Short Summary, 5 Stale Rows).

Thông qua quy trình Data Repair tự động tái thiết lập từ Raw Snapshot cục bộ (`crossref_records.json`), toàn bộ các tín hiệu Data Quality & Freshness khôi phục về PASSED/FRESH, đồng thời các chỉ số RAG Agent được phục hồi hoàn hảo về mức Baseline (*Hit Rate* 100.0%, *Judge Accuracy* 90.0%, *Judge Score* 4.5/5.0, *Token F1* 0.5793).

Blocker chính đã xử lý gồm lỗi ô nhiễm collection ChromaDB giữa các pha (giải quyết bằng cô lập collection và clean slate directory) và xử lý quy tắc intent retrieval QA bị nhận nhầm summary thành categories.

## 3. Kiến trúc và luồng dữ liệu

### Luồng end-to-end

```text
Crossref API (REST /works endpoint)
    ├──> raw response (crossref_response.json) & raw records (crossref_records.json) [Người 1]
    ├──> cleaning & data modeling (filtering non-Latin, inferring categories, text_for_embedding) [Người 2]
    ├──> embedding (all-MiniLM-L6-v2) + ChromaDB index (papers-baseline) [Người 5]
    ├──> evaluation baseline (frozen test_set.json) [Người 3]
    ├──> data quality & freshness reports (baseline_quality.json, freshness_report.json) [Người 4]
    ├──> controlled corruption (blank summary, semantic poisoning, stale dates, duplicates) [Người 6]
    ├──> re-index (papers-corrupted) & re-evaluate corrupted state [Người 6]
    ├──> data repair từ Immutable Raw Snapshot (crossref_records.json) [Người 6]
    └──> re-index (papers-repaired), re-evaluate & output comparison report (corruption_report.md) [Người 6]
```

### Trách nhiệm của từng khối

| Khối             | Input          | Xử lý chính             | Output/artifact          | Owner          |
| ----------------- | -------------- | -------------------------- | ------------------------ | -------------- |
| Ingestion         | Crossref REST API (`/works`) | Fetch HTTP, retry backoff 1-16s, parse `PaperRecord` | `data/raw/crossref_response.json`, `data/raw/crossref_records.json` | Nguyễn Việt Thắng |
| Cleaning          | `list[PaperRecord]` | Gỡ HTML/JATS XML, lọc non-Latin, suy luận category, tính `age_days` | `data/clean/papers_clean.csv`, `data/clean/papers_clean.json` | Nguyễn Đức Thiện |
| Embedding/index   | Cleaned DataFrame | MiniLM 384-d embeddings, ChromaDB collection `papers-baseline` | `data/embeddings/papers_embeddings.json`, `data/chroma/` | Vũ Minh Đức |
| Evaluation        | Cleaned DF & Chroma Index | Sinh bộ câu hỏi đóng băng `test_set.json`, tính Token F1, LLM Judge | `data/eval/test_set.json`, `data/results/baseline_metrics.json` | Kim Duy Hưng |
| Observability     | Clean/Corrupted DF | 8 Quality checks (volume, schema, null, unique, summary len) & Freshness | `data/quality/baseline_quality_report.json`, `freshness_report.json` | Lê Hồng Đức |
| Corruption/repair | Clean DF & Raw Snapshot | Tiêm 4 kịch bản lỗi; Repair từ raw snapshot; Re-index & Re-evaluate | `data/results/corruption_log.json`, `corrupted_metrics.json`, `repaired_metrics.json` | Nguyễn Hữu Kiên |
| Orchestration     | Toàn bộ modules | Điều phối Phase 1 baseline flow & Phase 2 corruption flow end-to-end | `script/run_phase1.py`, `script/run_corruption_flow.py`, `corruption_report.md` | Vũ Minh Đức & Nguyễn Hữu Kiên |

## 4. Cách tái hiện kết quả

### Cấu hình không chứa secret

| Biến/cấu hình             | Giá trị sử dụng |
| ---------------------------- | ------------------- |
| `LLM_PROVIDER`             | `openai` (hoặc mock/judge provider tương đương) |
| `LLM_MODEL`                | `gpt-4o-mini` |
| Embedding model              | `sentence-transformers/all-MiniLM-L6-v2` |
| Số lượng Crossref records | 24 raw records / 23 clean records |
| Retrieval `top_k`           | 4 |
| Freshness threshold          | 180 days |
| Frozen Test Set Seed / Samples | 10 samples (`data/eval/test_set.json`) |

### Lệnh cài đặt

Sử dụng `uv` (khuyến nghị):

```bash
uv sync
```

Hoặc với môi trường `pip`:

```bash
python -m pip install -e .
```

### Lệnh chạy

#### 1. Khởi chạy Pipelines CLI (Xử lý dữ liệu & Đánh giá)

Baseline pipeline (Phase 1):

```bash
uv run python script/run_phase1.py
```

Corruption flow & Repair (Phase 2):

```bash
uv run python script/run_corruption_flow.py
```

#### 2. Khởi chạy Hệ sinh thái UI Dashboard & Backend API

**Khởi chạy đồng thời cả Backend và UI bằng runner duy nhất (Khuyên dùng):**

```bash
uv run python script/run_ui.py
```

Hoặc với môi trường `pip`:

```bash
python script/run_ui.py
```

Lệnh trên sẽ khởi chạy song song 2 dịch vụ:
- **Backend API & Web Observability Dashboard (FastAPI)** tại `http://localhost:8000`
- **Streamlit RAG Chatbot Test Sandbox** tại `http://localhost:8501`

**Khởi chạy riêng biệt từng dịch vụ (nếu cần debug thủ công):**

- **Backend API (FastAPI Server)** — Quản lý REST Endpoints và Web Observability Dashboard:
  ```bash
  uv run python -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload
  ```
  *Truy cập:* `http://localhost:8000` (TailwindCSS Dark Mode Dashboard cho Data Observability & Health Signals).

- **Frontend UI (Streamlit Chatbot Sandbox)** — Giao diện thử nghiệm tương tác RAG Chatbot:
  ```bash
  uv run streamlit run app.py
  ```
  *Truy cập:* `http://localhost:8501` (RAG Chatbot Sandbox thử nghiệm câu hỏi ở 3 chế độ Baseline/Corrupted/Repaired và so sánh 3 cột song song).

### Kết quả tái hiện

| Lệnh / Dịch vụ             | Trạng thái                                    | Thời điểm chạy gần nhất | Bằng chứng / Địa chỉ truy cập                       |
| ----------------- | ----------------------------------------------- | ----------------------------- | ------------------------------------ |
| Baseline pipeline | Thành công 100% | 2026-08-06T05:02:48+00:00 | `data/results/baseline_metrics.json`, `data/quality/baseline_quality_report.json` |
| Corruption flow   | Thành công 100% | 2026-08-06T05:22:02+00:00 | `data/results/corrupted_metrics.json`, `data/results/repaired_metrics.json`, `corruption_report.md` |
| Backend API & Web Dashboard | Thành công 100% | 2026-08-06 | `http://localhost:8000` (`src/server.py`, `src/web/index.html`) |
| Streamlit Chatbot Sandbox | Thành công 100% | 2026-08-06 | `http://localhost:8501` (`app.py`, `.streamlit/config.toml`) |

## 5. Ingestion, cleaning và data contract

### Nguồn dữ liệu

| Thuộc tính                | Giá trị                             |
| --------------------------- | ------------------------------------- |
| Source                      | Crossref REST API endpoint `/works` |
| Query/filter                | `agentic retrieval augmented generation large language model` |
| Thời điểm lấy dữ liệu | 2026-08-06 |
| Số record nhận được    | 24 raw records |
| Cơ chế retry/backoff      | Timeout 30s, Polite Pool User-Agent (`mailto`), Exponential backoff 1, 2, 4, 8, 16s cho HTTP 429/503 |

### Raw và clean schema

| Trường        | Kiểu dữ liệu | Bắt buộc?  | Ý nghĩa   | Xử lý khi thiếu/sai |
| --------------- | --------------- | ------------ | ----------- | ---------------------- |
| `paper_id` | `str` | Có | DOI duy nhất của bài báo làm khóa chính | Loại bỏ record nếu thiếu DOI |
| `title` | `str` | Có | Tiêu đề bài báo học thuật | Lấy title đầu tiên; loại nếu rỗng |
| `summary` | `str` | Có | Bản tóm tắt (abstract/description) | Ưu tiên `abstract`, gỡ JATS XML; loại nếu rỗng |
| `authors` | `list[str]` | Không | Danh sách tên tác giả | Ghép `given` + `family`; fallback danh sách rỗng |
| `categories` | `list[str]` | Không | Các chủ đề/thể loại học thuật | Lấy `subject`; suy luận từ keyword nếu rỗng |
| `published` | `str` | Có | Ngày xuất bản | Parse `date-parts` về `YYYY-MM-DD`; loại nếu sai |
| `age_days` | `int` | Có | Tuổi của bài báo tính theo ngày chạy | Tính từ `run_date - published` |
| `text_for_embedding` | `str` | Có | Chuỗi tổng hợp phục vụ sinh vector embedding | Ghép Title + Summary + Authors + Categories + Published |

### Quy tắc cleaning

| Quy tắc                                 | Quality dimension liên quan | Số record bị tác động | Cách xác minh      |
| ---------------------------------------- | ---------------------------- | -------------------------: | -------------------- |
| Lọc bản ghi thiếu DOI, Title hoặc Summary | Completeness | 0 record | `parse_crossref_payload` |
| Gỡ HTML/JATS XML tag và decode entity | Validity / Cleanliness | 24 records | So sánh `summary` raw và clean |
| Lọc bài báo chứa từ 5 ký tự non-Latin trở lên | Validity / Language Control | 1 record (drop bài tiếng Nga) | Clean CSV có 23 dòng (từ 24 raw) |
| Suy luận category từ keyword trong Title/Summary | Completeness | 5 records | Cột `categories_joined` không rỗng |
| Loại bỏ duplicate `paper_id` | Uniqueness | 0 record | `paper_id_unique` check pass |

**Giải thích cách tạo `text_for_embedding`, document ID và `age_days`:**
- **`paper_id`**: Lấy trực tiếp từ DOI nguyên bản của bài báo trên Crossref (ví dụ `10.1111/exsy.70341`), đảm bảo tính nhất quán tuyệt đối giữa các tầng.
- **`text_for_embedding`**: Đội ngũ thiết kế chuỗi định dạng: `Title: {title} | Summary: {summary} | Authors: {authors_joined} | Categories: {categories_joined} | Published: {published}`. Việc bổ sung metadata tác giả và danh mục giúp không gian vector ghi nhận đầy đủ bối cảnh ngữ nghĩa.
- **`age_days`**: Được tính toán theo công thức `(run_date - published_date).days`. Sử dụng `run_date` cố định thay vì `datetime.now()` giúp tính toán mang tính deterministic khi tái thiết lập pipeline.

## 6. Evaluation setup

| Thành phần                             | Cấu hình thực tế          |
| ---------------------------------------- | ----------------------------- |
| Số câu hỏi                            | 10 mẫu (Frozen Test Set) |
| Các `question_type`                    | `summary`, `authors`, `date`, `categories` |
| Ground-truth document ID                 | Trích xuất trực tiếp từ DOI bài báo gốc tương ứng |
| Embedding model                          | `sentence-transformers/all-MiniLM-L6-v2` (384 Dimensions) |
| Vector store/collection                  | ChromaDB persistent client (`papers-baseline`, `papers-corrupted`, `papers-repaired`) |
| Retrieval `top_k`                       | 4 |
| LLM provider/model                       | OpenAI `gpt-4o-mini` |
| Test set dùng chung cho ba trạng thái | `data/eval/test_set.json` |

**Giải thích vì sao test set được giữ nguyên khi đánh giá baseline, corrupted và repaired:**
Test set đóng vai trò là **hằng số sinh học (control variable)** trong thực nghiệm khoa học. Việc đóng băng và dùng chung một `test_set.json` duy nhất xuyên suốt 3 pha đảm bảo nguyên tắc so sánh đồng nhất ("Apples-to-Apples"). Mọi sự biến động về chỉ số (*Retrieval Hit Rate*, *Token F1*, *Judge Score*) giữa các pha hoàn toàn phản ánh **chất lượng dữ liệu và vector index**, chứ không phải do sự thay đổi độ khó hay chủ đề của câu hỏi.

## 7. Kết quả baseline

### Artifact checklist

| Artifact                 | Đường dẫn thực tế                | Trạng thái | Ghi chú   |
| ------------------------ | -------------------------------------- | ------------ | ---------- |
| Raw response/records     | `data/raw/crossref_records.json` | Có | 24 raw records (232 KB payload gốc) |
| Cleaned dataset          | `data/clean/papers_clean.json` | Có | 23 clean records hợp lệ |
| Embedding manifest/index | `data/embeddings/papers_embeddings.json` | Có | 23 vectors 384 dimensions trong ChromaDB |
| Evaluation set           | `data/eval/test_set.json` | Có | 10 frozen evaluation samples |
| Baseline metrics         | `data/results/baseline_metrics.json` | Có | Ghi nhận Hit Rate 1.0, Judge Accuracy 0.9 |
| Quality/freshness        | `data/quality/baseline_quality_report.json` | Có | 8/8 Quality checks PASSED, 0 stale |
| Baseline report          | `data/reports/phase1_report.md` | Có | Báo cáo chi tiết Phase 1 |

### Baseline metrics

| Metric                 |       Giá trị | Diễn giải                             |
| ---------------------- | --------------: | --------------------------------------- |
| `retrieval_hit_rate` |     `1.0000` (100%) | Top-4 retrieval luôn chứa đúng ground-truth document ID |
| `mean_token_f1`      |     `0.5824` | Trùng khớp từ vựng giữa câu trả lời LLM và ground truth |
| `judge_accuracy`     |     `0.9000` (90%) | LLM Judge đánh giá 9/10 câu trả lời chính xác về mặt ngữ nghĩa |
| `mean_judge_score`   |     `4.50 / 5.0` | Điểm chất lượng câu trả lời trung bình rất cao |
| Ragas                | `Skipped` | Yêu cầu `RUN_RAGAS=1`; không chạy ở pass mặc định để tối ưu tốc độ |

## 8. Data quality và freshness

### Quality checks

| Check        | Quality dimension | Ngưỡng/kỳ vọng | Kết quả baseline      | Bằng chứng |
| ------------ | ----------------- | ------------------ | ----------------------- | ------------ |
| `minimum_row_count` | Volume | Row count $\ge 4$ | PASSED (24 rows) | `baseline_quality_report.json` |
| `required_columns` | Schema | Có đủ 5 cột bắt buộc | PASSED (Full columns) | `baseline_quality_report.json` |
| `paper_id_not_null` | Completeness | 0 blank ID | PASSED (0 blank) | `baseline_quality_report.json` |
| `paper_id_unique` | Uniqueness | 0 duplicate ID | PASSED (0 duplicates) | `baseline_quality_report.json` |
| `title_not_blank` | Completeness | 0 blank title | PASSED (0 blank) | `baseline_quality_report.json` |
| `summary_length` | Validity | Summary len $\ge 30$ chars | PASSED (0 short/blank) | `baseline_quality_report.json` |
| `published_date_valid` | Validity | Parseable YYYY-MM-DD | PASSED (0 invalid) | `baseline_quality_report.json` |
| `freshness` | Temporal Quality | Age $\le 180$ days | PASSED (0 stale rows) | `baseline_quality_report.json` |

### Freshness

| Thuộc tính               | Giá trị                           |
| -------------------------- | ----------------------------------- |
| Freshness được đo tại | Cleaned DataFrame (`papers_clean.json`) |
| Timestamp mới nhất       | `published` từ bài báo mới nhất trong tập dữ liệu |
| Ngưỡng freshness         | 180 ngày |
| Trạng thái baseline      | **FRESH** |
| Lý do                     | 24/24 bản ghi có `age_days` $\le 180$ ngày, 0 stale row |

## 9. Corruption scenarios và repair

| Corruption         | Cách tạo | Record bị tác động | Quality signal kỳ vọng | Tác động thực tế | Cách repair   |
| ------------------ | ---------- | ---------------------: | ------------------------ | --------------------- | -------------- |
| **Blank Summary** | Xóa rỗng summary bài Hi-RAG (`10.1111/exsy.70341`) | 1 record | `summary_length` check FAILED | Embedding mất ngữ cảnh; Retrieval bỏ sót document | Rebuild từ Raw Snapshot |
| **Semantic Poisoning** | Thay summary bài CM-RAF & JADE-Plus bằng văn bản ẩm thực/nông nghiệp | 2 records | Semantic drift | ChromaDB tìm sai bài báo; LLM trả lời sai/hallucinate | Rebuild từ Raw Snapshot |
| **Stale Date Injection** | Đổi ngày `published` của 5 bài báo về năm `2000-01-01` (`age > 9500` ngày) | 5 records | Freshness check FAILED (5 stale) | Tín hiệu Freshness báo 🔴 STALE DATA | Re-parse date từ Raw Snapshot |
| **Duplicates & Missing ID** | Nhân đôi 2 dòng và xóa `paper_id` của 1 dòng | 2 records | `paper_id_unique` FAILED | Vi phạm Data Contract; tổng số row tăng lên 25 | Re-apply unique filter từ Raw Snapshot |

**Corruption log:**
- Đường dẫn: `data/results/corruption_log.json`
- Trạng thái: **Có đầy đủ**
- Nhận xét: File log mô tả chính xác 4 kịch bản, ghi rõ DOI bài báo bị tác động, danh sách câu hỏi ảnh hưởng và lý do cơ học sụt giảm chỉ số.

**Giải thích cách repair đảm bảo dữ liệu được phục hồi từ nguồn đáng tin cậy:**
Hệ thống Repair không sử dụng các phương pháp "vá víu" bề mặt (như điền giá trị mặc định hoặc xóa thủ công các dòng lỗi trên cleaned dataset). Thay vào đó, Repair thực thi cơ chế **Single Source of Truth**: nạp lại nguyên bản file Raw Snapshot thô (`data/raw/crossref_records.json`), sau đó chạy lại toàn bộ quy tắc Cleaning đã qua kiểm định (`build_clean_dataframe()`). Quy trình này tự động làm sạch XML, tự động lọc bài tiếng Nga, chuẩn hóa ngày tháng và tái cấu trúc vector index từ đầu. Điều này bảo đảm tính bất biến (immutability) và khả năng tái lập 100% (reproducibility).

## 10. So sánh baseline, corrupted và repaired

| Metric/signal            | Baseline | Corrupted | Repaired | Thay đổi do corruption | Mức phục hồi | Nhận xét   |
| ------------------------ | -------: | --------: | -------: | -----------------------: | --------------: | ------------ |
| `retrieval_hit_rate`   | **1.0000** | 🔻 **0.9000** | 🟢 **1.0000** | -10.0% | **100%** | Corrupted làm rớt Hit Rate do trôi ngữ nghĩa; Repair phục hồi hoàn toàn |
| `mean_token_f1`        | **0.5824** | 🔻 **0.4599** | 🟢 **0.5793** | -0.1225 | **99.5%** | F1 sụt mạnh khi thiếu context; Repair đưa về mức ~0.58 chuẩn |
| `judge_accuracy`       | **0.9000** | 🔻 **0.7000** | 🟢 **0.9000** | -20.0% | **100%** | Agent trả lời sai 3 câu ở pha corrupted; Repair giúp 9/10 câu đúng |
| `mean_judge_score`     | **4.5000** | 🔻 **3.7000** | 🟢 **4.5000** | -0.8000 | **100%** | Điểm Judge khôi phục lại mốc 4.5/5.0 tối ưu |
| Quality checks pass/fail | 🟢 **PASSED** | 🔴 **FAILED** | 🟢 **PASSED** | Fail 3 checks | **100%** | Corrupted vi phạm uniqueness, summary len; Repair đạt 8/8 checks |
| Freshness status         | 🟢 **PASS (0)** | 🔴 **FAIL (5)** | 🟢 **PASS (0)** | 5 stale rows | **100%** | Corrupted phát hiện 5 bài năm 2000; Repair sạch 100% stale |

**Hai kết luận có quan hệ nhân quả:**

1. **[Data Corruption] $\rightarrow$ [Quality/Freshness Signal] $\rightarrow$ [Agent Metrics]**:
   Khi kịch bản Blank Summary và Semantic Poisoning được tiêm vào dữ liệu $\rightarrow$ Quality check `summary_length` báo FAILED và Freshness check báo 5 stale rows $\rightarrow$ Vector embedding của bài báo Hi-RAG và CM-RAF bị trôi khỏi không gian ngữ nghĩa, làm *Retrieval Hit Rate* giảm từ 100% xuống 90%, *LLM Judge Accuracy* tụt từ 90% xuống 70% và *Mean Judge Score* giảm từ 4.5 xuống 3.7.

2. **[Data Repair Action] $\rightarrow$ [Quality/Freshness Recovery] $\rightarrow$ [Agent Metric Recovery]**:
   Khi tiến hành Data Repair bằng cách nạp lại Immutable Raw Snapshot (`crossref_records.json`) và thực thi lại logic Cleaning $\rightarrow$ Tín hiệu Data Quality quay lại 8/8 PASSED và Freshness quay về PASS (0 stale rows) $\rightarrow$ Vector store ChromaDB được xây dựng lại chuẩn xác, giúp *Retrieval Hit Rate* phục hồi về 100%, *Judge Accuracy* phục hồi về 90% và *Mean Judge Score* đạt lại 4.5/5.0.

## 11. Vấn đề tích hợp quan trọng

Mô tả một vấn đề phát sinh khi ghép các module trong pipeline và cách nhóm xử lý:

- **Triệu chứng:** Khi thực thi pipeline Phase 2 nhiều lần liên tiếp, dữ liệu truy xuất từ ChromaDB bị sai lệch (số bản ghi tăng đột biến, kết quả Hit Rate không đúng kỳ vọng) hoặc báo lỗi `InvalidCollectionException`.
- **Nguyên nhân:** ChromaDB lưu trữ dữ liệu bền vững trên đĩa (`data/chroma/`). Khi khởi tạo collection mới mà không dọn dẹp thư mục cũ hoặc không cô lập tên collection, ChromaDB tự động chèn thêm (append) vector mới, gây ô nhiễm chéo (data contamination) giữa 3 pha Baseline, Corrupted và Repaired.
- **Cách xử lý:** Trong `LocalEmbeddingIndex.build()`, bổ sung cơ chế dọn dẹp thư mục đĩa (clean slate) trước khi khởi tạo Chroma client mới, đồng thời phân rã định danh collection riêng biệt cho từng trạng thái (`papers-baseline`, `papers-corrupted`, `papers-repaired`).
- **Cách xác minh:** Chạy `uv run python script/run_corruption_flow.py`, kiểm tra log cho thấy số lượng bản ghi từng collection chính xác tuyệt đối (Baseline: 23, Corrupted: 25, Repaired: 23) và các chỉ số phục hồi 100%.

## 12. Giới hạn và hướng cải thiện

| Giới hạn hiện tại | Ảnh hưởng   | Hướng cải thiện có thể kiểm chứng |
| --------------------- | -------------- | ----------------------------------------- |
| Metric `mean_token_f1` ở pha Repaired (0.5793) chênh lệch cực nhỏ so với Baseline (0.5824) | Tính bất định (non-determinism) của LLM OpenAI khi sinh từ nối tự nhiên | Cấu hình `temperature=0.0` hoặc tính điểm trung bình qua 5 lần chạy (Monte Carlo evaluation) |
| Check `paper_id_not_null` trong Data Quality sử dụng `.notnull()` | Chuỗi rỗng `""` không bị xem là null nếu không trích xuất `.str.strip()` | Cải tiến quy tắc check thành `df["paper_id"].astype(str).str.strip().ne("")` |
| Ragas evaluation mặc định bị skipped để tối ưu tốc độ | Chưa đo lường sâu chỉ số *Faithfulness* và *Context Precision* | Thiết lập cron job chạy độc lập với `RUN_RAGAS=1` trên môi trường CI/CD |

## 13. Checklist trước khi nộp

- [x] Thông tin nhóm và repository chính xác.
- [x] Phân công khớp với module, artifact và kết quả thực tế.
- [x] Lệnh tái hiện đã được chạy lại trên phiên bản dùng để nộp.
- [x] Baseline, corrupted và repaired dùng cùng evaluation set.
- [x] Bảng metrics khớp với các file trong `data/results/`.
- [x] Quality/freshness conclusions khớp với `data/quality/`.
- [x] Các đường dẫn báo cáo và artifact truy cập được.
- [x] Mỗi thành viên đã hoàn thành báo cáo vai trò riêng.
- [x] Không có `.env`, API key, token hoặc secret trong source, report, log hay ảnh.

