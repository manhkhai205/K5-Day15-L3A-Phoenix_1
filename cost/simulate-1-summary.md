# Tóm tắt mô phỏng simulate-1@20261128-143602

Do `python run.py simulate` sinh ra — không sửa tay. Chép bảng sang `cost/cost-estimate.md`.

| Persona | Số phiên mô phỏng | Lượt hỏi / phiên | Token vào / phiên | Token ra / phiên | Gọi model / phiên | Gọi công cụ / phiên |
|---|---:|---:|---:|---:|---:|---:|
| lap_lich_1_lan | 30 | 2 | 17139 | 3587 | 4.6 | 25.1 |
| can_nhac_nhieu_phuong_an | 12 | 3 | 21526 | 4414 | 5.8 | 34.3 |
| tai_lap_giua_ngay | 8 | 4 | 25294 | 5108 | 6.6 | 37.8 |

Tỉ lệ đạt dùng để tính: 23/24 (96%) — lượt run-2@20261128-142324

- Tỉ lệ đạt lấy từ lượt nhóm chọn: eval/run-2.csv (--rate-from).

| Model (giá) | Chi phí / phiên | Chi phí / task thành công | Chi phí / câu hỏi đạt | Chi phí / tháng — thấp (1.425 người) | Chi phí / tháng — cơ sở (4.275 người) | Chi phí / tháng — cao (14.250 người) | Chi phí / người / tháng (cơ sở) |
|---|---:|---:|---:|---:|---:|---:|---:|
| gemini-3.1-flash-lite (vào 0.25 · ra 1.5 $/1M) | $0.0109 | $0.0114 | $0.0045 | $42.21 | $126.63 | $422.09 | $0.0296 |
| gemini-3.5-flash-lite (vào 0.3 · ra 2.5 $/1M) | $0.0159 | $0.0166 | $0.0065 | $61.50 | $184.50 | $614.98 | $0.0432 |
| gemini-3.8-flash (vào 0.75 · ra 3.75 $/1M) | $0.0297 | $0.0310 | $0.0121 | $115.01 | $345.02 | $1,150.06 | $0.0807 |

- Chi phí / task thành công = chi phí / phiên ÷ tỉ lệ đạt. Chi phí / câu hỏi đạt = chi phí / phiên ÷ số lượt hỏi trung bình mỗi phiên (2.6) ÷ tỉ lệ đạt — tỉ lệ đạt đo theo từng câu thử.
- Token đo trên model: gemini-3.1-flash-lite. Giá tính theo từng model trong bảng — model khác bộ tách token thì số token thật có thể lệch; ghi rõ "đo trên model X, tính giá model Y" trong cost/cost-estimate.md.
- Phiên lỗi (không tính vào trung bình): 0/50.
