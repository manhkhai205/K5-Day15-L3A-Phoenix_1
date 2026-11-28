# Reflection — Nguyễn Viết Mạnh Khải

1. **Vai trò + phần mình làm (trỏ tới file / commit):**
   Đội trưởng, Cặp X — điều phối CP, kiến trúc AI và luồng chính. Khung repo + kế hoạch CP2 (`21eeb3e`, `docs/cp2-plan.md`); CP2: ảnh chụp chính thức `spec.md` §0, mẫu phỏng vấn, merge 2 cặp, chấm chéo khớp 4/5 (`9097b00`, `a8e8e9b`, `1a06ba5`); CP3: JoyPlan AI đa tổ hợp, FastAPI 9 endpoint, B15–B24, tài liệu kiến trúc & kế hoạch CP3 (`c2f7f7b`, `3c2c9e4`, `dc6ef0b`); CP4: Lượt 2 `run-2` 23/24 (96%), `simulate` 50 phiên, slide & kịch bản demo, hiển thị khách sạn/media (`19435c1`, `09db528`, `00370b1`). File chính: `codebase/agent.py`, `codebase/ai.py`, `codebase/api.py`, `spec.md`.

2. **AI hỗ trợ mình thế nào (việc gì, công cụ gì, chỗ nào phải sửa lại output AI):**
   Dùng coding agent để viết khung workflow `agent.py`, `api.py` và gợi ý prompt hệ thống + định dạng JSON `PlanResponse`; model chạy thật là Gemini `gemini-3.5-flash-lite`. Mình không nhận output của agent nguyên trạng: đọc lại code, chạy `python run.py` và `eval --try`, rồi kiểm bằng Lượt 1 (24 câu, 0 lỗi parse JSON). Phần phải sửa sau khi đo là cách agent đọc ràng buộc từ input — logic trích giờ về và thời điểm mưa ban đầu bỏ sót, phải mở rộng `_extract_time_window`, `_extract_rain_query` trước Lượt 2.

3. **Một câu thử trượt của nhóm và mình học được gì từ nó:**
   `B16` — gia đình có ông bà 65 tuổi và bé 1,15m, "đến 09:00 về 18:30". Lượt 1 trượt: agent giả định khung mặc định 09:00–19:30 nên xếp Once 18:30–19:05 sau giờ về và bỏ trống 09:00–10:00. Sau khi mở rộng `_extract_time_window`, câu này đạt ở `run-2` (23/24). Bài học: lỗi đắt nhất không nằm ở model mà ở bước đọc ràng buộc người dùng nhập — giá trị mặc định nguy hiểm vì nó im lặng thay cho thông tin thật; cần câu thử ở biên (giờ về sớm, mưa giữa ngày) ngay từ đầu.
