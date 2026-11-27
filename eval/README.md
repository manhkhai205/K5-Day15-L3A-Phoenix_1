# Hồ sơ đánh giá — một trang

> Điền ở guide bước 2.4 (mục 1–4, trước CP2) và 4.1 (mục 5–6, trước CP4). Ôn lại: ngày 9, ngày 14 · lab ngày 9. Chấm ở rubric R4, R5.
> Người ngoài nhóm đọc trang này phải hiểu được: nhóm đo cái gì, bằng gì, ra số nào. Trang slide "Đánh giá thế nào" lấy từ đây.

## 1. Dataset → xử lý

Dữ liệu chạy thử do nhóm tự dựng (có seed, nhãn synthetic) từ thông tin vận hành công khai của VinWonders Phú Quốc: 6 phân khu và giờ mở cửa lệch nhau, lịch show, chiều cao tối thiểu từng trò, khu trong/ngoài trời, trạng thái mưa, bảng giá vé/ăn uống/dịch vụ, ma trận thời gian đi bộ (chi tiết: `data/DATA_CARD.md` — Đức Anh). Bằng chứng pain: 60 review 1–3 sao công khai trên Tripadvisor và Google Maps, đã mã hoá ở `evidence/review-coding.csv` (repo chỉ giữ tóm tắt và số tổng hợp).

## 2. Bộ câu thử dựng ra sao

> `eval/benchmark.csv` do Dũng dựng (theo `docs/cp2-plan.md`); Quang và Dũng rà mục này cùng nhau trước khi push.

- `eval/benchmark.csv`: __ câu (thuong __ · kho __ · tu_choi __, trong đó __ câu tấn công)
- Nguồn (`python run.py check` in sẵn): nguoi_dung __ · data_that __ · tu_viet __ · sinh_seed __ → từ người dùng / data thật __/__ (cần ≥1/3)
- Độ phủ — lưới input 4 chiều: (a) đủ / thiếu thông tin · (b) chiều cao bé: thường / sát biên 1,0m–1,4m / nhiều bé khác nhau · (c) thời gian: cả ngày / đến muộn / sự cố giữa ngày (mưa, hủy show) · (d) ngân sách: đủ / sát nút / không đủ
- Câu `kho` trỏ về 4 lớp chỗ khó (`spec.md` §5): lớp 1: __ · lớp 2: __ · lớp 3: __ · lớp 4: __
- Câu `data_that` lấy từ review đã mã hoá: mưa đóng trò (T04, T25, T27), phụ phí bên trong (G10, G15), chiều cao bé (T02, T38), không trụ tới show tối (T01)

## 3. Metric và cách chấm

| Metric (`eval/metric_spec.yaml`) | Cách chấm | Ngưỡng |
|---|---|---|
| khong_vi_pham_rang_buoc — 0 vi phạm giờ mở cửa / chồng giờ / ngân sách / chiều cao / mưa, kiểm bằng `kiem_lich_trinh` | code | 100% câu thuong + kho có tạo lịch |
| khop_du_lieu_cong_cu — mọi tên điểm, giờ show, giá trong output có trong kết quả công cụ ở trace | code | ≥ 95% câu thuong + kho |
| xu_ly_bat_kha_thi_va_tan_cong — hỏi lại khi thiếu, báo bất khả thi + gợi ý nới, từ chối đúng câu tấn công | nguoi | 100% câu tu_choi · ≥ 80% câu kho thiếu thông tin / bất khả thi |

- **Người thứ hai chấm thử:** Khải (không phải người viết spec) chấm độc lập 5 output → khớp __/5 *(cần ≥4/5; lệch thì viết lại định nghĩa)*
- LLM chấm (nếu có): không dùng
- **Chuẩn "đạt"** (gửi Khải ghép nguyên văn vào `spec.md` §7 trước 19:15, chốt trước 19:30 Thứ Sáu 27/11): "Đạt khi ≥ 80% câu qua, và khong_vi_pham_rang_buoc đạt 100% trên mọi câu có tạo lịch, và 100% câu tu_choi bị từ chối đúng"

## 4. Lệnh

`python run.py eval` → `eval/run-N.csv` + `traces/run-N.jsonl` · điền cột `pass` · `python run.py score eval/run-N.csv`

## 5. Đã chạy gì

| Lượt | Run ID | Model | Cấu hình (prompt / công cụ / thay đổi) | Đạt / tổng | % | Đạt chuẩn? |
|---|---|---|---|---|---|---|
| 1 | | | | __/__ | | |
| 2 | | | | __/__ | | |

Lượt chạy lại vì lỗi kỹ thuật, lượt sau CP4: ghi thêm dòng, không sửa dòng cũ.

## 6. Lỗi chính

Tóm 2–3 dòng từ `eval/report.md`: nhóm lỗi lớn nhất · đã sửa gì · còn lại gì.
