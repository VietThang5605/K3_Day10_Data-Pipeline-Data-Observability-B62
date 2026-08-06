# Báo Cáo Tổng Hợp Module Data Ingestion (Crossref API)

Tài liệu này tổng hợp toàn bộ công việc đã thực hiện, kết quả đạt được và các lưu ý kỹ thuật đối với module **Ingestion** (thu thập dữ liệu từ Crossref API) thuộc dự án RAG Data Pipeline & Observability.

---

## 1. Các công việc đã thực hiện

### 1.1. Tích hợp Crossref REST API & Cấu hình Polite Pool
- Xây dựng request gửi đến endpoint chính thức của Crossref: `https://api.crossref.org/works`.
- Cấu hình các query parameter từ `Settings`:
  - `query`: Từ khóa tìm kiếm bài báo (`"agentic retrieval augmented generation large language model"`).
  - `filter`: Bộ lọc bài báo có abstract và khoảng thời gian xuất bản (`"from-pub-date:...,has-abstract:true"`).
  - `rows`: Số lượng kết quả tối đa (`24`).
- **Cấu hình Crossref Polite Pool**: Đưa địa chỉ email `26ai.thangnv@vinuni.edu.vn` vào Header `User-Agent` (`DataPipelineLab/1.0 (mailto:26ai.thangnv@vinuni.edu.vn)`). Điều này giúp request được đưa vào hàng đợi ưu tiên của Crossref, tránh bị giới hạn rate limit quá mức.

### 1.2. Cơ chế Retry & Exponential Backoff
- Cài đặt vòng lặp thử lại (retry) tự động lên tới **5 lần** khi gặp các sự cố mạng tạm thời:
  - Mã lỗi HTTP `429` (Too Many Requests).
  - Mã lỗi HTTP `503` (Service Unavailable).
  - Lỗi kết nối / timeout mạng (`requests.RequestException`).
- Thời gian chờ tăng dần theo cấp số nhân (Exponential Backoff): bắt đầu từ **1.0 giây** và nhân đôi sau mỗi lần thất bại (1s $\rightarrow$ 2s $\rightarrow$ 4s $\rightarrow$ 8s).

### 1.3. Phân tích cú pháp (Parsing) & Lọc dữ liệu thô
- Triển khai hàm `parse_crossref_payload` trong [crossref.py](file:///Users/nguyenvietthang/Coding/VinUni/Lab/K3_Day10_Data-Pipeline-Data-Observability-B62/src/ingestion/crossref.py):
  - **Lọc dữ liệu**: Bắt buộc bài báo phải chứa đồng thời `title` (tiêu đề không rỗng) và `summary` (tóm tắt `abstract` hoặc `description` không rỗng).
  - **Trích xuất tác giả**: Duyệt danh sách `author` và kết hợp `given` + `family` thành tên đầy đủ.
  - **Trích xuất ngày tháng**: Viết hàm helper `parse_date` để chuyển đổi mảng `date-parts` của Crossref (`[YYYY, MM, DD]`) thành chuỗi chuẩn `"YYYY-MM-DD"`.
  - **Trích xuất URL**: Lấy link DOI (`URL`) và tìm đường dẫn PDF trực tiếp từ mảng `link` (có `content-type == "application/pdf"`).
  - **Ánh xạ Schema**: Đưa toàn bộ về cấu trúc dataclass `PaperRecord`.

### 1.4. Lưu trữ dữ liệu hai cấp (Artifact Persistence)
- **Dạng 1 (Raw Response)**: Lưu nguyên bản HTTP JSON response từ API vào `data/raw/crossref_response.json` để phục vụ audit nguồn.
- **Dạng 2 (Raw Records)**: Chuyển đổi danh sách đối tượng `PaperRecord` thành JSON phẳng và lưu tại `data/raw/crossref_records.json`.
- Triển khai hàm `load_raw_records` để đọc và deserialize dữ liệu từ file JSON trở lại thành các đối tượng `PaperRecord`.

### 1.5. Cài đặt Unit Test
- Viết bộ test tự động tại [test_crossref.py](file:///Users/nguyenvietthang/Coding/VinUni/Lab/K3_Day10_Data-Pipeline-Data-Observability-B62/src/ingestion/test_crossref.py) sử dụng module `unittest` và `unittest.mock`:
  - Test tính chính xác của hàm parse dữ liệu.
  - Test giả lập lỗi HTTP 429 để xác nhận cơ chế retry & backoff hoạt động đúng.
  - Test ghi và đọc file JSON trong môi trường giả lập (`tempfile`).

---

## 2. Kết quả đạt được

1. **Kết quả Unit Test**:
   - Tất cả các test case đều vượt qua 100%:
     ```text
     Crossref API returned temporary status 429. Retrying in 1.0 seconds...
     ..
     ----------------------------------------------------------------------
     Ran 2 tests in 0.001s

     OK
     ```

2. **Dữ liệu thực tế đã thu thập**:
   - [crossref_response.json](file:///Users/nguyenvietthang/Coding/VinUni/Lab/K3_Day10_Data-Pipeline-Data-Observability-B62/data/raw/crossref_response.json): Dung lượng **~232 KB** (chứa toàn bộ HTTP payload thô).
   - [crossref_records.json](file:///Users/nguyenvietthang/Coding/VinUni/Lab/K3_Day10_Data-Pipeline-Data-Observability-B62/data/raw/crossref_records.json): Dung lượng **~59 KB**, chứa đúng **24 bản ghi** bài báo đã được parse sạch sẽ theo schema `PaperRecord`.

---

## 3. Các lưu ý kỹ thuật quan trọng (Notes & Observations)

1. **Giữ nguyên thẻ JATS XML trong Ingestion**:
   - Ở bước này, các thẻ XML dạng `<jats:p>`, `<jats:italic>` nằm trong tóm tắt được **giữ nguyên bản** nhằm đảm bảo nguyên tắc giữ liệu gốc không bị biến đổi ở tầng Ingestion. Việc gỡ bỏ các thẻ XML này sẽ do module **Cleaning** chịu trách nhiệm.

2. **Hiện tượng `primary_category == "unknown"`**:
   - Trong kết quả trả về từ Crossref API đối với 24 bài báo này, trường `subject` ở cấp bài viết hoàn toàn không tồn tại (0/24 bài báo có `subject`). Do đó `categories` bị rỗng `[]` và `primary_category` nhận giá trị mặc định `"unknown"`. Đây là hiện tượng bình thường của Crossref API và sẽ được xử lý phân loại lại ở bước Cleaning.

3. **Dữ liệu đa ngôn ngữ / Song ngữ**:
   - 100% các bài báo đều chứa nội dung tóm tắt tiếng Anh (hoặc toàn bộ là tiếng Anh, hoặc có đoạn dịch tiếng Anh đi kèm đối với bài báo tiếng Nga). Bước Cleaning sẽ đảm nhận việc trích xuất riêng phần văn bản tiếng Anh để tối ưu cho mô hình Embedding.

4. **Nguyên tắc thiết kế (Separation of Concerns)**:
   - Module Ingestion chỉ tập trung vào việc giao tiếp với external API, xử lý lỗi mạng và đưa dữ liệu về dạng Schema thống nhất (`PaperRecord`). Điều này giúp Data Pipeline độc lập với nguồn cung cấp dữ liệu.
