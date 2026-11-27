# Kế hoạch & Chia việc CP2 — Nhóm Phoenix_1 (Track C · C1)

> **Bài toán:** Lập & tái lập lịch trình 1 ngày tại **VinWonders Phú Quốc** cho gia đình có trẻ nhỏ (`< 1,4m`).
> **Mốc nộp CP2:** **19:30 Thứ Sáu 27/11** (**4 điểm** · Đội trưởng **Nguyễn Viết Mạnh Khải** — mã `2A202603664` nộp form).
> **Khung giờ làm việc:** 17:10 – 19:30 (140 phút, 4 nhịp).

---

## 1. Thông tin nhanh CP2 & Luật khóa cứng

- **Nhóm:** `Phoenix_1` · Lớp: `L3A` · Track: `C` · Repo: `https://github.com/manhkhai205/K5-Day15-L3A-Phoenix_1`
- **Các file mục tiêu cho CP2:**
  - Bằng chứng bước đầu: `evidence/data-mining.md`, `evidence/interviews/`, `evidence/survey/`
  - Cập nhật định hướng: `canvas.md` (dòng 4, dòng 5, dòng `*(CP2)* Đã đổi gì so với CP1`)
  - Thiết kế & chuẩn đạt: `spec.md` (§3–§7)
  - Dữ liệu mẫu & mô tả: `data/`, `data/DATA_CARD.md`
  - Bộ đánh giá: `eval/metric_spec.yaml`, `eval/benchmark.csv` (≥10 câu), `eval/README.md` (mục 1–4)
  - Bản chạy thử khung (AI giả): `codebase/tools.py`, `codebase/agent.py`

> **⚠️ LUẬT KHÓA CỨNG TẠI CP2 (ĐỌC KỸ TRƯỚC KHI LÀM):**
> 1. **Chuẩn "đạt" bằng số trong `spec.md` §7 và `eval/metric_spec.yaml` phải CHỐT & COMMIT trước 19:30.** Tuyệt đối **không sửa** sau CP2 (sửa sau 19:30 → khối R4 bị **0 điểm**).
> 2. **Sau CP2 không được đổi track**, chỉ được thu hẹp lát cắt; mọi thay đổi sau 19:30 đều phải ghi vào changelog ở `spec.md` §10.
> 3. **Tuyệt đối không commit** `.env`, API key, hoặc dữ liệu cá nhân thật (họ tên, SĐT, mã học viên người phỏng vấn, tên tác giả review). Vi phạm bị trừ **−10 điểm**.

---

## 2. Kiến trúc & Công cụ thống nhất (Cặp X và Cặp Y khớp từ đầu)

- **Hình dạng đã chốt:** **Workflow cố định có vòng tự kiểm & sửa** *(không chọn multi-agent vì bài toán có các bước rõ ràng, rẻ hơn, dễ đo lường và kiểm soát token tốt hơn)*.
- **Luồng xử lý 5 bước:**
  1. **Trích ràng buộc từ input:** số người lớn/trẻ em, chiều cao bé, ngân sách tối đa, khung giờ có mặt, sở thích, thời tiết/sự cố. Nếu thiếu thông tin quan trọng (vd: chưa có chiều cao bé hoặc số người) → **hỏi lại 1 câu ngắn** (nguyên tắc HAX **G10**).
  2. **Gọi 5 công cụ chỉ đọc** trong `codebase/tools.py` để lấy dữ liệu thật (tuyệt đối không để model tự nhớ giờ/giá):
     - `tra_diem_choi(phan_khu, chieu_cao_min, trong_nha)` → danh sách trò/điểm, giờ mở–đóng, chiều cao tối thiểu, thời lượng, khu trong/ngoài trời.
     - `tra_lich_show(ngay)` → khung giờ cố định (Nàng tiên cá `11:00–11:10` & `14:00–14:10`, Cho cá ăn `15:00–15:15`, Once Show `18:45–19:05` / `19:00–19:20`), thời gian cần đến sớm.
     - `tra_thoi_tiet(ngay, khung_gio)` → trạng thái nắng/mưa (mưa lớn → đóng trò ngoài trời & công viên nước *Thế giới Lốc xoáy*).
     - `uoc_thoi_gian_di(khu_a, khu_b)` → thời gian di chuyển (phút) giữa 6 phân khu.
     - `tinh_chi_phi(so_nguoi_lon, so_tre_em_1m_1m4, so_tre_duoi_1m, dich_vu)` → tổng chi phí vé + ăn uống + xe đẩy/locker/buggy/Fastpass.
  3. **AI lập / tái lập lịch trình dự kiến** dựa trên dữ liệu trả về từ công cụ *(ở CP2 để `codebase/ai.py` chạy chế độ giả cố định đi trọn luồng)*.
  4. **Chỗ chặn rủi ro (Guardrail bằng code):** `kiem_lich_trinh(lich, rang_buoc)` kiểm **0 vi phạm**:
     - Giờ mở cửa phân khu lệch nhau (toàn công viên `09:00–19:30` vs Cung điện Hải Vương & Công viên nước `10:00–18:00`)
     - Không chồng giờ hoạt động / đủ thời gian di chuyển giữa các khu
     - Tổng chi phí ≤ ngân sách
     - Không xếp trò vượt chiều cao nhỏ nhất của trẻ (trừ khi ghi rõ chia nhóm người lớn đi kèm)
     - Không xếp trò ngoài trời / công viên nước trong khung giờ mưa
  5. **Vòng sửa tối đa 2 vòng:** Nếu `kiem_lich_trinh` trả về danh sách vi phạm → sửa tối đa 2 vòng. Nếu vẫn không khả thi (vd: *"chỉ có 3 tiếng nhưng muốn chơi hết 6 khu"*) → **kết luận không xếp được + gợi ý nới ràng buộc nào** (không xếp bừa).

---

## 3. Quy ước Git & Chủ sở hữu file (tránh xung đột merge)

Chia **2 nhánh từ `main`**, mỗi cặp chỉ sửa file thuộc quyền sở hữu của mình:

| Nhánh | Thành viên | File sở hữu độc quyền |
|---|---|---|
| `cp2-pair-x` | **Khải + Đức Anh** | `spec.md`, `canvas.md`, `data/*`, `codebase/tools.py`, `codebase/agent.py` |
| `cp2-pair-y` | **Quang + Dũng** | `evidence/data-mining.md`, `evidence/interviews/*`, `evidence/survey/*`, `eval/metric_spec.yaml`, `eval/benchmark.csv`, `eval/README.md` |

- **Quy tắc ghép `spec.md` §7:** Cặp Y **không** sửa trực tiếp `spec.md`. Cặp Y chốt chuẩn "đạt" vào `eval/README.md` mục 3 rồi gửi qua chat nhóm; lúc **19:00**, Khải ghép nguyên văn chuẩn "đạt" vào `spec.md` §7 và merge cả 2 nhánh vào `main`.

### Lệnh Git mẫu cho mỗi cặp
```bash
# Cặp X (Khải / Đức Anh)
git checkout main && git pull origin main
git checkout -b cp2-pair-x
# ... làm việc, kiểm tra xong ...
git add spec.md canvas.md data/ codebase/tools.py codebase/agent.py && git commit -m "CP2 pair X: spec, data, codebase skeleton" && git push -u origin cp2-pair-x
```

```bash
# Cặp Y (Quang / Dũng)
git checkout main && git pull origin main
git checkout -b cp2-pair-y
# ... làm việc, kiểm tra xong ...
git add evidence/ eval/metric_spec.yaml eval/benchmark.csv eval/README.md && git commit -m "CP2 pair Y: evidence, metrics, benchmark CP2" && git push -u origin cp2-pair-y
```

---

## 4. Lịch chạy 4 nhịp theo thời gian (17:10 – 19:30)

| Nhịp | Khung giờ | Ai làm | Mục tiêu phải xong |
|---|---|---|---|
| **Nhịp 1** | **17:10 – 17:40** *(30')* | **Cả 4 bạn** (3 mũi song song) | Quang đào 30–60 review Google Maps/Tripadvisor · Dũng mở Google Form khảo sát & phỏng vấn 1–2 bạn ngoài nhóm · Khải & Đức Anh mỗi người phỏng vấn nhanh 1 bạn + chụp ảnh app VinWonders + rà thông số 6 khu. |
| **Nhịp 2** | **17:40 – 18:00** *(20')* | **Cả nhóm họp tổng hợp** | Chốt số bằng chứng đầu + trích dẫn → cập nhật `canvas.md` → thống nhất sơ đồ §4, signature 6 hàm `tools.py`, 4 lớp chỗ khó + 2 câu tấn công → tách 2 nhánh `cp2-pair-x` & `cp2-pair-y`. |
| **Nhịp 3** | **18:00 – 19:00** *(60')* | **2 cặp chạy song song** | **Cặp X:** `data/` + `DATA_CARD.md` + `codebase/` (AI giả đi hết luồng) + `spec.md` §3–§6.<br>**Cặp Y:** chạy tay 10–15 prompt nháp → `eval/metric_spec.yaml` (≥3 metric) + `eval/benchmark.csv` (12–15 câu, xoá `B01–B03`) + `eval/README.md` mục 1–4. |
| **Nhịp 4** | **19:00 – 19:30** *(30')* | **Đổi chéo, merge & nộp** | 2 người khác cặp chấm độc lập 5 output (khớp ≥4/5) → Khải ghép §7 vào `spec.md` → merge 2 nhánh vào `main` → `python run.py` & `python run.py check` → Khải lắp key vào `.env` (local) test `python run.py eval --try` (token > 0) → kiểm `git status` → push `main` & nộp CP2. |

---

## 5. Checklist chia việc chi tiết cho từng thành viên

### 5.1. Nguyễn Viết Mạnh Khải (`2A202603664` · Đội trưởng · Cặp X · nhánh `cp2-pair-x`)
- **File sở hữu:** `canvas.md`, `spec.md`, `codebase/agent.py` (phụ trách merge `main`, test `.env` local & nộp form CP2).
- **Nhịp 1 (17:10 – 17:40):**
  - [ ] Phỏng vấn nhanh 1 bạn ngoài nhóm từng đi công viên chủ đề lớn (10 phút theo `evidence/interviews/TEMPLATE.md`, ghi ẩn danh `P3.md` gửi Dũng trước khi tách nhánh).
  - [ ] Chụp màn hình app *VinWonders* / bảng giờ show công khai (che thông tin cá nhân) để dẫn nguồn ở `spec.md` §0.
- **Nhịp 2 (17:40 – 18:00):**
  - [ ] Điều phối buổi họp 20 phút tổng hợp số bằng chứng đầu & chốt lát cắt.
  - [ ] Cập nhật `canvas.md`: dòng 4 (số bằng chứng đầu + 1 trích dẫn nguyên văn), dòng 5 (lát cắt đã chốt), dòng `*(CP2)* Đã đổi gì so với CP1`.
- **Nhịp 3 (18:00 – 19:00):**
  - [ ] Hoàn thiện `spec.md` **§3** (giải pháp tương tự: app VinWonders, blog/bản đồ giấy, ChatGPT — đáng học, đáng né, điểm khác biệt).
  - [ ] Hoàn thiện `spec.md` **§4**: lát cắt 1 câu + ≥3 điều không làm · sơ đồ Mermaid workflow tự kiểm & sửa · lý do chọn hình dạng và vì sao không chọn multi-agent · bảng 6 công cụ khớp 100% với Đức Anh · mức tự động · chỗ chặn rủi ro · chỗ người duyệt · ≥3 nguyên tắc HAX (bắt buộc **G10**, chỉ rõ vị trí trên sơ đồ) · ghi rõ phần đang giả.
  - [ ] Hoàn thiện `spec.md` **§5** (4 lớp chỗ khó + ≥6 kịch bản + **2 kịch bản tấn công**) và **§6** (4 đường đi của trải nghiệm).
  - [ ] Viết luồng chính trong `codebase/agent.py` (`answer(text)` gọi các tool của Đức Anh + `call_model` chế độ giả + vòng kiểm/sửa `kiem_lich_trinh`).
- **Nhịp 4 (19:00 – 19:30):**
  - [ ] Cùng Quang chấm thử độc lập 5 output mẫu theo `metric_spec.yaml` (cần khớp ≥4/5).
  - [ ] Ghép chuẩn "đạt" từ Cặp Y vào `spec.md` §7; merge `cp2-pair-x` và `cp2-pair-y` vào `main`.
  - [ ] Chạy `python run.py` (đi hết luồng AI giả không lỗi) và `python run.py check`.
  - [ ] Tạo `.env` ở máy (tuyệt đối không commit), lắp API key, chạy thử `python run.py eval --try` xác nhận `tokens_in > 0, tokens_out > 0`.
  - [ ] Kiểm `git status` không lọt `.env`, push `main`, mở link ẩn danh kiểm tra và **nộp form CP2 trước 19:30**.
- **Xong khi:** `main` có đủ commit của cả 2 cặp trước 19:25, `python run.py` chạy thông, `python run.py eval --try` nối model thành công, form CP2 đã gửi.

---

### 5.2. Vũ Đức Anh (`2A202603573` · Thành viên · Cặp X · nhánh `cp2-pair-x`)
- **File sở hữu:** `data/` (vd `data/vinwonders_phuquoc.json`), `data/DATA_CARD.md`, `codebase/tools.py`.
- **Nhịp 1 (17:10 – 17:40):**
  - [ ] Phỏng vấn nhanh 1 bạn ngoài nhóm (10 phút, gửi ghi chép ẩn danh cho Dũng tổng hợp).
  - [ ] Rà soát & chuẩn hoá thông số công khai VinWonders Phú Quốc (6 phân khu, 15–20 trò/điểm tiêu biểu, giờ mở–đóng lệch `09:00–19:30` vs `10:00–18:00`, chiều cao tối thiểu `1,0m–1,4m+`, khu trong/ngoài trời, lịch show Nàng tiên cá / Cho cá ăn / Once Show, giá vé/buffet/xe đẩy/locker/buggy/Fastpass, ma trận thời gian đi bộ giữa 6 khu).
- **Nhịp 2 (17:40 – 18:00):**
  - [ ] Thống nhất với Khải schema dữ liệu trong `data/` và chữ ký (input/output) của 6 hàm công cụ trong `codebase/tools.py`.
- **Nhịp 3 (18:00 – 19:00):**
  - [ ] Dựng file dữ liệu chạy thử trong `data/` (vd `data/vinwonders_phuquoc.json`), **chú ý cài sẵn dữ liệu bẫy thực tế**: phân khu đóng cửa 18:00, trò yêu cầu `≥1,2m`/`1,4m`, show chỉ 10 phút, trạng thái mưa đóng trò ngoài trời (tránh bẫy *"dữ liệu quá sạch"*).
  - [ ] Viết `data/DATA_CARD.md` bản đầu: mục đích, nguồn thông tin công khai (ngày lấy `27/11/2026`), bước xử lý/cách dựng có seed, số dòng/số điểm, nhãn `synthetic`, giới hạn dữ liệu.
  - [ ] Code đủ 6 hàm `@tool` trong `codebase/tools.py` (mỗi hàm có docstring đúng 4 ý: *tên · input · output · không tác động ra ngoài*). Trọng tâm: hàm `kiem_lich_trinh` bắt đủ 5 lỗi (lệch giờ mở cửa, chồng giờ, vượt ngân sách, vượt chiều cao bé, ngoài trời lúc mưa).
- **Nhịp 4 (19:00 – 19:30):**
  - [ ] Chạy thử `python run.py` cùng Khải để xác nhận toàn bộ tool đọc đúng `data/` và trả trace chuẩn.
  - [ ] Đối chiếu bảng công cụ trong `spec.md` §4 khớp 100% tên và input/output trong `codebase/tools.py`.
- **Xong khi:** `codebase/tools.py` không lỗi import/runtime, `kiem_lich_trinh` bắt chuẩn các ca vi phạm, `data/DATA_CARD.md` điền đủ mục.

---

### 5.3. Nguyễn Đình Quang (`2A202603620` · Thành viên · Cặp Y · nhánh `cp2-pair-y`)
- **File sở hữu:** `evidence/data-mining.md`, `eval/metric_spec.yaml`, `eval/README.md` (mục 1–4).
- **Nhịp 1 (17:10 – 17:40):**
  - [ ] Mở trực tiếp trang **VinWonders Phú Quốc** trên **Google Maps** & **Tripadvisor**.
  - [ ] Ghi **trước** cách chọn mẫu vào `evidence/data-mining.md` mục 1 (vd: *"60 review 1–3 sao gần nhất tính đến 27/11/2026"*) và 5 nhãn lỗi vào mục 2 (quá rộng/mệt · lỡ show · vướng chiều cao bé · mưa/nắng gián đoạn · vỡ ngân sách phát sinh).
  - [ ] Đọc, gắn nhãn và đếm mẻ đầu (`x/N`, `%`), lưu ≥3–5 trích dẫn nguyên văn (tối đa 2 câu/review, **bỏ tên người viết**, kèm link nguồn & ngày xem `27/11/2026`).
- **Nhịp 2 (17:40 – 18:00):**
  - [ ] Báo cáo số bằng chứng đầu + 1 trích dẫn nguyên văn nổi bật để Khải cập nhật `canvas.md` dòng 4.
  - [ ] Cùng cả nhóm thống nhất 4 lớp chỗ khó & 2 kịch bản tấn công.
- **Nhịp 3 (18:00 – 19:00):**
  - [ ] Chạy tay 10–15 input nháp qua prompt để ghi danh sách lỗi thực tế (làm căn cứ viết metric).
  - [ ] Viết `eval/metric_spec.yaml` (≥3 metric kiểm chứng được, đủ 5 trường `name`, `definition`, `grader`, `threshold`, `why` bám pain):
    1. `khong_vi_pham_rang_buoc` (`grader: code`) — 0 vi phạm giờ mở cửa/chồng giờ/ngân sách/chiều cao/thời tiết.
    2. `khop_du_lieu_cong_cu` (`grader: code | nguoi`) — mọi tên điểm, giờ show, giá vé khớp 100% kết quả công cụ.
    3. `xu_ly_bat_kha_thi_va_tan_cong` (`grader: nguoi`) — biết hỏi lại khi thiếu thông tin (G10), báo bất khả thi + gợi ý nới khi quá gắt, từ chối đúng câu tấn công.
  - [ ] Soạn **chuẩn "đạt" bằng số** (kèm điều kiện cứng từ Track C) và điền `eval/README.md` mục 1–4; gửi ngay câu chuẩn "đạt" vào nhóm để Khải đưa vào `spec.md` §7 trước 19:15.
- **Nhịp 4 (19:00 – 19:30):**
  - [ ] Cùng Khải (người không viết spec) chấm độc lập **5 output mẫu** theo `metric_spec.yaml`. Nếu khớp `< 4/5`, chỉnh lại định nghĩa ngay trước 19:30; ghi kết quả khớp vào `eval/README.md` mục 3.
  - [ ] Chạy `python run.py check` trên nhánh `cp2-pair-y` xác nhận 0 cảnh báo ở phần `eval/metric_spec.yaml` rồi push.
- **Xong khi:** `eval/metric_spec.yaml` đủ ≥3 metric (không còn `<...>`), hai người chấm thử khớp ≥4/5, `evidence/data-mining.md` có số liệu thật kiểm lại được.

---

### 5.4. Phạm Công Dũng (`2A202603428` · Thành viên · Cặp Y · nhánh `cp2-pair-y`)
- **File sở hữu:** `evidence/interviews/*`, `evidence/survey/*`, `eval/benchmark.csv`.
- **Nhịp 1 (17:10 – 17:40):**
  - [ ] Tạo Google Form khảo sát 8–10 câu theo `evidence/survey/TEMPLATE.md` (chỉ hỏi **hành vi đã xảy ra**: lần đi gần nhất, mất bao lâu chuẩn bị, có lỡ show/vướng chiều cao/mưa không; **không** hỏi *"bạn có thích dùng app này không"*), gửi ngay vào các nhóm lớp / người thân để gom ≥20 phản hồi trước sáng mai.
  - [ ] Phỏng vấn trực tiếp 1–2 bạn ngoài nhóm từng đi VinWonders / công viên chủ đề lớn trong 1 tháng–1 năm qua theo `evidence/interviews/TEMPLATE.md` (ghi file ẩn danh `P1.md`, `P2.md` — **không** ghi họ tên thật/SĐT/mã HV).
- **Nhịp 2 (17:40 – 18:00):**
  - [ ] Gom các file ghi chép phỏng vấn (`P1`–`P3`) + đếm số phản hồi khảo sát ban đầu; đóng góp câu chuyện thực tế vào bảng 4 lớp chỗ khó.
- **Nhịp 3 (18:00 – 19:00):**
  - [ ] Xây dựng `eval/benchmark.csv` bản CP2 (**xoá sạch 3 dòng mẫu `B01, B02, B03`**): viết **12–15 câu thử** (vượt ngưỡng CP2 ≥10 câu), đủ 6 cột `id,input,expected,pass_criterion,type,source`:
    - `thuong` (**5–6 câu**): gia đình có bé `<1,4m`, ngân sách rõ ràng, đủ ngày nắng/có trẻ nhỏ cần nghỉ trưa.
    - `kho` (**≥5 câu**): thiếu chiều cao/số người (phải hỏi lại), mưa đổ lúc 14:00 giữa ngày (phải tái lập sang khu trong nhà), chỉ còn 3 tiếng nhưng đòi chơi hết 6 khu (báo không xếp được + gợi ý nới), ngân sách sát nút (~2,5tr cho 3 người), bé `<1,0m` (miễn phí vé nhưng giới hạn nhiều trò).
    - `tu_choi` (**≥2 câu tấn công**): ép AI nhét trò tàu lượn `≥1,4m` cho bé `1,1m` hoặc tự bịa giá giảm 50%; ép AI đặt/thanh toán vé trực tiếp hoặc sửa giá vé hệ thống.
    - **Nguồn `source`:** **≥1/3 số câu (≥4–5 câu)** phải bắt đầu bằng `nguoi_dung:` (từ `P1`–`P3` / khảo sát) hoặc `data_that:` (từ review Quang đào); còn lại dùng `tu_viet`.
    - **Tiêu chí `pass_criterion`:** viết cụ thể, đọc output là biết Đạt (1) hay Trượt (0), tránh viết chung chung kiểu *"trả lời hay"*.
- **Nhịp 4 (19:00 – 19:30):**
  - [ ] Xuất log phản hồi khảo sát bước đầu (đã bỏ tên/email) vào `evidence/survey/`.
  - [ ] Chạy `python run.py check` trên `cp2-pair-y` kiểm `eval/benchmark.csv` (không còn lỗi thiếu cột, dòng mẫu `B01–B03`, ô trống, sai mã `source`, dưới 10 câu, thiếu `kho`/`tu_choi`, dưới 1/3 nguồn thật).
  - [ ] Rà lại mục 2 của `eval/README.md` cùng Quang (số câu, phân bố nguồn, lưới input 3–5 chiều) rồi commit & push nhánh `cp2-pair-y`.
- **Xong khi:** `eval/benchmark.csv` có ≥10 câu sạch chuẩn `python run.py check` (chỉ còn cảnh báo số câu CP3 cần 20–30 là bình thường), `evidence/interviews/` và `evidence/survey/` đã có dữ liệu bước đầu.

---

## 6. Bảng đối chiếu Checklist tự soát CP2 (Guide 2.5 — 19:15 Khải rà lần cuối)

| # | Hạng mục kiểm tra trước khi nộp CP2 | Chủ sở hữu | Trạng thái |
|---|---|---|---|
| 1 | `canvas.md` đã cập nhật dòng 4 (số đầu + trích dẫn), dòng 5 (lát cắt chốt) và dòng `*(CP2)* Đã đổi gì so với CP1` | Khải | [ ] |
| 2 | Đã bắt đầu thu bằng chứng thật: có số đầu & trích dẫn trong `evidence/data-mining.md`, `evidence/interviews/`, `evidence/survey/` | Quang + Dũng | [ ] |
| 3 | `spec.md` §3–§6 hoàn chỉnh (có sơ đồ kiến trúc §4, bảng 6 công cụ, chỗ chặn rủi ro, chỗ người duyệt, ≥3 nguyên tắc HAX có G10, 4 lớp chỗ khó + 2 tấn công) | Khải | [ ] |
| 4 | `spec.md` §7 đã **chốt chuẩn "đạt" bằng số** và commit trước 19:30 | Khải + Quang | [ ] |
| 5 | `data/` có dữ liệu mẫu + `data/DATA_CARD.md` bản đầu | Đức Anh | [ ] |
| 6 | `eval/benchmark.csv` **≥10 câu** (đã xoá `B01–B03`, đủ `kho` ≥5 / `tu_choi` ≥2 / ≥1/3 nguồn thật) + `eval/metric_spec.yaml` **≥3 metric** + 2 người chấm thử khớp **≥4/5** (ghi ở `eval/README.md`) | Quang + Dũng | [ ] |
| 7 | `python run.py` đi hết luồng AI giả không lỗi; `python run.py check` không còn lỗi `TEAMS.md`, `metric_spec.yaml`, dòng mẫu, dưới 10 câu | Khải + Đức Anh | [ ] |
| 8 | *(Chuẩn bị CP3)* Đã cài `.env` ở máy (không commit) và test `python run.py eval --try` thấy token > 0; `git status` sạch sẽ trước khi push `main` | Khải | [ ] |

---

## 7. Lệnh kiểm tra nhanh trên máy

```powershell
# 1. Kiểm tra format TEAMS.md, metric_spec.yaml và benchmark.csv
python run.py check

# 2. Chạy thử bản chạy thử với AI giả (phải đi trọn luồng, không traceback)
python run.py

# 3. Kiểm tra khung runner (không gọi agent)
python run.py eval --fake

# 4. (Khải chạy local sau khi tạo .env từ .env.example — KHÔNG commit .env)
python run.py eval --try

# 5. Bắt buộc kiểm trước mỗi lần git add / push
git status
```

---

## 8. Bẫy cần tránh & Quy tắc an toàn Track C

- **Không để dữ liệu chạy thử quá "đẹp":** Dữ liệu trong `data/` bắt buộc phải có giờ đóng cửa sớm (`18:00` cho Công viên nước & Thủy cung), trò có giới hạn chiều cao `1,2m–1,4m+` và trạng thái mưa đóng cửa khu ngoài trời — nếu lúc nào cũng mở và hợp lệ hết thì câu thử `kho` sẽ vô nghĩa.
- **Không để LLM tự nhẩm tiền hoặc cộng giờ:** Mọi phép tính tổng vé/phát sinh (`tinh_chi_phi`) và kiểm tra chồng giờ/giờ mở cửa (`kiem_lich_trinh`) **phải chạy bằng code Python** trong `codebase/tools.py`.
- **Không có công cụ tác động ra ngoài:** Toàn bộ công cụ ở C1 là chỉ đọc / kiểm tra / tính toán; AI tuyệt đối không tự đặt vé, không giữ chỗ thanh toán và phải ghi rõ trong `spec.md` §4 phần *"Không làm"*.
- **Bảo mật & ẩn danh:** Khi gửi dữ liệu phỏng vấn hoặc review vào LLM gói miễn phí hoặc commit lên repo công khai, phải bỏ toàn bộ tên người dùng/tên tác giả review, chỉ trích tối đa 2 câu mỗi review và ghi kèm link nguồn + ngày xem.
