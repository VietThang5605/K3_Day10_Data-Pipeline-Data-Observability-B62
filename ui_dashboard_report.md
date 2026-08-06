# Báo Cáo Xây Dựng Tách Biệt UI Dashboard & Streamlit Chatbot Sandbox

Báo cáo này tổng hợp chi tiết toàn bộ các nội dung công việc đã thực hiện để xây dựng hệ thống giao diện kép: **FastAPI Web Dashboard (TailwindCSS Dark Mode)** phục vụ Data Observability & Health Monitoring và **Streamlit App** phục vụ RAG Chatbot Test Sandbox.

---

## 1. Các Công Việc Đã Thực Hiện (Work Completed)

### A. Khắc Phục Dứt Điểm Lỗi Streamlit File Watcher
- Khởi tạo file cấu hình [.streamlit/config.toml](file:///Users/nguyenvietthang/Coding/VinUni/Lab/K3_Day10_Data-Pipeline-Data-Observability-B62/.streamlit/config.toml) với tham số `fileWatcherType = "none"`.
- Giải quyết triệt để lỗi tràn màn hình do Streamlit quét các submodule của thư viện `transformers`.

### B. Triển Khai Streamlit Chatbot Sandbox (`app.py`)
- Xây dựng ứng dụng Chatbot tương tác chuyên biệt tại [app.py](file:///Users/nguyenvietthang/Coding/VinUni/Lab/K3_Day10_Data-Pipeline-Data-Observability-B62/app.py).
- **Sidebar Mode Switcher (Chuyển Đổi Chế Độ Dữ Liệu)**:
  - 🟢 **Baseline Mode (Clean Data)**: Nạp ChromaDB collection `papers-baseline` (23 bài báo sạch). RAG Agent trả lời chính xác 90-100%.
  - 🔴 **Corruption Mode (Lỗi Dữ Liệu)**: Nạp ChromaDB collection `papers-corrupted` (Dữ liệu bị xóa summary / chèn nhiễu). Agent **trả lời SAI hoặc từ chối trả lời** trên một số câu hỏi đóng băng (`q1`, `q2`, `q7`).
  - 🔵 **Repaired Mode (Khôi Phục)**: Nạp ChromaDB collection `papers-repaired` (Dữ liệu đã được phục hồi từ Raw Snapshot). Agent phục hồi trả lời chính xác.
- **RAG QA Sandbox**:
  - Chọn nhanh 10 câu hỏi đóng băng từ dropdown hoặc gõ câu hỏi bất kỳ.
  - Hiển thị câu trả lời sinh tự nhiên từ `gpt-4o-mini`.
  - Hiển thị **Top-4 Thẻ Bài Báo Ngữ Cảnh (Retrieved Context Cards)** tô sáng.
  - Đối chiếu trực tiếp câu trả lời với Ground Truth reference.

### C. Triển Khai Web Dashboard Data Observability bằng TailwindCSS (`src/server.py` + `src/web/index.html`)
- Xây dựng **FastAPI Web Server** [src/server.py](file:///Users/nguyenvietthang/Coding/VinUni/Lab/K3_Day10_Data-Pipeline-Data-Observability-B62/src/server.py) phục vụ các REST API Endpoints:
  - `GET /api/observability`: Trả về dữ liệu Quality Checks & Freshness Status.
  - `GET /api/comparison`: Trả về số liệu 3 cột.
  - `GET /api/corruption-log`: Trả về 4 kịch bản gây lỗi.
  - `GET /api/papers`: Trả về 23 bài báo sạch.
- Xây dựng giao diện Web HTML5 [src/web/index.html](file:///Users/nguyenvietthang/Coding/VinUni/Lab/K3_Day10_Data-Pipeline-Data-Observability-B62/src/web/index.html) thiết kế riêng bằng **TailwindCSS Dark Mode / Glassmorphism**:
  - **4 Health Metrics Cards**: Total Records (`23`), Data Quality Status (`PASSED`), Freshness Check (`100% FRESH`), Uniqueness Check (`PASS`).
  - **3-State Comparative Matrix Table**: Bảng đối chiếu 3 cột nổi bật (Baseline vs Corrupted vs Repaired).
  - **Controlled Corruption Scenario Inspector**: Thẻ xem chi tiết các bản ghi bị xóa summary, chèn nhiễu, làm cũ ngày.
  - **Clean Papers Data Explorer**: Bảng 23 bài báo sạch kèm bộ lọc tìm kiếm.

---

## 2. Kết Quả Đạt Được (Key Deliverables)

| Thành phần UI | Công nghệ sử dụng | Cổng (Port) | Mục đích / Chức năng chính |
| :--- | :--- | :---: | :--- |
| **Data Observability Dashboard** | FastAPI + TailwindCSS HTML5 | `http://localhost:8000` | Giám sát chất lượng dữ liệu, Freshness, Bảng đối chiếu 3 cột và Nhật ký lỗi |
| **RAG Chatbot Sandbox** | Streamlit + Custom CSS | `http://localhost:8501` | Đặt câu hỏi tương tác cho RAG Agent ở 3 chế độ (Baseline / Corrupted / Repaired) |

---

## 3. Hướng Dẫn Khởi Chạy Hệ Thống UI

Chạy lệnh runner duy nhất để khởi chạy song song cả 2 giao diện Web:

```bash
# Khởi chạy hệ sinh thái Dashboard & Chatbot UI
uv run python script/run_ui.py
```

- **Observability Dashboard (TailwindCSS)**: Mở `http://localhost:8000`
- **Streamlit RAG Chatbot**: Mở `http://localhost:8501`
