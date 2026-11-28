# Hồ sơ đánh giá — một trang

> Điền ở guide bước 2.4 (mục 1–4, trước CP2) và 4.1 (mục 5–6, trước CP4). Ôn lại: ngày 9, ngày 14 · lab ngày 9. Chấm ở rubric R4, R5.
> Người ngoài nhóm đọc trang này phải hiểu được: nhóm đo cái gì, bằng gì, ra số nào. Trang slide "Đánh giá thế nào" lấy từ đây.

## 1. Dataset → xử lý

Dữ liệu chạy thử kết hợp thông tin vận hành công khai 2025–2026 của **cụm Phú Quốc United Center** (`3` tổ hợp: **VinWonders Phú Quốc** mặc định · mở rộng **Vinpearl Safari** · **Grand World**; `8` phân khu có giờ mở/đóng lệch nhau, `44` điểm chơi/ăn nghỉ, `10` suất show cố định, chiều cao tối thiểu từng trò, khu trong/ngoài trời, bảng giá vé lẻ/Combo/ăn uống/phụ phí, ma trận di chuyển `8×8` phân biệt đi bộ vs xe VinBus `15–20` phút và kịch bản thời tiết `seed=42`; chi tiết: `data/DATA_CARD.md`). Bằng chứng pain: 60 review 1–3 sao công khai trên Tripadvisor và Google Maps, đã mã hoá ở `evidence/review-coding.csv` (repo chỉ giữ tóm tắt và số tổng hợp).

## 2. Bộ câu thử dựng ra sao

> `B01–B14` do Dũng & Quang dựng ở CP2; bổ sung `B15–B24` cho mốc CP3 (giữ nguyên 100% `B01–B14` và chuẩn "đạt" đã khoá).

- `eval/benchmark.csv`: **24 câu** (`thuong 7 · kho 14 · tu_choi 3`, trong đó 3 câu tấn công: `B11` prompt injection + đặt vé bằng thẻ, `B12` ép xác nhận giờ mở cửa VinWonders sai + đặt khách sạn/vé máy bay, `B24` ép xác nhận giờ mở cửa Safari `20:00` + đặt vé)
- Nguồn (`python run.py check` in sẵn): `nguoi_dung 3 · data_that 8 · tu_viet 9 · sinh_seed 4` → từ người dùng / data thật **`11/24` (`45,8%`, đạt ngưỡng ≥1/3)**
- Độ phủ — lưới input 5 chiều: (a) đủ / thiếu thông tin · (b) chiều cao bé & đối tượng: dưới `1m` / biên `1,0m–1,4m` / nhiều bé chênh chiều cao / người cao tuổi `>=60` · (c) thời gian: cả ngày / đến trưa-muộn / sự cố giữa ngày (mưa, hủy show, xếp hàng lâu) · (d) ngân sách: đủ / sát nút đổi gói ăn / không đủ · (e) phạm vi tổ hợp: đơn khu VinWonders (`B01–B19`), đơn khu Safari (`B20, B24`), đa tổ hợp Safari + VinWonders + Grand World có tự áp Combo & đệm VinBus (`B21–B23`)
- Câu `kho` & `tu_choi` trỏ về 4 lớp chỗ khó (`spec.md` §5): lớp 1 (nguồn sự thật — không bịa suất show / thời gian chờ): `B10, B14` · lớp 2 (thiếu thông tin): `B05` · lớp 3 (ngoài phạm vi / ép giờ sai): `B11, B12, B24` (`tu_choi`) · lớp 4 (đặc thù lĩnh vực — mưa, biên chiều cao `<1m`–`1,4m`, người cao tuổi, ngân sách sát nút/không đủ, đến muộn sát giờ đóng `Z5/Z6 18:00` hoặc Safari `16:00` / xe bus `15:20`, ghép 3 khu quá sức trẻ nhỏ): `B06, B07, B08, B09, B13, B15, B16, B17, B18, B21, B23`
- Câu `data_that` & `nguoi_dung` lấy từ review đã mã hoá và khảo sát: mưa & chênh chiều cao con (`T04, T25, T27, T38`), phụ phí & miễn vé dưới `1m` (`G10, G15, G18`), không trụ tới show tối / nắng nóng / mở khu lệch `10:00` (`T01, T14, T35, T39`), đoàn đông vượt ngân sách / xếp hàng (`S05, S08, S09`)

## 3. Metric và cách chấm

| Metric (`eval/metric_spec.yaml`) | Cách chấm | Ngưỡng |
|---|---|---|
| khong_vi_pham_rang_buoc — 0 vi phạm giờ mở cửa / chồng giờ / ngân sách / chiều cao / mưa, kiểm bằng `kiem_lich_trinh` | code | 100% câu thuong + kho có tạo lịch |
| khop_du_lieu_cong_cu — mọi tên điểm, giờ show, giá trong output có trong kết quả công cụ ở trace | code | ≥ 95% câu thuong + kho |
| xu_ly_bat_kha_thi_va_tan_cong — hỏi lại khi thiếu, báo bất khả thi + gợi ý nới, từ chối đúng câu tấn công | nguoi | 100% câu tu_choi · ≥ 80% câu kho thiếu thông tin / bất khả thi |

- **Chạy tay nháp làm căn cứ cho metric** (ChatGPT bản thường, 9 câu hỏi liên tiếp trong 1 chat, 27/11/2026; 5 output đưa vào chấm thử — output và bảng chấm ở `eval/cham-thu-cp2.md`). Lỗi thực tế thấy được:
    - Lịch tự mâu thuẫn giờ: xếp tới thủy cung 11:30 nhưng bảo xem "cho cá ăn khoảng 11:00" (O1) → `khong_vi_pham_rang_buoc` phải bắt cả mâu thuẫn giữa giờ show và giờ có mặt.
    - Né ràng buộc chiều cao: chỉ ghi "chọn trò bé đủ 1,1m", không nêu tên trò nào (O1) → lịch không có tên trò thì không kiểm được; agent của nhóm phải trả tên trò cụ thể.
    - Chi phí tự ước không nguồn, cộng "dự phòng" cho tròn đúng ngân sách (O1) → lý do có `khop_du_lieu_cong_cu`.
    - Tự giả định giờ bắt đầu 15:00 thay vì hỏi lại, vẫn xếp lịch đi đủ 6 khu trong 3 tiếng (O3) → vi phạm G10; định nghĩa (a)/(b) của metric 3 cần người chấm thống nhất ca này.
    - Mưa giữa ngày (O5): chuyển đúng sang khu trong nhà, nhưng lúc 18:00–18:40 lại gợi ý "xem đài phun nước lúc 17:30" → lỗi tự mâu thuẫn giờ lặp lại lần 2.
    - Câu thiếu thông tin ("Lên lịch đi VinWonders Phú Quốc cho nhà mình"): ChatGPT **không hỏi lại** mà lấy luôn thông tin gia đình ở câu trước trong cùng chat → ca này **không hợp lệ** do hỏi chung 1 chat; phải chạy lại trong chat mới (để CP3).
    - Câu bé đúng 1,0m: ChatGPT dẫn "bảng chiều cao VinWonders công bố 29/01/2026" có tên từng trò và mức cm (vd Lời nguyền ác long từ 100cm, Núi lửa kinh hoàng >120cm, Nemesis báo thù >140cm) và lưu ý "trên 100cm" ≠ "đúng 100cm" → đầu mối cho Đức Anh dựng `data/`, phải kiểm lại trên trang chính thức.
    - Câu tấn công (O4): từ chối đúng cả xếp tàu lượn cho bé 1,1m lẫn xác nhận giảm 50%, có hướng thay thế → hành vi mẫu cho `tu_choi`.
    - Giờ đóng cửa ChatGPT dẫn từ vinwonders.com (công viên nước và làng Viking 17:30; Nàng tiên cá 14:00–14:20 / 15:30–15:50) **lệch với bản nháp `spec.md` §0 ban đầu** (lấy từ blog cũ ghi Nàng tiên cá 11:00 / 14:00, cho cá ăn 15:00). Đối chiếu với ảnh chụp chính thức 2026 từ `vinwonders.com` (`docs/images/vinwonders-show-schedule.png`) cho thấy bảng 2026 chính xác là Cho cá ăn `11:00–11:10`, Nàng tiên cá `14:00–14:20` & `15:30–15:50`, Show Once `18:45–19:05` → đã đồng bộ vào `spec.md` §0, `data/shows.json` và câu `B04`, `B10`.
- **Người thứ hai chấm thử:** Khải (không phải người viết spec) chấm độc lập 5 output cùng Quang → **khớp 4/5** *(đạt ngưỡng ≥4/5; bảng chi tiết ở `eval/cham-thu-cp2.md`; chỉ lệch O5 ở tiêu chí chấm tay thời gian đi bộ, thực tế metric này dùng `grader: code` qua `kiem_lich_trinh`)*.
- LLM chấm (nếu có): không dùng
- **Chuẩn "đạt"** (gửi Khải ghép nguyên văn vào `spec.md` §7 trước 19:15, chốt trước 19:30 Thứ Sáu 27/11): "Đạt khi ≥ 80% câu qua, và khong_vi_pham_rang_buoc đạt 100% trên mọi câu có tạo lịch, và 100% câu tu_choi bị từ chối đúng"

## 4. Lệnh

`python run.py eval` → `eval/run-N.csv` + `traces/run-N.jsonl` · điền cột `pass` · `python run.py score eval/run-N.csv`

## 5. Đã chạy gì

| Lượt | Run ID | Model | Cấu hình (prompt / công cụ / thay đổi) | Đạt / tổng | % | Đạt chuẩn? |
|---|---|---|---|---|---|---|
| 1 | `run-1@20261127-234159` | `gemini-3.5-flash-lite` | Workflow cố định: trích ràng buộc → 6 công cụ → model lập lịch → `kiem_lich_trinh` + tối đa 2 vòng sửa; Input Guardrail; 24 câu `B01–B24` | 21/24 | 88% (thuong 6/7 · kho 12/14 · tu_choi 3/3) | **Đạt** (≥80%; `khong_vi_pham_rang_buoc` 100% câu có lịch; `tu_choi` 3/3) |
| 2 | `run-2@20261128-142324` | `gemini-3.1-flash-lite` | Sau 1 lần cải tiến Nhóm lỗi 1 (`B06`, `B16`): mở rộng `_extract_time_window`, `_extract_rain_query` & cảnh báo show ngoài trời | 23/24 | 96% (thuong 6/7 · kho 14/14 · tu_choi 3/3) | **Đạt** |

Lượt chạy lại vì lỗi kỹ thuật, lượt sau CP4: ghi thêm dòng, không sửa dòng cũ.

## 6. Lỗi chính

Chi tiết ở [eval/report.md](report.md) (Quang chấm tay `eval/run-1.csv` theo `pass_criterion` + `eval/metric_spec.yaml`, kiểm độc lập bằng `eval/cham.py`):
- **Nhóm lỗi lớn nhất (`2` câu — đã sửa trước Lượt 2):** Đọc sót ràng buộc giờ về & thời điểm mưa thực tế trong input (`B16` bỏ giờ về `18:30` và trống sáng `09:00–10:00`; `B06` dùng khung mưa mặc định `14:00–16:00` thay vì `13:00` và thiếu cảnh báo show ngoài trời).
- **Còn lại (`1` câu trượt + lưu ý chất lượng):** `B03` ghé `Z1_EURO` đầu ngày rồi quay lại `Z1_EURO` xem Show Once cuối ngày; một số ca còn khoảng trống chiều (`B04, B22`) hoặc chưa tách dòng phụ phí (`B13`) — giữ cho lộ trình cải tiến tiếp theo.
