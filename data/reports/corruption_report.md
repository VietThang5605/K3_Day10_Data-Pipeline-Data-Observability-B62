# Báo Cáo Thí Nghiệm Corruption, Repair & So Sánh 3 Trạng Thái (Phase 2)

Báo cáo này tổng hợp kết quả đối chiếu hiệu năng RAG và tín hiệu Data Observability giữa 3 trạng thái hệ thống:
1. **Baseline State**: Trạng thái dữ liệu sạch chuẩn ban đầu (23 bài báo).
2. **Corrupted State**: Trạng thái dữ liệu bị giả lập lỗi có kiểm soát (Blank summary, Add noise, Stale date, Duplicates).
3. **Repaired State**: Trạng thái dữ liệu được phục hồi chuẩn hóa từ Raw Snapshot.

---

## 1. Bảng So Sánh Chỉ Số Đánh Giá RAG (RAG Evaluation Metrics)

| Chỉ số (Metric) | Baseline (Sạch) | Corrupted (Lỗi) | Repaired (Phục hồi) | Nhận xét Biến động |
| :--- | :---: | :---: | :---: | :--- |
| **Retrieval Hit Rate** | **100.0%** | **90.0%** | **100.0%** | 🔻 Corrupted sụt giảm mạnh khi bị xóa summary/thêm nhiễu $ightarrow$ 🟢 Repaired khôi phục 100% |
| **Mean Token F1** | **0.5824** | **0.4599** | **0.5793** | 🔻 Corrupted bị suy giảm trùng khớp từ vựng $ightarrow$ 🟢 Repaired khôi phục về mức chuẩn |
| **LLM Judge Accuracy** | **90.0%** | **70.0%** | **90.0%** | 🔻 Corrupted tụt giảm do Agent bị trả lời sai/từ chối $ightarrow$ 🟢 Repaired đạt 90% |
| **Mean Judge Score** | **4.50 / 5.0** | **3.70 / 5.0** | **4.50 / 5.0** | 🔻 Corrupted bị đánh giá điểm thấp $ightarrow$ 🟢 Repaired đạt điểm 4.5/5.0 |

---

## 2. Bảng So Sánh Tín Hiệu Data Quality & Observability

| Tín hiệu Observability | Baseline | Corrupted | Repaired |
| :--- | :---: | :---: | :---: |
| **Quality Check Status** | 🟢 **PASSED** | 🔴 **FAILED** | 🟢 **PASSED** |
| **Completeness & Uniqueness** | 🟢 **PASS** | 🔴 **FAIL** (Duplicate & Missing ID) | 🟢 **PASS** |
| **Freshness Status (`is_fresh`)** | 🟢 **PASS** (`0` stale) | 🔴 **FAIL** (`7` stale rows) | 🟢 **PASS** (`0` stale) |
| **Tổng số bản ghi trong index** | `23` | `25` | `23` |

---

## 3. Giải Đáp Kỹ Thuật (Checkpoint C4 Q&A)

### **Câu 1: Kịch bản corruption nào gây ảnh hưởng nghiêm trọng nhất đến khả năng tìm kiếm (retrieval)? Vì sao?**
- **Trả lời**: Kịch bản **Xóa tóm tắt (Blank Summary)** và **Gây nhiễu nội dung (Add Noise / Poisoning)** là 2 kịch bản tàn phá khả năng tìm kiếm nghiêm trọng nhất.
- **Vì sao**:
  - *Blank Summary*: Khi `summary` và `text_for_embedding` bị xóa sạch, vector embedding chỉ còn lại tiêu đề ngắn hoặc vector rỗng, làm khoảng cách Cosine giữa câu hỏi và bài báo bị đẩy xa hoàn toàn $ightarrow$ Retriever bỏ sót bài báo tham chiếu (`retrieval_hit = false`).
  - *Add Noise*: Khi bị chèn văn bản rác vô nghĩa, vector embedding của tài liệu bị trôi dạt ngữ nghĩa (semantic drift), dẫn đến việc ChromaDB truy xuất nhầm bài báo khác.

### **Câu 2: Vì sao khi repair, chúng ta bắt buộc phải dựng lại dữ liệu từ raw snapshot (`crossref_records.json`) thay vì trực tiếp fetch lại API?**
- **Trả lời**: Có 2 lý do cốt lõi:
  1. **Tính Bất Biến và Tái Lập (Immutable Raw Snapshot & Reproducibility)**: Dữ liệu trên API bên ngoài (Crossref REST API) có thể thay đổi liên tục theo thời gian (thêm bài viết mới, sửa đổi metadata, lỗi server hoặc thay đổi schema). Việc phục hồi từ file Raw Snapshot đã lưu ở Pha 1a đảm bảo quy trình Data Pipeline mang tính deterministic (100% tái lập được kết quả) và độc lập tuyệt đối với hạ tầng bên ngoài.
  2. **Tối ưu Chi phí & Hiệu năng**: Phục hồi từ đĩa cục bộ không tiêu tốn băng thông mạng, tránh rủi ro sập API hay bị cấm IP (Rate Limiting).
