# Reflection — Nguyễn Đình Quang

1. **Vai trò + phần mình làm (trỏ tới file / commit):**
   Thành viên Cặp Y — đào bằng chứng review, bộ câu thử và đánh giá. CP2: đào 60 review (24/60 = 40%, `evidence/data-mining.md`, `evidence/review-coding.csv`), `eval/metric_spec.yaml`, `eval/README.md` mục 1–4, chạy tay 5 output & bảng chấm thử (`984d9fe`, `c022d37`, `066795c`); CP3: nối Gemini thật, Lượt 1 `run-1` 21/24 (88%), `eval/cham.py`, cập nhật `spec.md` §1/§2/§10 và `docs/ai-usage.md` (`d35c07c`, `5dc80ca`), ghép nhánh kiểm thử `cp3-test`.

2. **AI hỗ trợ mình thế nào (việc gì, công cụ gì, chỗ nào phải sửa lại output AI):**
   Dùng Claude để lấy 60 review công khai, đề xuất nhãn L1–L5 cho từng review và viết `evidence/review-coding.csv`; mình đọc lại các review giáp ranh (T01, T06, T13, G01, G19) và chốt nhãn, quy tắc đếm ghi trước khi đếm. Claude cũng viết `eval/cham.py` kiểm bằng code 2 metric và đề xuất pass/lý do, nhưng nhóm không dùng LLM chấm: mình đọc đủ 24/24 output và tự quyết cột `pass` (21/24), trước đó chấm chéo với Khải khớp 4/5.

3. **Một câu thử trượt của nhóm và mình học được gì từ nó:**
   `B06` — "Đang 13:00, mưa to… xếp lại lịch buổi chiều". Khi chấm Lượt 1, mình thấy agent bỏ qua "mưa từ 13:00", dùng khung mưa mặc định 14:00–16:00 và xếp show ngoài trời không cảnh báo; mình xếp nó cùng `B16` vào nhóm lỗi lớn nhất "đọc sai ràng buộc người dùng" để nhóm sửa một lần cho cả hai — Lượt 2 cả hai đều đạt. Bài học: gom câu trượt theo nguyên nhân chứ không theo từng câu giúp cải tiến trúng chỗ, và `pass_criterion` viết cụ thể (giờ mưa, cảnh báo) mới bắt được lỗi mà metric code tổng quát vẫn cho qua.
