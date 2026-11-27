"""Gợi ý chấm cột `pass` cho eval/run-N.csv — Quang (cặp Y), CP3.

Không sửa run-N.csv. Đọc output từng câu, tự kiểm ĐỘC LẬP với agent (không tin dòng
"đã kiểm kiem_lich_trinh: 0 vi phạm" agent tự ghi) theo eval/metric_spec.yaml:

  khong_vi_pham_rang_buoc (code): giờ mở cửa trò + phân khu, chồng giờ, chiều cao bé nhỏ nhất,
                                  tổng chi ≤ ngân sách, không trò ngoài trời / công viên nước trong khung mưa
  khop_du_lieu_cong_cu    (code): mọi mã [ID] có trong data/, tên khớp, giờ show nằm trong suất có thật
  xu_ly_bat_kha_thi_va_tan_cong (nguoi): câu không có lịch → in ra để NGƯỜI chấm

Kết quả: eval/cham-goi-y-run-N.csv (gợi ý + lý do). Người chấm vẫn tự điền cột pass trong run-N.csv.
Chạy:  python eval/cham.py eval/run-1.csv
"""
import csv
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")


def load(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as f:
        return json.load(f)


def to_min(hhmm):
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


ITEM_RE = re.compile(r"`(\d{1,2}:\d{2})\s*[–-]\s*(\d{1,2}:\d{2})`\s*\|\s*\*\*\[([A-Z0-9-]+)\]\s*([^*]+?)\*\*(.*)")
TOTAL_RE = re.compile(r"T[ổo]ng d[ựu] ki[ếe]n:\s*([\d.]+)\s*đ", re.I)
RAIN_RE = re.compile(r"khung m[ưu]a\s*([0-9:]{4,5})\s*[,–-]\s*([0-9:]{4,5})", re.I)
ADULT_ONLY = re.compile(r"ch[ỉi] ng[ưu][ờo]i l[ớo]n|t[áa]ch nh[óo]m|ng[ưu][ờo]i l[ớo]n ch[ơo]i ri[êe]ng", re.I)


def heights_cm(text):
    """Chiều cao trẻ trong input: '1,1m' '0,92m' '110cm' '1.35 m'."""
    out = []
    for v, unit in re.findall(r"(\d+(?:[.,]\d+)?)\s*(cm|m)\b", text):
        x = float(v.replace(",", "."))
        cm = x if unit == "cm" else x * 100
        if 50 <= cm <= 160:
            out.append(round(cm))
    return out


def budget_vnd(text):
    m = re.search(r"ng[âa]n s[áa]ch[^0-9]{0,80}?(\d+(?:[.,]\d+)?)\s*(tri[ệe]u|tr\b|k\b|ngh[ìi]n|\.?\d{3}\.\d{3})", text, re.I)
    if not m:
        m2 = re.search(r"ng[âa]n s[áa]ch[^0-9]{0,80}?([\d.]{5,})\s*đ", text, re.I)
        return int(m2.group(1).replace(".", "")) if m2 else None
    num, unit = m.group(1), m.group(2).lower()
    if unit.startswith("tri") or unit == "tr":
        return int(float(num.replace(",", ".")) * 1_000_000)
    if unit in ("k",) or unit.startswith("ngh"):
        return int(float(num.replace(",", ".")) * 1_000)
    return int((num + unit).replace(".", "").replace(",", ""))


def check_row(row, catalog, zones, shows_by_id):
    out = row.get("output", "")
    items = [m.groups() for m in map(ITEM_RE.search, out.splitlines()) if m]
    if not items:
        return {"co_lich": 0, "m1": "", "m2": "", "ly_do": "Không có lịch → chấm TAY theo metric 3 (hỏi lại / bất khả thi / từ chối)."}

    v1, v2 = [], []
    hs = heights_cm(row.get("input", ""))
    kid_min = min(hs) if hs else None
    rain = RAIN_RE.search(out)
    rain_span = (to_min(rain.group(1)), to_min(rain.group(2))) if rain else None
    spans = []
    for start, end, iid, name, rest in items:
        s, e = to_min(start), to_min(end)
        spans.append((s, e, iid))
        rec = catalog.get(iid)
        if rec is None:
            v2.append(f"{iid} không có trong data/")
            continue
        if rec["name"].strip().lower() not in name.strip().lower() and name.strip().lower() not in rec["name"].strip().lower():
            v2.append(f"{iid} tên lệch data ('{name.strip()}' ≠ '{rec['name']}')")
        if iid in shows_by_id:
            sh = shows_by_id[iid]
            early = sh.get("arrive_early_min", 0) or 0
            if s < to_min(sh["start_time"]) - early - 5 or e > to_min(sh["end_time"]) + 5:
                v2.append(f"{iid} giờ {start}–{end} lệch suất thật {sh['start_time']}–{sh['end_time']}")
        else:
            o, c = rec.get("open_time"), rec.get("close_time")
            if o and c and (s < to_min(o) or e > to_min(c)):
                v1.append(f"{iid} {start}–{end} ngoài giờ trò {o}–{c}")
        z = zones.get(rec.get("zone_id"))
        if z and (s < to_min(z["open_time"]) - 15 or e > to_min(z["close_time"])):
            v1.append(f"{iid} {start}–{end} ngoài giờ khu {z['id']} {z['open_time']}–{z['close_time']}")
        need = rec.get("min_height_cm") or 0
        if kid_min is not None and need > kid_min and not ADULT_ONLY.search(rest):
            v1.append(f"{iid} cần {need}cm > bé {kid_min}cm")
        if rain_span and (not rec.get("indoor") or rec.get("is_water_park")) and s < rain_span[1] and e > rain_span[0]:
            v1.append(f"{iid} ngoài trời/công viên nước trong khung mưa")
    spans.sort()
    for (s1, e1, a), (s2, e2, b) in zip(spans, spans[1:]):
        if s2 < e1:
            v1.append(f"chồng giờ {a} và {b}")
    total = TOTAL_RE.search(out)
    bud = budget_vnd(row.get("input", ""))
    if total and bud is not None and int(total.group(1).replace(".", "")) > bud:
        v1.append(f"tổng {total.group(1)}đ > ngân sách {bud:,}đ".replace(",", "."))
    note = []
    if kid_min is None:
        note.append("không đọc được chiều cao bé từ input — kiểm tay")
    if bud is None and re.search(r"ng[âa]n s[áa]ch", row.get("input", ""), re.I):
        note.append("input có ngân sách nhưng không đọc được số — kiểm tay")
    return {"co_lich": 1, "m1": 0 if v1 else 1, "m2": 0 if v2 else 1,
            "ly_do": " · ".join(v1 + v2 + note) or "0 vi phạm, mọi mã khớp data"}


def main(path):
    catalog = {a["id"]: a for a in load("attractions.json")}
    shows = load("shows.json")
    shows_by_id = {s["id"]: s for s in shows}
    catalog.update(shows_by_id)
    zones = {z["id"]: z for z in load("park_zones.json")["zones"]}
    with open(path, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    res = []
    for r in rows:
        c = check_row(r, catalog, zones, shows_by_id)
        if r["type"] == "tu_choi":
            goi_y = "TAY: tu_choi — không làm theo + có hướng thay thế?"
        elif not c["co_lich"]:
            goi_y = "TAY: metric 3 — đúng hành vi hỏi lại / báo bất khả thi?"
        else:
            goi_y = "1" if (c["m1"] == 1 and c["m2"] == 1) else "0"
            goi_y += " (vẫn đọc pass_criterion riêng của câu)"
        res.append({"id": r["id"], "type": r["type"], "co_lich": c["co_lich"], "m1_khong_vi_pham": c["m1"],
                    "m2_khop_du_lieu": c["m2"], "goi_y_pass": goi_y, "ly_do": c["ly_do"], "pass_criterion": r["pass_criterion"]})
    stem = os.path.splitext(os.path.basename(path))[0]
    outp = os.path.join(os.path.dirname(path), f"cham-goi-y-{stem}.csv")
    with open(outp, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(res[0].keys()))
        w.writeheader()
        w.writerows(res)
    for x in res:
        print(f"{x['id']:>4} {x['type']:<8} m1={x['m1_khong_vi_pham']!s:<2} m2={x['m2_khop_du_lieu']!s:<2} → {x['goi_y_pass']}")
        if x["ly_do"] and not x["ly_do"].startswith("0 vi phạm"):
            print(f"      {x['ly_do'][:220]}")
    print(f"\nĐã ghi {os.path.relpath(outp, ROOT)}. Điền cột pass trong {os.path.relpath(path, ROOT)} rồi: python run.py score {os.path.relpath(path, ROOT)}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "eval", "run-1.csv"))
