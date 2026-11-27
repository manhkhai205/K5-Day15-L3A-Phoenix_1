# Tổng hợp bằng chứng pain

> Điền ở guide bước 1.2, xong trước **CP3 10:00 Thứ Bảy 28/11**. Chấm ở rubric R1.
> Ba nguồn ngang nhau — tối thiểu **≥1 nguồn đạt ngưỡng**. Mạnh nhất: đào data ra insight → hỏi người dùng để kiểm lại (hoặc ngược lại).

## 1. Nguồn đã dùng

| Nguồn | Đạt ngưỡng? | File |
|---|---|---|
| Đào data (x/N, %, cách đếm chạy lại được, ≥5 ví dụ) | ☑ Đạt ngưỡng (24/60 = 40%, 6 ví dụ có link, bảng mã hoá `review-coding.csv`) | `evidence/data-mining.md` |
| Phỏng vấn (≥3 người ngoài nhóm, đúng người dùng) | ☐ chưa đủ đúng vai — đã phỏng vấn 3 người ngoài nhóm, nhưng chỉ **1/3 (P2) đúng vai** gia đình có trẻ nhỏ; P1, P3 là nhóm người lớn | `evidence/interviews/P1.md`, `P2.md`, `P3.md` |
| Khảo sát (≥20 người ngoài nhóm, đúng người dùng) | ☐ chưa — mới 6 người đúng đối tượng / 9 phiếu (27/11 17:36), cần ≥20 trước CP3 | `evidence/survey/results.csv` · cách đếm: `python evidence/survey/count.py` |

## 2. Số chính

- Đào data (`evidence/data-mining.md`): **24/60 (40%)** review 1–3 sao (40 Tripadvisor + 20 Google Maps, lấy 27/11/2026) nhắc ≥1/5 lỗi sắp lịch (Tripadvisor 15/40 = 38%; Google Maps 9/20 = 45%). Cụ thể: **L5 chi phí phát sinh 9/60 (15%)**, **L3 chiều cao bé 7/60 (12%)**, **L4 nắng/mưa 6/60 (10%)**, **L2 lỡ/khó xem show 5/60 (8%)**, **L1 quá rộng 2/60 (3%)**; **36/60 (60%)** phàn nàn chuyện khác (thái độ nhân viên, trò đóng/bảo trì).
- Phỏng vấn *(n nhỏ không ghi %)*: **3/3 người kể được ít nhất 1 lần kế hoạch bị vỡ** (đi vòng, chờ lâu, lỡ show, vướng chiều cao, mưa) · số lần đi khu vui chơi lớn / 12 tháng: P1 2, P2 3, P3 3–4 · thời gian tìm hiểu trước chuyến: P1 20–30 phút, P3 45 phút, P2 ~60 phút mà vẫn chưa biết nên đi khu nào trước · cả 3 đều chi ăn uống cao hơn dự kiến. Chỉ P2 đúng vai người dùng chính (phụ huynh có bé dưới 1,4m) — P2 là người duy nhất gặp vướng chiều cao bé.
- Khảo sát *(bản CP2, n nhỏ nên chỉ ghi x/n)*: 9 phiếu · 6/9 đúng đối tượng (đã đi công viên chủ đề cùng trẻ dưới 12 tuổi trong 12 tháng) · 4/6 lần gần nhất là VinWonders Phú Quốc.
  - **Chi tiêu vượt dự tính: 6/6** · trong đó vượt trên 20%: 3/6 — tín hiệu mạnh nhất.
  - Lỡ show muốn xem 4/6 · đi vòng / quay lại khu đã qua 4/6 · bé không đủ chiều cao chơi trò đã định 4/6 · mưa/nắng làm đổi lịch 3/6.
  - Chuẩn bị lịch chủ yếu bằng blog/review 5/6 và hội nhóm 4/6; ChatGPT/AI 2/6. Thời gian chuẩn bị: trên 60 phút 2/6, dưới 15 phút 2/6.
  - Khi kế hoạch vỡ, quyết lại mất 5–15 phút: 3/6; trên 15 phút: 2/6.
  - ⚠️ 3/6 phiếu (S02–S04) tự mâu thuẫn — chọn cả "Không có chuyện nào kể trên" cùng mọi chuyện khác ở câu 6. Chỉ tính 3 phiếu không mâu thuẫn (S05, S08, S09): chi vượt 3/3, nhưng lỡ show / đi vòng / vướng chiều cao chỉ 1/3. Không xoá phiếu nào; đánh dấu ở cột `canh_bao`.

Phỏng vấn nhiều vai thì đếm theo từng vai, không cộng chung.

| | Vai | Gặp pain? | Số lần / 1 tháng qua | Lần gần nhất mất | Đang xoay xở bằng |
|---|---|---|---|---|---|
| P1 | Người lớn, nhóm bạn, không có trẻ *(không đúng vai chính)* | Một phần — đi vòng, xếp hàng lâu, bỏ lỡ trò, không xem hết show | ~2 lần / 12 tháng | 20–30 phút tìm hiểu | TikTok, Google, bản đồ tại cổng |
| P2 | **Phụ huynh có bé ~1m25 (đúng vai)** | Có — bé không đủ chiều cao, đổi kế hoạch tại chỗ, bé mệt vì đi giữa các khu, không xem hết show, ăn uống vượt dự kiến | 3 lần / 12 tháng | ~60 phút tìm hiểu | Google, blog kinh nghiệm, bản đồ |
| P3 | Người lớn, nhóm bạn, không có trẻ *(không đúng vai chính)* | Có — chờ lâu, bỏ điểm vì hết giờ, lỡ 1 show vì không nắm giờ, mưa phải đổi sang khu trong nhà | 3–4 lần / 12 tháng | 45 phút tìm hiểu | TikTok, Google Maps, website chính thức |

## 3. ≥5 trích dẫn hoặc ví dụ nguyên văn (có nguồn, bỏ tên)

1. "xếp hàng lâu để chơi trò chơi" — phiếu khảo sát S05 (VinWonders Phú Quốc)
2. "Giá đắt vl" — phiếu khảo sát S09 (VinWonders Phú Quốc, nguyên văn)
3. "mất thời gian vì không thời gian chuẩn bị kế hoạch" — phiếu khảo sát S04 (VinWonders Phú Quốc, phiếu có cảnh báo mâu thuẫn ở câu 6)
4. "I suggest not to go there early in the morning especially with young kids as they won’t last till 645pm for the show , it was also very hot, so rmb to sunscreen" — T01 (Tripadvisor, 3 sao, 11/2026)
5. "My 5 year old daughter could only get on a few rides. Nothing much for toddlers." — T02 (Tripadvisor, 3 sao, 06/2026)
6. "Đi với trẻ con thì quan trọng nhất là biết trước trò nào bé được chơi, chứ đến nơi mới biết không được chơi thì rất mất thời gian." — P2 (phụ huynh, VinWonders Phú Quốc)
7. "Bản đồ có chỉ đường nhưng mình không biết nên đi trò nào trước để đỡ mất thời gian." — P1
8. "Nhóm mình tìm hiểu khá nhiều trước khi đi nhưng đến nơi vẫn không biết nên ưu tiên địa điểm nào." — P3

## 4. Các nguồn có khớp nhau không

Hai nguồn hiện có **khớp rõ ở điểm đau số 1 là chi phí phát sinh / vượt dự tính**: review công khai có L5 đứng đầu trong 5 nhóm lỗi (`9/60 = 15%`), còn khảo sát bước đầu (`n=6`) ghi nhận **6/6 phiếu chi tiêu vượt dự tính** (`3/3` phiếu không mâu thuẫn). Review cũng xác nhận hai ràng buộc đặc thù là **chiều cao trẻ em (`7/60`)** và **mưa/nắng (`6/60`)**, trong khi tỷ lệ nhắc trực tiếp "quá rộng" chỉ `2/60`. Đồng thời, cả hai nguồn đều chỉ ra nguyên nhân ngoài sắp lịch (thái độ nhân viên, trò đóng cửa, xếp hàng lâu, giá đắt) — khớp với "cách giải thích khác" trong `evidence/hypothesis.md`.

## 5. Kết luận

*(Chốt tại CP3, 28/11/2026)* Giả thuyết ở `evidence/hypothesis.md` bước đầu **đạt đúng ngưỡng 40% (`24/60`) trên tập review**, nhưng **phần lớn pain thực tế nghiêng mạnh về chi phí phát sinh (L5) và giới hạn chiều cao trẻ em (L3)** hơn là "quá rộng" (L1). Phỏng vấn (3/3 kể được kế hoạch bị vỡ, 3/3 ăn uống vượt dự kiến) khớp với review và khảo sát ở hai điểm: **chi phí phát sinh** và **không biết thứ tự đi / lỡ show**; P2 (phụ huynh) xác nhận trực tiếp pain **chiều cao bé**. Giới hạn: khảo sát mới 6/20 phiếu đúng đối tượng (3 phiếu tự mâu thuẫn), phỏng vấn chỉ 1/3 đúng vai — nên nguồn đạt ngưỡng chắc chắn duy nhất vẫn là đào review (24/60). Điều vẫn chưa biết: phụ huynh có trẻ nhỏ có thật sự muốn AI dự toán phụ phí và xoay lịch khi mưa/hủy show không (cần phỏng vấn thêm S03, S05, S09 — đều đã đồng ý hỏi thêm).

## Lịch hẹn (dùng cho CP2 — chỉ ghi vai và giờ, không tên)

| Vai | Giờ hẹn | Đã xong? |
|---|---|---|
| Người trả lời khảo sát S03 (đi VinWonders khác, đồng ý hỏi thêm) | __ | ☐ |
| Người trả lời khảo sát S05 (đi VinWonders Phú Quốc, đồng ý hỏi thêm) | __ | ☐ |
| Người trả lời khảo sát S09 (đi VinWonders Phú Quốc, đồng ý hỏi thêm) | __ | ☐ |
| | |
