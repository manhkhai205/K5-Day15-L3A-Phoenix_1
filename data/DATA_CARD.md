# Data card — dữ liệu bản chạy thử dùng

> Điền ở guide bước 2.4 (bản đầu ở CP2, đủ ở CP3). Ôn lại: ngày 6 · lab ngày 6. Chấm ở rubric R4.
> Một trang. Mỗi dataset một mục. Dữ liệu chạy thử (bài mẫu, thông báo mẫu, đoạn transcript…) để trong thư mục `data/` này.
> Không commit nguyên tài liệu khoá, dữ liệu cá nhân thật hay nguyên file data BTC cấp — chỉ đoạn trích ngắn, bản viết lại, hoặc số đã tổng hợp.
> **Lưu ý quan trọng:** Toàn bộ dữ liệu vận hành & mô phỏng dưới đây chỉ dùng cho bản chạy thử và 6 công cụ trong `codebase/tools.py`, **không phải bằng chứng pain** (bằng chứng pain nằm ở `evidence/`).

---

## Dataset 1 · `data/park_zones.json` (6 phân khu & ma trận đi bộ)

| | |
|---|---|
| Dùng để làm gì | Nguồn cho công cụ `tra_lich_show`, `uoc_thoi_gian_di` và `kiem_lich_trinh` (kiểm giờ mở/đóng lệch nhau giữa 6 phân khu và thời gian di chuyển giữa các khu). |
| Từ đâu | Tổng hợp từ thông tin công khai của VinWonders Phú Quốc (website/app chính thức, VNPAY, Rooty Trip, Vietravel) + ma trận đi bộ ước lượng chuẩn hóa (`synthetic`). |
| Xử lý những bước gì | Chuẩn hóa mã 6 phân khu (`Z1_EURO`..`Z6_SEASHELL`), tách khung giờ chung (`09:00–19:30`) với 2 khu đóng sớm (`10:00–18:00` cho `Z5_TYPHOON` và `Z6_SEASHELL`), dựng ma trận thời gian đi bộ đối xứng 6×6 (đơn vị: phút). |
| Số dòng / số đoạn | 1 bản ghi tổng quan công viên, 6 phân khu, ma trận đi bộ 6×6 (36 cặp điểm). |
| Phiên bản / ngày lấy | 27/11/2026 |
| Nhãn | Hỗn hợp: giờ mở cửa & tên 6 phân khu là **thông tin công khai thật** · ma trận phút đi bộ là **`synthetic` (nhóm ước lượng chuẩn hóa)** |
| Giới hạn | Thời gian đi bộ thực tế của gia đình có thể tăng thêm 3–5 phút vào giờ cao điểm hoặc khi đi cùng trẻ nhỏ/xe đẩy; chưa phản ánh việc đóng bảo trì phân khu đột xuất. |

---

## Dataset 2 · `data/attractions.json` (Điểm chơi, ăn uống & nghỉ ngơi)

| | |
|---|---|
| Dùng để làm gì | Nguồn cho công cụ `tra_diem_choi` và `kiem_lich_trinh` (lọc trò theo chiều cao bé, trong nhà/ngoài trời, giờ mở cửa và gợi ý điểm trong nhà thay thế khi mưa). |
| Từ đâu | Tổng hợp từ thông số vận hành công khai của VinWonders Phú Quốc (Vinpearl, Rooty Trip, Mia.vn, PhuQuocGo, Daivietourist) + chuẩn hóa thời lượng chơi (`synthetic`). |
| Xử lý những bước gì | Gắn mã định danh chuẩn (`VW-Z1-01`..`VW-Z6-04`, `VW-MEAL-01`..`03`, `VW-REST-01`), chuẩn hóa `min_height_cm` (có các bẫy `120–140cm`), `companion_required_below_cm`, cờ `indoor` / `is_water_park`, gắn tag và đối chiếu chéo giờ mở cửa với `park_zones.json`. |
| Số dòng / số đoạn | 35 mục (31 điểm vui chơi/tham quan trải đều 6 phân khu + 3 điểm ăn uống + 1 mục nghỉ ngơi). |
| Phiên bản / ngày lấy | 27/11/2026 |
| Nhãn | Hỗn hợp: danh sách điểm nổi bật & quy định nhóm chiều cao là **thông tin công khai thật** · thời lượng chơi `duration_min` và một số điểm ăn/nghỉ đại diện là **`synthetic` (nhóm chuẩn hóa)** |
| Giới hạn | Chưa liệt kê toàn bộ >100 trò nhỏ lẻ; một số trò cảm giác mạnh có thể thay đổi ngưỡng chiều cao 5–10 cm theo đợt kiểm định kỹ thuật hoặc tạm dừng bảo trì theo ngày. |

---

## Dataset 3 · `data/shows.json` (Lịch biểu diễn show cố định)

| | |
|---|---|
| Dùng để làm gì | Nguồn cho công cụ `tra_lich_show` và `kiem_lich_trinh` (khớp giờ show cố định ngắn 10–30 phút, nhắc đến sớm 10–15 phút, xử lý show ngoài trời khi mưa/hủy). |
| Từ đâu | Bảng lịch biểu diễn chính thức 2026 trên website VinWonders (`https://vinwonders.com/vi/wonderpedia/news/lich-trinh-vinwonders-phu-quoc/`, ảnh chụp xác thực tại `docs/images/vinwonders-show-schedule.png`, kiểm ngày 27/11/2026). |
| Xử lý những bước gì | Chuẩn hóa `start_time`, `end_time` khớp bảng 2026 (Cho cá ăn `11:00–11:10`, Mascot Chim cánh cụt `13:00–13:30`, Nàng tiên cá `14:00–14:20` & `15:30–15:50`, Carnival `17:00–17:30`, Show Once `18:45–19:05`), thời gian đến sớm (`arrive_early_min`), phân loại trong nhà (`indoor: true` tại Cung điện Hải Vương) và ngoài trời (`indoor: false`). |
| Số dòng / số đoạn | 6 suất show chính trong ngày. |
| Phiên bản / ngày lấy | 27/11/2026 |
| Nhãn | **Thật** (theo bảng lịch biểu diễn chính thức 2026 trên `vinwonders.com`). |
| Giới hạn | Lịch diễn thực tế có thể điều chỉnh theo mùa hoặc tạm dừng show ngoài trời (Carnival, Show Once) khi mưa lớn; bản chạy thử chưa nối API lịch diễn thời gian thực. |

---

## Dataset 4 · `data/pricing.json` (Bảng giá vé, ăn uống & phụ phí)

| | |
|---|---|
| Dùng để làm gì | Nguồn cho công cụ `tinh_chi_phi` và `kiem_lich_trinh` (tính dự toán tổng chi phí gia đình và kiểm ràng buộc không vượt ngân sách). |
| Từ đâu | Bảng giá niêm yết tham chiếu công khai từ VinWonders, Rooty Trip, VisitPhuQuoc, Trip.com (cộng quy định không mang đồ ăn mặn ngoài vào công viên). |
| Xử lý những bước gì | Chuẩn hóa đơn vị `VND`, phân 4 hạng vé theo chiều cao/độ tuổi (`adult`, `child_100_140`, `senior`, `child_under_100`), 4 mức ăn (`buffet`, `a_la_carte`, `fastfood`, `none`) và 6 phụ phí phát sinh (`stroller` có tách riêng tiền cọc hoàn lại 500.000đ, `locker`, `buggy`, `fastpass`, `raincoat`, `drinks_snacks`). |
| Số dòng / số đoạn | 4 hạng vé, 4 gói ăn uống, 6 phụ phí dịch vụ, 2 quy tắc chính sách. |
| Phiên bản / ngày lấy | 27/11/2026 |
| Nhãn | **Thật (tham chiếu niêm yết công khai)** cho vé/buffet/xe đẩy/buggy · **`synthetic` (ước lượng tham chiếu)** cho mức món lẻ trung bình, nước uống & Fastpass. |
| Giới hạn | Giá vé thực tế có thể giảm khi đặt qua OTA (Klook/Traveloka) hoặc mua combo Safari; chưa tự động tính giá combo khuyến mãi theo từng ngày. |

---

## Dataset 5 · `data/weather.json` (Kịch bản thời tiết mô phỏng có seed)

| | |
|---|---|
| Dùng để làm gì | Nguồn cho công cụ `tra_thoi_tiet`, `tra_lich_show` và `kiem_lich_trinh` (kiểm tra nắng gắt trưa, mưa chiều 14:00–16:00, mưa tối hoặc mưa cả ngày để chặn/tái lập lịch ngoài trời & Công viên nước). |
| Từ đâu | Nhóm tự dựng (`synthetic`, `seed=42`) theo quy luật mùa khô (tháng 11–4) và mùa mưa (tháng 5–10) tại Phú Quốc. |
| Xử lý những bước gì | Định nghĩa 5 trạng thái thời tiết chuẩn (`nang`, `nang_gat`, `mua_chieu`, `mua_toi`, `mua_lon`), gán 6 ngày kịch bản cố định trong `scenarios_by_date` và quy tắc suy theo tháng cho ngày bất kỳ. |
| Số dòng / số đoạn | 5 trạng thái thời tiết, 6 ngày kịch bản mẫu, 1 bảng quy tắc mặc định theo tháng. |
| Phiên bản / ngày lấy | 27/11/2026 (`seed=42`) |
| Nhãn | **`synthetic`** |
| Giới hạn | Chỉ mô phỏng kịch bản cố định để kiểm thử và tái lập lịch xác định, không thay thế dự báo thời tiết thời gian thực qua API khí tượng. |

---

**Kiểm chứng dữ liệu `synthetic`:** Toàn bộ 5 file JSON trong `data/` đã được **Vũ Đức Anh** (`seed=42` cho kịch bản thời tiết, ước lượng chuẩn hóa cho thời lượng/ma trận đi bộ/phụ phí tham chiếu) kiểm tay 100% số bản ghi ngày 27/11/2026 để đảm bảo có đủ các ca bẫy (khu đóng cửa 18:00, trò yêu cầu 120–140cm, show 10 phút, mưa đóng khu ngoài trời) khớp `spec.md` §0–§2 và `docs/cp2-plan.md`.
