# Đào data — cách đếm và kết quả

> Điền ở guide bước 1.2. Ôn lại: ngày 2, ngày 6 · lab ngày 2, lab ngày 6.
> Không đào data thì xoá file này. Script / công thức đếm để trong repo (vd `evidence/count.py` hoặc ghi công thức Sheets ngay dưới), người khác chạy lại phải ra cùng số.
> Repo chỉ chứa số đã tổng hợp và vài dòng ví dụ — không chép lại nguyên file data.

## 1. Cách đếm — viết TRƯỚC khi chạy

- Data dùng: review 1–3 sao công khai về VinWonders Phú Quốc, lấy ngày 27/11/2026. Dự kiến 30 Google Maps + 30 Tripadvisor; **thực tế 40 Tripadvisor + 20 Google Maps** vì Google Maps chỉ tải được 20 review trong danh sách (xem mục 5).
    - Tripadvisor: trang VinWonders Phu Quoc (d8111328), lọc Terrible + Poor + Average, ngôn ngữ English (183 review khớp lọc), sắp "Most recent", lấy 40 review đầu (09/2024 → 11/2026). Mã T01–T40.
    - Google Maps: tab Bài đánh giá, sắp "Xếp hạng thấp nhất", lấy 20 review đầu (đều 1 sao). Mã G01–G20 theo thứ tự hiển thị.
- Đếm gì: số review nhắc **rõ** ít nhất 1 trong 5 lỗi sắp lịch: (L1) quá rộng/đi không hết/đi bộ mệt/không kịp chơi · (L2) lỡ show/khó xem show/chờ show lâu · (L3) vướng chiều cao trẻ em/ít trò cho bé · (L4) nắng/mưa làm đóng trò hoặc phải bỏ về · (L5) chi phí phát sinh bên trong (phụ phí, vé VIP, thuê đồ) · trên tập: 60 review trên · lọc gì: bỏ review chỉ có sao không có chữ
- **Mẫu số là gì:** 60 review 1–3 sao đã lấy (không phải toàn bộ review). Review chỉ phàn nàn chuyện khác (nhân viên, trò hỏng, động vật…) vẫn nằm trong mẫu số, ghi ở cột `khac`.
- Script / công thức: bảng mã hoá `evidence/review-coding.csv` (mỗi dòng 1 review: mã, nguồn, sao, thời gian, tóm tắt tự viết lại, L1–L5 = 0/1, `bat_ky` = 1 nếu có ít nhất 1 lỗi, `khac`, link Tripadvisor). Đếm = tổng từng cột. Mỗi review chỉ chấm 1 khi review nói rõ chuyện đó, không suy diễn.

## 2. Đọc trước, đếm sau

5 nhãn lỗi chốt trước khi chấm: **L1** quá rộng/mệt/không kịp chơi · **L2** lỡ show/khó xem show · **L3** vướng chiều cao bé · **L4** mưa/nắng gián đoạn · **L5** vỡ ngân sách vì chi phí phát sinh.

Đã đọc 10 review đầu mỗi nguồn trước khi chấm. Các *kiểu* phàn nàn thấy được:
- Trò hỏng/đóng/bảo trì, nhiều khi không báo trước
- Thái độ nhân viên (Google Maps chiếm phần lớn)
- Phụ phí bên trong sau khi đã mua vé (ghế, khăn, xe điện, ghế VIP xem show)
- Giới hạn chiều cao (và cân nặng ở công viên nước) làm trẻ nhỏ không chơi được
- Mưa làm đóng trò, nắng nóng làm bỏ về sớm

## 3. Kết quả

| Đếm gì | x / N | % | Ghi chú |
|---|---|---|---|
| ≥1 trong 5 lỗi sắp lịch (`bat_ky`) | 24/60 | 40% | Tripadvisor 15/40 (38%) · Google 9/20 (45%) |
| L5 · chi phí phát sinh bên trong | 9/60 | 15% | Tripadvisor 3/40 · Google 6/20 |
| L3 · vướng chiều cao trẻ em | 7/60 | 12% | Tripadvisor 6/40 · Google 1/20 |
| L4 · nắng/mưa làm hỏng lịch | 6/60 | 10% | Tripadvisor 6/40 · Google 0/20 |
| L2 · lỡ show / khó xem show | 5/60 | 8% | Tripadvisor 4/40 · Google 1/20 |
| L1 · quá rộng / không kịp chơi | 2/60 | 3% | Tripadvisor 1/40 · Google 1/20 |
| Chỉ phàn nàn chuyện khác (không có L1–L5) | 36/60 | 60% | chủ yếu nhân viên và trò hỏng/đóng |

So với giả thuyết (`evidence/hypothesis.md`: ≥40% review 1–3 sao nhắc ít nhất 1 lỗi): **vừa chạm ngưỡng (24/60 = 40%)**, không vượt rõ. Lỗi nhắc nhiều nhất là chi phí phát sinh và chiều cao trẻ em; "quá rộng/đi không hết" ít hơn dự kiến. Giải thích khác trong giả thuyết (nhân viên, trò hỏng) xuất hiện nhiều hơn — 36/60 review không nhắc lỗi sắp lịch nào.

## 4. ≥5 ví dụ cụ thể (mã dòng / mã đã ẩn danh, không đoán ai là ai)

Trích nguyên văn, tối đa 2 câu/review, đã bỏ tên người viết; ngày xem 27/11/2026.

1. **T01** (3 sao, Tripadvisor, 11/2026 · L2, L4) — "I suggest not to go there early in the morning especially with young kids as they won’t last till 645pm for the show , it was also very hot, so rmb to sunscreen" — https://www.tripadvisor.com/ShowUserReviews-g12666019-d8111328-r1086538121-VinWonders_Phu_Quoc.html
2. **T02** (3 sao, Tripadvisor, 06/2026 · L3) — "My 5 year old daughter could only get on a few rides. Nothing much for toddlers." — https://www.tripadvisor.com/ShowUserReviews-g12666019-d8111328-r1077144914-VinWonders_Phu_Quoc.html
3. **T04** (2 sao, Tripadvisor, 07/2026 · L3, L4) — "However we didn’t know they close down all the rides in the rain so it felt like they shouldn’t be selling tickets when all the rides were closed." — https://www.tripadvisor.com/ShowUserReviews-g12666019-d8111328-r1069765233-VinWonders_Phu_Quoc.html
4. **T38** (2 sao, Tripadvisor, 10/2024 · L3) — "My children could hardly try any of their pleasures, as in most pleasures one should be min. 130 cm." — https://www.tripadvisor.com/ShowUserReviews-g12666019-d8111328-r976341202-VinWonders_Phu_Quoc.html
5. **G10** (1 sao, Google Maps, ~4 tháng trước · L5) — "Đã mua vé trọn gói xong vào trong tất cả cách dịch vụ đều tính tiền 1 cái ghế xếp 235 ngàn 1 cái khăn tắm 50 ngàn ." — https://www.google.com/maps/place/VinWonders+Ph%C3%BA+Qu%E1%BB%91c (tab Bài đánh giá, sắp "Xếp hạng thấp nhất"), vị trí #10
6. **T35** (2 sao, Tripadvisor, 11/2024 · L4) — tóm tắt: nóng 30 độ, chỗ chờ không có mái che nên phải bỏ về sớm — https://www.tripadvisor.com/ShowUserReviews-g12666019-d8111328-r979565293-VinWonders_Phu_Quoc.html

Trích dẫn đề xuất cho `canvas.md` dòng 4 (gửi Khải): **24/60 review 1–3 sao (40%) nhắc ít nhất 1 lỗi sắp lịch** + T02: "My 5 year old daughter could only get on a few rides. Nothing much for toddlers."

## 5. Giới hạn của data

Data cho biết người ta **làm gì**, không cho biết **vì sao**. Thiếu gì, lệch về phía nào:
- Chỉ lấy review 1–3 sao nên lệch về phía tiêu cực; không đại diện cho mọi khách.
- Không biết review nào là gia đình có trẻ dưới 1,4m — nhiều review là cặp đôi/nhóm bạn, nên tỉ lệ L3 trong đúng nhóm người dùng có thể cao hơn.
- Tripadvisor chỉ lấy tiếng Anh (khách nước ngoài); Google Maps chỉ tải được 20 review (đều 1 sao) nên lệch về phàn nàn gay gắt và không có mốc thời gian chính xác (chỉ "x tháng trước").
- Review Tripadvisor trải từ 09/2024 đến 11/2026, một số giờ/giá đã thay đổi.
- Chấm 0/1 do 1 người (Quang) đọc và chấm; chưa có người thứ hai chấm lại để kiểm độ khớp.
→ Kiểm lại bằng phỏng vấn / khảo sát nào: phỏng vấn ≥3 gia đình có trẻ nhỏ từng đi VinWonders (Dũng, `evidence/interviews/`) hỏi riêng về chiều cao bé, phụ phí và mưa/nắng; khảo sát ≥20 người có câu "bạn từng gặp lỗi nào trong 5 lỗi".
