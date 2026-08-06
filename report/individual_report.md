# Individual Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
| --- | --- |
| Họ và tên | [Họ và tên] |
| MSSV | [MSSV] |
| Khóa/Lớp | [Khóa/Lớp] |
| Tên nhóm | [Tên hoặc mã nhóm] |
| Vai trò chính | Người 4 — Data observability và reporting |
| Repository | [Đường dẫn repository] |
| Ngày hoàn thành | [YYYY-MM-DD] |

## 2. Vai trò và phạm vi công việc

Tôi phụ trách lớp quan sát dữ liệu (data observability) cho pipeline RAG: kiểm tra chất lượng dataframe, theo dõi độ tươi mới của dữ liệu và sinh các báo cáo Markdown dựa trên artifact thực tế. Phần việc được triển khai ở commit `27d356a` trên nhánh phần 4.

| Deliverable | File/hàm phụ trách | Input | Output | Trạng thái |
| --- | --- | --- | --- | --- |
| Data quality checks | `src/observability/quality.py` — `run_data_quality_checks` | Clean/corrupted/repaired dataframe và `Settings` | JSON quality report theo từng trạng thái | Đã triển khai ở `27d356a`; cần khôi phục vào `main` |
| Freshness monitoring | `src/observability/quality.py` — `build_freshness_report` | Dataframe, threshold freshness và đường dẫn output | JSON freshness report | Đã triển khai ở `27d356a`; cần khôi phục vào `main` |
| Baseline report | `src/observability/reporting.py` — `generate_phase1_report` | Source summary, metrics, quality, freshness | `phase1_report.md` | Đã triển khai ở `27d356a`; cần khôi phục vào `main` |
| Comparison report | `src/observability/reporting.py` — `generate_corruption_report` | Metrics và observability payload của baseline/corrupted/repaired | `corruption_report.md` | Đã triển khai ở `27d356a`; cần khôi phục vào `main` |
| Unit test | `src/observability/test_quality_reporting.py` | Dataframe mẫu sạch/lỗi và payload metrics | Kiểm tra JSON/Markdown được tạo đúng | Đã viết; hiện phát hiện regression trên `main` |

Phần observability phụ thuộc vào dataframe do cleaning tạo ra và được pipeline baseline/corruption gọi sau khi evaluation hoàn tất. Module này không tự fetch hoặc sửa raw data.

## 3. Kết quả bàn giao

| Nhiệm vụ | Kết quả kỹ thuật | Cách xác minh |
| --- | --- | --- |
| Quality checks | Kiểm tra số dòng tối thiểu, schema bắt buộc, `paper_id` không rỗng/không trùng, title, summary, ngày xuất bản và freshness | Xem implementation tại `git show 27d356a:src/observability/quality.py` |
| Freshness report | Ghi `latest_published`, `oldest_published`, `stale_rows`, `total_rows`, `is_fresh` cùng các dấu hiệu age/day lỗi | Cùng module `quality.py` tại commit trên |
| Baseline report | Render source summary, bốn metrics chính, Ragas (nếu có), quality checks, freshness và limitation | Xem `git show 27d356a:src/observability/reporting.py` |
| Comparison report | Hiển thị baseline/corrupted/repaired, delta metrics và quality/freshness; không tự suy diễn quan hệ nhân quả khi thiếu artifact | Cùng module `reporting.py` tại commit trên |
| Test | Hai test cho dữ liệu sạch/lỗi và nội dung Markdown | `src/observability/test_quality_reporting.py` |

Chưa có artifact baseline/corrupted/repaired thực tế trong `data/quality/` hoặc `data/reports/`, vì baseline integration và corruption flow chưa được chạy hoàn chỉnh trên nhánh hiện tại. Do đó báo cáo này không điền các metric hay kết luận thực nghiệm chưa có bằng chứng.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Pipeline không thể chỉ dựa vào retrieval metrics để phát hiện lỗi dữ liệu. Cần có tín hiệu độc lập cho completeness, uniqueness, validity và freshness, đồng thời report phải phản ánh đúng payload đầu vào thay vì tự điền số liệu lạc quan. Khi corruption xảy ra, các report này là bằng chứng để đối chiếu chất lượng dữ liệu với thay đổi metrics.

### Cách triển khai

`run_data_quality_checks` nhận dataframe ở bất kỳ trạng thái nào và tạo payload có danh sách checks, chi tiết số lượng lỗi, threshold và `overall_passed`. Các check chính gồm:

- Số dòng tối thiểu phục vụ bốn loại câu hỏi evaluation.
- Sự hiện diện của các cột bắt buộc: `paper_id`, `title`, `summary`, `published`, `age_days`.
- `paper_id` không rỗng và unique; title không rỗng.
- Summary không rỗng và đạt độ dài tối thiểu.
- `published` parse được; `age_days` có giá trị hợp lệ, không là ngày tương lai và không vượt `settings.freshness_threshold_days`.

Thay vì ném exception khi thiếu cột, hàm trả về check thất bại có chi tiết lỗi. Điều này giúp corrupted artifact vẫn tạo được bằng chứng chẩn đoán.

`build_freshness_report` dùng `age_days` do cleaning tính theo `run_date` làm nguồn sự thật. Cách này tránh lấy thời gian hiện tại để tính lại tuổi dữ liệu, nhờ đó cùng một raw snapshot cho cùng kết quả khi chạy lại. Các ngày `published` chỉ được dùng để ghi bằng chứng bài mới nhất/cũ nhất.

Hai hàm report nhận dữ liệu đã được pipeline tạo sẵn. `generate_phase1_report` trình bày source summary, bốn metrics chính (`retrieval_hit_rate`, `mean_token_f1`, `judge_accuracy`, `mean_judge_score`), Ragas, quality, freshness và limitation. `generate_corruption_report` so sánh ba trạng thái, tự tính delta từ payload thực tế, đồng thời chỉ mô tả thay đổi quan sát được; kết luận nhân quả vẫn cần corruption log và answer artifact xác nhận.

### Input, output và contract

| Thành phần | Mô tả |
| --- | --- |
| Input quality/freshness | Dataframe có ít nhất `paper_id`, `title`, `summary`, `published`, `age_days`; `Settings` cung cấp `max_results`, freshness threshold và output paths |
| Output quality | `<report_name>_quality_report.json` trong `settings.paths.quality_dir`, gồm checks, threshold, tổng hợp pass/fail |
| Output freshness | JSON chứa `latest_published`, `oldest_published`, `stale_rows`, `total_rows`, `is_fresh` và các giá trị invalid/missing nếu có |
| Input reporting | Source summary, metrics JSON và quality/freshness payload do pipeline tạo |
| Output reporting | Markdown baseline tại `data/reports/phase1_report.md` và comparison tại `data/reports/corruption_report.md` |
| Module phụ thuộc | `core.config`, `core.utils`, cleaning dataframe contract và evaluation metrics |
| Module dùng output | `pipelines/phase1.py`, `pipelines/corruption_flow.py` và người review artifact |

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Có thể tính freshness bằng `datetime.now() - published`, hoặc dùng `age_days` đã được cleaning tính cho snapshot.
- **Các phương án:** Tính lại theo wall-clock time; hoặc coi `age_days` là nguồn sự thật và báo riêng giá trị thiếu/sai.
- **Phương án đã chọn:** Dùng `age_days` làm nguồn sự thật trong observability.
- **Lý do:** Raw snapshot cần reproducible. Tính lại theo thời gian thực sẽ làm cùng dữ liệu bị đổi trạng thái freshness chỉ vì ngày chạy khác nhau.
- **Bằng chứng trong thiết kế:** Payload freshness phân tách `stale_rows`, `missing_age_days`, `invalid_age_days`, `future_dated_rows` và `is_fresh`, không biến dữ liệu lỗi thành một age giả.

## 6. Lỗi hoặc blocker đã phát hiện

- **Triệu chứng:** Trên nhánh `main` hiện tại, lệnh test observability báo `KeyError: 'overall_passed'` và report test không tìm thấy chuỗi `retrieval_hit_rate`.
- **Lệnh tái hiện:**

```bash
python -m unittest discover -s src/observability -t src -p test_quality_reporting.py
```

- **Nguyên nhân gốc:** Implementation đã có ở commit `27d356a`, nhưng source tại `main` hiện đã bị thay bằng phiên bản cũ của `src/observability/quality.py` và `src/observability/reporting.py`. Vì vậy schema output hiện tại không khớp unit test và report có các số liệu/nhận định hard-code.
- **Phạm vi ảnh hưởng:** Quality report, freshness report và cả baseline/comparison Markdown report không đạt contract đã thiết kế; không nên chạy end-to-end để tạo artifact trước khi đồng bộ lại code.
- **Bước tiếp theo:** Khôi phục hoặc reconcile hai file observability từ commit `27d356a`, sau đó chạy lại unit test và pipeline integration. Trong phạm vi cập nhật báo cáo này, tôi không tự sửa source code observability.
- **Bài học:** Test contract phải được chạy sau merge; merge thành công về Git không đồng nghĩa output schema và report semantics vẫn đúng.

## 7. Hiểu biết về luồng end-to-end

1. Crossref được fetch và lưu raw snapshot; cleaning chuẩn hóa thành dataframe, tạo `text_for_embedding` và `age_days`; embedding tạo vector và ChromaDB index phục vụ retrieval.
2. Evaluation set chứa câu hỏi, ground truth và `ground_truth_doc_ids`. Retrieval hit rate kiểm tra document đúng có trong kết quả; token F1/judge metric đo câu trả lời so với ground truth.
3. Quality checks đánh giá tính hợp lệ/toàn vẹn của dataframe. Freshness monitoring tập trung vào độ cũ của dữ liệu qua `age_days` và ngưỡng cấu hình.
4. Baseline, corrupted và repaired phải dùng cùng test set để mọi chênh lệch metric có thể quy cho trạng thái dữ liệu/index thay vì do thay đổi câu hỏi hoặc ground truth.
5. Repair chỉ được coi là thành công khi dataset được dựng lại từ raw snapshot, có artifact riêng, quality/freshness cải thiện và metrics được đối chiếu với baseline/corrupted trên cùng test set.

## 8. Phân tích kết quả

### Metrics và tín hiệu hiện có

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét |
| --- | ---: | ---: | ---: | --- |
| `retrieval_hit_rate` | Chưa có artifact | Chưa có artifact | Chưa có artifact | Không suy diễn số liệu |
| `mean_token_f1` | Chưa có artifact | Chưa có artifact | Chưa có artifact | Không suy diễn số liệu |
| `judge_accuracy` | Chưa có artifact | Chưa có artifact | Chưa có artifact | Không suy diễn số liệu |
| `mean_judge_score` | Chưa có artifact | Chưa có artifact | Chưa có artifact | Không suy diễn số liệu |
| Quality checks | Chưa tạo JSON thực tế | Chưa tạo JSON thực tế | Chưa tạo JSON thực tế | Chờ khôi phục code và chạy pipeline |
| Freshness status | Chưa tạo JSON thực tế | Chưa tạo JSON thực tế | Chưa tạo JSON thực tế | Chờ khôi phục code và chạy pipeline |

Hiện chưa thể hoàn thành chuỗi “corruption → quality/freshness signal → metric thay đổi” bằng số liệu thật. Bất kỳ khẳng định rằng corrupted giảm metric hoặc repaired phục hồi metric đều phải chờ `corruption_log.json`, answers và metrics artifacts được tạo lại.

## 9. Điều học được và hướng cải thiện

1. Observability cần dữ liệu đầu vào ổn định và contract rõ ràng; chỉ một thay đổi schema trong merge cũng có thể làm report sai nghĩa.
2. Freshness phải tách “stale” khỏi “không xác định” để không đánh đồng record thiếu/sai ngày với record cũ.
3. Report phải hiển thị dữ liệu thiếu hoặc check fail thay vì điền số mặc định, vì report chính là artifact phục vụ audit.

Nếu có thêm thời gian, tôi sẽ bổ sung contract test ở mức pipeline để phát hiện ngay khi `quality.py`, `reporting.py` và pipeline caller không còn dùng cùng schema; đồng thời thêm test cho missing column, giá trị `age_days` không parse được và ngày tương lai.

## 10. Cam kết của thành viên

- [ ] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [ ] Tôi có thể giải thích luồng end-to-end, không chỉ module observability.
- [ ] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [ ] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [ ] Báo cáo không chứa `.env`, API key, token hoặc secret.

**Họ và tên:** [Họ và tên]
**Ngày xác nhận:** [YYYY-MM-DD]
