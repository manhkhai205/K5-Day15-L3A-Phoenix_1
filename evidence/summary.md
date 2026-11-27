# Tổng hợp bằng chứng pain

> Điền ở guide bước 1.2, xong trước **CP3 10:00 Thứ Bảy 28/11**. Chấm ở rubric R1.
> Ba nguồn ngang nhau — tối thiểu **≥1 nguồn đạt ngưỡng**. Mạnh nhất: đào data ra insight → hỏi người dùng để kiểm lại (hoặc ngược lại).

## 1. Nguồn đã dùng

| Nguồn | Đạt ngưỡng? | File |
|---|---|---|
| Đào data (x/N, %, cách đếm chạy lại được, ≥5 ví dụ) | ☑ Đạt ngưỡng (24/60 = 40%, 6 ví dụ có link, bảng mã hoá `review-coding.csv`) | `evidence/data-mining.md` |
| Phỏng vấn (≥3 người ngoài nhóm, đúng người dùng) | ☐ *(đã tạo sẵn `P1.md`–`P3.md`, lịch hẹn S03/S05/S09 — hoàn thành trước CP3)* | `evidence/interviews/P1.md`… |
| Khảo sát (≥20 người ngoài nhóm, đúng người dùng) | ☐ chưa — mới 6 người đúng đối tượng / 9 phiếu (27/11 17:36), cần ≥20 trước CP3 | `evidence/survey/results.csv` · cách đếm: `python evidence/survey/count.py` |

## 2. Số chính

- Đào data (`evidence/data-mining.md`): **24/60 (40%)** review 1–3 sao (40 Tripadvisor + 20 Google Maps, lấy 27/11/2026) nhắc ≥1/5 lỗi sắp lịch (Tripadvisor 15/40 = 38%; Google Maps 9/20 = 45%). Cụ thể: **L5 chi phí phát sinh 9/60 (15%)**, **L3 chiều cao bé 7/60 (12%)**, **L4 nắng/mưa 6/60 (10%)**, **L2 lỡ/khó xem show 5/60 (8%)**, **L1 quá rộng 2/60 (3%)**; **36/60 (60%)** phàn nàn chuyện khác (thái độ nhân viên, trò đóng/bảo trì).
- Phỏng vấn: __/3 người gặp *(n nhỏ không ghi %)* · số lần / tháng: P1 __, P2 __, P3 __ · mỗi lần mất __–__ phút
- Khảo sát *(bản CP2, n nhỏ nên chỉ ghi x/n)*: 9 phiếu · 6/9 đúng đối tượng (đã đi công viên chủ đề cùng trẻ dưới 12 tuổi trong 12 tháng) · 4/6 lần gần nhất là VinWonders Phú Quốc.
  - **Chi tiêu vượt dự tính: 6/6** · trong đó vượt trên 20%: 3/6 — tín hiệu mạnh nhất.
  - Lỡ show muốn xem 4/6 · đi vòng / quay lại khu đã qua 4/6 · bé không đủ chiều cao chơi trò đã định 4/6 · mưa/nắng làm đổi lịch 3/6.
  - Chuẩn bị lịch chủ yếu bằng blog/review 5/6 và hội nhóm 4/6; ChatGPT/AI 2/6. Thời gian chuẩn bị: trên 60 phút 2/6, dưới 15 phút 2/6.
  - Khi kế hoạch vỡ, quyết lại mất 5–15 phút: 3/6; trên 15 phút: 2/6.
  - ⚠️ 3/6 phiếu (S02–S04) tự mâu thuẫn — chọn cả "Không có chuyện nào kể trên" cùng mọi chuyện khác ở câu 6. Chỉ tính 3 phiếu không mâu thuẫn (S05, S08, S09): chi vượt 3/3, nhưng lỡ show / đi vòng / vướng chiều cao chỉ 1/3. Không xoá phiếu nào; đánh dấu ở cột `canh_bao`.

Phỏng vấn nhiều vai thì đếm theo từng vai, không cộng chung.

| | Vai | Gặp pain? | Số lần / 1 tháng qua | Lần gần nhất mất | Đang xoay xở bằng |
|---|---|---|---|---|---|
| P1 | | | | | |
| P2 | | | | | |
| P3 | | | | | |

## 3. ≥5 trích dẫn hoặc ví dụ nguyên văn (có nguồn, bỏ tên)

1. "xếp hàng lâu để chơi trò chơi" — phiếu khảo sát S05 (VinWonders Phú Quốc)
2. "Giá quá đắt" — phiếu khảo sát S09 (VinWonders Phú Quốc)
3. "mất thời gian vì không thời gian chuẩn bị kế hoạch" — phiếu khảo sát S04 (VinWonders Phú Quốc, phiếu có cảnh báo mâu thuẫn ở câu 6)
4. "I suggest not to go there early in the morning especially with young kids as they won’t last till 645pm for the show , it was also very hot, so rmb to sunscreen" — T01 (Tripadvisor, 3 sao, 11/2026)
5. "My 5 year old daughter could only get on a few rides. Nothing much for toddlers." — T02 (Tripadvisor, 3 sao, 06/2026)

## 4. Các nguồn có khớp nhau không

Hai nguồn hiện có **khớp rõ ở điểm đau số 1 là chi phí phát sinh / vượt dự tính**: review công khai có L5 đứng đầu trong 5 nhóm lỗi (`9/60 = 15%`), còn khảo sát bước đầu (`n=6`) ghi nhận **6/6 phiếu chi tiêu vượt dự tính** (`3/3` phiếu không mâu thuẫn). Review cũng xác nhận hai ràng buộc đặc thù là **chiều cao trẻ em (`7/60`)** và **mưa/nắng (`6/60`)**, trong khi tỷ lệ nhắc trực tiếp "quá rộng" chỉ `2/60`. Đồng thời, cả hai nguồn đều chỉ ra nguyên nhân ngoài sắp lịch (thái độ nhân viên, trò đóng cửa, xếp hàng lâu, giá đắt) — khớp với "cách giải thích khác" trong `evidence/hypothesis.md`.

## 5. Kết luận

*(Chốt tạm tại CP2; hoàn tất sau khi đủ khảo sát ≥20 và phỏng vấn P1–P3 trước CP3)* Giả thuyết ở `evidence/hypothesis.md` bước đầu **đạt đúng ngưỡng 40% (`24/60`) trên tập review**, nhưng **phần lớn pain thực tế nghiêng mạnh về chi phí phát sinh (L5) và giới hạn chiều cao trẻ em (L3)** hơn là "quá rộng" (L1). Điều vẫn chưa biết: trải nghiệm cụ thể của gia đình có trẻ dưới 1,4m ngoài nhóm về mức độ hữu ích của việc dự toán phụ phí và xoay lịch khi mưa/hủy show (cần phỏng vấn sâu S03, S05, S09 và gom đủ ≥20 phiếu khảo sát).

## Lịch hẹn (dùng cho CP2 — chỉ ghi vai và giờ, không tên)

| Vai | Giờ hẹn | Đã xong? |
|---|---|---|
| Người trả lời khảo sát S03 (đi VinWonders khác, đồng ý hỏi thêm) | __ | ☐ |
| Người trả lời khảo sát S05 (đi VinWonders Phú Quốc, đồng ý hỏi thêm) | __ | ☐ |
| Người trả lời khảo sát S09 (đi VinWonders Phú Quốc, đồng ý hỏi thêm) | __ | ☐ |
| | |
