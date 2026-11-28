# Reflection — Vũ Đức Anh

1. **Vai trò + phần mình làm (trỏ tới file / commit):**
   Thành viên Cặp X — dữ liệu công viên, công cụ kiểm ràng buộc và giao diện web. CP2: 5 bộ dữ liệu, `data/DATA_CARD.md` và 6 công cụ tiếng Việt trong `codebase/tools.py` (`60d34ed`); CP3: dữ liệu 3 tổ hợp / 8 phân khu với toạ độ & polygon, `web/` (React + MapLibre, `ParkMap` vẽ tuyến), cập nhật `shows.json` (`1f3b74a`, `28a478e`, `43c2d01`); CP4 (`8e3bf8c`).

2. **AI hỗ trợ mình thế nào (việc gì, công cụ gì, chỗ nào phải sửa lại output AI):**
   Dùng coding agent để viết giao diện React `web/` và sinh dữ liệu `synthetic` (thời tiết, thời lượng trò, ma trận đi bộ) với seed 42. Phần phải kiểm lại là toạ độ: mình tự kiểm 44/44 điểm chơi và 10/10 show có toạ độ nằm trong polygon phân khu, ghi trong `data/DATA_CARD.md`, và gắn nhãn rõ phần nào là thông tin công khai thật, phần nào là ước lượng. Với web, mình mở thử luồng chính để kiểm, sửa vị trí show và cách vẽ tuyến trên bản đồ (`43c2d01`).

3. **Một câu thử trượt của nhóm và mình học được gì từ nó:**
   `B03` — "chỉ có 1 ngày… chọn những điểm đáng đi nhất", tiêu chí "mỗi phân khu chỉ ghé 1 lần liền mạch". Lịch ghé Đại lộ châu Âu (Z1) đầu ngày rồi quay lại Z1 xem Once cuối ngày, và vẫn trượt ở cả Lượt 2. Bài học: `kiem_lich_trinh` mình viết kiểm đủ giờ mở cửa, chiều cao, ngân sách, mưa nhưng chưa kiểm "đi vòng" — mà đi vòng chính là pain review và khảo sát nhắc tới. Một ràng buộc chỉ được bảo đảm khi có code kiểm nó, nên việc tiếp theo là thêm luật phạt quay lại phân khu.
