# Data card — dữ liệu bản chạy thử dùng

> Điền ở guide bước 2.4 (bản đầu ở CP2, đủ ở CP3). Ôn lại: ngày 6 · lab ngày 6. Chấm ở rubric R4.
> Một trang. Mỗi dataset một mục. Dữ liệu chạy thử (bài mẫu, thông báo mẫu, đoạn transcript…) để trong thư mục `data/` này.
> Không commit nguyên tài liệu khoá, dữ liệu cá nhân thật hay nguyên file data BTC cấp — chỉ đoạn trích ngắn, bản viết lại, hoặc số đã tổng hợp.
> **Lưu ý quan trọng:** Toàn bộ dữ liệu vận hành & mô phỏng dưới đây chỉ dùng cho bản chạy thử và 7 công cụ trong `codebase/tools.py` (`6` công cụ trong phạm vi đánh giá + `tra_khach_san` ngoài phạm vi đánh giá), **không phải bằng chứng pain** (bằng chứng pain nằm ở `evidence/`).

---

## Dataset 1 · `data/park_zones.json` (3 tổ hợp Phú Quốc United Center · 8 phân khu & ma trận di chuyển)

| | |
|---|---|
| Dùng để làm gì | Nguồn cho công cụ `tra_lich_show`, `uoc_thoi_gian_di`, `kiem_lich_trinh` và bản đồ MapLibre `ParkMap` (kiểm giờ mở/đóng lệch nhau giữa 3 tổ hợp / 8 phân khu và thời gian đi bộ / xe VinBus). |
| Từ đâu | Thông tin công khai của cụm Phú Quốc United Center: VinWonders (`vinwonders.com`, VNPAY, Rooty Trip), Vinpearl Safari (`newlifetravel.vn`, `vinpearl.com`) và Grand World (`datviettour.com.vn`, `vinpearl.com`), kèm tọa độ WGS84 & ma trận 8×8. |
| Xử lý những bước gì | Chuẩn hóa 3 tổ hợp (`vinwonders` 09:00–19:30, `safari` 09:00–16:00 / bus cuối 15:20, `grandworld` 08:00–22:30), 8 phân khu (`Z1_EURO`..`Z6_SEASHELL`, `Z7_SAFARI`, `Z8_GRANDWORLD`), thêm `color`, `center` và GeoJSON `polygon` khép kín; dựng ma trận di chuyển đối xứng 8×8 (đi bộ nội khu `3–12` phút; VinBus liên tổ hợp `15–20` phút). |
| Số dòng / số đoạn | 1 bản ghi `park` gốc (tương thích ngược), 3 bản ghi `venues`, 8 phân khu (kèm GeoJSON polygon), ma trận di chuyển 8×8 (`64` cặp điểm). |
| Phiên bản / ngày lấy | 27/11/2026 |
| Nhãn | Hỗn hợp: tên, giờ mở/đóng 3 tổ hợp & 8 phân khu là **thông tin công khai thật** · ma trận phút di chuyển & hình bao `polygon` từng phân khu trên nền tọa độ thật là **`synthetic` (ước lượng chuẩn hóa)** |
| Giới hạn | Thời gian đi bộ/chờ xe VinBus thực tế có thể tăng thêm 3–5 phút vào giờ cao điểm hoặc khi đi cùng trẻ nhỏ/xe đẩy; chưa phản ánh việc đóng bảo trì đột xuất. |

---

## Dataset 2 · `data/attractions.json` (44 điểm chơi, tham quan, ăn uống & nghỉ ngơi)

| | |
|---|---|
| Dùng để làm gì | Nguồn cho công cụ `tra_diem_choi`, `kiem_lich_trinh` và bản đồ `ParkMap` (lọc theo tổ hợp, chiều cao bé, trong nhà/ngoài trời, giờ mở cửa, điểm thu phí riêng Grand World). |
| Từ đâu | Tổng hợp từ thông số vận hành công khai của VinWonders (35 mục), Vinpearl Safari (4 mục: Xe buýt bán hoang dã, Open Zoo, Kid Zoo/Giraffe, nhà hàng Safari) và Grand World (5 mục: Bảo tàng Gấu Teddy, thuyền Gondola, dạo phố Venice, phố mua sắm mái che, ẩm thực). |
| Xử lý những bước gì | Gắn `venue_id` (`vinwonders` | `safari` | `grandworld`), tọa độ `lat`/`lng` trong polygon phân khu, `min_height_cm`, `companion_required_below_cm`, `indoor`, `is_water_park`, `paid_ticket_key` (`gw_teddy`, `gw_venice_boat`), giờ phục vụ (như `SF-Z7-01` chuyến cuối `15:20`). |
| Số dòng / số đoạn | **44 mục** (`35` mục VinWonders trải đều 6 phân khu + `4` mục Vinpearl Safari + `5` mục Grand World). |
| Phiên bản / ngày lấy | 27/11/2026 |
| Nhãn | Hỗn hợp: danh sách điểm nổi bật, giờ mở/chuyến bus cuối & ngưỡng chiều cao là **thông tin công khai thật** · thời lượng `duration_min` và vị trí chi tiết `lat`/`lng` trong từng phân khu là **`synthetic` (ước lượng chuẩn hóa)** |
| Giới hạn | Chưa liệt kê toàn bộ >100 trò nhỏ lẻ; một số trò cảm giác mạnh có thể thay đổi ngưỡng chiều cao 5–10 cm hoặc tạm dừng bảo trì theo ngày. |

---

## Dataset 3 · `data/shows.json` (10 suất show cố định của 3 tổ hợp)

| | |
|---|---|
| Dùng để làm gì | Nguồn cho công cụ `tra_lich_show` và `kiem_lich_trinh` (khớp giờ show cố định ngắn, nhắc đến sớm `10–15` phút, phân biệt show ngoài trời/trong nhà và miễn phí/có thu vé). |
| Từ đâu | 6 suất show VinWonders từ bảng lịch biểu diễn chính thức 2026 (`vinwonders.com`, ảnh chụp `docs/images/vinwonders-show-schedule.png`), cộng 2 show Safari (`Zulu Dance`, `Animal Show`) và 2 show Grand World (`Tinh hoa Việt Nam`, `Sắc màu Venice`) tham chiếu từ nguồn công khai 2025–2026. |
| Xử lý những bước gì | Chuẩn hóa `venue_id`, `start_time`, `end_time`, `arrive_early_min`, `indoor`, `paid_ticket_key` (`gw_tinh_hoa`) và tọa độ `lat`/`lng` đặt marker bản đồ. |
| Số dòng / số đoạn | **10 suất show** (`6` show VinWonders + `2` show Safari + `2` show Grand World). |
| Phiên bản / ngày lấy | 27/11/2026 |
| Nhãn | **Thật** (VinWonders khớp bảng 2026 chính thức; Safari & Grand World tham chiếu giờ diễn công khai 2025–2026) · `lat`/`lng` đặt điểm trong phân khu là **`synthetic`** |
| Giới hạn | Show động vật Safari và show ngoài trời (`Carnival`, `Show Once`, `Tinh hoa Việt Nam`, `Sắc màu Venice`) có thể điều chỉnh lịch theo ngày hoặc tạm dừng khi mưa lớn. |

---

## Dataset 4 · `data/pricing.json` (Bảng giá vé lẻ, Combo 2 khu, Grand World, ăn uống & phụ phí)

| | |
|---|---|
| Dùng để làm gì | Nguồn cho công cụ `tinh_chi_phi` và `kiem_lich_trinh` (tính dự toán tổng chi phí gia đình, tự áp vé **Combo VinWonders + Safari** và **Combo Tinh hoa + Gấu Teddy** khi đi kèm). |
| Từ đâu | Bảng giá niêm yết & tham chiếu công khai 2025–2026 từ VinWonders, Rooty Trip, VisitPhuQuoc, Trip.com, DatVietTour, SaigonStar, Klook (kiểm 27/11/2026). |
| Xử lý những bước gì | Giữ nguyên khóa `tickets`, `meals`, `extras` của VinWonders; bổ sung `venue_tickets` (`vinwonders`, `safari`, `combo_vinwonders_safari` `1.500k/1.100k`, `grandworld_entry` `0đ`) và `grandworld_paid_items` (`gw_teddy`, `gw_venice_boat`, `gw_tinh_hoa`, `gw_combo_tinh_hoa_teddy`). |
| Số dòng / số đoạn | 4 hạng vé chuẩn, 4 gói vé tổ hợp, 4 gói điểm trả phí Grand World, 4 gói ăn, 6 phụ phí dịch vụ. |
| Phiên bản / ngày lấy | 27/11/2026 |
| Nhãn | **Thật (tham chiếu niêm yết công khai)** cho vé tổ hợp, Combo, điểm Grand World, buffet, xe đẩy, buggy · **`synthetic` (ước lượng tham chiếu)** cho món lẻ trung bình, nước uống & Fastpass. |
| Giới hạn | Giá vé thực tế có thể giảm thêm theo khuyến mãi OTA/VinWonders theo mùa; bản chạy thử ưu tiên lấy một mức tham chiếu chuẩn hóa cho minh bạch tính toán. |

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

**Kiểm chứng dữ liệu:** Toàn bộ 5 file JSON trong `data/` đã được **Vũ Đức Anh** đối chiếu bản đồ OpenStreetMap Nominatim (28/11/2026) và chạy script kiểm tự động (VinWonders 2026 chính thức + thông số tham chiếu Safari & Grand World; 8 GeoJSON polygon khép kín bám ranh giới đất liền thật, 100% 44/44 điểm và 10/10 show có tọa độ `(lat, lng)` nằm gọn trong polygon phân khu tương ứng và tách rời không trùng marker; kịch bản thời tiết `seed=42`; nhãn `thật` / `synthetic` tách bạch ở từng bảng) để giữ 100% tương thích với bộ câu thử CP2 `B01–B14` đồng thời kiểm cứng đủ các bẫy đa tổ hợp.
