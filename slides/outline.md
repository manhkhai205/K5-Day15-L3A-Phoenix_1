# Dàn slide → lấy số từ file nào

> Làm ở guide bước 5.1. Luật: **không có bằng chứng thì không có slide** — mỗi trang ≥1 con số / trích dẫn có nguồn / kết quả đo.
> Xuất PDF thành `demo-slides.pdf` ở thư mục gốc repo (`python slides/build_slides.py`), nộp tại CP4 14:30 Thứ Bảy 28/11. Nộp PDF, không nộp link.
> Sau khi chạy xong `run-2.csv` và `simulate-1` trên máy có `.env`, chạy `python slides/build_slides.py --sync-docs` để tự đồng bộ số mới nhất vào tài liệu và xuất lại `demo-slides.pdf`.

| # | Trang | Có gì | Số lấy từ | Xong |
|---|---|---|---|---|
| 1 | Người dùng & pain | Ai · việc gì · chỗ đau + số và trích dẫn (`24/60 = 40%`, `6/6` vượt chi, `3/3` vỡ lịch) | `evidence/summary.md` | ☑ |
| 2 | Vì sao chọn bài này | Bảng impact rút gọn (`~14.250 gđ/tháng × ~75 phút = ~17.812 giờ/tháng`) + hướng C2, C3 bị loại | `spec.md` §2 | ☑ |
| 3 | Giải pháp | Lát cắt một câu · sơ đồ workflow 5 bước · AI gợi ý, người quyết (`kiem_lich_trinh` 0 vi phạm) | `spec.md` §4 | ☑ |
| 4 | Demo live | Ca thường (`B01`) + ca khó mưa 13:00 (`B06`) + ca tấn công (`B11`, `B12`); mạng hỏng → video dự phòng | `eval/benchmark.csv` | ☑ |
| 5 | **Đánh giá thế nào** | `24` câu · `11/24` nguồn thật · khớp `4/5` · 3 metric · Lượt 1 `21/24 (88%)` (`run-1@20261127-234159`) → cải tiến Nhóm lỗi 1 (`B06`, `B16`) → Lượt 2 | `eval/README.md`, `eval/report.md` | ☑ |
| 6 | **Chi phí khi dùng thật** | `50` phiên (`seed 42`) · `3` persona `2,4` phiên/tháng · `1.425 / 4.275 / 14.250` gđ · 2 mức Gemini Paid Standard · đối chiếu `~75p` & `3,5–5tr/ngày` | `cost/cost-estimate.md` | ☑ |
| 7 | Kết luận | **ITERATE → GO có kiểm soát** — dẫn 3 trụ cột số liệu từ trang 1, 5, 6 | — | ☑ |
| 8 | Nếu có thêm 1 tuần | 3 việc: xử lý nốt `B03` & khoảng trống chiều (`B04/B22`) · nối Live Weather API & `HotelProvider` Deep Link · User Testing 5 nhịp `validation/log.md` | `eval/report.md` mục 4 · `docs/data-strategy.md` | ☑ |

**Trước khi lên:** tải repo về một máy khác (hoặc thư mục mới), chạy theo mục "Chạy trong 3 phút" của `README.md` · `.env` có trên máy demo, đã gọi thử 1 câu trong vòng 1 giờ trước giờ demo · video dự phòng mở được bằng cửa sổ ẩn danh · biết bản chạy thử sẽ làm gì với **1 câu thử lạ** của giám khảo.

Ai nói trang nào (mỗi người ≥1 phần):

| Trang | Người nói |
|---|---|
| Trang 1 · Người dùng & pain + Trang 2 · Vì sao chọn C1 | Phạm Công Dũng (`2A202603428`) |
| Trang 3 · Giải pháp & Kiến trúc + Trang 4 · Demo live (CLI / Web UI) | Vũ Đức Anh (`2A202603573`) & Nguyễn Viết Mạnh Khải (`2A202603664`) |
| Trang 5 · Đánh giá thế nào (Lượt 1 → Cải tiến → Lượt 2) | Nguyễn Đình Quang (`2A202603620`) |
| Trang 6 · Chi phí khi dùng thật | Phạm Công Dũng (`2A202603428`) |
| Trang 7 · Kết luận & Trang 8 · Nếu có thêm 1 tuần | Nguyễn Viết Mạnh Khải (`2A202603664`) |
