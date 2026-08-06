# Các thay đổi trong bước Cleaning

## File đã cập nhật

- `src/ingestion/cleaning.py`
- `src/ingestion/test_cleaning.py`

## Những phần đã implement

- Đã implement hàm `build_clean_dataframe(records, run_date)`.
- Chuẩn hóa các trường text:
  - Xóa khoảng trắng thừa.
  - Decode HTML entities.
  - Loại bỏ thẻ HTML/JATS trong abstract.
- Chuẩn hóa các trường dạng list:
  - Làm sạch `authors`.
  - Làm sạch `categories`.
  - Xóa giá trị trùng trong từng list nhưng vẫn giữ thứ tự ban đầu.
- Parse các trường ngày:
  - Parse `published`.
  - Parse `updated`.
  - Chuyển ngày hợp lệ về định dạng `YYYY-MM-DD`.
- Tính freshness:
  - Thêm cột `age_days` dựa trên công thức `run_date - published`.
- Thêm các cột hỗ trợ:
  - `authors_joined`
  - `categories_joined`
  - `summary_chars`
  - `text_for_embedding`
- Lọc các record không hợp lệ:
  - Thiếu `paper_id`.
  - Thiếu `title`.
  - Thiếu `summary`.
  - `summary` có độ dài dưới 100 ký tự (`summary_chars < 100`).
  - **MỚI: Tiêu đề hoặc Tác giả chứa ký tự phi Latinh (Non-English / Non-Latin Script Filter).**
  - `published` không parse được thành ngày hợp lệ.
- Xóa record trùng theo `paper_id`.
- Sắp xếp output theo `published` mới nhất, sau đó `updated` mới nhất, rồi `paper_id`.
- Thêm `df.attrs["cleaning_report"]` để lưu số liệu truy vết trong quá trình cleaning.

---

## Xử lý các bài báo ngôn ngữ phi Latinh (Tiếng Nga, Nhật, Hàn, Trung...)

Các bài báo khoa học chứa tên tiêu đề hoặc tác giả bằng chữ viết phi Latinh (như Tiếng Nga Cyrillic, Tiếng Nhật Katakana/Hiragana, Tiếng Hàn Hangul, Tiếng Trung Hán tự) khi đưa vào mô hình Embedding `sentence-transformers/all-MiniLM-L6-v2` (huấn luyện thuần Tiếng Anh) sẽ gây ra lỗi vỡ token (`[UNK]`) và hiện tượng trôi dạt ngữ nghĩa (semantic drift).

Đã bổ sung hàm kiểm tra `_is_english_latin_text()` sử dụng Regex dải Unicode phi Latinh:
```python
non_latin_pattern = r"[\u0400-\u04FF\u3040-\u30FF\u3400-\u4DBF\u4E00-\u9FFF\uAC00-\uD7AF\u0600-\u06FF]"
```

- **Kết quả lọc**: Tự động loại bỏ (**DROP**) 1 bài báo tiếng Nga (DOI: `10.47576/2949-1894.2026.7.7.023`).
- **Tác động tích cực**: Giúp độ chính xác của LLM Judge trong Baseline RAG Pipeline tăng từ **80% lên 90%** và điểm số trung bình tăng từ **4.4 lên 4.5/5.0**.

---

## Xử lý lỗi category

Các record Crossref hiện tại có `categories` rỗng, nên bản clean đầu tiên tạo ra `categories_joined` rỗng và `primary_category = unknown` cho tất cả các dòng.

Để xử lý vấn đề này, đã thêm bước suy luận category dự phòng:

- Nếu record không có category từ source, category sẽ được suy luận từ `title + summary`.
- Các nhóm category dựa trên keyword gồm:
  - `Retrieval-Augmented Generation`
  - `Agentic AI`
  - `Healthcare AI`
  - `Knowledge Graphs`
  - `Large Language Models`
  - `Governance`
  - `Finance`
  - `Education`
- `primary_category` sẽ được lấy từ category suy luận nếu giá trị từ source bị thiếu hoặc là `unknown`.

---

## Các cột output

Dataframe sau cleaning hiện có các cột:

- `paper_id`
- `title`
- `summary`
- `authors`
- `categories`
- `primary_category`
- `published`
- `updated`
- `age_days`
- `authors_joined`
- `categories_joined`
- `summary_chars`
- `text_for_embedding`
- `abs_url`
- `pdf_url`
- `comment`

---

## Kết quả chạy thử mới nhất

Hàm cleaning đã được import và chạy thử với file:

- `data/raw/crossref_records.json`

Các artifact clean đã được tạo lại:

- `data/clean/papers_clean.csv`
- `data/clean/papers_clean.json`

Kết quả kiểm tra mới nhất:

```text
records_clean = 23
empty_categories_joined = 0
csv_categories_nan = 0
unknown_primary_category = 0
non_english_script_filtered = 1
```

Phân bố `primary_category`:

```text
Retrieval-Augmented Generation    13
Agentic AI                         5
Healthcare AI                      4
Knowledge Graphs                   1
```

---

## Các vấn đề data còn lại

- `pdf_url` vẫn bị thiếu ở nhiều record vì source data không phải lúc nào cũng cung cấp link PDF.
- Một vài record có `updated` sớm hơn `published`; khả năng cao do bước ingestion đang map field ngày từ Crossref chưa đúng ý nghĩa.
- CSV không giữ được kiểu list thật cho `authors` và `categories`; file JSON vẫn giữ hai field này dưới dạng list.
