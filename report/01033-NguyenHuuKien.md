# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên       | Nguyễn Hữu Kiên             |
| MSSV               | 2A202601033                     |
| Khóa/Lớp         | K3 / AI-B62              |
| Tên nhóm         | Nhóm 6 người (B62)     |
| Vai trò chính    | Người 6: Corruption, repair và comparison                 |
| Repository         | [VietThang5605/K3_Day10_Data-Pipeline-Data-Observability-B62](https://github.com/VietThang5605/K3_Day10_Data-Pipeline-Data-Observability-B62) |
| Ngày hoàn thành | 2026-08-06               |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao  | Trạng thái                                 |
| ------------------ | --------------------- | ---------------- | ----------------- | -------------------------------------------- |
| **Data Corruption & Noise Injection** | [corruption.py](src/ingestion/corruption.py) | Cleaned DataFrame từ `papers_clean.json` | Corrupted DataFrame (`papers_clean_corrupted.json`, `.csv`) và file log `corruption_log.json` | Hoàn thành |
| **Orchestration & Phase 2 Pipeline** | [corruption_flow.py](src/pipelines/corruption_flow.py)| Baseline metrics, Cleaned DataFrame, Raw snapshot | ChromaDB Collections lỗi và sạch, kết quả RAG đánh giá trạng thái Corrupted và Repaired | Hoàn thành |
| **Comparison Report & Variance Analysis** | [corruption_report.md](corruption_report.md)<br>[repair_variance_analysis.md](repair_variance_analysis.md) | Metrics và Quality Reports từ cả 3 trạng thái | Báo cáo so sánh 3 cột chi tiết và báo cáo phân tích biến động chỉ số | Hoàn thành |
| **Unit Testing for Corruption** | [test_corruption.py](src/ingestion/test_corruption.py) | Cleaned DataFrame thực tế | Toàn bộ các test case xác minh logic gây lỗi và ghi log thành công | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động                         | Thành viên/module được hỗ trợ | Kết quả                    |
| ------------------------------------ | ------------------------------------ | ---------------------------- |
| **Hỗ trợ thiết kế Data Observability** | Người 4 (Data Observability) | Đảm bảo các checks trong [quality.py](src/observability/quality.py) bắt được đúng các lỗi do tôi cố ý gây ra (như duplicate, rỗng ID, stale date). |
| **Đóng băng và tích hợp Test Set** | Người 3 (Evaluation và Test Set) | Tích hợp bộ câu hỏi cố định từ `test_set.json` vào luồng đánh giá Phase 2 để kết quả so sánh hoàn toàn khách quan. |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao       | Cách xác minh         |
| --------------------------- | ----------------------------- | ------------------------- | ----------------------- |
| Lập trình logic làm hỏng dữ liệu | [corruption.py](src/ingestion/corruption.py) | Sinh dữ liệu lỗi, tiêm mã độc ngữ nghĩa, đổi thời gian bài báo về năm 2000, tạo bản ghi trùng lặp và thiếu ID. | Chạy bộ unit test [test_corruption.py](file:///d:/ai_thuc_chien/K3_Day10_Data-Pipeline-Data-Observability-B62/src/ingestion/test_corruption.py) |
| Lập trình pipeline Phase 2 | [corruption_flow.py](src/pipelines/corruption_flow.py) | Tự động hóa luồng: Làm hỏng -> Re-index -> Đánh giá lỗi -> Khôi phục từ Raw Snapshot -> Re-index -> Đánh giá phục hồi -> Xuất báo cáo. | Chạy lệnh `uv run python src/pipelines/corruption_flow.py` |
| Báo cáo so sánh & Phân tích | [corruption_report.md](corruption_report.md)<br>[repair_variance_analysis.md](repair_variance_analysis.md) | Bảng kết quả đối chiếu chi tiết 3 cột cho RAG Metrics và Quality Signals; phân tích sự biến động nhỏ của Mean Token F1. | Xem trực tiếp các file báo cáo Markdown trong thư mục gốc. |

**Output cụ thể:**
* [corruption_log.json](data/results/corruption_log.json): File nhật ký chi tiết ghi lại 4 kịch bản gây lỗi đã tiêm vào tập dữ liệu (Blank Summary, Add Noise/Semantic Poisoning, Stale Date, Duplicates & Missing ID) cùng lý do ảnh hưởng kỳ vọng đến RAG Agent.
* [corruption_report.md](corruption_report.md): Báo cáo so sánh trực quan cho thấy sự sụt giảm nghiêm trọng của RAG Agent khi dữ liệu bị lỗi (Retrieval Hit Rate sụt từ 100% xuống 90%, LLM Judge Accuracy sụt từ 90% xuống 70%) và khả năng khôi phục toàn vẹn khi dữ liệu được sửa chữa.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Trong một hệ thống RAG phục vụ doanh nghiệp, chất lượng dữ liệu đầu vào quyết định trực tiếp đến độ chính xác của câu trả lời từ RAG Agent. Chúng ta cần giả lập lỗi dữ liệu một cách có kiểm soát trên môi trường thử nghiệm để:
1. Xác minh hệ thống giám sát dữ liệu (Data Observability) có phát hiện kịp thời các lỗi vi phạm hợp đồng dữ liệu (Data Contract) hay dữ liệu quá cũ (Stale Data) hay không.
2. Đo lường định lượng mức độ sụt giảm hiệu năng của RAG Agent khi bị lỗi dữ liệu tấn công.
3. Thiết lập và chứng minh quy trình khôi phục dữ liệu (Data Repair) tự động từ một snapshot thô nguồn đáng tin cậy giúp đưa hệ thống trở lại trạng thái ban đầu một cách hoàn hảo.

### Cách triển khai

Tôi đã lập trình module `src/ingestion/corruption.py` để tiêm các lỗi sau vào cleaned dataset:
* **Scenario 1 (Blank Summary)**: Xóa thông tin tóm tắt của bài báo Hi-RAG (`10.1111/exsy.70341`), khiến vector embedding mất toàn bộ thông tin chi tiết về bài báo.
* **Scenario 2 (Semantic Poisoning)**: Thay thế nội dung tóm tắt của bài CM-RAF-Lag-Llama và JADE-Plus bằng nội dung ẩm thực và nông nghiệp cổ đại, gây trôi dạt ngữ nghĩa (semantic drift).
* **Scenario 3 (Stale Published Date)**: Ép ngày xuất bản của 5 bài báo về năm `2000-01-01` để làm tăng số ngày cũ (`age_days` > 9500) nhằm kích hoạt cảnh báo Stale Data của freshness monitoring.
* **Scenario 4 (Duplicates & Missing ID)**: Nhân bản 2 dòng dữ liệu và xóa `paper_id` của 1 dòng để kiểm tra tính toàn vẹn dữ liệu (Completeness & Uniqueness).

Trong [corruption_flow.py](src/pipelines/corruption_flow.py), tôi điều phối toàn bộ thí nghiệm:
1. Đọc dữ liệu sạch và gọi hàm `corrupt_clean_dataframe()`.
2. Tạo collection `papers-corrupted` trên ChromaDB, tạo vector index mới và đánh giá RAG Agent bằng bộ câu hỏi đóng băng `test_set.json`.
3. Khôi phục dữ liệu bằng cách nạp lại snapshot thô ban đầu `crossref_records.json`, chạy lại hàm `build_clean_dataframe()` (hàm này loại bỏ trùng lặp, chuẩn hóa ngày tháng, làm sạch XML, tự động loại bỏ bài báo phi Latinh/tiếng Nga), rebuild collection `papers-repaired` trên ChromaDB và chạy đánh giá lần cuối.
4. Trích xuất metrics từ cả 3 trạng thái và tự động ghi báo cáo so sánh.

### Input, output và contract

| Thành phần                   | Mô tả                                     |
| ------------------------------ | ------------------------------------------- |
| Input                          | Cleaned DataFrame (`papers_clean.json`), Raw Snapshot (`crossref_records.json`), cấu hình hệ thống `Settings`. |
| Output                         | `papers_clean_corrupted.json`, `papers_clean_repaired.json`, `corruption_log.json`, `corrupted_metrics.json`, `repaired_metrics.json`, và `corruption_report.md`. |
| Module phụ thuộc             | [cleaning.py](src/ingestion/cleaning.py) (để làm sạch dữ liệu lúc repair), [metrics.py](src/evaluation/metrics.py) (để tính chỉ số đánh giá). |
| Module sử dụng output        | Các báo cáo chất lượng, dashboard UI, và báo cáo tổng kết của nhóm. |
| Điều kiện lỗi cần xử lý | - DataFrame đầu vào bị rỗng (`ValueError`).<br>- Không tìm thấy tệp Snapshot thô cục bộ (`RuntimeError`).<br>- Collection ChromaDB bị trùng tên hoặc nhiễm dữ liệu cũ (Xử lý bằng cách xóa/reset collection trước khi index). |

### Cách xác minh

Chạy script kiểm thử đơn vị cho module gây lỗi dữ liệu:
```bash
uv run python -m unittest src/ingestion/test_corruption.py
```
Hoặc thực thi toàn bộ pipeline Phase 2:
```bash
uv run python src/pipelines/corruption_flow.py
```

* **Kết quả mong đợi:**
  - 100% test cases trong `test_corruption.py` vượt qua (`OK`).
  - Pipeline chạy trơn tru, ghi nhận đúng sự sụt giảm chỉ số ở pha lỗi (hit rate sụt còn 0.9, Judge Accuracy sụt còn 0.7) và sự phục hồi hoàn hảo ở pha sửa chữa.
* **Kết quả thực tế:**
  - `test_corruption.py` chạy thành công, xác minh đúng số lượng dòng tăng do duplicate, summary của paper mục tiêu bị xóa rỗng, và ngày xuất bản bị đưa về năm 2000.
  - Pipeline Phase 2 chạy hoàn thành xuất sắc, tự động xuất đầy đủ báo cáo so sánh và phân tích biến động.
* **Artifact/log:**
  - [corruption_log.json](data/results/corruption_log.json)
  - [corruption_report.md](corruption_report.md)
  - [repair_variance_analysis.md](repair_variance_analysis.md)

## 5. Một quyết định kỹ thuật quan trọng

* **Bối cảnh:** Lựa chọn phương pháp phục hồi dữ liệu (Data Repair). Khi hệ thống phát hiện dữ liệu trong cơ sở dữ liệu hoặc vector store bị lỗi, chúng ta nên khôi phục từ snapshot sạch đã lưu ở tầng Cleaning hay khôi phục hoàn toàn từ Raw Snapshot gốc (`crossref_records.json`) và chạy lại quy trình Cleaning?
* **Các phương án đã cân nhắc:**
  1. *Phương án A*: Khôi phục trực tiếp từ snapshot sạch (`papers_clean.json`).
  2. *Phương án B*: Khôi phục từ Raw Snapshot thô (`crossref_records.json`) và thực thi lại toàn bộ logic làm sạch dữ liệu (`build_clean_dataframe`).
* **Phương án đã chọn:** Phương án B (Khôi phục từ Raw Snapshot).
* **Lý do:**
  - Trong thực tế sản xuất, logic làm sạch dữ liệu (Cleaning) và các quy tắc nghiệp vụ (Business Rules) luôn biến đổi theo thời gian (ví dụ: cần lọc thêm từ nhạy cảm, loại bỏ các ký tự đặc biệt mới phát sinh, hoặc thay đổi ngưỡng độ dài summary).
  - Nếu chọn Phương án A, chúng ta chỉ khôi phục được dữ liệu sạch của quá khứ. Mọi lỗi hoặc sự thiếu sót trong logic làm sạch cũ sẽ bị đóng băng vĩnh viễn trong snapshot sạch đó.
  - Chọn Phương án B giúp đảm bảo dữ liệu luôn được xử lý qua phiên bản logic làm sạch mới nhất. Điều này tuân thủ đúng nguyên lý "Single Source of Truth" bất biến (Immutable Data Source), giúp toàn bộ pipeline mang tính tái lập 100% (Reproducible).
* **Bằng chứng quyết định phù hợp:** Khi chạy repair, hệ thống đã nạp thành công 24 raw records từ snapshot thô, tự động loại bỏ trùng lặp, làm sạch XML, tự động drop 1 bài báo tiếng Nga không hợp lệ, thu về đúng 23 records sạch và đưa các chỉ số chất lượng/chỉ số RAG về trạng thái tối ưu như Baseline.

## 6. Một lỗi hoặc blocker đã xử lý

* **Triệu chứng/lỗi nguyên văn:** Khi thực thi pipeline Phase 2 nhiều lần, dữ liệu truy xuất từ ChromaDB bị sai lệch (số lượng bản ghi tăng lên, kết quả retrieval hit rate không đúng kỳ vọng) hoặc báo lỗi `InvalidCollectionException` do dữ liệu cũ từ lần chạy trước chưa được giải phóng.
* **Lệnh hoặc bước tái hiện:** Thực thi liên tiếp `uv run python script/run_phase1.py` rồi `uv run python src/pipelines/corruption_flow.py` trên cùng một cơ sở dữ liệu ChromaDB persistent mà không xóa thư mục index cũ.
* **Nguyên nhân gốc:** ChromaDB lưu trữ dữ liệu bền vững trên đĩa cứng. Khi tạo collection mới mà không dọn dẹp thư mục lưu trữ tương ứng hoặc không thiết lập cơ chế reset/overwrite collection một cách tường minh, ChromaDB sẽ tự động chèn thêm (append) các vector mới hoặc gây xung đột khóa (primary key), làm ô nhiễm chéo dữ liệu giữa các pha Baseline, Corrupted và Repaired.
* **Cách xử lý:** Trong hàm `LocalEmbeddingIndex.build()`, tôi đã bổ sung cơ chế kiểm tra và xóa thư mục dữ liệu cũ của ChromaDB (dưới `data/chroma/...`) tương ứng với collection đang xây dựng trước khi khởi tạo Chroma client mới. Đồng thời, phân rã độc lập tên collection cho từng trạng thái để đảm bảo tính cô lập tuyệt đối.
* **Cách xác minh sau khi sửa:** Chạy lại pipeline từ đầu đến cuối, kiểm tra log hiển thị số lượng bản ghi của mỗi collection hoàn toàn chính xác (Baseline: 23, Corrupted: 25, Repaired: 23). Các chỉ số đánh giá phục hồi khớp hoàn toàn với thiết kế.
* **Điều học được:** Khi làm việc với Vector Database persistent trong môi trường pipeline thử nghiệm hoặc CI/CD, luôn phải thiết kế cơ chế dọn dẹp (clean slate) hoặc định danh collection độc lập để loại bỏ hoàn toàn hiện tượng ô nhiễm dữ liệu (data contamination).

## 7. Hiểu biết về luồng end-to-end

1. **Dữ liệu đi từ Crossref đến vector index như thế nào?**
   - Dữ liệu thô (raw JSON) được fetch từ Crossref REST API qua HTTP request và lưu thành snapshot `crossref_response.json` / `crossref_records.json`.
   - Dữ liệu thô được parse thành các đối tượng `PaperRecord`, sau đó đưa qua module Cleaning để xóa thẻ HTML/JATS XML, lọc ký tự phi Latinh (tiếng Nga), tính toán số ngày tuổi `age_days` và tạo cột văn bản tổng hợp `text_for_embedding` (nối title, summary, authors, categories, dates).
   - `text_for_embedding` được đưa qua mô hình `all-MiniLM-L6-v2` để sinh vector embeddings 384 chiều, sau đó lưu trữ cùng metadata vào ChromaDB.

2. **Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?**
   - Bộ câu hỏi đóng băng (`test_set.json`) chứa các câu hỏi đa dạng loại kèm danh sách `ground_truth_doc_ids` (ID của bài báo chứa câu trả lời đúng).
   - RAG Agent gửi câu hỏi vào ChromaDB để thực hiện tìm kiếm ngữ nghĩa và lấy ra Top-K bài báo liên quan nhất.
   - **Retrieval Quality (Hit Rate)**: Được tính bằng tỷ lệ số câu hỏi mà Top-K tài liệu tìm được có chứa đúng ID bài báo trong `ground_truth_doc_ids`.
   - **Answer Quality**:
     - *Token F1*: Đo mức độ trùng khớp từ vựng trực tiếp giữa câu trả lời sinh ra bởi Agent với văn bản `ground_truth`.
     - *LLM Judge Score / Accuracy*: Sử dụng một LLM Judge độc lập (GPT-4o-mini) chấm điểm từ 1 đến 5 và đánh giá đúng/sai dựa trên mức độ tương đồng về mặt ý nghĩa ngữ nghĩa (semantic correctness), loại bỏ nhiễu do cách dùng từ khác biệt.

3. **Quality checks khác freshness monitoring ở điểm nào trong bài lab?**
   - **Quality checks**: Tập trung vào tính toàn vẹn tĩnh và cấu trúc của dữ liệu (Data Schema). Ví dụ: kiểm tra ID bài báo có bị null hay không, ID có độc nhất (unique) không, tiêu đề bài báo có bị rỗng không, độ dài phần tóm tắt có đạt tối thiểu 100 ký tự hay không.
   - **Freshness monitoring**: Tập trung vào khía cạnh thời gian (Temporal quality). Đo lường độ mới của dữ liệu bằng cách tính khoảng cách ngày từ ngày xuất bản đến ngày chạy pipeline (`age_days`) và đối chiếu với một ngưỡng cấu hình cụ thể (ngưỡng 180 ngày) để phát hiện dữ liệu lỗi thời (stale rows).

4. **Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?**
   - Đây là nguyên tắc kiểm soát biến số trong thực nghiệm khoa học. Việc giữ nguyên tập câu hỏi đánh giá giúp đảm bảo mọi sự thay đổi trong các chỉ số chất lượng đầu ra (Hit Rate, Token F1, Judge Score) hoàn toàn là do chất lượng dữ liệu và chất lượng index quyết định, chứ không phải do sự thay đổi độ khó/dễ của câu hỏi.

5. **Repair được xem là thành công dựa trên artifact và metric nào?**
   - **Artifact**: Sinh ra đầy đủ tệp dữ liệu đã sửa chữa `papers_clean_repaired.json` và `.csv` trùng khớp số lượng 23 dòng sạch.
   - **Quality & Freshness Metric**: Tín hiệu Quality check chuyển về `PASSED`, Freshness check chuyển về `PASS` (số lượng stale rows quay về bằng 0).
   - **RAG Performance Metric**: Retrieval Hit Rate phục hồi về đúng `100.0%`, LLM Judge Accuracy phục hồi về đúng `90.0%`, Mean Judge Score đạt lại `4.5 / 5.0` và Mean Token F1 quay về sát Baseline (~0.58).

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal          | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| ---------------------- | -------: | --------: | -------: | ------------------------- |
| `retrieval_hit_rate` |      `1.0000` |       `0.9000` |      `1.0000` | Sụt giảm 10% khi dữ liệu bị làm hỏng ngữ nghĩa và xóa rỗng summary; phục hồi hoàn toàn sau khi sửa dữ liệu. |
| `mean_token_f1`      |      `0.5824` |       `0.4599` |      `0.5793` | Sụt giảm mạnh ở pha lỗi do Agent thiếu ngữ cảnh chuẩn; phục hồi sát mức baseline (chênh lệch cực nhỏ 0.0031 do tính ngẫu nhiên của LLM). |
| `judge_accuracy`     |      `0.90` |       `0.70` |      `0.90` | Sụt giảm còn 70% ở pha lỗi (Agent trả lời sai/từ chối 3 câu); phục hồi hoàn toàn về mức 90%. |
| `mean_judge_score`   |      `4.50` |       `3.70` |      `4.50` | Điểm trung bình bị kéo xuống thấp ở pha lỗi; khôi phục hoàn hảo mốc 4.5/5.0 điểm sau repair. |
| Quality checks         |      `PASSED` |       `FAILED` |      `PASSED` | Pha corrupted vi phạm quy tắc unique ID và độ dài summary tối thiểu; repair khôi phục thành công. |
| Freshness status       |      `PASS` |       `FAIL` |      `PASS` | Pha corrupted phát hiện 5 dòng dữ liệu cũ (tuổi > 9500 ngày) bị đẩy về năm 2000; repair xóa bỏ hoàn toàn stale rows. |

### Kết luận từ số liệu

Hoàn thành hai chuỗi nguyên nhân–bằng chứng sau:
1. **Xóa rỗng summary bài viết và chèn văn bản rác nông nghiệp/ẩm thực (Data corruption)** $\rightarrow$ **Quality check báo FAILED, `summary_len_ge_100` báo False, Freshness báo FAIL với 5 stale rows (quality/freshness signal thay đổi)** $\rightarrow$ **Retrieval hit rate giảm từ 100% xuống 90%, Mean Token F1 giảm từ 0.5824 xuống 0.4599, Judge Accuracy giảm từ 90% xuống 70% (agent metric thay đổi)**.
2. **Khôi phục dữ liệu thô từ Raw Snapshot cục bộ và chạy lại logic Cleaning (Repair action)** $\rightarrow$ **Quality check quay về PASSED, Freshness quay về PASS với 0 stale rows (quality/freshness signal phục hồi)** $\rightarrow$ **Retrieval hit rate quay lại 100%, Judge Accuracy quay lại 90%, Mean Token F1 khôi phục về mức 0.5793 (agent metric phục hồi)**.

**Corruption nào ảnh hưởng rõ nhất và vì sao?**
- Corruption **Xóa rỗng summary (Blank Summary)** và **Chèn văn bản rác (Semantic Poisoning)** ảnh hưởng nghiêm trọng nhất đến RAG Agent.
- *Lý do*: Vì ChromaDB tìm kiếm bài báo dựa trên độ tương đồng Cosine của các vector embedding được sinh ra từ trường `text_for_embedding`. Khi summary bị xóa rỗng, bài báo chỉ còn tiêu đề quá ngắn khiến vector bị đẩy ra rất xa câu hỏi. Khi bị chèn rác, vector bị trôi dạt ngữ nghĩa (semantic drift) hoàn toàn sang chủ đề nông nghiệp/ẩm thực, dẫn đến ChromaDB truy xuất sai tài liệu trong Top-4. Khi thiếu ngữ cảnh chính xác, Agent bắt buộc phải từ chối trả lời hoặc sinh câu trả lời sai lệch (hallucination), làm sụt giảm trực tiếp chất lượng RAG đầu ra.

**Kết quả nào khác với kỳ vọng ban đầu?**
- Chỉ số `Mean Token F1` ở trạng thái phục hồi (`Repaired State`) đạt `0.5793`, không bằng tuyệt đối 100% so với Baseline (`0.5824`) dù dữ liệu đầu vào đã được khôi phục sạch hoàn hảo 100% giống hệt ban đầu.
- *Giả thuyết*: Do tính bất định ngẫu nhiên (non-determinism) của LLM OpenAI `gpt-4o-mini` khi sinh câu trả lời tự nhiên. Cho dù cùng một ngữ cảnh nạp vào prompt, mô hình vẫn có sai số nhỏ trong việc chọn từ nối hoặc cấu trúc câu ở các lần gọi API khác nhau.
- *Cách kiểm tra*: Đối chiếu trực tiếp câu trả lời của Agent ở `baseline_answers.json` và `repaired_answers.json` cho thấy về mặt ý nghĩa ngữ nghĩa chúng giống hệt nhau (do đó LLM Judge vẫn chấm điểm 4.5/5.0 và đạt Accuracy 90% tương đương), sự khác biệt chỉ nằm ở một vài từ ngữ nhỏ làm chỉ số so khớp từ vựng Token F1 biến động nhẹ ~0.3%.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. **Hiệu ứng cánh bướm của dữ liệu (Data-to-Agent Link)**: Một lỗi nhỏ ở tầng dữ liệu đầu vào (như mất summary hoặc chèn nhiễu ngữ nghĩa) có thể khuếch đại thành thảm họa ở đầu ra của RAG Agent (Agent trả lời sai, ảo tưởng thông tin). Đo lường chất lượng RAG bắt buộc phải gắn liền với giám sát chất lượng dữ liệu.
2. **Vai trò then chốt của Data Observability**: Các kiểm tra Quality và Freshness tự động hoạt động như một hệ thống cảnh báo sớm (early warning system). Nó giúp phát hiện dữ liệu lỗi ngay khi vừa đi vào pipeline, trước khi dữ liệu đó kịp làm nhiễm độc vector database và gây ảnh hưởng đến người dùng cuối.
3. **Giá trị của Immutable Raw Snapshot**: Lưu trữ snapshot thô ban đầu là chìa khóa vàng cho khả năng tái lập (reproducibility) và khả năng sửa chữa dữ liệu (data repair). Nó là nguồn gốc đáng tin cậy duy nhất giúp phục hồi toàn bộ hệ thống mà không cần phụ thuộc vào API mạng bên ngoài luôn thay đổi.

### Nếu có thêm thời gian

Tôi sẽ xây dựng **Cơ chế Tự động Khôi phục Dữ liệu (Auto-Healing Pipeline)**:
- Tích hợp một service giám sát liên tục (cron job/event trigger). Khi Observability báo cáo Quality Check `FAILED` hoặc Freshness `FAIL` ở môi trường production, hệ thống sẽ tự động gửi cảnh báo qua Slack/Email, đồng thời kích hoạt luồng sửa chữa tự động: Tự nạp lại dữ liệu từ raw snapshot, chạy clean, rebuild index và re-evaluate tự động mà không cần kỹ sư can thiệp thủ công.
- Cách đo lường cải tiến này là tính toán thời gian phục hồi hệ thống (Mean Time to Recovery - MTTR). Mục tiêu là giảm MTTR từ vài giờ (phát hiện và sửa bằng tay) xuống dưới 1 phút (tự động hóa hoàn toàn).

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Nguyễn Hữu Kiên
**Ngày xác nhận:** 2026-08-06
