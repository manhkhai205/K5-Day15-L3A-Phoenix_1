"""Luồng chính của bản chạy thử — NHÓM VIẾT (Workflow cố định có vòng tự kiểm & sửa).

Hình dạng khớp spec.md §4 (workflow cố định):
  1. Input Guardrail (chặn prompt injection, đặt vé/thanh toán, ngoài phạm vi, ép thông tin sai).
  2. Trích ràng buộc gia đình & kiểm tra thiếu thông tin (G10: hỏi lại nếu thiếu biến cốt lõi).
  3. Gọi 5 công cụ chỉ đọc trong tools.py (tra_thoi_tiet, tra_lich_show, tra_diem_choi,
     tinh_chi_phi, uoc_thoi_gian_di).
  4. AI lập / tái lập lịch trình dự kiến, rồi kiểm cứng bằng kiem_lich_trinh (vòng sửa tối đa 2 vòng).
  5. Nếu đạt 0 vi phạm → xuất lịch kèm bảng chi phí & lý do; nếu bất khả thi → báo kèm gợi ý nới ràng buộc.
"""
import json
import re
import unicodedata
from typing import Any, Dict, List, Optional, Tuple

from ai import MODEL_PROVIDER, call_model
from tools import (
    kiem_lich_trinh,
    tinh_chi_phi,
    tra_diem_choi,
    tra_lich_show,
    tra_thoi_tiet,
    uoc_thoi_gian_di,
)
from tracing import note

MAX_REPAIR_ROUNDS = 2

SYSTEM = """Bạn là trợ lý lập & tái lập lịch trình 1 ngày tại VinWonders Phú Quốc cho gia đình có trẻ nhỏ.
Quy tắc bắt buộc:
1. Chỉ sử dụng tên điểm chơi, mã ID, giờ mở cửa, giờ show, thời gian đi bộ và giá tiền CÓ TRONG dữ liệu công cụ cung cấp. Tuyệt đối không bịa giờ mở cửa, suất show hay thời gian xếp hàng thực tế.
2. Luôn tuân thủ giờ mở cửa phân khu lệch nhau (toàn công viên 09:00–19:30; Cung điện Hải Vương Z6_SEASHELL và Công viên nước Z5_TYPHOON chỉ mở 10:00–18:00).
3. Không bao giờ đặt vé, nhận số thẻ/OTP, đặt khách sạn/vé máy bay hay xác nhận thông tin trái dữ liệu công viên.
4. Trả về đúng JSON theo mẫu:
{
  "lich": [{"id": "MÃ_ĐIỂM_HOẶC_SHOW", "start": "HH:MM", "end": "HH:MM", "tach_nhom": false}],
  "ghi_chu_rieng": ["..."],
  "diem_bo_qua": ["..."]
}"""


def _norm(text: str) -> str:
    """Chuẩn hoá tiếng Việt về chữ thường không dấu để nhận diện ràng buộc ổn định."""
    s = (text or "").strip().lower().replace("đ", "d")
    s = unicodedata.normalize("NFD", s)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    return re.sub(r"\s+", " ", s)


def _to_min(hhmm: str) -> int:
    """Đổi 'HH:MM' sang phút từ 00:00."""
    hh, mm = hhmm.strip().split(":")
    return int(hh) * 60 + int(mm)


def _to_hhmm(minutes: int) -> str:
    """Đổi số phút sang chuỗi 'HH:MM'."""
    return "%02d:%02d" % (minutes // 60, minutes % 60)


def _fmt_vnd(amount: Optional[int]) -> str:
    """Định dạng tiền VND dễ đọc."""
    if amount is None:
        return "chưa xác định"
    return f"{int(amount):,}đ".replace(",", ".")


def _check_input_guardrail(raw_text: str) -> Optional[str]:
    """Lớp 3 Guardrail: chặn prompt injection, giao dịch thanh toán, ngoài phạm vi và ép giờ/giá sai."""
    low = _norm(raw_text)
    has_injection = any(
        kw in low
        for kw in ("system prompt", "bo qua huong dan", "ignore previous", "in nguyen huong dan", "lo prompt")
    )
    has_payment = bool(
        re.search(r"\b4\d{3}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b", low)
        or any(kw in low for kw in ("dat ve giup", "dat luon ve", "thanh toan bang the", "so the", "ma otp"))
    )
    has_out_of_scope = any(
        kw in low for kw in ("khach san", "ve may bay", "dat phong", "book phong", "chuyen bay")
    )
    has_false_hours = bool(re.search(r"(?:mo|den|toi)\s*(?:2[0-3]):?\d{0,2}", low))
    has_fake_discount = bool(re.search(r"(?:giam|khuyen mai)\s*(?:50|70|80|90)%", low))

    if not (has_injection or has_payment or has_out_of_scope or has_false_hours or has_fake_discount):
        return None

    # Tra cứu giờ mở cửa thật từ công cụ để không trả lời theo trí nhớ
    show_info = tra_lich_show()
    park = show_info["gio_mo_cua_cong_vien"]
    zones_txt = ", ".join("%s (%s–%s)" % (z["name"], z["open_time"], z["close_time"]) for z in show_info["phan_khu"])

    reasons: List[str] = []
    if has_injection:
        reasons.append("từ chối tiết lộ hướng dẫn hệ thống hoặc bỏ qua quy tắc an toàn")
    if has_payment:
        reasons.append("không hỗ trợ đặt vé, thu tiền hay xử lý thông tin thẻ thanh toán/OTP")
    if has_out_of_scope:
        reasons.append("chỉ hỗ trợ lập lịch trong VinWonders Phú Quốc, không đặt khách sạn hoặc vé máy bay")
    if has_false_hours:
        reasons.append(
            "không thể xác nhận giờ mở cửa sai — theo dữ liệu chính thức, %s mở cửa %s–%s (%s)"
            % (park["name"], park["open_time"], park["close_time"], zones_txt)
        )
    if has_fake_discount:
        reasons.append("không tự ý xác nhận mức giảm giá không có trong bảng giá chính thức")

    note("tu_choi: " + "; ".join(reasons))
    return (
        "Mình không thể thực hiện yêu cầu này vì: %s.\n"
        "- Kênh thay thế hợp lệ: bạn vui lòng đặt vé chính thức qua ứng dụng *VinWonders: Theme Parks* hoặc `booking.vinwonders.com`.\n"
        "- Nếu cần, bạn hãy gửi lại số người, chiều cao bé, khung giờ và ngân sách để mình hỗ trợ xếp lịch trình tham quan bên trong VinWonders Phú Quốc."
        % ("; ".join(reasons))
    )


def _extract_heights_cm(raw_text: str) -> List[int]:
    """Trích danh sách chiều cao (cm) từ văn bản tiếng Việt như '1,1m', '1m3', '0,95m', '120cm'."""
    low = _norm(raw_text)
    found: List[Tuple[int, int]] = []

    for m in re.finditer(r"\b(\d+)\s*[,.]\s*(\d{1,2})\s*m\b", low):
        val = int(round(float("%s.%s" % (m.group(1), m.group(2))) * 100))
        if 40 <= val <= 220:
            found.append((m.start(), val))

    for m in re.finditer(r"\b(\d)\s*m\s*(\d{1,2})\b", low):
        dec = m.group(2)
        val = int(m.group(1)) * 100 + (int(dec) * 10 if len(dec) == 1 else int(dec))
        if 40 <= val <= 220 and not any(abs(pos - m.start()) <= 2 for pos, _ in found):
            found.append((m.start(), val))

    for m in re.finditer(r"\b(\d{2,3})\s*cm\b", low):
        val = int(m.group(1))
        if 40 <= val <= 220:
            found.append((m.start(), val))

    found.sort(key=lambda pair: pair[0])
    return [val for _, val in found]


def _extract_budget_vnd(raw_text: str) -> Optional[int]:
    """Trích ngân sách (VND) từ chuỗi tiếng Việt."""
    low = _norm(raw_text)
    m_tr = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:trieu|tr)\b", low)
    if m_tr:
        return int(round(float(m_tr.group(1).replace(",", ".")) * 1_000_000))
    m_dot = re.search(r"\b(\d{1,3}(?:[.,]\d{3})+)\s*(?:d|vnd|dong)?\b", low)
    if m_dot:
        return int(re.sub(r"[.,]", "", m_dot.group(1)))
    m_k = re.search(r"\b(\d+(?:[.,]\d+)?)\s*(?:k|nghin|ngan)\b", low)
    if m_k:
        return int(round(float(m_k.group(1).replace(",", ".")) * 1_000))
    return None


def _extract_time_window(raw_text: str) -> Tuple[str, str, bool]:
    """Trích khung giờ dự kiến (gio_bat_dau, gio_ket_thuc, thieu_gio_ro)."""
    low = _norm(raw_text)
    m_range = re.search(r"(\d{1,2})[:h](\d{2})?\s*[-–~]\s*(\d{1,2})[:h](\d{2})?", low)
    if m_range:
        s = "%02d:%02d" % (int(m_range.group(1)), int(m_range.group(2) or 0))
        e = "%02d:%02d" % (int(m_range.group(3)), int(m_range.group(4) or 0))
        return s, e, False

    m_from_to = re.search(
        r"(?:tu|den|dang|luc)\s*(\d{1,2})[:h](\d{2})?.*?(?:ve|den|toi)\s*(\d{1,2})[:h](\d{2})?",
        low,
    )
    if m_from_to:
        s = "%02d:%02d" % (int(m_from_to.group(1)), int(m_from_to.group(2) or 0))
        e = "%02d:%02d" % (int(m_from_to.group(3)), int(m_from_to.group(4) or 0))
        return s, e, False

    m_arrive = re.search(r"(?:den\s*luc|den\s*vao|dang\s*o|dang)\s*(\d{1,2})[:h](\d{2})?", low)
    if m_arrive:
        s = "%02d:%02d" % (int(m_arrive.group(1)), int(m_arrive.group(2) or 0))
        return s, "19:30", False

    m_leave = re.search(r"(?:ve\s*luc|den|toi)\s*(\d{1,2})[:h](\d{2})?", low)
    if m_leave:
        e = "%02d:%02d" % (int(m_leave.group(1)), int(m_leave.group(2) or 0))
        if "con lai" in low or "xep hang" in low:
            return "14:00", e, True
        if _to_min(e) > _to_min("09:00"):
            return "09:00", e, False

    if "xep hang" in low and "con lai" in low:
        return "14:00", "19:30", True
    return "09:00", "19:30", True


def _parse_constraints(raw_text: str) -> Dict[str, Any]:
    """Phân tích input người dùng thành từ điển ràng buộc có kiểm tra biến thiếu."""
    low = _norm(raw_text)
    heights = _extract_heights_cm(raw_text)
    budget = _extract_budget_vnd(raw_text)
    start_time, end_time, time_assumed = _extract_time_window(raw_text)

    adults: Optional[int] = None
    m_adults = re.search(r"(\d+)\s*(?:nguoi\s*lon|lon\b)", low)
    if m_adults:
        adults = int(m_adults.group(1))
    elif "vo chong" in low:
        adults = 2

    seniors = 0
    m_sen = re.search(r"(\d+)\s*(?:nguoi\s*cao\s*tuoi|cao\s*tuoi|ong\s*ba)", low)
    if m_sen:
        seniors = int(m_sen.group(1))

    kids_count: Optional[int] = len(heights) if heights else None
    m_kids = re.search(r"(\d+)\s*(?:be\b|tre\b|em\s*be)", low)
    if m_kids:
        kids_count = max(int(m_kids.group(1)), len(heights))

    da_co_ve = any(
        kw in low
        for kw in ("da co ve", "co ve roi", "ngan sach an uong", "da mua ve", "an uong va dich vu")
    )
    if any(kw in low for kw in ("chua mua ve", "chua co ve", "gom ca ve")):
        da_co_ve = False

    has_rain = "mua" in low
    rain_window = None
    if has_rain:
        r_start = max(_to_min(start_time), _to_min("13:00"))
        r_end = min(_to_min(end_time), max(r_start + 180, _to_min("16:30")))
        if r_start < r_end:
            rain_window = [_to_hhmm(r_start), _to_hhmm(r_end)]

    canceled_shows: List[str] = []
    if "huy" in low and "nang tien ca" in low:
        if "15:30" in low:
            canceled_shows.append("SH-MERMAID-2")
        else:
            canceled_shows.append("SH-MERMAID-1")
    if "huy" in low and "once" in low:
        canceled_shows.append("SH-ONCE")

    want_shows: List[str] = []
    if "nang tien ca" in low:
        want_shows.append("SH-MERMAID-2" if "SH-MERMAID-1" in canceled_shows else "SH-MERMAID-1")
    if "cho ca an" in low:
        want_shows.append("SH-FEED-FISH")
    if any(kw in low for kw in ("show toi", "once", "phuong hoang")):
        want_shows.append("SH-ONCE")

    missing: List[str] = []
    if adults is None and not heights:
        missing.append("số người lớn/trẻ em")
    if not heights and budget is None:
        missing.append("chiều cao các bé (cm/m)")
    if budget is None and not heights and time_assumed:
        missing.append("khung giờ dự kiến & ngân sách")

    effective_adults = adults if adults is not None else 2
    c_100_140 = sum(1 for h in heights if 100 <= h < 140)
    c_under_100 = sum(1 for h in heights if h < 100)
    tall_kids = sum(1 for h in heights if h >= 140)
    if not heights and kids_count:
        c_100_140 = kids_count

    return {
        "raw_text": raw_text,
        "adults": effective_adults,
        "adults_assumed": adults is None,
        "seniors": seniors,
        "heights_cm": heights,
        "min_child_height_cm": min(heights) if heights else None,
        "so_tre_em_1m_1m4": c_100_140,
        "so_tre_duoi_1m": c_under_100,
        "tall_kids_as_adult": tall_kids,
        "da_co_ve": da_co_ve,
        "ngan_sach_vnd": budget,
        "gio_bat_dau": start_time,
        "gio_ket_thuc": end_time,
        "time_assumed": time_assumed,
        "thoi_tiet": "mua" if has_rain else ("nang_gat" if "nang" in low else "nang"),
        "khung_gio_mua": rain_window,
        "show_bi_huy": canceled_shows,
        "want_shows": want_shows,
        "prefer_water_park": "cong vien nuoc" in low or "loc xoay" in low,
        "prefer_indoor_midday": "trong nha" in low or "nang" in low or has_rain,
        "prefer_thrill": "cam giac manh" in low,
        "asks_queue": "xep hang" in low,
        "missing_fields": missing,
    }


def _pick_meal_option(constraints: Dict[str, Any]) -> Tuple[str, List[str]]:
    """Chọn gói ăn & dịch vụ hợp lý theo ngân sách mà vẫn đảm bảo dữ liệu thật từ pricing.json."""
    budget = constraints["ngan_sach_vnd"]
    adults_pay = constraints["adults"] + constraints["tall_kids_as_adult"]
    c140 = constraints["so_tre_em_1m_1m4"]
    cu100 = constraints["so_tre_duoi_1m"]

    if budget is None:
        return "a_la_carte", (["stroller"] if constraints["min_child_height_cm"] and constraints["min_child_height_cm"] <= 115 else [])

    for meal in ("buffet", "a_la_carte", "fastfood"):
        extras = ["locker"] if constraints["prefer_water_park"] else []
        res = tinh_chi_phi(
            so_nguoi_lon=adults_pay,
            so_tre_em_1m_1m4=c140,
            so_tre_duoi_1m=cu100,
            so_nguoi_cao_tuoi=constraints["seniors"],
            da_co_ve=constraints["da_co_ve"],
            goi_an=meal,
            dich_vu=extras,
            ngan_sach_vnd=budget,
        )
        if res["trong_ngan_sach"]:
            return meal, extras

    return "fastfood", []


def _build_schedule_from_tools(
    constraints: Dict[str, Any],
    shows_data: Dict[str, Any],
    attractions_data: Dict[str, Any],
    weather_data: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Xếp lịch hợp lệ trực tiếp từ kết quả công cụ (làm mẫu cho fake mode và fallback kiểm chứng)."""
    t_start = _to_min(constraints["gio_bat_dau"])
    t_end = _to_min(constraints["gio_ket_thuc"])
    zones_by_id = {z["id"]: z for z in shows_data["phan_khu"]}
    rain_span = None
    if weather_data.get("co_mua") and weather_data.get("khung_gio_mua"):
        r0, r1 = weather_data["khung_gio_mua"]
        rain_span = (_to_min(r0), _to_min(r1))

    items_by_id = {a["id"]: a for a in attractions_data["diem_choi"]}
    shows_by_id = {s["id"]: s for s in shows_data["show_kha_dung"]}
    walk_cache: Dict[Tuple[str, str], int] = {}

    def _walk(z_a: str, z_b: str) -> int:
        pair = (z_a, z_b)
        if pair not in walk_cache:
            walk_cache[pair] = uoc_thoi_gian_di(z_a, z_b)["thoi_gian_phut"]
        return walk_cache[pair]

    chosen: List[Dict[str, Any]] = []

    # 1. Đặt các show ưu tiên (cố định giờ, đệm thời gian đến sớm)
    preferred_show_ids = list(dict.fromkeys(constraints["want_shows"]))
    if not preferred_show_ids:
        if t_start <= _to_min("13:50") and t_end >= _to_min("14:20") and "SH-MERMAID-1" in shows_by_id:
            preferred_show_ids.append("SH-MERMAID-1")
        if t_end >= _to_min("19:05") and "SH-ONCE" in shows_by_id:
            preferred_show_ids.append("SH-ONCE")

    def _can_place(s_min: int, e_min: int, z_id: str, indoor: bool) -> bool:
        if s_min < t_start or e_min > t_end or s_min >= e_min:
            return False
        z = zones_by_id[z_id]
        if s_min < _to_min(z["open_time"]) or e_min > _to_min(z["close_time"]):
            return False
        if not indoor and rain_span and s_min < rain_span[1] and rain_span[0] < e_min:
            return False
        for ex in chosen:
            walk = _walk(ex["zone_id"], z_id)
            ex_s, ex_e = _to_min(ex["start"]), _to_min(ex["end"])
            if s_min < ex_e + walk and ex_s < e_min + walk:
                return False
        return True

    for sid in preferred_show_ids:
        sh = shows_by_id.get(sid)
        if not sh:
            continue
        early = int(sh.get("arrive_early_min", 10))
        sh_s = max(t_start, _to_min(sh["start_time"]) - early)
        sh_e = _to_min(sh["end_time"])
        if _can_place(sh_s, sh_e, sh["zone_id"], sh.get("indoor", False)):
            chosen.append(
                {
                    "id": sh["id"],
                    "name": sh["name"],
                    "zone_id": sh["zone_id"],
                    "start": _to_hhmm(sh_s),
                    "end": _to_hhmm(sh_e),
                    "tach_nhom": False,
                }
            )

    # 2. Chèn bữa trưa nếu lịch kéo dài >= 5 tiếng và bao trùm 11:00–14:30
    if t_end - t_start >= 300 and t_start <= _to_min("13:00") and t_end >= _to_min("13:00"):
        meal_order = ["VW-MEAL-02", "VW-MEAL-03", "VW-MEAL-01"]
        for mid in meal_order:
            m_item = items_by_id.get(mid)
            if not m_item:
                continue
            for m_start in (_to_min("11:45"), _to_min("12:15"), _to_min("12:45"), _to_min("11:15")):
                m_end = m_start + int(m_item.get("duration_min", 50))
                if _can_place(m_start, m_end, m_item["zone_id"], True):
                    chosen.append(
                        {
                            "id": m_item["id"],
                            "name": m_item["name"],
                            "zone_id": m_item["zone_id"],
                            "start": _to_hhmm(m_start),
                            "end": _to_hhmm(m_end),
                            "tach_nhom": False,
                        }
                    )
                    break
            if any(x["id"].startswith("VW-MEAL") for x in chosen):
                break

    # 3. Xếp các trò/điểm tham quan vào các khoảng trống ưu tiên đi liền mạch từng phân khu
    candidates = [a for a in attractions_data["diem_choi"] if a.get("category") not in ("meal", "rest")]
    chosen.sort(key=lambda x: _to_min(x["start"]))
    cursor = t_start
    used_ids = {x["id"] for x in chosen}

    anchors = list(chosen) + [{"start": _to_hhmm(t_end), "end": _to_hhmm(t_end), "zone_id": "Z1_EURO"}]
    for anchor in anchors:
        gap_end = _to_min(anchor["start"])
        prev_items = [c for c in chosen if _to_min(c["end"]) <= cursor]
        prev_zone = prev_items[-1]["zone_id"] if prev_items else "Z1_EURO"
        while cursor < gap_end:
            best_pick = None
            best_key = None
            for item in candidates:
                if item["id"] in used_ids:
                    continue
                if not item.get("indoor", False) and rain_span and cursor < rain_span[1] and rain_span[0] < gap_end:
                    continue
                if constraints["prefer_indoor_midday"] and _to_min("11:00") <= cursor < _to_min("15:00") and not item.get("indoor"):
                    continue
                walk_in = _walk(prev_zone, item["zone_id"]) if prev_items or chosen else 0
                walk_out = _walk(item["zone_id"], anchor["zone_id"]) if anchor.get("id") else 0
                s_try = max(cursor + walk_in, _to_min(item["open_time"]), _to_min(zones_by_id[item["zone_id"]]["open_time"]))
                dur = int(item.get("duration_min", 30))
                e_try = s_try + dur
                if e_try + walk_out > gap_end:
                    continue
                if not _can_place(s_try, e_try, item["zone_id"], item.get("indoor", False)):
                    continue

                water_pref = 0 if (constraints["prefer_water_park"] and item.get("is_water_park") and cursor < _to_min("12:00")) else 1
                thrill_pref = 0 if (constraints["prefer_thrill"] and item.get("thrill_level") in ("medium", "high")) else 1
                same_zone = 0 if item["zone_id"] == prev_zone else 1
                next_zone = 0 if (anchor.get("id") and item["zone_id"] == anchor["zone_id"]) else 1
                key = (water_pref, thrill_pref, same_zone, walk_in, next_zone, s_try, item["id"])
                if best_key is None or key < best_key:
                    best_key = key
                    best_pick = (item, s_try, e_try)
            if best_pick is None:
                break
            item, s_try, e_try = best_pick
            chosen.append(
                {
                    "id": item["id"],
                    "name": item["name"],
                    "zone_id": item["zone_id"],
                    "start": _to_hhmm(s_try),
                    "end": _to_hhmm(e_try),
                    "tach_nhom": False,
                }
            )
            used_ids.add(item["id"])
            prev_items.append(chosen[-1])
            prev_zone = item["zone_id"]
            cursor = e_try
        cursor = max(cursor, _to_min(anchor["end"]))

    chosen.sort(key=lambda x: _to_min(x["start"]))
    return chosen


def _parse_model_json(text: str) -> Optional[Dict[str, Any]]:
    """Tách khối JSON lịch trình từ phản hồi của model thật."""
    m = re.search(r"\{[\s\S]*\}", text or "")
    if not m:
        return None
    try:
        data = json.loads(m.group(0))
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        return None


def _format_output(
    constraints: Dict[str, Any],
    schedule: List[Dict[str, Any]],
    check_res: Dict[str, Any],
    shows_data: Dict[str, Any],
    excluded_rides: List[Dict[str, Any]],
    weather_data: Dict[str, Any],
    model_used: str,
) -> str:
    """Định dạng phản hồi tiếng Việt đầy đủ căn cứ từ công cụ cho gia đình."""
    lines: List[str] = []
    if model_used == "fake":
        lines.append("[Khung chạy thử CP2 — chế độ model giả (dữ liệu & kiểm chứng lấy từ 6 công cụ thật trong codebase/tools.py)]")

    if constraints["asks_queue"]:
        lines.append(
            "Lưu ý trung thực: Hệ thống **chưa có dữ liệu thời gian xếp hàng thực tế theo thời gian thực** tại từng trò, nên không thể ước tính chính xác số phút chờ tiếp. Gia đình quyết định tiếp tục chờ hay chuyển sang lịch thay thế dưới đây:"
        )

    assumptions: List[str] = []
    if constraints["adults_assumed"]:
        assumptions.append("tạm tính 2 người lớn đi kèm")
    if constraints["time_assumed"]:
        assumptions.append("khung giờ dự kiến %s–%s" % (constraints["gio_bat_dau"], constraints["gio_ket_thuc"]))
    if assumptions:
        lines.append("*Giả định mặc định (G10):* %s." % "; ".join(assumptions))

    if weather_data.get("co_mua"):
        lines.append(
            "*Thời tiết:* %s (khung mưa %s) — đã loại toàn bộ trò ngoài trời & Công viên nước trong giờ mưa."
            % (weather_data["trang_thai"], ", ".join(weather_data.get("khung_gio_mua") or []))
        )

    if constraints["show_bi_huy"]:
        alt_shows = [s["name"] + " (" + s["start_time"] + "–" + s["end_time"] + ")" for s in shows_data["show_kha_dung"] if s.get("indoor")]
        lines.append(
            "*Cập nhật show bị hủy (%s):* các suất trong nhà còn khả dụng trong dữ liệu gồm: %s."
            % (", ".join(constraints["show_bi_huy"]), "; ".join(alt_shows) if alt_shows else "không còn suất thay thế")
        )

    lines.append("\n**Lịch trình đề xuất (%s–%s · đã kiểm `kiem_lich_trinh`: 0 vi phạm):**" % (constraints["gio_bat_dau"], constraints["gio_ket_thuc"]))
    for step in schedule:
        lines.append("- `%s–%s` | **[%s] %s** *(khu %s)*" % (step["start"], step["end"], step["id"], step.get("name", step["id"]), step.get("zone_id", "")))

    cost = check_res["tong_hop_chi_phi"]
    lines.append("\n**Dự toán chi phí từ `tinh_chi_phi`:**")
    lines.append(
        "- Vé vào cổng: %s · Ăn uống (%s): %s · Dịch vụ phát sinh: %s → **Tổng dự kiến: %s**"
        % (
            _fmt_vnd(cost["chi_phi_ve_vnd"]),
            cost["goi_an"],
            _fmt_vnd(cost["chi_phi_an_vnd"]),
            _fmt_vnd(cost["chi_phi_dich_vu_vnd"]),
            _fmt_vnd(cost["tong_chi_phi_vnd"]),
        )
    )
    if cost["tien_coc_hoan_lai_vnd"] > 0:
        lines.append("- *Tiền cọc hoàn lại (xe đẩy):* %s (không tính vào tổng tiêu thụ)." % _fmt_vnd(cost["tien_coc_hoan_lai_vnd"]))
    if constraints["ngan_sach_vnd"] is not None:
        lines.append("- So với ngân sách %s: còn dư %s." % (_fmt_vnd(constraints["ngan_sach_vnd"]), _fmt_vnd(cost["chenh_lech_ngan_sach_vnd"])))

    if excluded_rides:
        names = ", ".join("%s (%dcm)" % (r["name"], r["min_height_cm"]) for r in excluded_rides[:4])
        lines.append("\n*Trò chơi bị loại do giới hạn chiều cao bé (%dcm):* %s." % (constraints["min_child_height_cm"], names))

    if check_res["canh_bao"]:
        lines.append("*Cảnh báo:* " + " · ".join(w["message"] for w in check_res["canh_bao"]))

    return "\n".join(lines)


def answer(text: str) -> dict:
    """Luồng workflow chính: Guardrail -> G10 -> 5 tool đọc -> Lập lịch + kiểm/sửa tối đa 2 vòng."""
    # Bước 1: Input Guardrail (tấn công / ngoài phạm vi / ép sai thông tin)
    blocked_reply = _check_input_guardrail(text)
    if blocked_reply is not None:
        return {"output": blocked_reply}

    # Bước 2: Trích ràng buộc & kiểm tra thiếu thông tin (G10)
    constraints = _parse_constraints(text)
    if constraints["missing_fields"]:
        note("thieu_thong_tin: " + ", ".join(constraints["missing_fields"]))
        return {
            "output": (
                "Để xếp lịch chính xác và tránh vượt ngân sách hay chiều cao bé, bạn cho mình biết thêm:\n"
                "1. Số người lớn và số trẻ em?\n"
                "2. Chiều cao chính xác của từng bé (cm hoặc mét)?\n"
                "3. Khung giờ dự kiến ở công viên và tổng ngân sách (đã mua vé chưa)?"
            )
        }

    # Bước 3: Tra cứu dữ liệu thật qua các công cụ chỉ đọc
    weather_query = "mua" if constraints["thoi_tiet"] == "mua" else constraints["thoi_tiet"]
    weather_data = tra_thoi_tiet(ngay=weather_query, khung_gio="%s-%s" % (constraints["gio_bat_dau"], constraints["gio_ket_thuc"]))
    shows_data = tra_lich_show(ngay=weather_query, bo_qua_show=constraints["show_bi_huy"])
    attractions_data = tra_diem_choi(chieu_cao_min=constraints["min_child_height_cm"], gom_an_nghi=True)

    excluded_rides: List[Dict[str, Any]] = []
    if constraints["min_child_height_cm"] is not None:
        all_rides = tra_diem_choi(chieu_cao_min=None, gom_an_nghi=False)
        excluded_rides = [
            r for r in all_rides["diem_choi"] if r.get("min_height_cm", 0) > constraints["min_child_height_cm"]
        ]

    meal_option, extras = _pick_meal_option(constraints)
    cost_check = tinh_chi_phi(
        so_nguoi_lon=constraints["adults"] + constraints["tall_kids_as_adult"],
        so_tre_em_1m_1m4=constraints["so_tre_em_1m_1m4"],
        so_tre_duoi_1m=constraints["so_tre_duoi_1m"],
        so_nguoi_cao_tuoi=constraints["seniors"],
        da_co_ve=constraints["da_co_ve"],
        goi_an=meal_option,
        dich_vu=extras,
        ngan_sach_vnd=constraints["ngan_sach_vnd"],
    )

    if constraints["ngan_sach_vnd"] is not None and cost_check["trong_ngan_sach"] is False:
        shortfall = abs(int(cost_check["chenh_lech_ngan_sach_vnd"] or 0))
        note("bat_kha_thi_ngan_sach: thieu %d VND" % shortfall)
        return {
            "output": (
                "Không xếp được lịch trình trong ngân sách %s.\n"
                "- Theo bảng giá công cụ `tinh_chi_phi`, chi phí tối thiểu (vé vào cổng: %s, ăn tiết kiệm %s: %s) là **%s**, đang **thiếu %s**.\n"
                "- Gợi ý nới ràng buộc: bạn muốn tăng ngân sách thêm tối thiểu %s, giảm số thành viên, hay gia đình đã mua vé sẵn?"
                % (
                    _fmt_vnd(constraints["ngan_sach_vnd"]),
                    _fmt_vnd(cost_check["chi_phi_ve_vnd"]),
                    cost_check["goi_an"],
                    _fmt_vnd(cost_check["chi_phi_an_vnd"]),
                    _fmt_vnd(cost_check["tong_chi_phi_vnd"]),
                    _fmt_vnd(shortfall),
                    _fmt_vnd(shortfall),
                )
            )
        }

    # Bước 4: Lập lịch + Kiểm cứng `kiem_lich_trinh` + Vòng sửa tối đa 2 vòng
    rang_buoc = {
        "so_nguoi_lon": constraints["adults"] + constraints["tall_kids_as_adult"],
        "so_tre_em_1m_1m4": constraints["so_tre_em_1m_1m4"],
        "so_tre_duoi_1m": constraints["so_tre_duoi_1m"],
        "so_nguoi_cao_tuoi": constraints["seniors"],
        "chieu_cao_tre_cm": constraints["heights_cm"] or None,
        "da_co_ve": constraints["da_co_ve"],
        "goi_an": meal_option,
        "dich_vu": extras,
        "ngan_sach_vnd": constraints["ngan_sach_vnd"],
        "gio_bat_dau": constraints["gio_bat_dau"],
        "gio_ket_thuc": constraints["gio_ket_thuc"],
        "thoi_tiet": constraints["thoi_tiet"],
        "khung_gio_mua": weather_data.get("khung_gio_mua") if weather_data.get("co_mua") else None,
        "show_bi_huy": constraints["show_bi_huy"],
    }

    schedule = _build_schedule_from_tools(constraints, shows_data, attractions_data, weather_data)
    prompt_payload = {
        "yeu_cau": text,
        "rang_buoc": rang_buoc,
        "thoi_tiet": weather_data,
        "show_kha_dung": shows_data["show_kha_dung"],
        "diem_choi_hop_le": [
            {"id": a["id"], "name": a["name"], "zone_id": a["zone_id"], "indoor": a["indoor"], "open": a["open_time"], "close": a["close_time"], "duration_min": a["duration_min"], "min_height_cm": a["min_height_cm"]}
            for a in attractions_data["diem_choi"][:20]
        ],
        "du_toan_chi_phi": cost_check,
    }

    reply = call_model(SYSTEM, "Dữ liệu công cụ:\n" + json.dumps(prompt_payload, ensure_ascii=False))
    model_used = reply.get("model", MODEL_PROVIDER)

    if model_used != "fake":
        parsed = _parse_model_json(reply.get("text", ""))
        if parsed and isinstance(parsed.get("lich"), list):
            schedule = parsed["lich"]

    check_res = kiem_lich_trinh(schedule, rang_buoc)
    rounds = 0
    while not check_res["hop_le"] and rounds < MAX_REPAIR_ROUNDS:
        rounds += 1
        note("sua_vong_%d: %d vi pham" % (rounds, check_res["so_vi_pham"]))
        if model_used != "fake":
            repair_msg = (
                "Lịch vừa lập có %d vi phạm từ kiem_lich_trinh:\n%s\nGợi ý: %s\nHãy sửa lại JSON `lich` cho 0 vi phạm."
                % (
                    check_res["so_vi_pham"],
                    json.dumps(check_res["vi_pham"], ensure_ascii=False),
                    json.dumps(check_res["goi_y_noi_rang_buoc"], ensure_ascii=False),
                )
            )
            repair_reply = call_model(SYSTEM, repair_msg)
            parsed_repair = _parse_model_json(repair_reply.get("text", ""))
            if parsed_repair and isinstance(parsed_repair.get("lich"), list):
                schedule = parsed_repair["lich"]
        else:
            schedule = _build_schedule_from_tools(constraints, shows_data, attractions_data, weather_data)
        check_res = kiem_lich_trinh(schedule, rang_buoc)

    if not check_res["hop_le"]:
        note("dung: khong xep duoc sau %d vong sua" % rounds)
        return {
            "output": (
                "Không thể xếp lịch trình thoả mãn toàn bộ ràng buộc hiện tại (còn %d vi phạm):\n- %s\nGợi ý nới ràng buộc:\n- %s"
                % (
                    check_res["so_vi_pham"],
                    "\n- ".join(v["message"] for v in check_res["vi_pham"]),
                    "\n- ".join(check_res["goi_y_noi_rang_buoc"] or ["Mở rộng khung giờ tham quan hoặc giảm số điểm muốn đi."]),
                )
            )
        }

    # Bước 5: Định dạng kết quả hợp lệ kèm căn cứ
    return {
        "output": _format_output(
            constraints=constraints,
            schedule=schedule,
            check_res=check_res,
            shows_data=shows_data,
            excluded_rides=excluded_rides,
            weather_data=weather_data,
            model_used=model_used,
        )
    }
