# Giải Thích Kỹ Thuật Đánh Giá RAG & Data Observability (Checkpoints C2 & C3)

Tài liệu này giải thích chi tiết các câu hỏi lý thuyết cốt lõi thuộc Checkpoint C2 và Checkpoint C3 trong quá trình xây dựng RAG Data Pipeline & Evaluation System.

---

## 1. Tại sao bộ câu hỏi phải được chốt và đóng băng trước khi chạy đánh giá RAG?

### **Giải thích:**
- **Đảm bảo tính nhất quán và khách quan (Benchmark Control & Fairness)**: Bộ câu hỏi đóng băng (**Frozen Evaluation Test Set**) đóng vai trò là "thước đo chuẩn" (Constant Meter) cố định. 
- Trong bài toán đánh giá RAG Data Pipeline, mục tiêu của chúng ta là so sánh hiệu năng hệ thống qua 3 trạng thái:
  1. **Baseline State** (Dữ liệu sạch chuẩn).
  2. **Corrupted State** (Dữ liệu bị giả lập lỗi/suy hao).
  3. **Repaired State** (Dữ liệu đã được phục hồi/sửa chữa).
- Để đo lường chính xác tác động của chất lượng dữ liệu giữa 3 trạng thái này, điều kiện tiên quyết là phải **cách ly biến số (Isolate variables)** bằng cách giữ nguyên 100% bộ câu hỏi và đáp án tham chiếu (`ground_truth`). 
- Nếu bộ câu hỏi bị thay đổi giữa các lần chạy, sự biến động về điểm số sẽ bị nhiễu do câu hỏi khác đi chứ không phản ánh đúng ảnh hưởng của chất lượng dữ liệu.

---

## 2. Xử lý thế nào nếu một bài báo trong `ground_truth_doc_ids` bị thiếu ở pha sau (khi giả lập dữ liệu lỗi)?

### **Giải thích & Phương pháp xử lý:**
- **Trạng thái thực tế khi bị hỏng dữ liệu**: Ở pha giả lập lỗi (**Corrupted State**), một số bài báo sẽ bị xóa hoặc suy thoái thông tin. Khi RAG Agent nhận câu hỏi liên quan, phần **Retriever** (ChromaDB Vector Store) sẽ không thể tìm thấy bài báo tham chiếu gốc (`ground_truth_doc_ids`).
- **Quy trình xử lý & Tính điểm tự động**:
  1. **Chỉ số `retrieval_hit_rate`**: Tự động ghi nhận điểm `0.0` (Thất bại truy xuất) cho câu hỏi đó do tài liệu tham chiếu không nằm trong Top-K kết quả trả về.
  2. **Chỉ số `token_f1` & `LLM Judge Score`**: Tự động bị tụt giảm mạnh do LLM Agent không có đủ thông tin ngữ cảnh để trả lời (hoặc Agent sẽ đưa ra câu trả lời ảo giác/từ chối trả lời).
- **Ý nghĩa Kỹ thuật**: Đây chính là **kết quả mong muốn** của quá trình kiểm thử Data Observability nhằm chứng minh bằng con số định lượng rằng: *Dữ liệu đầu vào bị thiếu/hỏng sẽ trực tiếp tàn phá hiệu năng truy xuất và chất lượng câu trả lời của RAG Agent.*

---

## 3. Chỉ số `retrieval_hit_rate` phản ánh hiệu suất của cấu phần nào trong hệ thống RAG?

### **Giải thích:**
- Chỉ số `retrieval_hit_rate` (Tỷ lệ truy xuất trúng) phản ánh trực tiếp hiệu suất của **Cấu phần Truy xuất (Retrieval Module / Dense Vector Search & Retriever)**.
- **Chi tiết**:
  - Chỉ số này đo lường khả năng của Mô hình Embedding (`sentence-transformers/all-MiniLM-L6-v2`) và Vector Database (ChromaDB) trong việc tìm thấy đúng bài báo tham chiếu chứa đáp án (`ground_truth_doc_ids`) nằm trong danh sách Top-K (Top-4) kết quả trả về.
  - Nếu `retrieval_hit_rate = 1.0 (100%)`, điều đó chứng tỏ bộ Retriever hoạt động hoàn hảo và luôn tìm đúng tài liệu ngữ cảnh cần thiết.

---

## 4. Tại sao điểm Token F1 của câu trả lời lại không bao giờ đạt tuyệt đối 1.0 kể cả khi retrieval tìm đúng tài liệu?

### **Giải thích:**
Có 2 lý do kỹ thuật chính:

1. **Năng lực diễn đạt tự nhiên của LLM (Generative Paraphrasing)**:
   - Khi RAG Agent sử dụng LLM (`gpt-4o-mini`) để trả lời, mô hình sẽ tổng hợp ngữ cảnh và diễn đạt theo văn phong tự nhiên, có thêm các từ nối giao tiếp (*"Based on the retrieved paper..."*, *"The framework introduces..."*, các mạo từ *a/an/the*), chứ không bao giờ trích xuất copy y nguyên 100% từng từ của `ground_truth`.
2. **Bản chất của thuật toán Token F1 (Exact Token Matching)**:
   - Token F1 tính toán dựa trên tập hợp trùng khớp từ vựng exact-token giữa 2 chuỗi văn bản. 
   - Bất kỳ sự khác biệt nào về cấu trúc câu, từ đồng nghĩa (synonyms), hoặc từ nối dư thừa cũng sẽ làm giảm tỷ lệ Overlapping Tokens, khiến F1 thường chỉ rơi vào khoảng `0.5 - 0.7` ngay cả khi câu trả lời đúng 100% về mặt ngữ nghĩa (như LLM Judge đã chấm 4.5/5.0).
