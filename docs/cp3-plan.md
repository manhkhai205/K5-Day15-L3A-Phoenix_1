# Kế hoạch & Chia việc CP3 → CP4 — Nhóm Phoenix_1 (VinPlanner)

> **Mốc CP3:** **10:00 Thứ Bảy 28/11** (**4 điểm** · Đội trưởng **Nguyễn Viết Mạnh Khải** — mã `2A202603664` nộp form).
> **Mục tiêu kép:** Hoàn tất đủ **6 hạng mục bắt buộc CP3** (AI Gemini thật · 20–30 câu thử · Lượt 1 + `score` · Video 30 giây · Bằng chứng pain ≥2 nguồn · `spec.md` §0–§7) **VÀ** hoàn thiện web **VinPlanner** để quay video CP3.

> [!WARNING]
> **CHỐT CHẶN AN TOÀN (KHÔNG ĐƯỢC QUÊN):**
> 1. Dù nhóm ưu tiên dồn sức làm web ngay tối nay để quay video CP3, **09:00 sáng Thứ Bảy 28/11 BẮT BUỘC Khải chạy `python run.py eval`, Quang chấm đủ cột `pass` và chạy `python run.py score eval/run-1.csv` qua `answer(text)`** dù web đã xong hay chưa (thiếu Lượt 1 = 0 điểm CP3).
> 2. **08:30 sáng Thứ Bảy 28/11**, nếu giao diện web vẫn chưa chạy thông luồng với Gemini thật → lập tức chuyển sang quay **video 30 giây trên CLI (`python run.py`)** làm bản nộp CP3 đúng hạn, rồi hoàn thiện web tiếp cho Demo CP4 lúc 14:30.
> 3. **Tuyệt đối KHÔNG sửa** `eval/metric_spec.yaml` và chuẩn "đạt" đã chốt ở `spec.md` §7.

---

## 1. Bảng phân công Task CP3 (`T1` – `T13`)

| ID | Việc cần làm | Người phụ trách | Bắt đầu – Hạn | Phụ thuộc | Xong khi (Definition of Done) | File chạm tới |
|---|---|---|---|---|---|---|
| **T1** | Điền `.env` với `MODEL_PROVIDER=gemini` (model rẻ để build/eval), test `python run.py eval --try` | **Khải** | 20:45 – **21:30** *(27/11)* | — | Thấy *"Nối model được"*, `tokens_in > 0`, `tokens_out > 0`; không commit `.env` | `.env` *(local)*, `codebase/ai.py` *(nếu cần chỉnh)* |
| **T2** | Tách `plan_day()` trả JSON có cấu trúc (`PlanResponse`), giữ `answer(text)` gọi lõi; sửa guardrail chỉ chặn ý định đặt/thanh toán; kiểm lại 14 câu hiện có | **Khải** | 21:30 – **23:00** *(27/11)* | T1 | `python run.py eval --try` chạy với Gemini thật đạt `0` lỗi parse JSON; `B11`, `B12` từ chối đúng | `codebase/agent.py`, `codebase/tools.py` *(thêm `tra_khach_san`)* |
| **T3** | Viết `codebase/api.py` (FastAPI) đủ 8 endpoint + phiên/undo stack + luật xoá mốc + kiểm `kiem_lich_trinh`; cập nhật `requirements.txt` (`fastapi`, `uvicorn`) | **Khải** | 23:00 – **00:30** *(28/11)* | T2, T8 | `uvicorn codebase.api:app --port 8000` chạy đủ 8 endpoint qua Swagger `/docs` | `codebase/api.py`, `requirements.txt` |
| **T4** | Bổ sung toạ độ `x, y` (0–100) cho điểm chơi/show và `polygon`/`bbox` 6 phân khu vào `data/`; cập nhật `data/DATA_CARD.md` | **Đức Anh** | 20:45 – **21:45** *(27/11)* | — | Mọi item trong `attractions.json`, `shows.json` có `x, y`; `DATA_CARD.md` ghi rõ nhãn `synthetic` | `data/park_zones.json`, `data/attractions.json`, `data/shows.json`, `data/DATA_CARD.md` |
| **T5** | Khởi tạo `web/` (React + Vite, proxy `/api` → `:8000`), dùng `web/src/mock/plan.json` dựng `ChatPanel` (`MessageList`, `HotelCards`, `StepsDrawer`, nút `Hoàn tác`) | **Đức Anh** | 21:45 – **23:30** *(27/11)* | T4 *(+ schema từ Architecture)* | Mở `localhost:5173` thấy cột chat trái khớp wireframe, chọn được thẻ khách sạn mock | `web/` |
| **T6** | Dựng cột phải: `DayTabs`, `DaySummaryBar`, `ParkMapSvg` (6 khu, 4 màu, nối tuyến), `TimelineStrip`, `ItemDetailModal` (media/swap/xoá), `CheckModal` (`0 vi phạm · N lưu ý`), nút Lưu lịch + nối API thật | **Đức Anh** | 23:30 – **01:00** *(28/11)* *(hoàn thiện nối API sáng sớm nếu cần)* | T3, T5 | Bấm chọn khách sạn → vẽ bản đồ SVG 3 ngày, bấm mốc đổi/xoá/hoàn tác chạy thật qua `:8000` | `web/` |
| **T7** | Phỏng vấn thật **≥3 người ngoài nhóm** (`P1.md`–`P3.md`, ưu tiên S03/S05/S09), đẩy khảo sát lên **≥20 phiếu** (`results.csv`), chốt `evidence/summary.md` | **Dũng** | 20:45 – **09:00** *(28/11)* | — | ≥20 phiếu khảo sát + `P1–P3` có trích dẫn thật (ẩn danh), `summary.md` tích đủ 2 nguồn đạt ngưỡng | `evidence/interviews/P1.md..P3.md`, `evidence/survey/results.csv`, `evidence/summary.md` |
| **T8** | Tạo `data/hotels.json` (3–5 khách sạn tên thật gần cổng, giá có link nguồn, `rooms_left` `seed=42`) và `data/media.json` (chỉ link YouTube/ảnh chính thức VinWonders); cập nhật `DATA_CARD.md` | **Dũng** | 20:45 – **22:30** *(27/11)* | — | `hotels.json` & `media.json` hợp lệ JSON, mọi nguồn giá & media có URL kiểm mở được (thiếu thì để trống) | `data/hotels.json`, `data/media.json`, `data/DATA_CARD.md` |
| **T9** | Điền `cost/personas.yaml` đúng Track C (≥3 persona từ bằng chứng, số người dùng VinWonders/Phú Quốc có nguồn, 2 mức giá Gemini từ `further-reading/model-prices.md` kèm link & ngày xem) + chạy thử `python run.py simulate --try` | **Dũng** | 07:30 – **09:30** *(28/11)* | T1, T7 | `python run.py simulate --try` chạy xong 10 phiên với Gemini thật không lỗi | `cost/personas.yaml`, `cost/simulate-try.csv` *(gitignored)* |
| **T10** | Mở rộng `eval/benchmark.csv` thêm `B15`–`B24` (**tổng 22–25 câu**, giữ ≥5 `kho`, ≥2 `tu_choi`, **≥1/3 nguồn thật** ưu tiên câu từ `P1–P3`/khảo sát/review) | **Quang** | 20:45 – **23:30** *(27/11)* | — | `python run.py check` đạt **0 cảnh báo**; cập nhật lại mục 2 của `eval/README.md` | `eval/benchmark.csv`, `eval/README.md` |
| **T11** | **CHỐT CHẶN 09:00:** Chạy `python run.py eval` (`--wait 4` nếu cần) → chấm đủ `pass` (`1`/`0`) theo `metric_spec.yaml` → `python run.py score eval/run-1.csv`; điền mục 5 `eval/README.md` & §7 `spec.md` | **Khải + Quang** | 08:00 – **09:00** *(28/11)* | T2, T10 | Có `eval/run-1.csv`, `traces/run-1.jsonl` (cả 2 đã commit), kết quả `x/N (%)` + `run_id` | `eval/run-1.csv`, `traces/run-1.jsonl`, `eval/README.md`, `spec.md` §7 |
| **T12** | Quay **video 30 giây** thao tác thật trên web VinPlanner (dự phòng CLI `python run.py` nếu 08:30 web chưa chạy ổn) gọi Gemini thật; up YouTube *"Không công khai"* / Drive công khai, kiểm bằng cửa sổ ẩn danh | **Quang** | 08:30 – **09:30** *(28/11)* | T6 *(hoặc T2 nếu dùng CLI)* | Video rõ thao tác + kết quả từ Gemini thật, mở được bằng tab ẩn danh | Link video nộp form CP3 |
| **T13** | Cập nhật `spec.md` §0–§7 (bỏ mục AI giả, thêm `tra_khach_san` ghi ngoài phạm vi), bảng Impact §2 theo `summary.md`, §10 changelog; cập nhật `README.md` tên model thật; kiểm `git status` sạch → push → **nộp form CP3 trước 10:00** | **Khải** | 09:15 – **09:50** *(28/11)* | T7, T9, T11, T12 | `python run.py check` 0 cảnh báo, `git status` không có `.env`, form CP3 đã gửi trước 10:00 | `spec.md`, `README.md`, form CP3 |

---

## 2. Lịch làm việc theo khung giờ

| Khung giờ | Khải | Đức Anh | Quang | Dũng |
|---|---|---|---|---|
| **20:45 – 21:30** *(27/11)* | **T1:** Nối Gemini `.env` + `eval --try`; công bố JSON `PlanResponse` cho Đức Anh | **T4:** Thêm `x, y` & `polygon` phân khu vào `data/` + `DATA_CARD.md` | **T10:** Thiết kế lưới phủ cho 10 câu mới `B15–B24` | **T8:** Tạo `data/hotels.json` + tìm link media chính thức `media.json` |
| **21:30 – 23:00** *(27/11)* | **T2:** Tách `plan_day()`, giữ `answer()`, sửa guardrail, chạy thử 14 câu | **T5:** Scaffold `web/` (Vite React) + `ChatPanel`, `HotelCards`, `StepsDrawer` | **T10:** Viết xong `B15–B24`, chạy `run.py check` 0 cảnh báo | **T8 + T7:** Xong `hotels.json`/`media.json` (22:30) · gửi tin nhắn hỏi `P1–P3` & đẩy khảo sát |
| **23:00 – 01:00** *(đêm 27–28/11)* | **T3:** Code `codebase/api.py` (8 endpoint + undo) & `requirements.txt` | **T6:** Code `ParkMapSvg`, `DayTabs`, `TimelineStrip`, `ItemDetailModal`, `CheckModal`, nối `:8000` | Rà soát chéo câu thử mới với Khải, nghỉ ngơi lấy sức chấm Lượt 1 | Tổng hợp phiếu khảo sát về đêm, chốt lịch hẹn sáng mai nếu thiếu |
| **07:30 – 08:30** *(sáng 28/11)* | Ghép nhánh, kiểm ổn định API + `answer()`, chốt sẵn phương án web/CLI | Fix bug UI khi nối API thật; chuẩn bị kịch bản demo quay video 30s | Hỗ trợ test câu khó trên web / chuẩn bị script chấm `run-1.csv` | **T7 + T9:** Hoàn tất `P1–P3`, khảo sát ≥20, `summary.md` + `personas.yaml` |
| **08:30 – 09:15** *(sáng 28/11)* | **T11:** Chạy `python run.py eval` ra `run-1.csv` (hạn cứng 09:00) | Hỗ trợ Quang quay video 30s web VinPlanner | **T11 + T12:** Chấm đủ cột `pass` → `run.py score` · quay video 30s | **T9:** Chạy `python run.py simulate --try` (10 phiên), chỉnh `personas.yaml` |
| **09:15 – 10:00** *(sáng 28/11)* | **T13:** Cập nhật `spec.md`, `README.md`, merge `main`, kiểm `git status`, push & **nộp CP3** | Kiểm tra lại bản web sau merge | Upload video, gửi link ẩn danh kiểm tra | Rà lại bảng Impact §2 khớp `summary.md` |

---

## 3. Hợp đồng giao tiếp & Quy ước Git

- **Hợp đồng `PlanResponse`:** Trước **21:30**, Khải xác nhận xong JSON trong [docs/vinplanner-architecture.md](file:///d:/workspace/VinAI/K5-Day15-L3A-Phoenix_1/docs/vinplanner-architecture.md#L73-L148) để Đức Anh tạo `web/src/mock/plan.json` làm frontend song song không phải chờ API.
- **Quy ước nhánh Git (mỗi người giữ file của mình, không sửa chéo):**
  - `cp3-khai`: `codebase/ai.py`, `codebase/agent.py`, `codebase/api.py`, `codebase/tools.py` *(phần `tra_khach_san`)*, `requirements.txt`, `spec.md`, `README.md`
  - `cp3-ducanh`: `web/**`, `data/park_zones.json`, `data/attractions.json`, `data/shows.json`, `data/DATA_CARD.md`
  - `cp3-quang`: `eval/benchmark.csv`, `eval/README.md`, `eval/run-1.csv`, `traces/run-1.jsonl`
  - `cp3-dung`: `evidence/**`, `data/hotels.json`, `data/media.json`, `cost/personas.yaml`
- **Luật Git an toàn:** Kiểm `git status` trước mọi lần `git add`. Tuyệt đối không commit `.env`, `eval/run-try.csv`, `eval/run-mock.csv`, `cost/simulate-try.csv`, `node_modules/`.

---

## 4. Việc sau CP3 cho CP4 (`10:00 – 14:30 Thứ Bảy 28/11`)

1. **Đánh giá Lượt 1 → 1 cải tiến → Lượt 2 (`10:00 – 11:30`):** Cả nhóm đọc các câu trượt ở `run-1.csv`, gom nhóm lỗi chính vào `eval/report.md` (≥3 lỗi), chọn 1 nhóm lỗi đau nhất để cải tiến prompt/logic, rồi chạy `python run.py eval` → `eval/run-2.csv` + `score`.
2. **Mô phỏng chi phí (`11:00 – 12:30`):** Chạy `python run.py simulate` (≥50 phiên) → tính chi phí / task thành công theo tỉ lệ đạt Lượt 2, phóng 3 kịch bản `thấp · cơ sở · cao` cho 2 mức model Gemini vào `cost/cost-estimate.md` + `spec.md` §8–§9.
3. **Bonus người dùng thử (`11:30 – 13:00`):** Mời 2–3 người ngoài nhóm dùng thử **web VinPlanner** theo 5 nhịp (guide 4.3), ghi log vào `validation/log.md`.
4. **Slide & Video dự phòng (`13:00 – 14:30`):** Xuất `demo-slides.pdf` (8 trang theo `slides/outline.md`), quay video demo dự phòng bản web hoàn chỉnh → nộp **CP4 trước 14:30**.

---

## 5. Checklist tự soát trước khi bấm nộp CP3 (`09:45`)

- [ ] Bằng chứng pain đạt ngưỡng ≥1 nguồn (`evidence/data-mining.md` `24/60`) + đã kiểm chéo nguồn 2 (`P1–P3` & khảo sát ≥20) trong `evidence/summary.md` + ≥5 trích dẫn nguyên văn.
- [ ] `eval/benchmark.csv` có `20–30` câu (`≥5 kho`, `≥2 tu_choi`, `≥1/3` nguồn thật) và `python run.py check` **0 cảnh báo**.
- [ ] Bản chạy thử gọi **Gemini thật** (`tokens > 0`) + đã chạy `python run.py simulate --try`.
- [ ] Đã có `eval/run-1.csv` + `traces/run-1.jsonl` (đã commit), chấm đủ 100% cột `pass` và chạy `python run.py score eval/run-1.csv`.
- [ ] Video **30 giây** thao tác thật + AI thật mở được bằng cửa sổ ẩn danh.
- [ ] `spec.md` §0–§7 & §10 changelog đã đẩy lên `origin/main`; `git status` tuyệt đối không chứa `.env` hay API key.
