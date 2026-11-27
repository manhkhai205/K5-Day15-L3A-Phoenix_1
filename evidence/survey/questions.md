# Khảo sát — bộ câu hỏi (chép sang Google Form)

> Người phụ trách: Phạm Công Dũng (TV4). Ngưỡng: **≥20 người ngoài nhóm, đúng người dùng** (đã đi công viên chủ đề cùng trẻ nhỏ trong 12 tháng qua).
> Hỏi **hành vi đã xảy ra**, không hỏi "có thích không". Không thu tên, email, SĐT.

- **Kênh gửi:** __ (vd nhóm Zalo phụ huynh, nhóm Facebook "Kinh nghiệm du lịch Phú Quốc", người thân)
- **Giờ mở form:** 27/11/2026, phiếu đầu tiên 17:28 · bản tổng hợp CP2 tính đến phiếu lúc 17:36 (9 phiếu) · **giờ chốt:** __ (chốt trước CP3 10:00 Thứ Bảy 28/11 để kịp tổng hợp)
- **Link form:** __
- **Tạo form tự động:** dán [`create_form.gs`](create_form.gs) vào https://script.google.com → chạy `createSurveyForm` → lấy link trong Execution log. Script tạo đủ 10 câu dưới đây (câu 3 tách thành 3a/3b, câu 1 "Chưa" → nộp luôn), không thu email, và đổ câu trả lời vào một Google Sheet.

## Câu hỏi

| # | Câu hỏi | Kiểu trả lời |
|---|---|---|
| 1 | Trong 12 tháng qua, bạn đã đi công viên chủ đề lớn (VinWonders, Sun World, Đầm Sen, Suối Tiên…) **cùng trẻ dưới 12 tuổi** chưa? | Có · Chưa *(Chưa → kết thúc form)* |
| 2 | Lần gần nhất là ở đâu? | VinWonders Phú Quốc · VinWonders khác · Sun World · khác |
| 3 | Lần đó nhóm bạn có mấy người, mấy trẻ cao dưới 1,4m? | Số người lớn / số trẻ |
| 4 | Trước hôm đó, bạn chuẩn bị lịch chơi bằng cách nào? | Chọn nhiều: blog/review · hội nhóm · app của công viên · ChatGPT/AI · hỏi người quen · không chuẩn bị · khác |
| 5 | Việc chuẩn bị lịch đó mất khoảng bao lâu? | Dưới 15' · 15–30' · 30–60' · trên 60' · không chuẩn bị |
| 6 | Trong ngày hôm đó, chuyện nào **đã xảy ra**? | Chọn nhiều: lỡ show muốn xem · đi vòng/quay lại khu đã qua · bé không đủ chiều cao chơi trò đã định · mưa/nắng làm đổi lịch · khu/trò đóng cửa · chi vượt dự tính · không có chuyện nào |
| 7 | Khi kế hoạch bị vỡ, bạn mất khoảng bao lâu để quyết lại nên đi đâu tiếp? | Không bị vỡ · dưới 5' · 5–15' · 15–30' · trên 30' |
| 8 | Tổng chi hôm đó so với dự tính trước? | Thấp hơn · gần bằng · vượt dưới 20% · vượt trên 20% · không dự tính |
| 9 | Điều gì khó chịu nhất trong ngày hôm đó? | Đoạn văn |
| 10 | (tuỳ chọn) Bạn có sẵn lòng cho nhóm hỏi thêm 10 phút không? | Có — cách liên hệ (không bắt buộc) · Không |

## Cách dùng kết quả

- Xuất CSV → **xoá** cột thời gian nộp chi tiết và câu 10 → lưu `evidence/survey/results.csv`. Bản gốc không commit.
- Đếm câu 6 theo từng lựa chọn: ghi `x/n (y%)` vào `evidence/summary.md` mục 2. Dưới ~10 người thì chỉ ghi `x/n`.
- Câu 5, 7 → hiệu chuẩn "~75 phút" ở `spec.md` §2 và `turns_per_session` ở `cost/personas.yaml`.
- Câu 9 → chọn ≥3 câu nguyên văn cho `evidence/summary.md` mục 3 và slide trang 1.
