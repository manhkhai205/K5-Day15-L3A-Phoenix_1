# Khai báo dùng AI

README của nhóm có mục "Dùng AI vào việc gì" (2–3 dòng, bắt buộc). Ghi chi tiết vào bảng dưới đây.

> Luật của đề: dùng AI để làm bài thoải mái, nhưng **ai không giải thích được phần có tên mình thì phần đó nhận 0 điểm**. Khai thiếu không bị trừ; giấu mới bị.

| Việc | Công cụ AI | AI làm gì | Người kiểm/sửa gì | Ai phụ trách |
|---|---|---|---|---|
| Code bản chạy thử | Coding agent (Khải dùng cho `codebase/`; Đức Anh cho `web/`) | Gợi ý & viết khung 6 công cụ, workflow `agent.py`, `api.py`, giao diện React | Người phụ trách đọc lại, chạy `python run.py`, `eval --try`, mở web thử luồng chính | Khải (codebase), Đức Anh (web) |
| Prompt / thiết kế lời gọi mô hình | Coding agent + Gemini `gemini-3.5-flash-lite` (model chạy thật) | Gợi ý prompt hệ thống, định dạng JSON `PlanResponse` | Kiểm bằng Lượt 1 (24 câu, 0 lỗi parse JSON) | Khải |
| Đào data (viết script đếm, gợi ý nhãn) | Claude | Lấy 60 review công khai 1–3 sao (Tripadvisor/Google Maps), đề xuất nhãn L1–L5 từng review, viết `evidence/review-coding.csv` | Quang đọc lại các review giáp ranh (T01, T06, T13, G01, G19) và chốt nhãn; quy tắc đếm ghi trước ở `data-mining.md` mục 1 | Quang |
| Rà câu hỏi phỏng vấn / khảo sát | Coding agent | Chỉ rà câu dẫn dắt | Người hỏi giữ câu hỏi về hành vi đã xảy ra (Mom Test) | Dũng |
| Viết câu thử (benchmark) | Claude (nháp B01–B12), coding agent (B15–B24) | Soạn nháp câu thử theo lưới phủ | Mỗi câu thử có `source`; câu `data_that` trỏ mã review thật; Dũng/Khải duyệt | Dũng, Quang, Khải |
| Sinh data `synthetic` (nếu có) | Coding agent | Thời tiết, thời lượng, ma trận đi bộ, `rooms_left` khách sạn | Seed 42 · Đức Anh kiểm 44/44 điểm + 10/10 show có tọa độ trong polygon (`data/DATA_CARD.md`) | Đức Anh, Dũng |
| Chấm cột `pass` bằng LLM (nếu có) | **Không dùng LLM chấm.** Claude viết `eval/cham.py` (kiểm bằng code 2 metric) và đề xuất pass/lý do | Gợi ý chấm, người quyết | Quang đọc đủ 24/24 output và quyết định cột `pass` (21/24); chấm thử chéo CP2 với Khải khớp 4/5 | Quang |
| Slide, văn bản | Claude & Coding agent | Soạn `metric_spec.yaml`, `eval/README.md`, cập nhật `spec.md` §1/§4/§7–§10, `eval/report.md`, `cost/cost-estimate.md`, wireframe & khung `slides/slides.html` + `slides/build_slides.py` | Quang & Dũng đọc lại, đối chiếu từng con số với `run-1.csv`, `summary.md`, `personas.yaml` và `data/DATA_CARD.md`; không tự bịa số `run-2` / `simulate-1` | Quang, Dũng |

**Không dùng AI để:** tạo người được phỏng vấn, trích dẫn, câu trả lời khảo sát; sửa kết quả các lượt đã chạy (`eval/run-*.csv`, `cost/simulate-*.csv`, `traces/`).
