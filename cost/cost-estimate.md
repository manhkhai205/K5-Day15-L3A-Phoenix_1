# Chi phí khi dùng thật

> Điền ở guide bước 4.2, nộp ở CP4 14:30 Thứ Bảy 28/11. Ôn lại: ngày 13, ngày 1, ngày 14 · lab ngày 13, lab ngày 14. Chấm ở rubric R6.
> Số **không điền tay**: điền `cost/personas.yaml` → `python run.py simulate --wait 4 --rate-from eval/run-2.csv` → chạy `python slides/build_slides.py --sync-docs` (hoặc chép bảng trong `cost/simulate-1-summary.md` vào đây).
> Lúc build dùng gói miễn phí vẫn tính theo **giá gói trả phí** — đây là chi phí cho lúc đưa vào dùng thật.

## 1. Đầu vào

- **Persona** (`cost/personas.yaml`, `sessions: 50`, `seed: 42`): `3` kiểu người dùng (`share` cộng bằng `1,0`, bình quân gia quyền **`2,4` phiên / gia đình / tháng có chuyến đi**):
  1. `lap_lich_1_lan` (`share: 0.5` · `1` phiên/tháng · `2` lượt/phiên · `types: [thuong]`): nguồn `spec.md` §2 & khảo sát `evidence/survey/results.csv` câu 5 (`2/6` chuẩn bị dưới 15 phút, `1/6` không chuẩn bị); tỉ lệ `50%` và `2` lượt/phiên là *(tự ước tính)*.
  2. `can_nhac_nhieu_phuong_an` (`share: 0.3` · `3` phiên/tháng · `3` lượt/phiên · `types: [thuong, kho]`): nguồn `spec.md` §2 (`2–3` phiên), khảo sát câu 5 (`2/6` > 60 phút) & phỏng vấn `P2` (~1 giờ tìm hiểu); tỉ lệ `30%` và `3` lượt/phiên là *(tự ước tính)*.
  3. `tai_lap_giua_ngay` (`share: 0.2` · `5` phiên/tháng · `4` lượt/phiên · `types: [thuong, kho, tu_choi]`): nguồn `spec.md` §2 (`3–5` phiên), khảo sát câu 6–7 (`3/6` đổi lịch vì mưa/nắng, `5/6` vỡ lịch) & phỏng vấn `P2`, `P3`; tỉ lệ `20%` và `4` lượt/phiên là *(tự ước tính)*.
- **Số người dùng thật** 3 kịch bản (thị trường đích ~`14.250` gia đình có trẻ nhỏ đi VinWonders Phú Quốc lần đầu / tháng từ VietnamPlus `>8,57` triệu lượt khách 9T/2026 ≈ `~950.000` lượt/tháng × `~20%` ghé VinWonders × `~30%` gia đình có trẻ nhỏ đi lần đầu ÷ `~4` người/gia đình; tỉ lệ tiếp cận `10% / 30% / 100%` là *(tự ước tính)*):
  - Thấp: **`1.425`** gia đình/tháng · Cơ sở: **`4.275`** gia đình/tháng · Cao: **`14.250`** gia đình/tháng.
- **Giá** 3 mức model (Paid Tier Standard, nguồn `https://ai.google.com/gemini-api/docs/pricing` & `https://aistudio.google.com/docs/pricing` · xem ngày `28/11/2026`):
  - `gemini-3.1-flash-lite`: **`$0.25`** / 1M token vào · **`$1.50`** / 1M token ra *(model chạy thật ở Lượt 2 `run-2` & mô phỏng `simulate-1`)*.
  - `gemini-3.5-flash-lite`: **`$0.30`** / 1M token vào · **`$2.50`** / 1M token ra *(model chạy ở Lượt 1 `run-1`, giữ đối chiếu)*.
  - `gemini-3.8-flash`: **`$0.75`** / 1M token vào · **`$3.75`** / 1M token ra *(giá áp dụng đến 31/12/2026)*.
- **Tỉ lệ đạt tham chiếu:** Lượt 1 đạt **`21/24 (88%)`** (`run-1@20261127-234159`, `134.979` token vào · `29.446` token ra, `gemini-3.5-flash-lite`) · Lượt 2 (`run-2`): **`23/24 (96%)`** (`run-2@20261128-142324`, `gemini-3.1-flash-lite` — đã dùng qua `--rate-from eval/run-2.csv` cho `cost/simulate-1.csv`).
- **Lưu ý đo lường:** Đo token trên model **`gemini-3.1-flash-lite`**, tính chi phí cho cả **`gemini-3.1-flash-lite`**, **`gemini-3.5-flash-lite`** *(đo trên `gemini-3.1-flash-lite`, tính giá `gemini-3.5-flash-lite`)* và **`gemini-3.8-flash`** *(đo trên `gemini-3.1-flash-lite`, tính giá `gemini-3.8-flash`)*.

## 2. Kết quả mô phỏng

Lượt mô phỏng: `cost/simulate-1.csv` · run ID `simulate-1@20261128-143602` · `50` phiên · `seed 42` · tỉ lệ đạt: 23/24 (96%) — lượt run-2@20261128-142324

| Model (giá) | Chi phí / phiên | Chi phí / task thành công | Chi phí / câu hỏi đạt | Chi phí / tháng — thấp (1.425 người) | Chi phí / tháng — cơ sở (4.275 người) | Chi phí / tháng — cao (14.250 người) | Chi phí / người / tháng (cơ sở) |
|---|---:|---:|---:|---:|---:|---:|---:|
| gemini-3.1-flash-lite (vào 0.25 · ra 1.5 $/1M) | $0.0109 | $0.0114 | $0.0045 | $42.21 | $126.63 | $422.09 | $0.0296 |
| gemini-3.5-flash-lite (vào 0.3 · ra 2.5 $/1M) | $0.0159 | $0.0166 | $0.0065 | $61.50 | $184.50 | $614.98 | $0.0432 |
| gemini-3.8-flash (vào 0.75 · ra 3.75 $/1M) | $0.0297 | $0.0310 | $0.0121 | $115.01 | $345.02 | $1,150.06 | $0.0807 |

> *(Tham chiếu sơ bộ trước mô phỏng chỉ từ Lượt 1 `run-1.csv`, chưa tính theo trọng số persona: trung bình 1 lượt hỏi Lượt 1 hết `~5.624` token vào và `~1.227` token ra, tương đương `~$0.0048`/lượt với `gemini-3.5-flash-lite`; số chính thức theo `50` phiên & `3` persona đã tổng hợp ở bảng trên từ `cost/simulate-1-summary.md`.)*

Chi phí / task thành công = chi phí trung bình mỗi phiên ÷ tỉ lệ đạt — **không coi như đạt 100%**.

## 3. So với impact

- **Impact / người / tháng (`spec.md` §2):** Tiết kiệm trung bình `~75 phút` tự ghép lịch, đi vòng và xoay sự cố mỗi gia đình/chuyến *(hiệu chuẩn bước đầu từ P1–P3 mất 20–60 phút tìm hiểu trước chuyến + khảo sát 5/6 mất 5–30+ phút xoay lịch tại chỗ)* và hỗ trợ tránh lỡ show / vỡ ngân sách trên tổng chi tiêu `~3,5–5 triệu đ/ngày`.
- **Chi phí / người / tháng (cơ sở, model `gemini-3.1-flash-lite`):** $0.0296 ($0.0114 / task thành công)
- **Kết luận một dòng — đáng làm không:** **Rất đáng làm** — chi phí $0.0296/gia đình/tháng nhỏ hơn rất nhiều so với giá trị ~75 phút tiết kiệm và chi tiêu 3,5–5 triệu đ/ngày.

## 4. *(Muốn sâu hơn, không bắt buộc)*

- **Các đòn bẩy tối ưu chi phí đã áp dụng trong kiến trúc JoyPlan AI:**
  1. **Nhánh chặn không gọi LLM (`0` token):** Ở Lượt 1 (`eval/run-1.csv`), `5/24` câu (`B05` thiếu thông tin G10, `B08` bất khả thi ngân sách, `B11/B12/B24` từ chối ngoài phạm vi) hoàn thành ở bước code `0` token model.
  2. **Rút gọn payload `_compact_attr` & cân đối số điểm (`per_venue_limit`):** Chỉ gửi trường thiết yếu (`id, name, zone, cat, indoor, open, close, dur, min_h`) kèm `lich_goi_y_tu_cong_cu` đã hợp lệ sẵn nên giảm đáng kể số vòng sửa (`MAX_REPAIR_ROUNDS = 2`).
  3. **Cache tĩnh cho dữ liệu công viên & bản đồ `$0`:** `codebase/tools.py` cache JSON trong bộ nhớ (`<50ms`/tool), bản đồ sử dụng OpenFreeMap Liberty (`$0`, không API key) kèm GeoJSON cục bộ ngoại tuyến.
- **Chi phí ngoài model:** Backend FastAPI + Vite tĩnh dùng lượng RAM/CPU nhỏ (có thể chạy trên 1 VPS cỡ nhỏ khi vận hành thử nghiệm); dữ liệu `hotels.json` + `media.json` dùng liên kết chính thức, không tốn chi phí băng thông lưu video `.mp4`.
- **Ngưỡng quy mô còn đáng làm:** Với mức giá `gemini-3.1-flash-lite` (và `gemini-3.5-flash-lite` đối chiếu), ngay cả ở kịch bản **Cao (`14.250` gia đình/tháng = 100% thị trường đích)**, chi phí AI vẫn nhỏ hơn rất nhiều so với giá trị `~75 phút` và rủi ro bỏ lỡ trải nghiệm trên chi phí chuyến đi `3,5–5 triệu đ/ngày` — phần quan trọng cần kiểm soát ở Production là giữ tỉ lệ quay vòng sửa (`repair rounds`) thấp và cache thời tiết / khách sạn theo TTL (`15–30` phút cho khách sạn, `1–3` giờ cho thời tiết).
