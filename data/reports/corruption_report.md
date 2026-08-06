# Corruption and Repair Comparison Report

Generated at (UTC): 2026-08-06T05:22:02+00:00

## Evaluation comparison

| Metric | Baseline | Corrupted | Repaired | Corruption delta | Repair delta |
| --- | --- | --- | --- | --- | --- |
| retrieval_hit_rate | 1 | 1 | 1 | +0.0000 | +0.0000 |
| mean_token_f1 | 0.9278 | 0.7611 | 0.9278 | -0.1667 | +0.1667 |
| judge_accuracy | 0.9167 | 0.7500 | 0.9167 | -0.1667 | +0.1667 |
| mean_judge_score | 4.6667 | 4 | 4.6667 | -0.6667 | +0.6667 |

## Quality and freshness comparison

| Signal | Baseline | Corrupted | Repaired | Corrupted detail | Repaired detail |
| --- | --- | --- | --- | --- | --- |
| Quality checks | pass | fail | pass | paper_id_unique, summary_length, freshness | none |
| Freshness | fresh | stale | fresh | 2 | 0 |

## Corrupted quality details

| Check | Trạng thái | Số liệu | Diễn giải |
| --- | --- | --- | --- |
| minimum_row_count | pass | {"actual": 22, "minimum": 4} | Tập dữ liệu có đủ số hàng cho phạm vi đánh giá yêu cầu. |
| required_columns | pass | {"missing_columns": []} | Tất cả các cột bắt buộc đều hiển thị. |
| paper_id_not_null | pass | {"blank_rows": 0} | Mọi hàng đều có paper_id không trống. |
| paper_id_unique | fail | {"duplicate_rows": 1} | Tìm thấy các giá trị paper_id không trống bị trùng lặp. |
| title_not_blank | pass | {"blank_rows": 0} | Mọi hàng đều có tiêu đề không trống. |
| summary_length | fail | {"blank_rows": 2, "minimum_chars": 30, "too_short_rows": 0} | Một hoặc nhiều tóm tắt bị trống hoặc ngắn hơn độ dài tối thiểu. |
| published_date_valid | pass | {"invalid_rows": 0, "missing_rows": 0} | Tất cả các giá trị published đều là ngày hợp lệ. |
| freshness | fail | {"freshness_threshold_days": 180, "future_dated_rows": 0, "invalid_age_days": 0, "missing_age_days": 0, "stale_rows": 2} | Một hoặc nhiều hàng cũ hơn ngưỡng freshness được cấu hình. |

## Repaired quality details

| Check | Trạng thái | Số liệu | Diễn giải |
| --- | --- | --- | --- |
| minimum_row_count | pass | {"actual": 24, "minimum": 4} | Tập dữ liệu có đủ số hàng cho phạm vi đánh giá yêu cầu. |
| required_columns | pass | {"missing_columns": []} | Tất cả các cột bắt buộc đều hiển thị. |
| paper_id_not_null | pass | {"blank_rows": 0} | Mọi hàng đều có paper_id không trống. |
| paper_id_unique | pass | {"duplicate_rows": 0} | Các giá trị paper_id là duy nhất. |
| title_not_blank | pass | {"blank_rows": 0} | Mọi hàng đều có tiêu đề không trống. |
| summary_length | pass | {"blank_rows": 0, "minimum_chars": 30, "too_short_rows": 0} | Tất cả tóm tắt đáp ứng độ dài tối thiểu. |
| published_date_valid | pass | {"invalid_rows": 0, "missing_rows": 0} | Tất cả các giá trị published đều là ngày hợp lệ. |
| freshness | pass | {"freshness_threshold_days": 180, "future_dated_rows": 0, "invalid_age_days": 0, "missing_age_days": 0, "stale_rows": 0} | Tất cả các hàng có giá trị age_days hợp lệ nằm trong ngưỡng cấu hình. |

## Corrupted freshness details

| Trường | Giá trị |
| --- | --- |
| status | stale |
| is_fresh | fail |
| freshness_threshold_days | 180 |
| total_rows | 22 |
| fresh_rows | 20 |
| stale_rows | 2 |
| missing_age_days | 0 |
| invalid_age_days | 0 |
| future_dated_rows | 0 |
| latest_published | 2026-08-01 |
| oldest_published | 2000-01-01 |
| missing_published | 0 |
| invalid_published | 0 |
| message | Một hoặc nhiều hàng cũ hơn ngưỡng freshness được cấu hình. |

## Repaired freshness details

| Trường | Giá trị |
| --- | --- |
| status | fresh |
| is_fresh | pass |
| freshness_threshold_days | 180 |
| total_rows | 24 |
| fresh_rows | 24 |
| stale_rows | 0 |
| missing_age_days | 0 |
| invalid_age_days | 0 |
| future_dated_rows | 0 |
| latest_published | 2026-08-01 |
| oldest_published | 2026-02-12 |
| missing_published | 0 |
| invalid_published | 0 |
| message | Tất cả các hàng có giá trị age_days hợp lệ nằm trong ngưỡng cấu hình. |

## Evidence-based observations

- `retrieval_hit_rate` không thay đổi giữa baseline và corrupted.
- `retrieval_hit_rate` repaired không gần baseline hơn so với corrupted.
- `mean_token_f1` giảm 0.1667 sau corruption (thay đổi quan sát được).
- `mean_token_f1` repaired gần baseline hơn so với corrupted.
- `judge_accuracy` giảm 0.1667 sau corruption (thay đổi quan sát được).
- `judge_accuracy` repaired gần baseline hơn so với corrupted.
- `mean_judge_score` giảm 0.6667 sau corruption (thay đổi quan sát được).
- `mean_judge_score` repaired gần baseline hơn so với corrupted.
- Các thay đổi trên là đối chiếu artifact; chỉ kết luận quan hệ nhân quả khi corruption log và answers truy vết được cùng xác nhận.
- Quality status: corrupted=fail, repaired=pass; freshness: corrupted=stale, repaired=fresh.
