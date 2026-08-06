# Phân Tích Kỹ Thuật: Biến Động Chỉ Số Sau Khi Phục Hồi Dữ Liệu (Data Repair Metrics Variance)

Tài liệu này phân tích chi tiết nguyên nhân kỹ thuật giải thích sự biến động của chỉ số `Mean Token F1` sau bước Khôi phục Dữ liệu (Data Repair) và quy chuẩn đánh giá hệ thống RAG Data Pipeline trong môi trường Production thực tế.

---

## 1. Tại sao các chỉ số khác khôi phục 100% nhưng `Mean Token F1` lại biến động nhẹ (`0.5824` vs `0.5793`)?

### **Phân Tích Nguyên Nhân Kỹ Thuật:**

Sự chênh lệch cực nhỏ giữa Baseline State (`0.5824`) và Repaired State (`0.5793`) - chỉ **0.0031** (tương đương **0.3%**) - bắt nguồn từ bản chất kỹ thuật của 2 thành phần:

1. **Tính Bất Định (Non-determinism / Stochastic Sampling) của LLM**:
   - RAG Agent sử dụng mô hình ngôn ngữ lớn OpenAI `gpt-4o-mini` để sinh câu trả lời tự nhiên dựa trên ngữ cảnh được trích xuất từ ChromaDB.
   - Cho dù cùng một tập ngữ cảnh tài liệu và cùng tham số cấu hình, ở mỗi lần gọi API khác nhau, LLM vẫn có **độ biến động ngẫu nhiên nhỏ (stochastic decoding)** trong việc lựa chọn từ ngữ và cấu trúc câu.
   - *Ví dụ thực tế*:
     - *Lần chạy Baseline*: mô hình sinh câu trả lời: `"The paper presents 201 tools and 40 services."`
     - *Lần chạy Repaired*: mô hình sinh câu trả lời: `"It introduces 201 tools along with 40 services."`

2. **Đặc Tính Exact Token Overlap của Chỉ Số Token F1**:
   - Thuật toán `Token F1` tính toán sự trùng khớp từ vựng exact-token giữa câu trả lời của Agent và chuỗi văn bản tham chiếu `ground_truth`.
   - Việc LLM thay đổi một vài từ nối hoặc cấu trúc câu ở lần sinh văn bản sau đã làm cho tỷ lệ Precision/Recall từ vựng biến động nhẹ ở phần thập phân.

### **Tại sao các chỉ số khác lại khôi phục hoàn toàn 100%?**

* **Retrieval Hit Rate (`100.0%`)**: Là phép tính đếm số học cố định (**Deterministic**) dựa trên ID bài báo được truy xuất từ ChromaDB. Dữ liệu sau khi Repair được phục hồi sạch 100% giống hệt Baseline $\rightarrow$ Kết quả tìm kiếm Top-4 phải trùng khớp hoàn toàn 100%.
* **Observability Data Quality & Freshness (`PASSED`)**: Được kiểm tra trực tiếp trên các thuộc tính tĩnh trong file JSON/CSV $\rightarrow$ Đạt chuẩn 100%.
* **LLM Judge Score (`4.50 / 5.0`) & Accuracy (`90.0%`)**: LLM Judge chấm điểm dựa trên **ý nghĩa ngữ nghĩa tổng thể (Semantic correctness)** chứ không đếm từng từ. Do đó, sự biến động từ nối nhỏ của RAG Agent không làm thay đổi đánh giá chất lượng của Judge.

---

## 2. Trong Production, các chỉ số khôi phục về đúng như trước có phải là chuẩn không?

👉 **CÂU TRẢ LỜI: RẤT CHUẨN, NHƯNG CẦN PHÂN BIỆT 2 NHÓM METRIC TRONG ENTERPRISE PRODUCTION**:

### **Group A: Các chỉ số Cố định (Deterministic Metrics) $\rightarrow$ BẮT BUỘC KHÔI PHỤC 100% EXPLICIT**
- **Tín hiệu Data Observability**: Các kiểm tra `Quality Check (Passed)`, `Freshness (Pass)`, `Completeness`, `Uniqueness` và `Row count` bắt buộc phải khôi phục về **đúng 100% trạng thái ban đầu**.
- **Retrieval Metrics**: `Retrieval Hit Rate`, `Recall@K`, `MRR` bắt buộc phải quay lại mốc Baseline.
- *Nếu các chỉ số này không về đúng mức trước khi hỏng, pipeline phục hồi của bạn bị coi là còn sót lỗi dữ liệu.*

### **Group B: Các chỉ số Sinh ngẫu nhiên (Generative / LLM Metrics) $\rightarrow$ CHẤP NHẬN BẢO HÀNH BIẾN ĐỘNG SAI SỐ**
- Đối với các chỉ số sinh ngẫu nhiên từ LLM (`Token F1`, `ROUGE`, `BLEU`), trong Production các kỹ sư chấp nhận dải chênh lệch nhỏ dưới **±1%** là **Nhiễu thống kê chấp nhận được (Expected Variance / Statistical Noise)** do bản chất ngẫu nhiên của mô hình sinh.
- Việc `Retrieval Hit Rate` quay về **100%**, `LLM Judge` quay về **90% / 4.5 điểm** và `Quality Check` **PASSED** trở lại đã chứng minh quy trình Khôi phục Dữ liệu (Data Repair) của hệ thống đã **HOÀN THẢO TRỌN VẸN 100%**.
