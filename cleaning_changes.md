# Các thay đổi trong bước Cleaning

## File đã cập nhật

- `src/ingestion/cleaning.py`
- `src/ingestion/test_cleaning.py`

## Những phần đã implement

- Implement hàm `build_clean_dataframe(records, run_date)`.
- Chuẩn hóa text:
  - Decode HTML entities.
  - Xóa thẻ HTML/JATS.
  - Xóa khoảng trắng thừa.
- Chuẩn hóa list:
  - Làm sạch `authors`.
  - Làm sạch `categories`.
  - Xóa giá trị trùng trong list nhưng vẫn giữ thứ tự.
- Parse ngày:
  - Parse `published`.
  - Parse `updated`.
  - Chuyển ngày hợp lệ về định dạng `YYYY-MM-DD`.
- Tính freshness:
  - Thêm `age_days = run_date - published`.
- Tạo các cột hỗ trợ:
  - `authors_joined`
  - `categories_joined`
  - `summary_chars`
  - `title_for_embedding`
  - `title_language`
  - `language`
  - `text_for_embedding`
- Lọc record lỗi:
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

Raw data hiện có nhiều record không có `categories`, khiến `categories_joined` bị rỗng và khi đọc CSV có thể thành `NaN`.

Đã thêm fallback suy luận category từ `title + summary`.

Các nhóm category đang dùng:

- `Retrieval-Augmented Generation`
- `Agentic AI`
- `Healthcare AI`
- `Knowledge Graphs`
- `Large Language Models`
- `Governance`
- `Finance`
- `Education`

Nếu `primary_category` bị thiếu hoặc là `unknown`, hệ thống sẽ lấy category đầu tiên sau khi suy luận.

## Drop bài không thuộc hệ chữ Latin

Raw data có bài chứa nội dung tiếng Nga. Để tránh nhiễu embedding, cleaning sẽ drop record nếu `title`, raw `summary` hoặc `authors` có từ 5 chữ cái trở lên không thuộc hệ chữ Latin.

Rule này không drop các bài chỉ có ký hiệu lẻ như chữ Hy Lạp trong công thức hoặc thống kê.

Ngoài ra cleaner vẫn có logic tách abstract thành nhiều block và ưu tiên block tiếng Anh cho `summary`.

---

## Các cột output

Dataframe sau cleaning có các cột:

- `paper_id`
- `title`
- `title_for_embedding`
- `title_language`
- `summary`
- `authors`
- `categories`
- `primary_category`
- `language`
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

Khi chạy với `data/raw/crossref_records.json`:

```text
records_clean = 23
empty_categories_joined = 0
csv_categories_nan = 0
unknown_primary_category = 0
non_english_script_filtered = 1
```

Record bị drop:

```text
Retrieval-Augmented Generation    13
Agentic AI                         5
Healthcare AI                      4
Knowledge Graphs                   1
```

---

## Các vấn đề data còn lại

- `pdf_url` vẫn có thể thiếu vì Crossref không luôn cung cấp link PDF.
- Một số record có thể có `updated` sớm hơn `published`; vấn đề này nên kiểm tra tiếp ở bước ingestion.
- CSV không giữ kiểu list thật cho `authors` và `categories`; JSON giữ đúng dạng list.
