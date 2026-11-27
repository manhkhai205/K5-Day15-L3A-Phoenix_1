# AGENTS.md — Hướng dẫn cho coding agent (JoyPlan AI · Nhóm Phoenix_1)

> Repo nộp bài hackathon AI20K của nhóm **Phoenix_1** (`L3A` · Track `C` — Du lịch): bản chạy thử **JoyPlan AI (`JOYPLAN / AI`)**.

## Repo này là gì

- **Lát cắt được chấm (`spec.md` §4 & §7):** Trợ lý AI lập & tái lập lịch trình tham quan **1 ngày** tại cụm **Phú Quốc United Center** (mặc định **VinWonders Phú Quốc** giữ tương thích `B01–B14`; hỗ trợ thêm **Vinpearl Safari** & **Grand World**) cho gia đình có trẻ nhỏ, có kiểm cứng bằng `kiem_lich_trinh` (`0 vi phạm`).
- **Ranh giới mở rộng (ngoài phạm vi chấm `eval/`):** Tab **Ngày 2 / Ngày 3**, công cụ `tra_khach_san` (dữ liệu phòng mô phỏng `seed=42`) và giao diện `web/`.

## Lệnh

```powershell
# Khung chấm & mô phỏng (chỉ dùng thư viện chuẩn Python 3.10+)
python run.py                    # chạy bản chạy thử CLI
python run.py check              # kiểm eval/benchmark.csv + eval/metric_spec.yaml + TEAMS.md
python run.py eval --try         # thử 3 câu đầu với model thật
python run.py eval               # chạy cả bộ → eval/run-N.csv + traces/run-N.jsonl
python run.py score eval/run-N.csv
python run.py simulate --try     # thử mô phỏng chi phí 10 phiên
python run.py simulate           # mô phỏng chi phí → cost/simulate-N.csv

# Backend FastAPI & Web UI (ngoài khung chuẩn)
python -m pip install -r requirements.txt
uvicorn codebase.api:app --reload --port 8000
cd web; npm install; npm run dev
```

- Test offline không tốn quota: đặt `MODEL_PROVIDER=fake`. Khi đọc `eval/benchmark.csv` bằng Python luôn dùng `encoding="utf-8-sig"`.

## Cấu trúc code

| File / Thư mục | Ai sửa | Hợp đồng & vai trò |
|---|---|---|
| `codebase/agent.py` | nhóm | `plan_day(...)` trả JSON có cấu trúc + `answer(text) -> {"output": str}` gọi lại `plan_day()`, giữ đúng hình dạng `spec.md` §4 |
| `codebase/ai.py` | nhóm | `call_model(system, user) -> {"text", "model", "tokens_in", "tokens_out"}`, giữ `@model_call`; token lấy từ `usage` API, không ước lượng |
| `codebase/tools.py` | nhóm | `7` công cụ chỉ đọc `@tool` (docstring: tên · input · output · tác động ngoài = `Không`); mặc định `to_hop=["vinwonders"]`; `tra_khach_san` ngoài `eval/` |
| `codebase/api.py` | nhóm | `9` endpoint FastAPI khớp `PlanResponse` (`docs/joyplan-architecture.md#L85-L165`), undo stack, luật xoá mốc; `swap`/`remove` bắt buộc qua `kiem_lich_trinh` |
| `data/` | nhóm | `park_zones.json`, `attractions.json`, `shows.json`, `pricing.json`, `weather.json`, `hotels.json`, `media.json`; sửa/thêm phải ghi nguồn & `thật`/`synthetic` vào `data/DATA_CARD.md` |
| `web/` | nhóm | React + Vite + MapLibre GL JS (OpenFreeMap Liberty + polygon `8` phân khu dự phòng mất mạng), tuân thủ `web/src/styles/tokens.css` & `docs/joyplan-architecture.md` |
| `docs/` | nhóm | `joyplan-product.md`, `joyplan-architecture.md`, `data-strategy.md`, `cp3-plan.md`, `ai-usage.md` |
| `codebase/tracing.py`, `eval/run_eval.py`, `cost/simulate.py`, `run.py` | **khung — không sửa** | ghi trace, chạy bộ câu thử, mô phỏng chi phí |

## Luật — agent KHÔNG được làm

- **Bảo mật & file nháp:** Không đọc để in ra hoặc commit `.env`, API key, PII, nguyên file data BTC cấp, `eval/run-try.csv`, `eval/run-mock.csv`, `cost/simulate-try.csv`, `node_modules/`, `.venv/`, `__pycache__/`.
- **Toàn vẹn đánh giá & câu thử:** Không sửa `eval/run-*.csv`, `cost/simulate-*.csv`, `traces/*` đã chạy (trừ điền cột `pass`, `ghi_chu`). Không sửa chuẩn "đạt" (`spec.md` §7), `eval/metric_spec.yaml` sau CP2; không xoá câu trượt, không sửa `B01–B14` hay `expected`, không giấu câu thử vào prompt/code.
- **Trung thực bằng chứng & số liệu:** Không bịa người được phỏng vấn, trích dẫn, câu trả lời khảo sát hay số liệu; số không có nguồn ghi rõ *(tự ước tính)*. Trường `rooms_left` luôn gắn nhãn *"dữ liệu mô phỏng"*.
- **Guardrail & `kiem_lich_trinh`:** Công cụ tác động ra ngoài chỉ tạo nháp/mở link chờ người duyệt; không tự đặt phòng/vé hay thu số thẻ/CVV/OTP. Mọi thay đổi lịch (`plan_day`, `swap`, `remove`) bắt buộc qua `kiem_lich_trinh`.
- **Media Hybrid (`docs/data-strategy.md` §7):** Không tải `.mp4` hay crawl ảnh bản quyền vào repo; video 100% link YouTube embed, ảnh CP3–CP4 chỉ lưu link chính thức trong `data/media.json` kèm fallback `onError`.
- **Ranh giới `eval/` & changelog:** Giữ mặc định `to_hop=["vinwonders"]` tương thích ngược `B01–B14`; thay đổi kiến trúc/dữ liệu đáng kể sau CP2 ghi 1 dòng vào `spec.md` §10.

## Quy ước của nhóm

- **Ngôn ngữ trả lời người dùng:** Tiếng Việt (ngắn gọn, rõ số liệu và căn cứ từ công cụ).
- **Phong cách code / đặt tên:** Python (`codebase/`) dùng `snake_case` + type hints, giữ tên hàm và key tiếng Việt không dấu cho các `@tool` (`tra_diem_choi`, `kiem_lich_trinh`…); Frontend (`web/`) dùng `PascalCase` cho component (`ParkMap.jsx`), `camelCase` cho hàm/biến, tuân thủ `web/src/styles/tokens.css`.
- **Ai duyệt & mức tự chủ của agent:** Thành viên gọi agent tự soát `git diff`, kiểm tra và chịu trách nhiệm phần việc có tên mình. Agent **không tự `git commit`/`push`** và **không tự chạy cả bộ `eval`/`simulate`** khi chưa có lệnh; được phép tự kiểm offline (`MODEL_PROVIDER=fake`, `python run.py check`, `TestClient`) và chạy `python run.py eval --try` (3 câu) khi sửa `codebase/agent.py` hoặc `codebase/ai.py`.
