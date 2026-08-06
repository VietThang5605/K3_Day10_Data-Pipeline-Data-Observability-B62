# Báo cáo cá nhân — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
| --- | --- |
| Họ và tên | Nguyễn Việt Thắng |
| MSSV | 2A202601321 |
| Khóa/Lớp | K3 |
| Tên nhóm | B62 |
| Vai trò chính | Ingestion từ Crossref |
| Repository | `K3_Day10_Data-Pipeline-Data-Observability-B62` |
| Ngày hoàn thành báo cáo | 2026-08-06 |

## 2. Vai trò và phạm vi công việc

Tôi phụ trách tầng đầu vào dữ liệu: lấy metadata bài báo từ Crossref, chuyển payload API về contract `PaperRecord`, và lưu snapshot để các tầng sau dùng lại mà không phải gọi mạng.

| Deliverable sở hữu | File/hàm phụ trách | Input | Output bàn giao | Trạng thái |
| --- | --- | --- | --- | --- |
| Kết nối nguồn | `src/ingestion/crossref.py::fetch_source_records` | `Settings`: query, filter, `max_results` | Payload JSON Crossref và danh sách `PaperRecord` | Hoàn thành |
| Parsing/schema | `parse_crossref_payload`, `parse_date`, `PaperRecord` | `message.items` của Crossref | Record chuẩn hóa ở tầng raw | Hoàn thành |
| Lưu/đọc snapshot | `fetch_source_records`, `load_raw_records` | Payload và path cấu hình | `data/raw/crossref_response.json`, `data/raw/crossref_records.json` | Hoàn thành |
| Kiểm thử module | `src/ingestion/test_crossref.py` | Payload và HTTP response giả lập | Test parse, retry, persistence | Hoàn thành |

Tầng Cleaning (`src/ingestion/cleaning.py`) nhận `list[PaperRecord]`; vì vậy output của tôi là đầu vào trực tiếp cho Người 2. Từ cleaned dataset, các tầng index, evaluation, quality/freshness và repair tiếp tục sử dụng dữ liệu này.

## 3. Kết quả bàn giao và bằng chứng

| Nhiệm vụ | Bằng chứng | Kết quả |
| --- | --- | --- |
| Gọi Crossref REST API | `https://api.crossref.org/works`; tham số lấy từ `Settings` | Query: `agentic retrieval augmented generation large language model`; tối đa 24 kết quả |
| Chống lỗi tạm thời | Retry tối đa 5 lần cho HTTP 429/503 hoặc `requests.RequestException`; backoff 1, 2, 4, 8, 16 giây | Giảm nguy cơ thất bại do rate limit/lỗi mạng tạm thời |
| Chuẩn hóa raw record | `PaperRecord` có DOI, title, summary, authors, categories, dates, DOI/PDF URL, publisher | Chỉ giữ record có DOI, title và abstract/description không rỗng |
| Lưu artifact truy vết | `data/raw/crossref_response.json` (232,192 bytes) và `data/raw/crossref_records.json` (58,717 bytes) | Payload gốc và 24 record đã parse |
| Cấu hình Judge LLM | `.env`, `.env.example`, `.env-example` | Có `JUDGE_LLM_PROVIDER` và `JUDGE_LLM_MODEL`; mẫu cấu hình không chứa secret |
| Tích hợp downstream | `data/clean/papers_clean.json` | Cleaning tạo 23 record hợp lệ từ 24 raw record |

Artifact then chốt của phần tôi là `data/raw/crossref_records.json`: file gồm 24 đối tượng theo contract `PaperRecord`. Nó được dùng để tái tạo clean dataset khi repair, thay vì fetch lại nguồn đang thay đổi.

## 4. Giải thích kỹ thuật

### Vấn đề cần giải quyết

Crossref trả về metadata không đồng nhất: trường ngày là `date-parts`, title/author/link là mảng, subject có thể vắng mặt và abstract có thể chứa JATS XML. Pipeline cần một đầu ra có schema ổn định, truy vết được về dữ liệu gốc, đồng thời chịu được lỗi HTTP tạm thời.

### Cách triển khai

`fetch_source_records` tạo request tới endpoint `/works` từ cấu hình, gắn `User-Agent` có `mailto` để sử dụng Crossref Polite Pool và đặt timeout 30 giây. Nếu nhận 429/503 hoặc exception mạng, hàm đợi theo exponential backoff và thử lại. Khi thành công, payload nguyên bản được ghi trước; sau đó `parse_crossref_payload` ánh xạ từng item thành `PaperRecord`.

Quy tắc parsing chính:

1. DOI làm `paper_id`; record thiếu DOI bị bỏ.
2. Lấy title đầu tiên; `summary` ưu tiên `abstract`, sau đó `description`; thiếu title hoặc summary thì bỏ record.
3. Ghép `given` và `family` thành danh sách authors; lấy `subject` làm categories và đặt `primary_category = "unknown"` khi không có category.
4. Chuẩn hóa ngày từ `date-parts` về `YYYY-MM-DD`, có fallback cho ngày chỉ có năm/tháng và cho trường ngày khác nhau.
5. Lấy DOI URL, PDF URL đầu tiên có `content-type == application/pdf`, và publisher. Các thẻ JATS trong abstract được giữ nguyên; Cleaning mới chịu trách nhiệm bỏ markup/text không phù hợp embedding.

### Input, output và contract

| Thành phần | Mô tả |
| --- | --- |
| Input | JSON Crossref `message.items`; `Settings.source_query`, `source_filter`, `max_results` và đường dẫn artifact |
| Output runtime | `list[PaperRecord]` (frozen dataclass) |
| Output lưu trữ | Raw HTTP payload và JSON list `PaperRecord` tại `data/raw/` |
| Module phụ thuộc | `requests`, `core.config.Settings` |
| Module sử dụng output | `ingestion.cleaning.build_clean_dataframe`; repair flow đọc bằng `load_raw_records` |
| Lỗi xử lý | 429/503, lỗi request/timeout, schema thiếu field, snapshot không tồn tại hoặc JSON raw-record không phải list |

## 5. Quyết định kỹ thuật quan trọng

- **Bối cảnh:** Sau corruption, có thể gọi lại Crossref hoặc khôi phục từ dữ liệu đã lấy.
- **Các phương án:** (1) fetch lại API; (2) dùng snapshot `crossref_records.json`.
- **Phương án chọn:** Lưu cả raw response lẫn raw records và dùng raw-record snapshot cho downstream/repair.
- **Lý do:** API bên ngoài có thể thay đổi theo thời gian; snapshot giữ đúng tập DOI làm cơ sở so sánh baseline–corrupted–repaired, không bị rate limit và tái lập nhanh hơn. Raw response vẫn giữ bằng chứng của payload gốc khi cần audit parsing.
- **Bằng chứng:** Repair trả về 23 record sạch, quality pass và retrieval hit rate 1.0, đúng số row/hit rate baseline; xem `data/quality/repaired_quality.json` và `data/results/repaired_metrics.json`.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng:** Request tới Crossref có thể nhận HTTP `429 Too Many Requests`, khiến việc lấy dữ liệu bị gián đoạn nếu chỉ gọi API một lần.
- **Cách tái hiện:** Trong `src/ingestion/test_crossref.py`, mock `requests.get` trả về lần lượt một response `429` rồi một response `200` chứa payload hợp lệ.
- **Nguyên nhân gốc:** Crossref áp dụng giới hạn tần suất truy cập để bảo vệ dịch vụ; đây là lỗi tạm thời từ nguồn bên ngoài, không phải lỗi schema của dữ liệu.
- **Cách xử lý:** `fetch_source_records` sử dụng `User-Agent` có `mailto` cho Crossref Polite Pool, timeout 30 giây, và retry tối đa 5 lần đối với HTTP 429/503 hoặc `requests.RequestException`. Thời gian chờ exponential backoff là 1, 2, 4, 8 và 16 giây.
- **Cách xác minh sau khi xử lý:** Chạy `UV_CACHE_DIR=/private/tmp/uv-cache uv run python -m unittest src/ingestion/test_crossref.py`. Kết quả log có dòng `Crossref API returned temporary status 429. Retrying in 1.0 seconds...`, sau đó toàn bộ 2 test pass (`OK`). Test cũng kiểm tra sự tồn tại và nội dung của cả raw response lẫn raw records.
- **Điều học được:** Với nguồn API công khai, retry có chọn lọc và lưu snapshot tại lần gọi thành công giúp pipeline bền vững hơn, tránh thất bại vì sự cố mạng/rate limit ngắn hạn và hỗ trợ tái lập downstream.

## 7. Hiểu biết về luồng end-to-end

1. Crossref cung cấp payload; ingestion lưu raw response, parse thành `PaperRecord` và lưu raw records. Cleaning làm sạch JATS/text, lọc record không đạt, tạo `text_for_embedding` và `age_days`; index tạo embedding MiniLM và ChromaDB.
2. Test set gồm 10 câu hỏi có `ground_truth_doc_ids`. Evaluation đối chiếu DOI của tài liệu được retrieve với các ID này để tính retrieval hit rate; câu trả lời được so với ground truth bằng token F1 và LLM judge.
3. Quality checks kiểm tra tính hợp lệ/toàn vẹn tại một thời điểm (ID null/unique, title, độ dài summary). Freshness riêng biệt đo tuổi dữ liệu qua `age_days` so với ngưỡng 180 ngày và báo stale rows.
4. Cùng test set là điều kiện kiểm soát thí nghiệm: khác biệt metric giữa baseline, corrupted và repaired khi đó phản ánh dữ liệu/index, không phải độ khó câu hỏi thay đổi.
5. Repair thành công khi rebuild từ snapshot tạo lại data contract/quality/freshness đúng, số row trở về 23 và các metric truy xuất/trả lời phục hồi gần hoặc bằng baseline.

## 8. Phân tích kết quả toàn pipeline

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét |
| --- | ---: | ---: | ---: | --- |
| `retrieval_hit_rate` | 1.0000 | 0.9000 | 1.0000 | Mất 0.1 khi summary/nội dung bị phá; phục hồi hoàn toàn |
| `mean_token_f1` | 0.5824 | 0.4599 | 0.5793 | Repair gần baseline, chênh -0.0031 |
| `judge_accuracy` | 0.90 | 0.70 | 0.90 | Phục hồi hoàn toàn |
| `mean_judge_score` | 4.50 | 3.70 | 4.50 | Phục hồi hoàn toàn |
| Quality checks | pass (23 rows) | fail (25 rows) | pass (23 rows) | Corrupted vi phạm unique/summary/freshness |
| Freshness | fresh, 0 stale | stale, 7 stale | fresh, 0 stale | Ngưỡng 180 ngày |

Chuỗi bằng chứng: (1) blank summary và semantic poisoning làm `text_for_embedding` mất/trôi ngữ nghĩa, nên retrieval hit rate giảm 1.0 → 0.9, token F1 giảm 0.5824 → 0.4599 và judge accuracy giảm 0.9 → 0.7. (2) Repair đọc raw snapshot, làm sạch lại và rebuild index; quality/freshness về pass/fresh, retrieval hit rate và judge metrics về baseline. Các giá trị lấy từ `data/results/*_metrics.json` và `data/quality/*_quality.json`.

Tín hiệu quan sát được khác với mô tả corruption là quality check `paper_id_not_null` vẫn `true` ở corrupted. Báo cáo ghi đã xóa một ID, nhưng check dùng `notnull()` nên chuỗi rỗng không bị xem là null. Đây là khoảng trống của rule quality; nên bổ sung kiểm tra `paper_id.str.strip().ne("")`.

## 9. Điều học được và cải thiện

1. Raw snapshot là ranh giới quan trọng giữa nguồn thay đổi và pipeline tái lập được.
2. Schema và rule lọc cần được phân tách rõ: Ingestion bảo toàn raw semantics/JATS, còn Cleaning quyết định chất lượng cho embedding.
3. Quan sát data quality/freshness giúp giải thích metric RAG suy giảm, thay vì chỉ thấy câu trả lời sai.

Nếu có thêm thời gian, tôi sẽ bổ sung test contract giữa `Settings` và tất cả test fixture, cùng test edge case cho title/summary/DOI rỗng. Tiêu chí đo là toàn bộ suite pass và quality check phát hiện được cả ID `null` lẫn ID rỗng.

## 10. Cam kết

- [x] Nội dung phản ánh đúng phần ingestion tôi phụ trách và các artifact có trong repository.
- [x] Tôi có thể giải thích luồng end-to-end và vai trò của raw snapshot trong repair.
- [x] Mọi metric nêu trên có file JSON/report đối chiếu.
- [x] Tôi đã sửa lỗi fixture và xác minh 2/2 kiểm thử ingestion pass.
- [x] Báo cáo không chứa API key, token hoặc secret.
- [x] Báo cáo được viết riêng theo vai trò Ingestion.

**Họ và tên:** Nguyễn Việt Thắng

**Ngày xác nhận:** 2026-08-06
