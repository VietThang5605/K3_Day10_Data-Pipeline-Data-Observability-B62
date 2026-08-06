# Các thay đổi trong bước Cleaning

## File đã cập nhật

- `src/ingestion/cleaning.py`

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
  - `published` không hợp lệ.
- Drop duplicate theo `paper_id`.
- Sort output theo `published` mới nhất, sau đó `updated` mới nhất, rồi `paper_id`.
- Lưu count truy vết trong `df.attrs["cleaning_report"]`.

## Xử lý category rỗng

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

## Kết quả kiểm tra gần nhất

Khi chạy với `data/raw/crossref_records.json`:

```text
records_in = 24
records_clean = 23
non_latin_record = 1
empty_categories_joined = 0
csv_categories_nan = 0
rows_title_contains_cyrillic = 0
rows_summary_contains_cyrillic = 0
rows_text_for_embedding_contains_cyrillic = 0
```

Record bị drop:

```text
10.47576/2949-1894.2026.7.7.023
```

Phân bố `primary_category` sau clean:

```text
Retrieval-Augmented Generation    13
Agentic AI                         5
Healthcare AI                      4
Knowledge Graphs                   1
```

## Ghi chú còn lại

- `pdf_url` vẫn có thể thiếu vì Crossref không luôn cung cấp link PDF.
- Một số record có thể có `updated` sớm hơn `published`; vấn đề này nên kiểm tra tiếp ở bước ingestion.
- CSV không giữ kiểu list thật cho `authors` và `categories`; JSON giữ đúng dạng list.
