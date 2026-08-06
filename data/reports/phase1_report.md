# Phase 1 Baseline Report

Generated at (UTC): 2026-08-06T05:02:48+00:00

## Source summary

| Trường | Giá trị |
| --- | --- |
| source | Crossref REST API |
| load_mode | raw snapshot |
| query | agentic retrieval augmented generation large language model |
| filter | from-pub-date:2026-02-07,has-abstract:true |
| raw_records | 24 |
| clean_records | 24 |
| cleaning_report | {"dropped_duplicates": 0, "filtered": {"invalid_published": 0, "missing_paper_id": 0, "missing_summary": 0, "missing_title": 0}, "input_records": 24, "kept_records": 24} |
| embedding_model | sentence-transformers/all-MiniLM-L6-v2 |
| collection | papers-baseline |
| top_k | 4 |

## Evaluation metrics

| Metric | Value |
| --- | --- |
| retrieval_hit_rate | 1 |
| mean_token_f1 | 0.9278 |
| judge_accuracy | 0.9167 |
| mean_judge_score | 4.6667 |
| samples | 12 |

## Data quality

| Overall status | Failed checks | Rows |
| --- | --- | --- |
| pass | none | 24 |

| Check | Trạng thái | Số liệu | Diễn giải |
| --- | --- | --- | --- |
| minimum_row_count | pass | {"actual": 24, "minimum": 4} | Dataset has enough rows for the required evaluation coverage. |
| required_columns | pass | {"missing_columns": []} | All required columns are present. |
| paper_id_not_null | pass | {"blank_rows": 0} | Every row has a non-blank paper_id. |
| paper_id_unique | pass | {"duplicate_rows": 0} | paper_id values are unique. |
| title_not_blank | pass | {"blank_rows": 0} | Every row has a non-blank title. |
| summary_length | pass | {"blank_rows": 0, "minimum_chars": 30, "too_short_rows": 0} | All summaries meet the minimum length. |
| published_date_valid | pass | {"invalid_rows": 0, "missing_rows": 0} | All published values are parseable dates. |
| freshness | pass | {"freshness_threshold_days": 180, "future_dated_rows": 0, "invalid_age_days": 0, "missing_age_days": 0, "stale_rows": 0} | All rows have valid age_days values within the configured threshold. |

## Freshness

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
| message | All rows have valid age_days values within the configured threshold. |

## Optional Ragas result

| Trường | Giá trị |
| --- | --- |
| skipped | Set RUN_RAGAS=1 to enable the slower Ragas pass. |

## Limitations and signals

- Ragas chưa chạy: Set RUN_RAGAS=1 to enable the slower Ragas pass.
