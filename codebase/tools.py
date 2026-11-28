"""Công cụ của bài toán — NHÓM VIẾT. Điền ở guide bước 2.2 (thiết kế) và 3.2 (code).

Mỗi công cụ là một hàm Python có @tool. Docstring ghi đúng 4 ý như sơ đồ ở spec.md §4:
    tên · input · output · có tác động ra ngoài không (gửi tin, sửa dữ liệu, chấm điểm…)
Khung tự ghi mỗi lần gọi công cụ vào trace (tên, input, output rút gọn, thời gian, lỗi).

6 công cụ thống nhất trong docs/cp2-plan.md:
    tra_diem_choi · tra_lich_show · tra_thoi_tiet · uoc_thoi_gian_di · tinh_chi_phi · kiem_lich_trinh
Dữ liệu đọc từ data/ và mô tả tại data/DATA_CARD.md.
"""
import datetime
import json
import os
import re
import unicodedata
import urllib.parse
from typing import Any, Dict, List, Optional, Tuple, Union

from tracing import tool, TOOLS  # noqa: F401

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
_CACHE: Dict[str, Any] = {}

_ZONE_ALIASES = {
    "z1": "Z1_EURO",
    "z1_euro": "Z1_EURO",
    "dai lo chau au": "Z1_EURO",
    "european avenue": "Z1_EURO",
    "z2": "Z2_FAIRY",
    "z2_fairy": "Z2_FAIRY",
    "the gioi dieu ky": "Z2_FAIRY",
    "fairy world": "Z2_FAIRY",
    "z3": "Z3_ADVENTURE",
    "z3_adventure": "Z3_ADVENTURE",
    "the gioi phieu luu": "Z3_ADVENTURE",
    "adventure world": "Z3_ADVENTURE",
    "z4": "Z4_VIKING",
    "z4_viking": "Z4_VIKING",
    "ngoi lang bi mat": "Z4_VIKING",
    "viking": "Z4_VIKING",
    "secret village": "Z4_VIKING",
    "z5": "Z5_TYPHOON",
    "z5_typhoon": "Z5_TYPHOON",
    "the gioi loc xoay": "Z5_TYPHOON",
    "cong vien nuoc": "Z5_TYPHOON",
    "typhoon world": "Z5_TYPHOON",
    "water park": "Z5_TYPHOON",
    "z6": "Z6_SEASHELL",
    "z6_seashell": "Z6_SEASHELL",
    "cung dien hai vuong": "Z6_SEASHELL",
    "thuy cung": "Z6_SEASHELL",
    "the sea shell": "Z6_SEASHELL",
    "aquarium": "Z6_SEASHELL",
    "z7": "Z7_SAFARI",
    "z7_safari": "Z7_SAFARI",
    "safari": "Z7_SAFARI",
    "vinpearl safari": "Z7_SAFARI",
    "vinpearl safari phu quoc": "Z7_SAFARI",
    "vuon thu": "Z7_SAFARI",
    "ban hoang da": "Z7_SAFARI",
    "z8": "Z8_GRANDWORLD",
    "z8_grandworld": "Z8_GRANDWORLD",
    "grand world": "Z8_GRANDWORLD",
    "grandworld": "Z8_GRANDWORLD",
    "grand world phu quoc": "Z8_GRANDWORLD",
    "venice": "Z8_GRANDWORLD",
    "tinh hoa viet nam": "Z8_GRANDWORLD",
    "thanh pho khong ngu": "Z8_GRANDWORLD",
}

_VENUE_ALIASES = {
    "vw": "vinwonders",
    "vinwonder": "vinwonders",
    "vinwonders": "vinwonders",
    "vinwonders phu quoc": "vinwonders",
    "cong vien chu de": "vinwonders",
    "sf": "safari",
    "safari": "safari",
    "vinpearl safari": "safari",
    "vinpearl safari phu quoc": "safari",
    "vuon thu": "safari",
    "ban hoang da": "safari",
    "gw": "grandworld",
    "grandworld": "grandworld",
    "grand world": "grandworld",
    "grand world phu quoc": "grandworld",
    "thanh pho khong ngu": "grandworld",
    "venice": "grandworld",
}

_VENUE_ORDER = ("safari", "vinwonders", "grandworld")

_GW_PAID_ALIASES = {
    "gw_teddy": "gw_teddy",
    "gw-z8-01": "gw_teddy",
    "bao tang gau teddy": "gw_teddy",
    "teddy": "gw_teddy",
    "teddy bear": "gw_teddy",
    "gw_venice_boat": "gw_venice_boat",
    "gw-z8-02": "gw_venice_boat",
    "thuyen gondola": "gw_venice_boat",
    "thuyen venice": "gw_venice_boat",
    "gondola": "gw_venice_boat",
    "gw_tinh_hoa": "gw_tinh_hoa",
    "sh-gw-tinhhoa": "gw_tinh_hoa",
    "tinh hoa viet nam": "gw_tinh_hoa",
    "gw_combo_tinh_hoa_teddy": "gw_combo_tinh_hoa_teddy",
}

_MEAL_ALIASES = {
    "buffet": "buffet",
    "an_buffet": "buffet",
    "a_la_carte": "a_la_carte",
    "mon_le": "a_la_carte",
    "nha_hang": "a_la_carte",
    "fastfood": "fastfood",
    "an_nhanh": "fastfood",
    "do_an_nhanh": "fastfood",
    "tiet_kiem": "fastfood",
    "none": "none",
    "khong_an": "none",
}

_EXTRA_ALIASES = {
    "stroller": "stroller",
    "xe_day": "stroller",
    "locker": "locker",
    "tu_do": "locker",
    "tu_gui_do": "locker",
    "buggy": "buggy",
    "xe_dien": "buggy",
    "fastpass": "fastpass",
    "uu_tien": "fastpass",
    "loi_di_uu_tien": "fastpass",
    "raincoat": "raincoat",
    "ao_mua": "raincoat",
    "drinks_snacks": "drinks_snacks",
    "nuoc_uong": "drinks_snacks",
    "do_an_vat": "drinks_snacks",
}


def _load_json(filename: str) -> Any:
    """Đọc và cache file JSON từ thư mục data/."""
    if filename not in _CACHE:
        path = os.path.join(DATA_DIR, filename)
        with open(path, encoding="utf-8") as f:
            _CACHE[filename] = json.load(f)
    return _CACHE[filename]


def _strip_accents(text: str) -> str:
    """Chuẩn hóa chuỗi tiếng Việt về chữ thường không dấu để khớp alias linh hoạt."""
    s = text.strip().lower().replace("đ", "d")
    s = unicodedata.normalize("NFD", s)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    return re.sub(r"\s+", " ", s)


def _resolve_zone_id(raw_zone: Optional[str]) -> Optional[str]:
    """Chuyển mã hoặc tên phân khu (tiếng Việt/Anh) thành mã chuẩn Z1_EURO..Z6_SEASHELL."""
    if raw_zone is None:
        return None
    cleaned = str(raw_zone).strip()
    if not cleaned:
        return None
    norm = _strip_accents(cleaned)
    norm_underscore = norm.replace(" ", "_")
    if norm in _ZONE_ALIASES:
        return _ZONE_ALIASES[norm]
    if norm_underscore in _ZONE_ALIASES:
        return _ZONE_ALIASES[norm_underscore]
    return cleaned.upper()


def _resolve_venues(raw_venues: Optional[Union[str, List[str], Tuple[str, ...]]]) -> List[str]:
    """Chuẩn hóa danh sách tổ hợp (vinwonders | safari | grandworld); mặc định ['vinwonders']."""
    if raw_venues is None:
        return ["vinwonders"]
    tokens: List[str] = []
    if isinstance(raw_venues, str):
        parts = re.split(r"[,;+|]+", raw_venues)
        tokens = [p.strip() for p in parts if p.strip()]
    elif isinstance(raw_venues, (list, tuple, set)):
        tokens = [str(p).strip() for p in raw_venues if str(p).strip()]
    else:
        raise ValueError("to_hop phải là chuỗi hoặc danh sách tên tổ hợp, nhận được: %r" % (raw_venues,))

    if not tokens:
        return ["vinwonders"]

    found: List[str] = []
    for tok in tokens:
        norm = _strip_accents(tok)
        norm_us = norm.replace(" ", "_")
        if norm in ("all", "ca cum", "3 khu", "ba khu", "united center", "phu quoc united center") or norm_us in ("all", "ca_cum", "united_center"):
            for vid in _VENUE_ORDER:
                if vid not in found:
                    found.append(vid)
            continue
        mapped = _VENUE_ALIASES.get(norm) or _VENUE_ALIASES.get(norm_us)
        if not mapped:
            raise ValueError("Tổ hợp không hợp lệ: %r (hợp lệ: vinwonders, safari, grandworld)" % (tok,))
        if mapped not in found:
            found.append(mapped)

    return [v for v in _VENUE_ORDER if v in found] or ["vinwonders"]


def _normalize_height_cm(val: Optional[Union[int, float]]) -> Optional[int]:
    """Chuẩn hóa chiều cao (chấp nhận cả cm như 110 và mét như 1.1) sang int cm."""
    if val is None:
        return None
    if isinstance(val, bool) or not isinstance(val, (int, float)):
        raise ValueError("Chiều cao phải là số >= 0 (cm hoặc mét), nhận được: %r" % (val,))
    if val < 0:
        raise ValueError("Chiều cao phải >= 0, nhận được: %r" % (val,))
    if 0 < val <= 3.0:
        return int(round(val * 100))
    return int(round(val))


def _parse_time_to_min(time_str: str) -> int:
    """Chuyển chuỗi giờ 'HH:MM' sang tổng số phút trong ngày (0..1439)."""
    if not isinstance(time_str, str):
        raise ValueError("Giờ không hợp lệ (cần chuỗi 'HH:MM'): %r" % (time_str,))
    s = time_str.strip()
    if len(s) != 5 or s[2] != ":" or not (s[:2].isdigit() and s[3:].isdigit()):
        raise ValueError("Định dạng giờ phải là 'HH:MM', nhận được: %r" % (time_str,))
    hh, mm = int(s[:2]), int(s[3:])
    if not (0 <= hh <= 23 and 0 <= mm <= 59):
        raise ValueError("Giá trị giờ/phút vượt phạm vi: %r" % (time_str,))
    return hh * 60 + mm


def _min_to_time(minutes: int) -> str:
    """Chuyển số phút trong ngày sang 'HH:MM'."""
    return "%02d:%02d" % (minutes // 60, minutes % 60)


def _intervals_overlap(a_start: int, a_end: int, b_start: int, b_end: int) -> bool:
    """Kiểm tra hai khoảng thời gian [start, end) có giao nhau không."""
    return a_start < b_end and b_start < a_end


def _parse_rain_window(rain_window: Optional[Union[List[str], Tuple[str, str], str]]) -> Optional[Tuple[int, int]]:
    """Chuyển khung giờ mưa ['HH:MM', 'HH:MM'] hoặc 'HH:MM-HH:MM' sang tuple phút."""
    if rain_window is None:
        return None
    if isinstance(rain_window, str):
        return _parse_time_range(rain_window)
    if not isinstance(rain_window, (list, tuple)) or len(rain_window) != 2:
        raise ValueError("khung_gio_mua phải gồm đúng 2 mốc ['HH:MM', 'HH:MM'], nhận được: %r" % (rain_window,))
    r_start = _parse_time_to_min(rain_window[0])
    r_end = _parse_time_to_min(rain_window[1])
    if r_start >= r_end:
        raise ValueError("khung_gio_mua có giờ bắt đầu >= kết thúc: %r" % (rain_window,))
    return r_start, r_end


def _parse_time_range(khung_gio: Optional[Any]) -> Optional[Tuple[int, int]]:
    """Phân tích khung_gio dạng ['HH:MM', 'HH:MM'], 'HH:MM-HH:MM', 'HH:MM–HH:MM' hoặc 'HH:MM'."""
    if khung_gio is None:
        return None
    if isinstance(khung_gio, (list, tuple)):
        if len(khung_gio) != 2:
            raise ValueError("khung_gio dạng danh sách cần đúng 2 mốc: %r" % (khung_gio,))
        s, e = _parse_time_to_min(khung_gio[0]), _parse_time_to_min(khung_gio[1])
        if s >= e:
            raise ValueError("khung_gio có giờ bắt đầu >= kết thúc: %r" % (khung_gio,))
        return s, e
    if isinstance(khung_gio, str):
        raw = khung_gio.strip()
        if not raw:
            return None
        parts = re.split(r"[-–~]", raw)
        if len(parts) == 2:
            s, e = _parse_time_to_min(parts[0].strip()), _parse_time_to_min(parts[1].strip())
            if s >= e:
                raise ValueError("khung_gio có giờ bắt đầu >= kết thúc: %r" % (khung_gio,))
            return s, e
        if len(parts) == 1:
            t = _parse_time_to_min(parts[0].strip())
            return t, min(t + 60, 23 * 60 + 59)
    raise ValueError("Định dạng khung_gio không hợp lệ: %r" % (khung_gio,))


def _normalize_date_str(ngay: str) -> Optional[str]:
    """Chuẩn hóa ngày YYYY-MM-DD hoặc DD/MM/YYYY sang YYYY-MM-DD."""
    s = ngay.strip()
    m_iso = re.fullmatch(r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})", s)
    if m_iso:
        return "%04d-%02d-%02d" % (int(m_iso.group(1)), int(m_iso.group(2)), int(m_iso.group(3)))
    m_vn = re.fullmatch(r"(\d{1,2})[-/](\d{1,2})[-/](\d{4})", s)
    if m_vn:
        return "%04d-%02d-%02d" % (int(m_vn.group(3)), int(m_vn.group(2)), int(m_vn.group(1)))
    return None


def _get_weather(ngay: Optional[str] = None, khung_gio: Optional[Any] = None) -> Dict[str, Any]:
    """Tra cứu trạng thái thời tiết từ data/weather.json (hỗ trợ ngày cụ thể và từ khóa mưa/nắng)."""
    wdata = _load_json("weather.json")
    conditions = wdata["conditions"]
    default_date = wdata["meta"]["default_date"]
    raw_ngay = (ngay or "").strip()
    query_span = _parse_time_range(khung_gio)

    cond_key: Optional[str] = None
    override_rain_window: Optional[List[str]] = None
    resolved_date = raw_ngay or default_date

    if not raw_ngay:
        cond_key = wdata["scenarios_by_date"].get(default_date, "nang_gat")
    else:
        iso_date = _normalize_date_str(raw_ngay)
        if iso_date is not None:
            resolved_date = iso_date
            if iso_date in wdata["scenarios_by_date"]:
                cond_key = wdata["scenarios_by_date"][iso_date]
            else:
                month = int(iso_date.split("-")[1])
                md = wdata["monthly_default"]
                cond_key = md["rainy_condition"] if month in md["rainy_months"] else md["dry_condition"]
        else:
            norm = _strip_accents(raw_ngay)
            if any(kw in norm for kw in ("mua", "rain", "bao")):
                m_time = re.search(r"(\d{1,2}):(\d{2})", norm)
                if m_time:
                    t_start = _parse_time_to_min("%02d:%02d" % (int(m_time.group(1)), int(m_time.group(2))))
                    dur = 180 if re.search(r"\b(?:to|lon)\b", norm) else 120
                    t_end = min(t_start + dur, _parse_time_to_min("19:30"))
                    override_rain_window = [_min_to_time(t_start), _min_to_time(t_end)]
                    cond_key = "mua_chieu"
                elif "toi" in norm or "once" in norm:
                    cond_key = "mua_toi"
                elif "chieu" in norm or "14h" in norm:
                    cond_key = "mua_chieu"
                elif "ca ngay" in norm or "lon" in norm or "all" in norm:
                    cond_key = "mua_lon"
                elif query_span is not None:
                    override_rain_window = [_min_to_time(query_span[0]), _min_to_time(query_span[1])]
                    cond_key = "mua_chieu"
                else:
                    cond_key = "mua_lon"
            elif "nang gat" in norm or "nang_gat" in norm or "hot" in norm:
                cond_key = "nang_gat"
            elif "nang" in norm or "sunny" in norm:
                cond_key = "nang"
            else:
                cond_key = "nang_gat"

    cond = dict(conditions[cond_key])
    rain_window = override_rain_window or cond.get("khung_gio_mua")
    co_mua = bool(cond["co_mua"])
    dong_ngoai_troi = bool(cond["dong_ngoai_troi"])
    dong_cv_nuoc = bool(cond["dong_cong_vien_nuoc"])
    canh_bao_nang_gat = bool(cond["canh_bao_nang_gat"])

    if query_span is not None:
        if co_mua and rain_window is not None:
            r_s, r_e = _parse_time_to_min(rain_window[0]), _parse_time_to_min(rain_window[1])
            hits = _intervals_overlap(query_span[0], query_span[1], r_s, r_e)
            co_mua = hits
            dong_ngoai_troi = hits and bool(cond["dong_ngoai_troi"])
            dong_cv_nuoc = hits and bool(cond["dong_cong_vien_nuoc"])
        if canh_bao_nang_gat and cond.get("khung_nang_gat"):
            h_s, h_e = _parse_time_to_min(cond["khung_nang_gat"][0]), _parse_time_to_min(cond["khung_nang_gat"][1])
            canh_bao_nang_gat = _intervals_overlap(query_span[0], query_span[1], h_s, h_e)

    return {
        "ngay": resolved_date,
        "khung_gio": "%s–%s" % (_min_to_time(query_span[0]), _min_to_time(query_span[1])) if query_span else "09:00–19:30",
        "trang_thai": cond["trang_thai"],
        "co_mua": co_mua,
        "khung_gio_mua": rain_window,
        "dong_ngoai_troi": dong_ngoai_troi,
        "dong_cong_vien_nuoc": dong_cv_nuoc,
        "canh_bao_nang_gat": canh_bao_nang_gat,
        "ghi_chu": cond["ghi_chu"],
    }


def _compute_cost(
    so_nguoi_lon: int,
    so_tre_em_1m_1m4: int = 0,
    so_tre_duoi_1m: int = 0,
    so_nguoi_cao_tuoi: int = 0,
    da_co_ve: bool = False,
    goi_an: Optional[str] = None,
    dich_vu: Optional[List[str]] = None,
    ngan_sach_vnd: Optional[int] = None,
    to_hop: Optional[Union[str, List[str]]] = None,
    diem_ve_le: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Hàm dùng chung để tính chi phí cho tinh_chi_phi và kiem_lich_trinh."""
    counts = {
        "nguoi_lon": so_nguoi_lon,
        "tre_em_1m_1m4": so_tre_em_1m_1m4,
        "tre_duoi_1m": so_tre_duoi_1m,
        "nguoi_cao_tuoi": so_nguoi_cao_tuoi,
    }
    for k, v in counts.items():
        if not isinstance(v, int) or isinstance(v, bool) or v < 0:
            raise ValueError("Số lượng %s phải là số nguyên >= 0, nhận được: %r" % (k, v))
    paying_persons = so_nguoi_lon + so_tre_em_1m_1m4 + so_nguoi_cao_tuoi
    all_persons = paying_persons + so_tre_duoi_1m
    if all_persons <= 0:
        raise ValueError("Tổng số thành viên phải >= 1.")

    pricing = _load_json("pricing.json")
    resolved_venues = _resolve_venues(to_hop)
    extracted_meal: Optional[str] = None
    extras_tokens: List[str] = []
    for raw_item in (dich_vu or []):
        token_norm = _strip_accents(str(raw_item)).replace(" ", "_")
        if not token_norm:
            continue
        if token_norm in _MEAL_ALIASES and goi_an is None and extracted_meal is None:
            extracted_meal = _MEAL_ALIASES[token_norm]
        elif token_norm in _MEAL_ALIASES and goi_an is not None:
            continue
        else:
            extras_tokens.append(str(raw_item))

    raw_meal = goi_an if goi_an is not None else (extracted_meal or "a_la_carte")
    meal_norm = _strip_accents(str(raw_meal)).replace(" ", "_")
    meal_key = _MEAL_ALIASES.get(meal_norm, meal_norm)
    if meal_key not in pricing["meals"]:
        valid_meals = ", ".join(sorted(pricing["meals"].keys()))
        raise ValueError("goi_an không hợp lệ: %r (hợp lệ: %s)" % (raw_meal, valid_meals))

    def _calc_tier_cost(tier: Dict[str, Any]) -> int:
        return (
            so_nguoi_lon * tier["adult"]
            + so_tre_em_1m_1m4 * tier["child_100_140"]
            + so_nguoi_cao_tuoi * tier["senior"]
            + so_tre_duoi_1m * tier["child_under_100"]
        )

    notes: List[str] = []
    vt = pricing.get("venue_tickets", {})
    has_vw = "vinwonders" in resolved_venues
    has_sf = "safari" in resolved_venues
    combo_savings = 0

    if da_co_ve:
        gate_ticket_cost = 0
        loai_ve = "da_co_ve"
    elif has_vw and has_sf and "combo_vinwonders_safari" in vt:
        gate_ticket_cost = _calc_tier_cost(vt["combo_vinwonders_safari"])
        separate_cost = _calc_tier_cost(vt["vinwonders"]) + _calc_tier_cost(vt["safari"])
        combo_savings += max(0, separate_cost - gate_ticket_cost)
        loai_ve = "combo_vinwonders_safari"
        if combo_savings > 0:
            notes.append(
                "Tự động áp dụng vé Combo 1 ngày VinWonders + Vinpearl Safari: tiết kiệm %sđ so với mua 2 vé lẻ."
                % f"{combo_savings:,}"
            )
    elif has_sf and "safari" in vt:
        gate_ticket_cost = _calc_tier_cost(vt["safari"])
        loai_ve = "safari"
    elif has_vw:
        t = pricing["tickets"]
        gate_ticket_cost = (
            so_nguoi_lon * t["adult"]["price_vnd"]
            + so_tre_em_1m_1m4 * t["child_100_140"]["price_vnd"]
            + so_nguoi_cao_tuoi * t["senior"]["price_vnd"]
            + so_tre_duoi_1m * t["child_under_100"]["price_vnd"]
        )
        loai_ve = "vinwonders"
    else:
        gate_ticket_cost = 0
        loai_ve = "grandworld_free_entry"
        notes.append("Grand World vào cổng miễn phí; chỉ tính vé tại các điểm tham quan/show thu phí riêng nếu chọn.")

    # Tính vé điểm lẻ Grand World (nếu có) và tự ghép Combo Tinh hoa + Gấu Teddy nếu đi cả 2
    gw_catalog = pricing.get("grandworld_paid_items", {})
    paid_set: set = set()
    for raw_p in (diem_ve_le or []):
        p_norm = _strip_accents(str(raw_p))
        mapped_p = _GW_PAID_ALIASES.get(p_norm) or _GW_PAID_ALIASES.get(p_norm.replace(" ", "_"))
        if mapped_p and mapped_p in gw_catalog:
            paid_set.add(mapped_p)

    if ("gw_teddy" in paid_set and "gw_tinh_hoa" in paid_set and "gw_combo_tinh_hoa_teddy" in gw_catalog):
        gw_combo_cost = _calc_tier_cost(gw_catalog["gw_combo_tinh_hoa_teddy"])
        gw_sep_cost = _calc_tier_cost(gw_catalog["gw_teddy"]) + _calc_tier_cost(gw_catalog["gw_tinh_hoa"])
        gw_saved = max(0, gw_sep_cost - gw_combo_cost)
        combo_savings += gw_saved
        paid_set.discard("gw_teddy")
        paid_set.discard("gw_tinh_hoa")
        paid_set.add("gw_combo_tinh_hoa_teddy")
        if gw_saved > 0:
            notes.append(
                "Tự động áp dụng Combo Tinh hoa Việt Nam + Bảo tàng Gấu Teddy (tiết kiệm %sđ)."
                % f"{gw_saved:,}"
            )

    gw_items_cost = sum(_calc_tier_cost(gw_catalog[k]) for k in sorted(paid_set) if k in gw_catalog)
    ticket_cost = gate_ticket_cost + gw_items_cost

    m = pricing["meals"][meal_key]
    meal_cost = (
        so_nguoi_lon * m["adult_vnd"]
        + so_tre_em_1m_1m4 * m["child_100_140_vnd"]
        + so_nguoi_cao_tuoi * m["senior_vnd"]
        + so_tre_duoi_1m * m["child_under_100_vnd"]
    )

    extras_cost = 0
    refundable_deposit = 0
    extras_breakdown: Dict[str, int] = {}
    unknown_extras: List[str] = []

    for raw_extra in extras_tokens:
        norm = _strip_accents(raw_extra)
        key = _EXTRA_ALIASES.get(norm) or _EXTRA_ALIASES.get(norm.replace(" ", "_"))
        spec = pricing["extras"].get(key) if key else None
        if spec is None:
            unknown_extras.append(raw_extra)
            continue
        unit = spec["unit"]
        if unit == "per_item":
            cost = spec["price_vnd"]
        elif unit == "per_paying_person":
            cost = spec["price_vnd"] * paying_persons
        elif unit == "per_person":
            cost = spec["price_vnd"] * all_persons
        else:
            cost = spec["price_vnd"]
        extras_cost += cost
        extras_breakdown[key] = extras_breakdown.get(key, 0) + cost
        if "deposit_refundable_vnd" in spec:
            refundable_deposit += spec["deposit_refundable_vnd"]
            notes.append(
                "%s cần đặt cọc %sđ (hoàn lại khi trả xe, không tính vào tổng chi phí tiêu thụ)."
                % (spec["label"], f"{spec['deposit_refundable_vnd']:,}")
            )

    total_cost = ticket_cost + meal_cost + extras_cost
    within_budget: Optional[bool] = None
    budget_diff: Optional[int] = None
    if ngan_sach_vnd is not None:
        if not isinstance(ngan_sach_vnd, int) or isinstance(ngan_sach_vnd, bool) or ngan_sach_vnd < 0:
            raise ValueError("ngan_sach_vnd phải là số nguyên >= 0, nhận được: %r" % (ngan_sach_vnd,))
        budget_diff = ngan_sach_vnd - total_cost
        within_budget = total_cost <= ngan_sach_vnd

    return {
        "don_vi_tien": pricing["currency"],
        "so_luong_khach": counts,
        "to_hop": resolved_venues,
        "da_co_ve": bool(da_co_ve),
        "loai_ve_ap_dung": loai_ve,
        "tiet_kiem_combo_vnd": combo_savings,
        "goi_an": meal_key,
        "chi_phi_ve_vnd": ticket_cost,
        "chi_phi_an_vnd": meal_cost,
        "chi_phi_dich_vu_vnd": extras_cost,
        "tong_chi_phi_vnd": total_cost,
        "tien_coc_hoan_lai_vnd": refundable_deposit,
        "chi_tiet": {
            "ve_vnd": ticket_cost,
            "ve_vao_cong_vnd": gate_ticket_cost,
            "ve_diem_le_grandworld_vnd": gw_items_cost,
            "an_uong_vnd": meal_cost,
            "dich_vu_vnd": extras_breakdown,
        },
        "dich_vu_khong_ro": unknown_extras,
        "trong_ngan_sach": within_budget,
        "chenh_lech_ngan_sach_vnd": budget_diff,
        "ghi_chu": notes,
    }


def _find_indoor_alternatives(
    attractions: List[Dict[str, Any]],
    min_child_height_cm: Optional[int],
    rain_windows: List[Tuple[int, int]],
    scheduled_ids: set,
    limit: int = 5,
) -> List[Dict[str, Any]]:
    """Tìm điểm trong nhà mở cửa khớp khung giờ mưa và phù hợp chiều cao bé."""
    candidates: List[Tuple[bool, Dict[str, Any]]] = []
    seen = set()
    for item in attractions:
        if not item.get("indoor", False):
            continue
        if min_child_height_cm is not None and min_child_height_cm < item.get("min_height_cm", 0):
            continue
        i_open = _parse_time_to_min(item["open_time"])
        i_close = _parse_time_to_min(item["close_time"])
        fits_window = not rain_windows or any(
            max(i_open, w_s) + min(item.get("duration_min", 25), w_e - w_s) <= min(i_close, w_e)
            for w_s, w_e in rain_windows
        )
        if not fits_window or item["id"] in seen:
            continue
        seen.add(item["id"])
        candidates.append((item["id"] in scheduled_ids, item))

    candidates.sort(key=lambda pair: (pair[0], pair[1].get("category") in ("meal", "rest"), pair[1]["id"]))
    return [
        {
            "id": item["id"],
            "name": item["name"],
            "zone_id": item["zone_id"],
            "open_time": item["open_time"],
            "close_time": item["close_time"],
            "duration_min": item["duration_min"],
            "min_height_cm": item["min_height_cm"],
        }
        for _, item in candidates[:limit]
    ]


def _extract_group_params(rang_buoc: Dict[str, Any]) -> Dict[str, Any]:
    """Chuẩn hóa tham số gia đình từ ràng buộc đầu vào (hỗ trợ cả key tiếng Việt và tiếng Anh)."""
    adults = int(rang_buoc.get("so_nguoi_lon", rang_buoc.get("adults", 1)))
    seniors = int(rang_buoc.get("so_nguoi_cao_tuoi", rang_buoc.get("seniors", 0)))

    raw_heights = rang_buoc.get("chieu_cao_tre_cm", rang_buoc.get("children_heights_cm"))
    heights: List[int] = []
    if raw_heights is not None:
        heights = [_normalize_height_cm(h) for h in raw_heights]
        min_child_height_cm = min(heights) if heights else None
    else:
        raw_min = rang_buoc.get("chieu_cao_min", rang_buoc.get("min_child_height_cm"))
        if raw_min is not None:
            min_child_height_cm = _normalize_height_cm(raw_min)
            heights = [min_child_height_cm]  # type: ignore[list-item]
        else:
            min_child_height_cm = None

    tall_kids_as_adult = sum(1 for h in heights if h >= 140)
    c_100_140 = rang_buoc.get("so_tre_em_1m_1m4", rang_buoc.get("children_100_140"))
    has_explicit_c140 = c_100_140 is not None
    if not has_explicit_c140:
        c_100_140 = sum(1 for h in heights if 100 <= h < 140)
    c_under_100 = rang_buoc.get("so_tre_duoi_1m", rang_buoc.get("children_under_100"))
    if c_under_100 is None:
        c_under_100 = sum(1 for h in heights if h < 100)

    return {
        "adults": adults,
        "adults_for_pricing": adults + (0 if has_explicit_c140 else tall_kids_as_adult),
        "seniors": seniors,
        "heights": heights,
        "min_child_height_cm": min_child_height_cm,
        "children_100_140": int(c_100_140),
        "children_under_100": int(c_under_100),
        "da_co_ve": bool(rang_buoc.get("da_co_ve", rang_buoc.get("already_has_ticket", False))),
        "goi_an": rang_buoc.get("goi_an", rang_buoc.get("meal_option")),
        "dich_vu": rang_buoc.get("dich_vu", rang_buoc.get("extras")) or [],
        "ngan_sach_vnd": rang_buoc.get("ngan_sach_vnd", rang_buoc.get("budget_vnd")),
    }


def _build_budget_relaxations(
    cost_summary: Dict[str, Any],
    budget_vnd: int,
    gp: Dict[str, Any],
    to_hop: Optional[Union[str, List[str]]] = None,
    diem_ve_le: Optional[List[str]] = None,
) -> List[str]:
    """Sinh gợi ý giảm chi phí cụ thể khi vượt ngân sách."""
    over = cost_summary["tong_chi_phi_vnd"] - budget_vnd
    suggestions = [
        "Tổng chi dự kiến %sđ vượt ngân sách %sđ (chênh %sđ)."
        % (f"{cost_summary['tong_chi_phi_vnd']:,}", f"{budget_vnd:,}", f"{over:,}")
    ]
    if cost_summary["goi_an"] != "fastfood":
        alt = _compute_cost(
            so_nguoi_lon=gp["adults_for_pricing"],
            so_tre_em_1m_1m4=gp["children_100_140"],
            so_tre_duoi_1m=gp["children_under_100"],
            so_nguoi_cao_tuoi=gp["seniors"],
            da_co_ve=gp["da_co_ve"],
            goi_an="fastfood",
            dich_vu=gp["dich_vu"],
            ngan_sach_vnd=budget_vnd,
            to_hop=to_hop,
            diem_ve_le=diem_ve_le,
        )
        saved = cost_summary["tong_chi_phi_vnd"] - alt["tong_chi_phi_vnd"]
        if saved > 0:
            suggestions.append(
                "Đổi bữa trưa sang gói tiết kiệm (fastfood/món lẻ) giúp giảm %sđ (còn %sđ)."
                % (f"{saved:,}", f"{alt['tong_chi_phi_vnd']:,}")
            )
    optional_tokens = [
        x for x in gp["dich_vu"]
        if _EXTRA_ALIASES.get(_strip_accents(str(x)).replace(" ", "_")) in ("fastpass", "buggy")
    ]
    if optional_tokens:
        kept = [x for x in gp["dich_vu"] if x not in optional_tokens]
        alt2 = _compute_cost(
            so_nguoi_lon=gp["adults_for_pricing"],
            so_tre_em_1m_1m4=gp["children_100_140"],
            so_tre_duoi_1m=gp["children_under_100"],
            so_nguoi_cao_tuoi=gp["seniors"],
            da_co_ve=gp["da_co_ve"],
            goi_an=cost_summary["goi_an"],
            dich_vu=kept,
            ngan_sach_vnd=budget_vnd,
            to_hop=to_hop,
            diem_ve_le=diem_ve_le,
        )
        saved2 = cost_summary["tong_chi_phi_vnd"] - alt2["tong_chi_phi_vnd"]
        suggestions.append(
            "Bỏ dịch vụ bổ sung %s giúp tiết kiệm %sđ (còn %sđ)."
            % (", ".join(optional_tokens), f"{saved2:,}", f"{alt2['tong_chi_phi_vnd']:,}")
        )
    gw_paid_cost = int(cost_summary.get("chi_tiet", {}).get("ve_diem_le_grandworld_vnd", 0))
    if gw_paid_cost > 0:
        suggestions.append(
            "Giữ các điểm/show miễn phí tại Grand World (dạo phố Venice, Sắc màu Venice 21:30) thay cho điểm thu phí riêng giúp giảm %sđ."
            % f"{gw_paid_cost:,}"
        )
    if not gp["da_co_ve"]:
        suggestions.append(
            "Kiểm tra lại xem gia đình đã mua vé sẵn chưa (đặt da_co_ve=True) hoặc cân nhắc combo vé + buffet qua OTA."
        )
    return suggestions


@tool
def tra_diem_choi(
    phan_khu: Optional[str] = None,
    chieu_cao_min: Optional[Union[int, float]] = None,
    trong_nha: Optional[bool] = None,
    tags: Optional[List[str]] = None,
    mo_luc: Optional[str] = None,
    gom_an_nghi: bool = True,
    to_hop: Optional[Union[str, List[str]]] = None,
) -> Dict[str, Any]:
    """Tên: tra_diem_choi — Tra cứu và lọc điểm chơi, ăn uống, nghỉ ngơi trong cụm Phú Quốc United Center (mặc định VinWonders).
    Input: phan_khu (str | None), chieu_cao_min (int | float | None — cm hoặc mét), trong_nha (bool | None), tags (list[str] | None), mo_luc ("HH:MM" | None), gom_an_nghi (bool), to_hop (str | list[str] | None — 'vinwonders', 'safari', 'grandworld').
    Output: dict gồm so_luong, bi_loai_do_chieu_cao, diem_choi (kèm venue_id, lat, lng, chiều cao tối thiểu, indoor, giờ mở/đóng và cờ can_nguoi_lon_di_kem).
    Tác động ra ngoài: Không (chỉ đọc dữ liệu tĩnh trong data/attractions.json)."""
    height_cm = _normalize_height_cm(chieu_cao_min)
    open_at_min = _parse_time_to_min(mo_luc) if mo_luc is not None else None
    norm_zone = _resolve_zone_id(phan_khu)
    norm_tags = {_strip_accents(str(t)).replace(" ", "_") for t in (tags or []) if str(t).strip()}

    allowed_venues: Optional[set] = None
    if to_hop is not None:
        allowed_venues = set(_resolve_venues(to_hop))
    elif norm_zone is None:
        allowed_venues = {"vinwonders"}

    attractions = _load_json("attractions.json")
    matched: List[Dict[str, Any]] = []
    excluded_by_height = 0

    for item in attractions:
        if allowed_venues is not None and item.get("venue_id", "vinwonders") not in allowed_venues:
            continue
        if not gom_an_nghi and item.get("category") in ("meal", "rest"):
            continue
        if norm_zone and item["zone_id"] != norm_zone:
            continue
        if trong_nha is True and not item.get("indoor", False):
            continue
        if trong_nha is False and item.get("indoor", False):
            continue
        if norm_tags:
            item_tags = {_strip_accents(t).replace(" ", "_") for t in item.get("tags", [])}
            if not (norm_tags & item_tags):
                continue
        if open_at_min is not None:
            if not (_parse_time_to_min(item["open_time"]) <= open_at_min < _parse_time_to_min(item["close_time"])):
                continue

        if height_cm is not None and height_cm < item.get("min_height_cm", 0):
            excluded_by_height += 1
            continue

        row = dict(item)
        comp_below = item.get("companion_required_below_cm", 0)
        row["can_nguoi_lon_di_kem"] = bool(height_cm is not None and comp_below > 0 and height_cm < comp_below)
        matched.append(row)

    return {
        "so_luong": len(matched),
        "bi_loai_do_chieu_cao": excluded_by_height,
        "diem_choi": matched,
    }


@tool
def tra_lich_show(
    ngay: Optional[str] = None,
    phan_khu: Optional[str] = None,
    bo_qua_show: Optional[List[str]] = None,
    to_hop: Optional[Union[str, List[str]]] = None,
) -> Dict[str, Any]:
    """Tên: tra_lich_show — Tra giờ mở cửa công viên/tổ hợp, các phân khu và lịch biểu diễn show cố định kèm tác động thời tiết theo ngày.
    Input: ngay (str | None — 'YYYY-MM-DD' hoặc mô tả thời tiết), phan_khu (str | None), bo_qua_show (list[str] | None), to_hop (str | list[str] | None).
    Output: dict gồm ngay, gio_mo_cua_cong_vien, to_hop, phan_khu, show_kha_dung và show_anh_huong_thoi_tiet.
    Tác động ra ngoài: Không (chỉ đọc data/park_zones.json, data/shows.json và data/weather.json)."""
    zones_data = _load_json("park_zones.json")
    shows_data = _load_json("shows.json")
    weather_info = _get_weather(ngay, None)

    norm_zone = _resolve_zone_id(phan_khu)
    excluded_ids = {str(sid).strip().upper() for sid in (bo_qua_show or []) if str(sid).strip()}
    rain_span = _parse_rain_window(weather_info["khung_gio_mua"]) if weather_info["co_mua"] else None

    if to_hop is not None:
        allowed_venues = set(_resolve_venues(to_hop))
    elif norm_zone is not None:
        matched_zones = [z for z in zones_data["zones"] if z["id"] == norm_zone]
        allowed_venues = {z.get("venue_id", "vinwonders") for z in matched_zones} or {"vinwonders"}
    else:
        allowed_venues = {"vinwonders"}

    zones = [
        z for z in zones_data["zones"]
        if z.get("venue_id", "vinwonders") in allowed_venues and (not norm_zone or z["id"] == norm_zone)
    ]
    available_shows: List[Dict[str, Any]] = []
    weather_impacted: List[Dict[str, Any]] = []

    for show in shows_data:
        if show.get("venue_id", "vinwonders") not in allowed_venues:
            continue
        if show["id"].upper() in excluded_ids:
            continue
        if norm_zone and show["zone_id"] != norm_zone:
            continue
        s_start = _parse_time_to_min(show["start_time"])
        s_end = _parse_time_to_min(show["end_time"])
        affected = (
            not show.get("indoor", False)
            and weather_info["co_mua"]
            and rain_span is not None
            and _intervals_overlap(s_start, s_end, rain_span[0], rain_span[1])
        )
        show_copy = dict(show)
        show_copy["anh_huong_thoi_tiet"] = affected
        if affected:
            weather_impacted.append(show_copy)
        else:
            available_shows.append(show_copy)

    venues_meta = {
        vid: vmeta for vid, vmeta in zones_data.get("venues", {}).items() if vid in allowed_venues
    }

    return {
        "ngay": weather_info["ngay"],
        "gio_mo_cua_cong_vien": zones_data["park"],
        "to_hop": venues_meta,
        "phan_khu": zones,
        "show_kha_dung": available_shows,
        "show_anh_huong_thoi_tiet": weather_impacted,
    }


@tool
def tra_thoi_tiet(ngay: Optional[str] = None, khung_gio: Optional[Any] = None) -> Dict[str, Any]:
    """Tên: tra_thoi_tiet — Tra cứu trạng thái nắng/mưa và ảnh hưởng tới trò ngoài trời, Công viên nước theo ngày và khung giờ.
    Input: ngay (str | None — 'YYYY-MM-DD' hoặc từ khóa như 'mưa 14:00'), khung_gio (str | list | None — vd '14:00-16:00').
    Output: dict gồm ngay, khung_gio, trang_thai, co_mua, khung_gio_mua, dong_ngoai_troi, dong_cong_vien_nuoc, canh_bao_nang_gat, ghi_chu.
    Tác động ra ngoài: Không (chỉ đọc kịch bản mô phỏng tĩnh trong data/weather.json)."""
    return _get_weather(ngay=ngay, khung_gio=khung_gio)


def _get_transfer_min(khu_a: str, khu_b: str) -> Tuple[int, str]:
    """Tra nội bộ (không @tool) thời gian di chuyển (phút) và phương tiện ('di_bo' | 'vinbus') giữa 2 phân khu."""
    zones_data = _load_json("park_zones.json")
    zones_by_id = {z["id"]: z for z in zones_data["zones"]}
    matrix = zones_data["walking_matrix_min"]

    z_a = _resolve_zone_id(khu_a)
    z_b = _resolve_zone_id(khu_b)
    if z_a not in zones_by_id or z_b not in zones_by_id:
        valid = ", ".join("%s (%s)" % (z["id"], z["name"]) for z in zones_data["zones"])
        raise ValueError("Phân khu không hợp lệ (%r, %r). Các phân khu hợp lệ: %s" % (khu_a, khu_b, valid))

    walk_min = matrix[z_a][z_b]
    v_a = zones_by_id[z_a].get("venue_id", "vinwonders")
    v_b = zones_by_id[z_b].get("venue_id", "vinwonders")
    return walk_min, ("vinbus" if v_a != v_b else "di_bo")


@tool
def uoc_thoi_gian_di(khu_a: str, khu_b: str) -> Dict[str, Any]:
    """Tên: uoc_thoi_gian_di — Ước lượng thời gian di chuyển (phút) giữa hai phân khu/tổ hợp trong cụm Phú Quốc United Center.
    Input: khu_a (str — mã hoặc tên phân khu xuất phát), khu_b (str — mã hoặc tên phân khu đích).
    Output: dict gồm khu_a, ten_khu_a, khu_b, ten_khu_b, phuong_tien ('di_bo' | 'vinbus'), thoi_gian_phut, ghi_chu.
    Tác động ra ngoài: Không (chỉ đọc ma trận di chuyển tĩnh 8x8 trong data/park_zones.json)."""
    zones_data = _load_json("park_zones.json")
    zones_by_id = {z["id"]: z for z in zones_data["zones"]}
    z_a = _resolve_zone_id(khu_a)
    z_b = _resolve_zone_id(khu_b)
    walk_min, mode = _get_transfer_min(khu_a, khu_b)
    is_cross_venue = mode == "vinbus"

    return {
        "khu_a": z_a,
        "ten_khu_a": zones_by_id[z_a]["name"],  # type: ignore[index]
        "khu_b": z_b,
        "ten_khu_b": zones_by_id[z_b]["name"],  # type: ignore[index]
        "phuong_tien": mode,
        "thoi_gian_phut": walk_min,
        "ghi_chu": (
            "Di chuyển liên tổ hợp bằng xe điện VinBus miễn phí / taxi nội khu (đã gồm thời gian chờ xe ~5–10 phút)."
            if is_cross_venue
            else "Ước lượng đi bộ trung bình cho gia đình có trẻ nhỏ (tăng thêm 3–5 phút vào giờ cao điểm)."
        ),
    }


@tool
def tinh_chi_phi(
    so_nguoi_lon: int,
    so_tre_em_1m_1m4: int = 0,
    so_tre_duoi_1m: int = 0,
    dich_vu: Optional[List[str]] = None,
    so_nguoi_cao_tuoi: int = 0,
    da_co_ve: bool = False,
    goi_an: Optional[str] = None,
    ngan_sach_vnd: Optional[int] = None,
    to_hop: Optional[Union[str, List[str]]] = None,
    diem_ve_le: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Tên: tinh_chi_phi — Tính tổng chi phí vé (tự áp Combo VinWonders+Safari nếu đi cả 2, vé lẻ Grand World), ăn uống, phụ phí và đối chiếu ngân sách.
    Input: so_nguoi_lon (int), so_tre_em_1m_1m4 (int), so_tre_duoi_1m (int), dich_vu (list[str] | None), so_nguoi_cao_tuoi (int), da_co_ve (bool), goi_an (str | None), ngan_sach_vnd (int | None), to_hop (str | list[str] | None), diem_ve_le (list[str] | None).
    Output: dict gồm loai_ve_ap_dung, tiet_kiem_combo_vnd, chi_phi_ve_vnd, chi_phi_an_vnd, chi_phi_dich_vu_vnd, tong_chi_phi_vnd, tien_coc_hoan_lai_vnd, chi_tiet, dich_vu_khong_ro, trong_ngan_sach, chenh_lech_ngan_sach_vnd.
    Tác động ra ngoài: Không (chỉ đọc bảng giá tĩnh trong data/pricing.json và tính toán)."""
    return _compute_cost(
        so_nguoi_lon=so_nguoi_lon,
        so_tre_em_1m_1m4=so_tre_em_1m_1m4,
        so_tre_duoi_1m=so_tre_duoi_1m,
        so_nguoi_cao_tuoi=so_nguoi_cao_tuoi,
        da_co_ve=da_co_ve,
        goi_an=goi_an,
        dich_vu=dich_vu,
        ngan_sach_vnd=ngan_sach_vnd,
        to_hop=to_hop,
        diem_ve_le=diem_ve_le,
    )


@tool
def kiem_lich_trinh(lich: List[Dict[str, Any]], rang_buoc: Dict[str, Any]) -> Dict[str, Any]:
    """Tên: kiem_lich_trinh — Guardrail kiểm tra toàn bộ ràng buộc cứng/mềm của lịch trình dự kiến và gợi ý điểm trong nhà hoặc nới ràng buộc khi lỗi.
    Input: lich (list[{id/ma, start/bat_dau, end/ket_thuc, tach_nhom/split_group?}]), rang_buoc (dict thông số nhóm, ngân sách, khung giờ, thời tiết, show hủy).
    Output: dict gồm hop_le (bool), so_vi_pham, vi_pham, canh_bao, tong_hop_chi_phi, goi_y_trong_nha, goi_y_noi_rang_buoc.
    Tác động ra ngoài: Không (chỉ kiểm tra bằng code trên dữ liệu tĩnh của công viên)."""
    zones_data = _load_json("park_zones.json")
    attractions = _load_json("attractions.json")
    shows = _load_json("shows.json")

    zones_by_id = {z["id"]: z for z in zones_data["zones"]}
    walking_matrix = zones_data["walking_matrix_min"]
    catalog: Dict[str, Dict[str, Any]] = {a["id"]: a for a in attractions}
    for s in shows:
        catalog[s["id"]] = s

    gp = _extract_group_params(rang_buoc)
    raw_weather = rang_buoc.get("thoi_tiet", rang_buoc.get("weather"))
    raw_rain_win = rang_buoc.get("khung_gio_mua", rang_buoc.get("rain_window"))
    ngay = rang_buoc.get("ngay", rang_buoc.get("date"))

    if raw_weather is None and raw_rain_win is None and ngay is not None:
        w_info = _get_weather(ngay, None)
        if w_info["co_mua"]:
            weather_norm = "rain"
            rain_span = _parse_rain_window(w_info["khung_gio_mua"])
        elif w_info["canh_bao_nang_gat"]:
            weather_norm = "hot"
            rain_span = None
        else:
            weather_norm = "sunny"
            rain_span = None
    else:
        w_str = _strip_accents(str(raw_weather or "sunny")).replace(" ", "_")
        if "mua" in w_str or "rain" in w_str:
            weather_norm = "rain"
        elif "gat" in w_str or "hot" in w_str:
            weather_norm = "hot"
        else:
            weather_norm = "sunny"
        rain_span = _parse_rain_window(raw_rain_win)
        if rain_span is None and "chieu" in w_str:
            rain_span = (_parse_time_to_min("14:00"), _parse_time_to_min("16:00"))
        elif rain_span is None and "toi" in w_str:
            rain_span = (_parse_time_to_min("18:30"), _parse_time_to_min("19:30"))

    raw_canceled = rang_buoc.get("show_bi_huy", rang_buoc.get("canceled_shows")) or []
    canceled_set = {str(sid).strip().upper() for sid in raw_canceled if str(sid).strip()}

    raw_venues = rang_buoc.get("to_hop", rang_buoc.get("venues"))
    explicit_venues = set(_resolve_venues(raw_venues)) if raw_venues is not None else set()
    scheduled_venues: set = set()
    for entry in (lich or []):
        eid = str(entry.get("id", entry.get("ma", entry.get("ma_diem", "")))).strip()
        emeta = catalog.get(eid)
        if emeta and emeta.get("zone_id") in zones_by_id:
            scheduled_venues.add(zones_by_id[emeta["zone_id"]].get("venue_id", "vinwonders"))
    combined_venues = scheduled_venues | explicit_venues
    active_venues = [v for v in _VENUE_ORDER if v in combined_venues] or ["vinwonders"]

    default_end = (
        "22:00" if "grandworld" in active_venues
        else ("16:00" if active_venues == ["safari"] else "19:30")
    )
    start_time = str(rang_buoc.get("gio_bat_dau", rang_buoc.get("start_time", "09:00")))
    end_time = str(rang_buoc.get("gio_ket_thuc", rang_buoc.get("end_time", default_end)))
    trip_start = _parse_time_to_min(start_time)
    trip_end = _parse_time_to_min(end_time)

    violations: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []
    relaxations: List[str] = []
    rain_hit_windows: List[Tuple[int, int]] = []
    height_violated_zones: List[str] = []
    parsed_items: List[Dict[str, Any]] = []
    scheduled_ids = set()

    if trip_start >= trip_end:
        violations.append({
            "code": "INVALID_TIME",
            "item_id": None,
            "message": "Khung giờ chuyến đi không hợp lệ (%s >= %s)." % (start_time, end_time),
        })

    if not lich:
        violations.append({
            "code": "EMPTY_ITINERARY",
            "item_id": None,
            "message": "Lịch trình đang trống, cần ít nhất 1 điểm tham quan hoặc show.",
        })

    for idx, entry in enumerate(lich or []):
        item_id = str(entry.get("id", entry.get("ma", entry.get("ma_diem", "")))).strip()
        start_str = str(entry.get("start", entry.get("bat_dau", entry.get("gio_bat_dau", "")))).strip()
        end_str = str(entry.get("end", entry.get("ket_thuc", entry.get("gio_ket_thuc", "")))).strip()
        split_group = bool(entry.get("tach_nhom", entry.get("split_group", False)))

        meta = catalog.get(item_id)
        if meta is None:
            violations.append({
                "code": "UNKNOWN_ID",
                "item_id": item_id or None,
                "index": idx,
                "message": "Mã điểm chơi/show '%s' không tồn tại trong dữ liệu VinWonders Phú Quốc." % item_id,
            })
            continue
        scheduled_ids.add(item_id)

        try:
            s_min = _parse_time_to_min(start_str)
            e_min = _parse_time_to_min(end_str)
            if s_min >= e_min:
                raise ValueError("giờ bắt đầu >= kết thúc")
        except ValueError as exc:
            violations.append({
                "code": "INVALID_TIME",
                "item_id": item_id,
                "index": idx,
                "message": "Khung giờ của '%s' (%s–%s) không hợp lệ: %s." % (item_id, start_str, end_str, exc),
            })
            continue

        if s_min < trip_start or e_min > trip_end:
            violations.append({
                "code": "OUTSIDE_TRIP_WINDOW",
                "item_id": item_id,
                "message": "%s (%s–%s) nằm ngoài khung giờ chuyến đi (%s–%s)."
                % (meta["name"], start_str, end_str, start_time, end_time),
            })

        zone = zones_by_id[meta["zone_id"]]
        z_open = _parse_time_to_min(zone["open_time"])
        z_close = _parse_time_to_min(zone["close_time"])
        if s_min < z_open or e_min > z_close:
            violations.append({
                "code": "OUTSIDE_OPENING_HOURS",
                "item_id": item_id,
                "zone_id": zone["id"],
                "message": "%s (%s–%s) nằm ngoài giờ mở cửa phân khu %s (%s–%s)."
                % (meta["name"], start_str, end_str, zone["name"], zone["open_time"], zone["close_time"]),
            })
        elif meta.get("category") != "show":
            i_open = _parse_time_to_min(meta["open_time"])
            i_close = _parse_time_to_min(meta["close_time"])
            if s_min < i_open or e_min > i_close:
                violations.append({
                    "code": "OUTSIDE_OPENING_HOURS",
                    "item_id": item_id,
                    "zone_id": zone["id"],
                    "message": "%s (%s–%s) nằm ngoài giờ phục vụ riêng của điểm này (%s–%s)."
                    % (meta["name"], start_str, end_str, meta["open_time"], meta["close_time"]),
                })

        if meta.get("category") == "show":
            if item_id.upper() in canceled_set:
                violations.append({
                    "code": "SHOW_CANCELED",
                    "item_id": item_id,
                    "message": "%s đang nằm trong danh sách show bị hủy/tạm dừng." % meta["name"],
                })
            sh_start = _parse_time_to_min(meta["start_time"])
            sh_end = _parse_time_to_min(meta["end_time"])
            if s_min > sh_start or e_min < sh_end:
                violations.append({
                    "code": "SHOW_TIME_MISMATCH",
                    "item_id": item_id,
                    "message": "%s diễn cố định lúc %s–%s; khung %s–%s chưa phủ trọn suất diễn."
                    % (meta["name"], meta["start_time"], meta["end_time"], start_str, end_str),
                })
            else:
                early = meta.get("arrive_early_min", 10)
                if sh_start - s_min < early:
                    warnings.append({
                        "code": "SHOW_ARRIVE_EARLY",
                        "item_id": item_id,
                        "message": "Nên đến %s sớm ít nhất %d phút trước %s (hiện chỉ đệm %d phút)."
                        % (meta["name"], early, meta["start_time"], sh_start - s_min),
                    })

        min_h = gp["min_child_height_cm"]
        req_h = meta.get("min_height_cm", 0)
        comp_h = meta.get("companion_required_below_cm", 0)
        if min_h is not None and min_h < req_h:
            if not split_group:
                height_violated_zones.append(meta["zone_id"])
                violations.append({
                    "code": "HEIGHT_RESTRICTION",
                    "item_id": item_id,
                    "message": "%s yêu cầu tối thiểu %dcm (bé thấp nhất cao %dcm)." % (meta["name"], req_h, min_h),
                })
            elif gp["adults"] < 2:
                violations.append({
                    "code": "INVALID_SPLIT_GROUP",
                    "item_id": item_id,
                    "message": "Không thể tách nhóm cho %s vì cần ít nhất 2 người lớn (1 người trông bé %dcm, 1 người chơi)."
                    % (meta["name"], min_h),
                })
            else:
                eligible = [h for h in gp["heights"] if h >= req_h]
                target = "trẻ đạt %dcm trở lên" % req_h if eligible else "người lớn"
                warnings.append({
                    "code": "SPLIT_GROUP_ACTIVE",
                    "item_id": item_id,
                    "message": "Đã kích hoạt tách nhóm tại %s cho %s; bố trí 1 người lớn trông bé %dcm."
                    % (meta["name"], target, min_h),
                })
        elif min_h is not None and comp_h > 0 and min_h < comp_h:
            warnings.append({
                "code": "COMPANION_REQUIRED",
                "item_id": item_id,
                "message": "Bé %dcm chơi được %s nhưng dưới %dcm nên bắt buộc có người lớn đi kèm." % (min_h, meta["name"], comp_h),
            })

        is_outdoor = not meta.get("indoor", False)
        rain_all_day = weather_norm == "rain" and rain_span is None
        rain_hits = rain_span is not None and _intervals_overlap(s_min, e_min, rain_span[0], rain_span[1])
        if is_outdoor and (rain_all_day or rain_hits):
            rain_hit_windows.append((s_min, e_min))
            violations.append({
                "code": "WEATHER_RAIN_OUTDOOR",
                "item_id": item_id,
                "message": "%s là hoạt động ngoài trời nên bị chặn khi trời mưa (%s–%s)."
                % (meta["name"], start_str, end_str),
            })
        elif (
            weather_norm in ("sunny", "hot")
            and is_outdoor
            and not meta.get("is_water_park", False)
            and meta.get("category") not in ("meal", "rest")
            and _intervals_overlap(s_min, e_min, 660, 900)
        ):
            warnings.append({
                "code": "MIDDAY_HEAT",
                "item_id": item_id,
                "message": "%s diễn ra ngoài trời trong khung nắng gắt 11:00–15:00; cân nhắc mũ/kem chống nắng hoặc chuyển sang điểm trong nhà."
                % meta["name"],
            })

        parsed_items.append({
            "id": item_id,
            "start_str": start_str,
            "end_str": end_str,
            "s_min": s_min,
            "e_min": e_min,
            "meta": meta,
        })

    parsed_items.sort(key=lambda x: (x["s_min"], x["e_min"]))
    for i in range(1, len(parsed_items)):
        prev_it, curr_it = parsed_items[i - 1], parsed_items[i]
        if prev_it["e_min"] > curr_it["s_min"]:
            violations.append({
                "code": "TIME_OVERLAP",
                "item_id": curr_it["id"],
                "message": "%s (%s–%s) bị trùng giờ với %s (%s–%s)."
                % (curr_it["meta"]["name"], curr_it["start_str"], curr_it["end_str"],
                   prev_it["meta"]["name"], prev_it["start_str"], prev_it["end_str"]),
            })
            continue
        walk_min = walking_matrix[prev_it["meta"]["zone_id"]][curr_it["meta"]["zone_id"]]
        prev_venue = zones_by_id[prev_it["meta"]["zone_id"]].get("venue_id", "vinwonders")
        curr_venue = zones_by_id[curr_it["meta"]["zone_id"]].get("venue_id", "vinwonders")
        gap_min = curr_it["s_min"] - prev_it["e_min"]
        if gap_min < walk_min:
            if prev_venue != curr_venue:
                violations.append({
                    "code": "INSUFFICIENT_TRANSFER_TIME",
                    "item_id": curr_it["id"],
                    "message": "Di chuyển bằng xe VinBus từ %s sang %s cần tối thiểu %d phút, hiện chỉ có %d phút (%s → %s)."
                    % (prev_it["meta"]["name"], curr_it["meta"]["name"], walk_min, gap_min,
                       prev_it["end_str"], curr_it["start_str"]),
                })
            else:
                violations.append({
                    "code": "INSUFFICIENT_WALK_TIME",
                    "item_id": curr_it["id"],
                    "message": "Từ %s sang %s cần tối thiểu %d phút đi bộ, hiện chỉ có %d phút (%s → %s)."
                    % (prev_it["meta"]["name"], curr_it["meta"]["name"], walk_min, gap_min,
                       prev_it["end_str"], curr_it["start_str"]),
                })

    if parsed_items:
        total_span = max(x["e_min"] for x in parsed_items) - min(x["s_min"] for x in parsed_items)
        has_meal_or_rest = any(x["meta"].get("category") in ("meal", "rest") for x in parsed_items)
        if total_span >= 300 and not has_meal_or_rest:
            warnings.append({
                "code": "NO_MEAL_OR_REST",
                "item_id": None,
                "message": "Lịch trình kéo dài >= 5 tiếng nhưng chưa có khoảng ăn trưa hoặc nghỉ ngơi cho trẻ nhỏ.",
            })
        has_young_kids = (
            (gp["min_child_height_cm"] is not None and gp["min_child_height_cm"] < 140)
            or (gp["children_100_140"] + gp["children_under_100"] > 0)
        )
        if len(scheduled_venues) > 2 and has_young_kids:
            warnings.append({
                "code": "MULTI_VENUE_FATIGUE",
                "item_id": None,
                "message": "Lịch đi cả 3 tổ hợp (Safari + VinWonders + Grand World) trong 1 ngày sẽ khá mệt cho trẻ nhỏ; nên tách thành 2 ngày (Ngày 1 VinWonders, Ngày 2 Safari sáng + Grand World chiều/tối) hoặc thuê xe đẩy.",
            })

    paid_keys: List[str] = list(rang_buoc.get("diem_ve_le") or [])
    for it in parsed_items:
        pk = it["meta"].get("paid_ticket_key")
        if pk:
            paid_keys.append(pk)

    cost_summary = _compute_cost(
        so_nguoi_lon=gp["adults_for_pricing"],
        so_tre_em_1m_1m4=gp["children_100_140"],
        so_tre_duoi_1m=gp["children_under_100"],
        so_nguoi_cao_tuoi=gp["seniors"],
        da_co_ve=gp["da_co_ve"],
        goi_an=gp["goi_an"],
        dich_vu=gp["dich_vu"],
        ngan_sach_vnd=gp["ngan_sach_vnd"],
        to_hop=active_venues,
        diem_ve_le=paid_keys,
    )
    if gp["ngan_sach_vnd"] is not None and cost_summary["trong_ngan_sach"] is False:
        violations.append({
            "code": "BUDGET_EXCEEDED",
            "item_id": None,
            "message": "Tổng chi phí %sđ vượt ngân sách %sđ."
            % (f"{cost_summary['tong_chi_phi_vnd']:,}", f"{gp['ngan_sach_vnd']:,}"),
        })
        relaxations.extend(
            _build_budget_relaxations(
                cost_summary,
                gp["ngan_sach_vnd"],
                gp,
                to_hop=active_venues,
                diem_ve_le=paid_keys,
            )
        )

    active_venue_set = set(active_venues)
    venue_attractions = [
        a for a in attractions if a.get("venue_id", "vinwonders") in active_venue_set
    ]
    indoor_alternatives: List[Dict[str, Any]] = []
    if rain_hit_windows:
        indoor_alternatives = _find_indoor_alternatives(
            attractions=venue_attractions,
            min_child_height_cm=gp["min_child_height_cm"],
            rain_windows=rain_hit_windows,
            scheduled_ids=scheduled_ids,
            limit=5,
        )
        if active_venue_set == {"vinwonders"}:
            relaxations.append(
                "Chuyển các hoạt động ngoài trời trong khung mưa sang điểm trong nhà gợi ý (ưu tiên Cung điện Hải Vương Z6_SEASHELL hoặc khu trong nhà ở Z2_FAIRY / Z1_EURO)."
            )
        else:
            relaxations.append(
                "Chuyển các hoạt động ngoài trời trong khung mưa sang điểm trong nhà gợi ý (ưu tiên Cung điện Hải Vương Z6_SEASHELL, Xe buýt Safari SF-Z7-01 hoặc Bảo tàng Gấu Teddy GW-Z8-01)."
            )

    if height_violated_zones:
        alt_height = [
            "%s (%s, >=%dcm)" % (a["name"], a["id"], a["min_height_cm"])
            for a in venue_attractions
            if a["zone_id"] in set(height_violated_zones)
            and a.get("category") not in ("meal", "rest")
            and (gp["min_child_height_cm"] is None or a.get("min_height_cm", 0) <= gp["min_child_height_cm"])
        ][:3]
        if alt_height:
            relaxations.append(
                "Thay trò vượt chiều cao bằng điểm phù hợp với bé %dcm cùng khu: %s."
                % (gp["min_child_height_cm"], "; ".join(alt_height))
            )
        if gp["adults"] >= 2:
            relaxations.append("Hoặc bật tach_nhom=True (vì nhóm có >=2 người lớn) để 1 người lớn chơi trò mạnh trong khi người còn lại trông bé.")

    if any(v["code"] == "OUTSIDE_OPENING_HOURS" for v in violations):
        if active_venue_set == {"vinwonders"}:
            relaxations.append(
                "Lưu ý giờ mở cửa lệch nhau: Công viên nước (Z5_TYPHOON) & Cung điện Hải Vương (Z6_SEASHELL) chỉ mở 10:00–18:00; các khu còn lại mở 09:00–19:30."
            )
        else:
            hours_notes: List[str] = []
            if "safari" in active_venue_set:
                hours_notes.append("Vinpearl Safari 09:00–16:00 (xe buýt bán hoang dã chuyến cuối 15:20)")
            if "vinwonders" in active_venue_set:
                hours_notes.append("VinWonders 09:00–19:30 (Công viên nước & Cung điện Hải Vương 10:00–18:00)")
            if "grandworld" in active_venue_set:
                hours_notes.append("Grand World mở cửa tự do, điểm/show tối đến 22:00–22:30")
            relaxations.append("Lưu ý giờ mở/đóng riêng từng tổ hợp: %s." % ("; ".join(hours_notes)))
    if any(v["code"] == "SHOW_CANCELED" for v in violations):
        relaxations.append(
            "Khi show ngoài trời bị hủy, ưu tiên thay bằng show trong nhà tại Cung điện Hải Vương (Nàng tiên cá SH-MERMAID-1/2, Cho cá ăn SH-FEED-FISH) hoặc Bảo tàng Gấu Teddy."
        )

    return {
        "hop_le": len(violations) == 0,
        "so_vi_pham": len(violations),
        "vi_pham": violations,
        "canh_bao": warnings,
        "tong_hop_chi_phi": cost_summary,
        "goi_y_trong_nha": indoor_alternatives,
        "goi_y_noi_rang_buoc": relaxations,
    }


def build_booking_deeplink(
    base_url: str,
    checkin: Optional[str] = None,
    checkout: Optional[str] = None,
    adults: int = 2,
    children_ages: Tuple[int, ...] = (),
) -> str:
    """Gắn sẵn tham số ngày nhận/trả phòng và số khách lên URL đặt phòng bên thứ 3 (không tác động ra ngoài)."""
    if not base_url:
        return ""
    parts = urllib.parse.urlsplit(str(base_url))
    query = urllib.parse.parse_qs(parts.query, keep_blank_values=True)
    if checkin:
        query["checkin"] = [str(checkin)]
    if checkout:
        query["checkout"] = [str(checkout)]
    query["adults"] = [str(max(1, int(adults)))]
    query["children"] = [str(max(0, len(children_ages)))]
    encoded = urllib.parse.urlencode(query, doseq=True)
    return urllib.parse.urlunsplit((parts.scheme, parts.netloc, parts.path, encoded, parts.fragment))


@tool
def tra_khach_san(
    ngay_den: Optional[str] = None,
    ngay_ve: Optional[str] = None,
    so_nguoi: int = 2,
    ngan_sach_vnd: Optional[int] = None,
    so_tre_em: int = 0,
) -> Dict[str, Any]:
    """Tên: tra_khach_san — Tra cứu danh sách khách sạn tham khảo gần cổng VinWonders / Grand World Phú Quốc (ngoài phạm vi chấm eval/).
    Input: ngay_den (str | None), ngay_ve (str | None), so_nguoi (int), ngan_sach_vnd (int | None), so_tre_em (int).
    Output: dict gồm so_luong, hotels (kèm fit_score, lat, lng, distance_to_gate_m, rooms_left mô phỏng, booking_url Deep Link, fetched_at), nguon, is_realtime.
    Tác động ra ngoài: Không (chỉ đọc data/hotels.json; không tự đặt phòng hay thanh toán)."""
    hotels_path = os.path.join(DATA_DIR, "hotels.json")
    fetched_at = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    if not os.path.exists(hotels_path):
        return {
            "so_luong": 0,
            "hotels": [],
            "nguon": "local_json",
            "is_realtime": False,
            "fetched_at": fetched_at,
            "ghi_chu": "Chưa có data/hotels.json.",
        }

    raw_hotels = _load_json("hotels.json")
    rows = raw_hotels.get("hotels", raw_hotels) if isinstance(raw_hotels, dict) else raw_hotels
    total_guests = max(1, int(so_nguoi or 2))
    adults_est = max(1, total_guests - max(0, int(so_tre_em or 0)))
    child_ages = (6,) * max(0, int(so_tre_em or 0))

    scored: List[Dict[str, Any]] = []
    for h in (rows or []):
        dist_m = int(h.get("distance_to_gate_m") or 1500)
        max_guests = int(h.get("max_guests") or 4)
        has_family = bool(h.get("has_family_room", False))
        price_ref = int(h.get("price_ref_vnd") or 0)

        fit = 82
        if dist_m <= 800:
            fit += 10
        elif dist_m <= 1500:
            fit += 5
        else:
            fit -= 8
        if so_tre_em > 0 and has_family:
            fit += 6
        if max_guests < total_guests:
            fit -= 18
        if ngan_sach_vnd is not None and price_ref > 0 and price_ref > ngan_sach_vnd:
            fit -= 15
        fit = max(35, min(99, fit))

        item = dict(h)
        item["fit_score"] = int(h.get("fit_score", fit))
        item["rooms_is_synthetic"] = True
        item["is_realtime"] = False
        item["fetched_at"] = fetched_at
        item["booking_url"] = build_booking_deeplink(
            str(h.get("booking_url", "")),
            checkin=ngay_den,
            checkout=ngay_ve,
            adults=adults_est,
            children_ages=child_ages,
        )
        scored.append(item)

    scored.sort(key=lambda x: (-x["fit_score"], int(x.get("distance_to_gate_m") or 9999)))
    return {
        "so_luong": len(scored),
        "hotels": scored,
        "nguon": "local_json",
        "is_realtime": False,
        "fetched_at": fetched_at,
        "ghi_chu": "Giá tham khảo từ nguồn công khai; số phòng trống (rooms_left) là dữ liệu mô phỏng (seed=42). Đặt phòng mở trang đối tác.",
    }


def search_example(query: str) -> list:
    """Hàm giữ tương thích tạm cho codebase/agent.py ở chế độ mẫu CP1/CP2 (không gắn @tool)."""
    return [
        {
            "code": "VW-COMPAT",
            "text": "Dữ liệu cụm Phú Quốc United Center đã sẵn sàng trong data/; agent.py nối các công cụ @tool chính thức.",
        }
    ]
