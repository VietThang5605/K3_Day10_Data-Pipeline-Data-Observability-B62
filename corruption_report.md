# Báo Cáo Thí Nghiệm Controlled Corruption, Data Repair & Observability (Phase 2)

Báo cáo này tổng hợp chi tiết toàn bộ các nội dung công việc đã thực hiện, kết quả định lượng đạt được và giải đáp kỹ thuật đối chiếu qua 3 trạng thái của hệ thống RAG Data Pipeline:
1. **Baseline State**: Trạng thái dữ liệu sạch chuẩn ban đầu (23 bài báo 100% Tiếng Anh).
2. **Corrupted State**: Trạng thái dữ liệu bị giả lập lỗi có kiểm soát (Blank summary, Add noise, Stale date, Duplicates).
3. **Repaired State**: Trạng thái dữ liệu được phục hồi chuẩn hóa từ Raw Snapshot.

---

## 1. Nội Dung Đã Thực Hiện (Work Completed)

### A. Thiết kế 4 Kịch bản Gây Lỗi Dữ Liệu Có Kiểm Soát (`src/ingestion/corruption.py`)
- **Kịch bản 1 (Blank Summary)**: Xóa rỗng `summary` và `summary_chars` của bài báo Hi-RAG (`10.1111/exsy.70341` - liên quan câu hỏi `q1`).
- **Kịch bản 2 (Add Noise / Semantic Poisoning)**: Thay thế `summary` bài CM-RAF-Lag-Llama (`10.21203/rs.3.rs-10178277/v1` - câu `q2`) và bài JADE-Plus (`10.1007/s10278-026-02086-9` - câu `q7`) bằng thông tin rác ngẫu nhiên về nông nghiệp và ẩm thực cổ đại.
- **Kịch bản 3 (Stale Date Injection)**: Đổi ngày `published` của 5 bài báo về năm `2000-01-01` (`age_days` > 9500 ngày) để đánh lừa tín hiệu Freshness.
- **Kịch bản 4 (Duplicates & Missing ID)**: Nhân đôi 2 bản ghi và gán `paper_id` rỗng cho 1 bản ghi để kích hoạt lỗi Completeness và Uniqueness.
- **Artifacts xuất ra**: `data/clean/papers_clean_corrupted.json`, `data/clean/papers_clean_corrupted.csv` và `data/results/corruption_log.json`.

### B. Triển khai Luồng Khôi Phục & Đánh Giá 3 Trạng Thái (`src/pipelines/corruption_flow.py`)
- **Pha Corrupted**: Build ChromaDB collection `papers-corrupted`, đánh giá câu hỏi đóng băng (`test_set.json`), thu thập tín hiệu Data Observability (Quality & Freshness).
- **Pha Repaired**: Nạp lại dữ liệu thô từ Raw Snapshot `data/raw/crossref_records.json`, thực thi lại toàn bộ quy tắc `build_clean_dataframe()` (gỡ XML, lọc tóm tắt ngắn, tự động drop bài báo phi Latinh/tiếng Nga), rebuild ChromaDB collection `papers-repaired`, đánh giá câu hỏi đóng băng và kiểm tra Observability.
- **Báo cáo đối chiếu**: Tự động sinh báo cáo tổng hợp 3 cột.

---

## 2. Bảng Kết Quả Đạt Được (Comparison Results)

### Bảng 1: Chỉ Số Đánh Giá RAG (RAG Evaluation Metrics)

| Chỉ số (Metric) | Baseline (Sạch) | Corrupted (Lỗi) | Repaired (Phục hồi) | Nhận xét Chi Tiết Biến Động |
| :--- | :---: | :---: | :---: | :--- |
| **Số mẫu câu hỏi** | `10` | `10` | `10` | Đóng băng cố định trong `test_set.json` |
| **Retrieval Hit Rate** | **100.0%** | 🔻 **90.0%** | 🟢 **100.0%** | Corrupted sụt 10% do bị xóa summary và chèn nhiễu $\rightarrow$ Repaired khôi phục 100% |
| **Mean Token F1** | **0.5824** | 🔻 **0.4599** | 🟢 **0.5793** | Corrupted bị sụt giảm từ vựng trùng khớp mạnh $\rightarrow$ Repaired khôi phục về mức 0.58 chuẩn |
| **LLM Judge Accuracy** | **90.0%** | 🔻 **70.0%** | 🟢 **90.0%** | Corrupted khiến Agent trả lời sai/từ chối 3 câu $\rightarrow$ Repaired phục hồi 90% (9/10 câu đúng) |
| **Mean Judge Score** | **4.50 / 5.0** | 🔻 **3.70 / 5.0** | 🟢 **4.50 / 5.0** | Corrupted bị LLM Judge chấm điểm thấp $\rightarrow$ Repaired đạt lại mốc điểm ấn tượng 4.5/5.0 |

---

### Bảng 2: Tín Hiệu Data Quality & Observability

| Tín hiệu Observability | Baseline State | Corrupted State | Repaired State |
| :--- | :---: | :---: | :---: |
| **Quality Check Status** | 🟢 **PASSED** | 🔴 **FAILED** | 🟢 **PASSED** |
| **Completeness & Uniqueness** | 🟢 **PASS** | 🔴 **FAIL** (Duplicate & Missing ID) | 🟢 **PASS** |
| **Freshness Check (`is_fresh`)** | 🟢 **PASS** (`0` stale) | 🔴 **FAIL** (`5` stale rows) | 🟢 **PASS** (`0` stale) |
| **Tổng số bản ghi trong Index** | `23` | `25` (do trùng lặp) | `23` (loại tự động tiếng Nga) |

---

## 3. Giải Đáp Kỹ Thuật (Checkpoint C4 Q&A)

### **Câu 1: Kịch bản corruption nào gây ảnh hưởng nghiêm trọng nhất đến khả năng tìm kiếm (retrieval)? Vì sao?**
- **Trả lời**: Kịch bản **Xóa tóm tắt (Blank Summary)** và **Gây nhiễu nội dung (Add Noise / Poisoning)** là 2 kịch bản tàn phá khả năng tìm kiếm nghiêm trọng nhất.
- **Vì sao**:
  - *Blank Summary*: Khi `summary` bị xóa rỗng, `text_for_embedding` chỉ còn lại tiêu đề ngắn, làm khoảng cách Cosine giữa câu hỏi và bài báo bị đẩy xa hoàn toàn $\rightarrow$ Retriever bỏ sót tài liệu tham chiếu.
  - *Add Noise*: Khi bị chèn văn bản rác ngẫu nhiên, vector embedding của bài báo bị trôi dạt ngữ nghĩa (semantic drift), dẫn đến việc ChromaDB truy xuất nhầm bài báo khác trong Top-4.

### **Câu 2: Vì sao khi repair, chúng ta bắt buộc phải dựng lại dữ liệu từ raw snapshot (`crossref_records.json`) thay vì trực tiếp fetch lại API?**
- **Trả lời**: Có 2 lý do cốt lõi:
  1. **Tính Bất Biến và Tái Lập (Immutable Raw Snapshot & Reproducibility)**: Dữ liệu trên API bên ngoài (Crossref REST API) có thể thay đổi liên tục theo thời gian (thêm bài viết mới, sửa đổi metadata, lỗi server hoặc thay đổi schema). Việc phục hồi từ file Raw Snapshot đã lưu ở Pha 1a đảm bảo quy trình Data Pipeline mang tính deterministic (100% tái lập được kết quả) và độc lập tuyệt đối với hạ tầng bên ngoài.
  2. **Tối ưu Chi phí & Hiệu năng**: Phục hồi từ đĩa cục bộ không tiêu tốn băng thông mạng, tránh rủi ro sập API hay bị cấm IP (Rate Limiting).
