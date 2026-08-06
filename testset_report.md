# Báo Cáo Tổng Hợp Module Đóng Băng Bộ Câu Hỏi Đánh Giá (Evaluation Test Set)

Tài liệu này tổng hợp toàn bộ công việc đã thực hiện, kết quả đạt được và các lưu ý kỹ thuật đối với module **Evaluation Test Set Builder** (tạo bộ câu hỏi đánh giá cố định - Frozen Evaluation Set) thuộc dự án RAG Data Pipeline & Observability.

---

## 1. Các công việc đã thực hiện

### 1.1. Phân tích Dữ liệu Sạch (`data/clean/papers_clean.json`)
- Phân tích tập dữ liệu 24 bài báo khoa học đã qua làm sạch.
- Trích chọn các bài báo tiêu biểu thuộc nhiều lĩnh vực chuyên ngành (Tool Selection, Y tế/Radiology, Địa chất/Dầu khí, Xây dựng, Bảo hiểm, Hallucination, Bibliometric Review, Deep RAG) để biên soạn câu hỏi.

### 1.2. Chuyển đổi & Chuẩn hóa Bộ Câu Hỏi sang Tiếng Anh (English Benchmark)
- **Lý do kỹ thuật**: Để phù hợp 100% với mô hình Embedding `sentence-transformers/all-MiniLM-L6-v2` (huấn luyện chuẩn tiếng Anh) và cơ chế tính toán độ trùng khớp từ vựng `_token_f1`, toàn bộ 10 câu hỏi và `ground_truth` đã được biên soạn bằng **Tiếng Anh (English)**. Điều này giúp cách ly rào cản ngôn ngữ và tập trung đánh giá đúng năng lực RAG Agent.
- **Quy mô bộ câu hỏi**: **10 câu hỏi chuẩn (Golden Samples)**.
- **Phân bổ 5 nhóm `question_type` (Mỗi type đúng 2 câu hỏi)**:
  1. `factual` (2 câu): Hỏi thông số, con số và kết quả thực nghiệm chi tiết.
  2. `metadata` (2 câu): Hỏi tác giả, năm công bố, tổ chức nghiên cứu.
  3. `summary` (2 câu): Hỏi tổng quan phương pháp, đóng góp chính hoặc kiến trúc.
  4. `application` (2 câu): Hỏi về miền ứng dụng thực tế (y tế, tài chính, địa chất, xây dựng).
  5. `comparative` (2 câu): Hỏi so sánh/liên kết thông tin giữa nhiều bài báo khác nhau.

### 1.3. Cài đặt Module `src/evaluation/testset.py`
- Triển khai hàm `build_test_set(df: pd.DataFrame, output_path: Path | str)`:
  - Kiểm tra `df` không rỗng.
  - Định nghĩa danh sách 10 mẫu câu hỏi tiếng Anh chuẩn hóa.
  - Kiểm tra đối chiếu tự động: Tất cả các `ground_truth_doc_ids` phải tồn tại trong cột `paper_id` của `df`.
  - Tự động tạo thư mục cha `data/eval/` và xuất file `data/eval/test_set.json`.

### 1.4. Viết Unit Test & Kiểm thử Tự động
- Viết file [test_testset.py](file:///Users/nguyenvietthang/Coding/VinUni/Lab/K3_Day10_Data-Pipeline-Data-Observability-B62/src/evaluation/test_testset.py) để kiểm thử tự động:
  - Kiểm tra số lượng câu hỏi bằng 10.
  - Kiểm tra schema từng câu hỏi (chứa đủ `id`, `question_type`, `question`, `ground_truth`, `ground_truth_doc_ids`).
  - Kiểm tra phân bổ đủ 5 nhóm `question_type` và mỗi nhóm có đúng 2 câu.

---

## 2. Kết quả đạt được

1. **Kết quả Unit Test**:
   - Bộ unit test chạy thành công 100%:
     ```text
     .
     ----------------------------------------------------------------------
     Ran 1 test in 0.004s

     OK
     ```

2. **Dữ liệu thực tế đã xuất ra**:
   - File chính thức lưu tại: [test_set.json](file:///Users/nguyenvietthang/Coding/VinUni/Lab/K3_Day10_Data-Pipeline-Data-Observability-B62/data/eval/test_set.json) chứa 10 mẫu câu hỏi tiếng Anh chuẩn hóa dưới dạng JSON Array.

---

## 3. Danh sách 10 Câu Hỏi Chuẩn trong Test Set

| ID | Type | Question | Ground Truth Doc IDs |
| :--- | :--- | :--- | :--- |
| **q1** | `factual` | In the Hi-RAG paper, how many tools and real-enterprise services are included in the MCPBench benchmark? | `10.1111/exsy.70341` |
| **q2** | `factual` | In the evaluation on the IDX7 dataset panel, by what percentage does the retrieval component in CM-RAF-Lag-Llama reduce the MSE compared to Lag-Llama alone? | `10.21203/rs.3.rs-10178277/v1` |
| **q3** | `metadata` | Who is the author of the study on adapting LLaMA-2-13B for insurance information delivery in Kenya? | `10.21203/rs.3.rs-9770645/v1` |
| **q4** | `metadata` | Which authors conducted the bibliometric review of Agentic AI architectures from 2023 to 2025? | `10.63646/kpqm1958` |
| **q5** | `summary` | According to the bibliometric review by Ben J. Weber et al., how did the annual output of publications on agentic AI change from 2023 to 2025? | `10.63646/kpqm1958` |
| **q6** | `summary` | According to Haopeng Yang's review, at which stages of a RAG-enhanced LLM system can errors leading to hallucination arise? | `10.54254/2753-8818/2026.dl34055` |
| **q7** | `application` | What is the primary medical application and objective of the JADE-Plus framework? | `10.1007/s10278-026-02086-9` |
| **q8** | `application` | In which specific domain and tasks is the SafeRAG framework applied? | `10.2118/234689-pa` |
| **q9** | `comparative` | What common objective do both JADE-Plus and SafeRAG share when applying RAG in specialized domains? | `10.1007/s10278-026-02086-9`, `10.2118/234689-pa` |
| **q10** | `comparative` | Compare the primary goals of RAG integration between AMOS MBEKI NYAGAR's study in Kenya and Sohail Khan's study on Knowledge Graphs. | `10.21203/rs.3.rs-9770645/v1`, `10.22214/ijraset.2026.82233` |

---

## 4. Các lưu ý kỹ thuật quan trọng (Technical Notes)

1. **Xác minh Ground Truth (100% Exact Matching)**:
   - Mọi con số (201 tools, 40 services, 28.85% MSE, 4 $\rightarrow$ 96 $\rightarrow$ 710 ấn phẩm), tên tác giả (AMOS MBEKI NYAGAR, Ben J. Weber,...) đều được lấy chính xác tuyệt đối từ văn bản gốc của bài báo tương ứng trong `papers_clean.json`.
2. **Thiết kế cho 3 trạng thái của Pipeline**:
   - Bộ 10 câu hỏi tiếng Anh đóng vai trò là "Freeze Benchmark". Khi chạy các trạng thái **Baseline**, **Corrupted** và **Repaired**, RAG Agent sẽ đều phải trả lời cùng bộ câu hỏi này để so sánh biến động điểm số một cách khách quan nhất.
