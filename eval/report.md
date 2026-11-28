# Báo cáo đánh giá — lượt 1 → một cải tiến → lượt 2

> Điền ở guide bước 4.1. Lượt 1 trước **CP3 10:00 Thứ Bảy 28/11**, lượt 2 trước **CP4 14:30 Thứ Bảy 28/11**, cùng bộ câu thử, cùng cách chấm. Chấm ở rubric R5.
> Số lấy từ `python run.py score eval/run-1.csv` (và `run-2.csv`) sau khi điền cột `pass`. **Kết quả thấp ghi thật vẫn đủ điểm.**
> Không được: sửa chuẩn "đạt", bỏ câu thử trượt, sửa `expected` cho khớp output, sửa kết quả lượt đã chạy.

## 1. Kết quả

| Lượt | Run ID | Đạt / tổng | % | thuong | kho | tu_choi | So với chuẩn "đạt" |
|---|---|---|---|---|---|---|---|
| 1 | `run-1@20261127-234159` | 21/24 | 88% | 6/7 | 12/14 | 3/3 | **Đạt** (`≥80%`, `khong_vi_pham_rang_buoc` 100%, `tu_choi` 3/3) |
| 2 | `[chờ chạy trên máy có .env]` | __/__ | __% | __/__ | __/__ | __/__ | `[chờ run-2]` |

Kết quả từng câu: `eval/run-1.csv`, `eval/run-2.csv` *(chạy sau cải tiến trên máy có `.env`)*. Trace: `traces/run-1.jsonl` (`134.979` token vào · `29.446` token ra · `0` lỗi kỹ thuật), `traces/run-2.jsonl`.

## 2. Lỗi lượt 1 — gom thành nhóm có tên

| Nhóm lỗi | Số câu | Câu |
|---|---|---|
| Đọc sót ràng buộc giờ về & thời điểm mưa thực tế trong input *(nhóm lỗi chính)* | 2 | `B06`, `B16` |
| Lộ trình ghé lại phân khu cổng chính cuối ngày *(không ghép liền mạch 1 vòng)* | 1 | `B03` |
| *(Lưu ý chất lượng — vẫn đạt `pass=1`)* Khoảng trống chiều dài, đệm show hoặc tách khoản phụ phí | 5 | `B04`, `B08`, `B09`, `B13`, `B22` |

**≥3 lỗi cụ thể:**

| Câu | Input | Output | Vì sao sai |
|---|---|---|---|
| `B16` | "Nhà mình 2 người lớn, 1 ông bà 65 tuổi và 1 bé cao 1,15m, đến VinWonders đúng 09:00 về 18:30, muốn đi Cung điện Hải Vương và Công viên nước, ngân sách 4,5 triệu (chưa mua vé)" | Ghi `*Giả định mặc định (G10):* khung giờ dự kiến 09:00–19:30`; bỏ trống `09:00–10:00`, bắt đầu chơi lúc `10:00` ở `Z5_TYPHOON` và kết thúc bằng `[SH-ONCE]` `18:30–19:05` | Regex `_extract_time_window` không bắt được mẫu `"đến VinWonders đúng 09:00 về 18:30"` nên rơi về giờ đóng mặc định `19:30`, đồng thời bộ xếp ưu tiên `Z5_TYPHOON` (`10:00`) bỏ qua khoảng `09:00–10:00` ở `Z1/Z2` — khiến gia đình về `18:30` bị lỡ Show Once |
| `B06` | "Đang 13:00, mưa to, các trò ngoài trời tạm dừng. Nhà mình còn ở đến 19:30, bé 1,1m. Xếp lại lịch buổi chiều giúp" | Ghi `*Thời tiết:* mua_chieu (khung mưa 14:00, 16:00)`; xếp `[SH-CARNIVAL]` `17:00–17:30` và `[SH-ONCE]` `18:45–19:05` mà không cảnh báo phụ thuộc thời tiết | `plan_day()` không truyền mốc giờ `"13:00"` sang `tra_thoi_tiet`, rơi về khung mưa mặc định `14:00–16:00` của `weather.json`; đồng thời `_format_output()` thiếu cảnh báo show tối ngoài trời phụ thuộc thời tiết như `expected` yêu cầu |
| `B03` | "Bọn mình chỉ có 1 ngày mà nghe nói đi không hết, nhà có bé 1,2m, chọn giúp những điểm đáng đi nhất từ 9:00 đến 19:30" | Đi `Z1_EURO` (`09:03–11:02`) → `Z2_FAIRY` → `Z6_SEASHELL` → `Z5_TYPHOON` → `Z4_VIKING` → quay lại `Z1_EURO` lúc `18:30–19:05` xem `[SH-ONCE]` | Vi phạm `pass_criterion` *"mỗi phân khu chỉ ghé 1 lần liền mạch"* (tuy nhiên `kiem_lich_trinh` 0 vi phạm giờ mở cửa, đi bộ, chiều cao và khớp dữ liệu công cụ) |

## 3. Một lần cải tiến

- **Nhắm vào nhóm lỗi:** *Đọc sót ràng buộc giờ về & thời điểm mưa thực tế trong input* (`B06`, `B16`) — **vì sao là nhóm đau nhất với người dùng:**
  - Nếu hệ thống bỏ qua giờ ra về của gia đình (`18:30` trong `B16`) và bỏ trống 1 tiếng đầu buổi sáng (`09:00–10:00`), gia đình có trẻ nhỏ và ông bà 65 tuổi sẽ mất thời gian chơi sáng và bị xếp show tối sau giờ xe đón/giờ về.
  - Nếu đang mưa to từ `13:00` (`B06`) mà agent vẫn tính khung mưa mặc định `14:00–16:00` và không nhắc show ngoài trời phụ thuộc thời tiết, gia đình có nguy cơ dính mưa ở trò ngoài trời hoặc mất công đợi show tối bị huỷ.
- **Đã sửa gì** (trong `codebase/agent.py` và `codebase/tools.py`, giữ nguyên hoàn toàn `eval/metric_spec.yaml`, `eval/benchmark.csv` và chuẩn "đạt" §7):
  1. Mở rộng `_extract_time_window()` trong `codebase/agent.py` nhận diện mẫu *"đến [tổ hợp] đúng HH:MM về HH:MM"* (có kiểm biên giờ hợp lệ `00:00–23:59`) và cập nhật `SYSTEM` prompt cấm xếp mục kết thúc sau giờ về.
  2. Chỉnh điều kiện `water_pref` trong `_build_schedule_from_tools()` chỉ ưu tiên nhảy sang Công viên nước (`10:00`) khi `(s_try - cursor) <= 35` phút, giúp khung `09:00–10:00` tự động xếp điểm tại `Z1_EURO` / `Z2_FAIRY` trước khi sang `Z5_TYPHOON` đúng `10:00`.
  3. Bổ sung `_extract_rain_query()` trong `codebase/agent.py` bắt mốc giờ mưa thực tế (`"Đang 13:00, mưa to"` → `"mua to 13:00"`), nâng độ dài khung mưa to trong `_get_weather()` (`codebase/tools.py`) lên `180` phút (`13:00–16:00`), và thêm trong `_format_output()` danh sách trò ngoài trời bị bỏ khớp `tra_diem_choi` kèm cảnh báo show ngoài trời phụ thuộc thời tiết từ `tra_lich_show`.
- **Kết quả:**
  - Kiểm chứng offline trước Lượt 2 (`MODEL_PROVIDER=fake` + kiểm độc lập qua `eval/cham.py` trên đủ `24/24` câu): nhóm lỗi `B06, B16` đạt **`2/2`** (sửa dứt điểm giờ về `18:30`, khung `09:00–10:00` tại `Z1_EURO`, khung mưa `13:00–16:00` và cảnh báo show ngoài trời), cả `19/19` câu tạo lịch đạt `m1=1, m2=1` và `5/5` câu còn lại (`B05, B08, B11, B12, B24`) giữ nguyên hành vi đúng.
  - Kết quả chạy model thật Lượt 2 (`eval/run-2.csv`): nhóm lỗi đó `0/2` → `__/__` · tổng `88%` → `__%` *(chờ chạy `python run.py eval --wait 4` trên máy có `.env`)*.
- **Câu nào tệ đi sau khi sửa:** Chưa ghi nhận câu nào tệ đi khi kiểm thử hồi quy offline `24/24` câu (`B01–B24`); sẽ đối soát lại từng câu sau khi có `eval/run-2.csv` trên Gemini thật.

## 4. Còn lại

- **Lỗi chưa sửa + nguy hiểm thế nào:**
  - `B03` (ghé lại `Z1_EURO` cuối ngày để xem `SH-ONCE` sau khi đã đi `Z1_EURO` buổi sáng): giữ nguyên để bảo đảm đúng phạm vi 1 nhóm lỗi cho Lượt 2. Mức rủi ro trung bình — không vi phạm ràng buộc cứng nào nhưng tăng ~5–10 phút đi bộ quay lại khu cổng lúc cuối ngày.
  - Một số lịch còn khoảng trống giữa chiều (`B04` `14:20–16:50`, `B22` `14:55–16:50` khi chờ show tối), cảnh báo đệm `0` phút trước show ở vài ca (`B09`), hoặc chưa liệt kê chi tiết từng dòng phụ phí nhỏ trong thuyết minh (`B13`).
  - Giới hạn nguồn dữ liệu tĩnh: hệ thống chưa có thời gian xếp hàng thực tế hoặc lịch bảo trì trò đột xuất (`B14`), phải dựa vào xác nhận trực tiếp của gia đình trên app chính thức.
- **Nếu có thêm 1 tuần:**
  1. Tối ưu thuật toán & prompt sắp phân khu một chiều (đẩy `Z1_EURO` về cuối ngày liền trước `SH-ONCE` để hết lỗi `B03` và lấp khoảng trống `14:20–16:50` hợp lý hơn).
  2. Nối Weather API theo giờ (`Open-Meteo`, TTL `1–3h`) và triển khai adapter `HotelProvider` + Deep Link (`docs/data-strategy.md`) để thay thế hoàn toàn dữ liệu phòng mô phỏng `seed=42`.
  3. Chạy thử nghiệm thực địa 5 nhịp (`validation/log.md`) với ≥5 gia đình có trẻ dưới `1,4m` ngay trước/trong chuyến đi Phú Quốc.
