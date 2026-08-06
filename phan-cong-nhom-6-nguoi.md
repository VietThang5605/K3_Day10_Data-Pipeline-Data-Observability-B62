# Phân công role nhóm 6 người

Tài liệu ghi nhớ phạm vi phụ trách, file chính, kết quả bàn giao và thứ tự phối hợp của nhóm.

## 1. Phân công công việc

| Thành viên | Phần phụ trách | File chính | Kết quả cần bàn giao |
|---|---|---|---|
| Người 1 | Ingestion từ Crossref | `src/ingestion/crossref.py` | Gọi API, retry, parse `PaperRecord`, lưu raw response và raw records |
| Người 2 | Cleaning và data modeling | `src/ingestion/cleaning.py` | Chuẩn hóa dữ liệu, tạo `text_for_embedding`, `age_days`, loại duplicate/record lỗi |
| Người 3 | Evaluation và test set | `src/evaluation/testset.py`, kiểm tra `src/evaluation/metrics.py` | Tạo câu hỏi summary/authors/date/categories, sinh `test_set.json`, kiểm tra metrics |
| Người 4 | Data observability | `src/observability/quality.py`, `src/observability/reporting.py` | Quality checks, freshness report, baseline report và comparison report |
| Người 5 | Retrieval và baseline pipeline | `src/pipelines/phase1.py`, kiểm tra `src/retrieval/` | Ghép flow end-to-end: raw → clean → embedding → evaluation → reports |
| Người 6 | Corruption, repair và comparison | `src/ingestion/corruption.py`, `src/pipelines/corruption_flow.py` | Tạo dữ liệu lỗi, rebuild index, repair từ raw, so sánh baseline/corrupted/repaired |

## 2. Thứ tự làm việc

1. Người 1 hoàn thành ingestion.
2. Người 2 dùng dữ liệu của Người 1 để hoàn thành cleaning.
3. Người 3 tạo evaluation set từ cleaned dataframe.
4. Người 4 xây quality/freshness checks độc lập theo schema của Người 2.
5. Người 5 ghép và chạy thành công baseline trước.
6. Người 6 chỉ bắt đầu corruption flow sau khi baseline chạy được.

## 3. Quy ước phối hợp

- Thống nhất schema `PaperRecord` trước khi code.
- Mỗi người làm một branch riêng, ví dụ: `feature/ingestion`, `feature/cleaning`, ...
- Không commit `.env`, API key hoặc dữ liệu quá lớn.
- Mỗi người phải ghi rõ cách chạy và artifact đầu ra.
- Người 5 chịu trách nhiệm tích hợp cuối; cả nhóm cùng kiểm tra kết quả.

## 4. Chuỗi bàn giao chính

```text
Người 1: Crossref/raw
    → Người 2: clean dataframe
    → Người 3: evaluation set
    → Người 4: quality/freshness checks
    → Người 5: baseline end-to-end
    → Người 6: corruption → repair → comparison
```

