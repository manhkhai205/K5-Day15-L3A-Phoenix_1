"""Công cụ của bài toán — NHÓM VIẾT. Điền ở guide bước 2.2 (thiết kế) và 3.2 (code).

Mỗi công cụ là một hàm Python có @tool. Docstring ghi đúng 4 ý như sơ đồ ở spec.md §4:
    tên · input · output · có tác động ra ngoài không (gửi tin, sửa dữ liệu, chấm điểm…)
Khung tự ghi mỗi lần gọi công cụ vào trace (tên, input, output rút gọn, thời gian, lỗi).

6 công cụ thống nhất trong docs/cp2-plan.md:
    tra_diem_choi · tra_lich_show · tra_thoi_tiet · uoc_thoi_gian_di · tinh_chi_phi · kiem_lich_trinh
Dữ liệu đọc từ data/ và mô tả tại data/DATA_CARD.md.
"""
import json
import os
import re
import unicodedata
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
                    t_end = min(t_start + 120, _parse_time_to_min("19:30"))
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

    t = pricing["tickets"]
    if da_co_ve:
        ticket_cost = 0
    else:
        ticket_cost = (
            so_nguoi_lon * t["adult"]["price_vnd"]
            + so_tre_em_1m_1m4 * t["child_100_140"]["price_vnd"]
            + so_nguoi_cao_tuoi * t["senior"]["price_vnd"]
            + so_tre_duoi_1m * t["child_under_100"]["price_vnd"]
        )

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
    notes: List[str] = []

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
        "da_co_ve": bool(da_co_ve),
        "goi_an": meal_key,
        "chi_phi_ve_vnd": ticket_cost,
        "chi_phi_an_vnd": meal_cost,
        "chi_phi_dich_vu_vnd": extras_cost,
        "tong_chi_phi_vnd": total_cost,
        "tien_coc_hoan_lai_vnd": refundable_deposit,
        "chi_tiet": {
            "ve_vnd": ticket_cost,
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


def _build_budget_relaxations(cost_summary: Dict[str, Any], budget_vnd: int, gp: Dict[str, Any]) -> List[str]:
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
        )
        saved2 = cost_summary["tong_chi_phi_vnd"] - alt2["tong_chi_phi_vnd"]
        suggestions.append(
            "Bỏ dịch vụ bổ sung %s giúp tiết kiệm %sđ (còn %sđ)."
            % (", ".join(optional_tokens), f"{saved2:,}", f"{alt2['tong_chi_phi_vnd']:,}")
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
) -> Dict[str, Any]:
    """Tên: tra_diem_choi — Tra cứu và lọc điểm chơi, ăn uống, nghỉ ngơi tại VinWonders Phú Quốc.
    Input: phan_khu (str | None), chieu_cao_min (int | float | None — cm hoặc mét), trong_nha (bool | None), tags (list[str] | None), mo_luc ("HH:MM" | None), gom_an_nghi (bool).
    Output: dict gồm so_luong, bi_loai_do_chieu_cao, diem_choi (kèm chiều cao tối thiểu, indoor, giờ mở/đóng và cờ can_nguoi_lon_di_kem).
    Tác động ra ngoài: Không (chỉ đọc dữ liệu tĩnh trong data/attractions.json)."""
    height_cm = _normalize_height_cm(chieu_cao_min)
    open_at_min = _parse_time_to_min(mo_luc) if mo_luc is not None else None
    norm_zone = _resolve_zone_id(phan_khu)
    norm_tags = {_strip_accents(str(t)).replace(" ", "_") for t in (tags or []) if str(t).strip()}

    attractions = _load_json("attractions.json")
    matched: List[Dict[str, Any]] = []
    excluded_by_height = 0

    for item in attractions:
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
) -> Dict[str, Any]:
    """Tên: tra_lich_show — Tra giờ mở cửa công viên, 6 phân khu và lịch biểu diễn show cố định kèm tác động thời tiết theo ngày.
    Input: ngay (str | None — 'YYYY-MM-DD' hoặc mô tả thời tiết), phan_khu (str | None), bo_qua_show (list[str] | None).
    Output: dict gồm ngay, gio_mo_cua_cong_vien, phan_khu, show_kha_dung và show_anh_huong_thoi_tiet.
    Tác động ra ngoài: Không (chỉ đọc data/park_zones.json, data/shows.json và data/weather.json)."""
    zones_data = _load_json("park_zones.json")
    shows_data = _load_json("shows.json")
    weather_info = _get_weather(ngay, None)

    norm_zone = _resolve_zone_id(phan_khu)
    excluded_ids = {str(sid).strip().upper() for sid in (bo_qua_show or []) if str(sid).strip()}
    rain_span = _parse_rain_window(weather_info["khung_gio_mua"]) if weather_info["co_mua"] else None

    zones = [z for z in zones_data["zones"] if not norm_zone or z["id"] == norm_zone]
    available_shows: List[Dict[str, Any]] = []
    weather_impacted: List[Dict[str, Any]] = []

    for show in shows_data:
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

    return {
        "ngay": weather_info["ngay"],
        "gio_mo_cua_cong_vien": zones_data["park"],
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


@tool
def uoc_thoi_gian_di(khu_a: str, khu_b: str) -> Dict[str, Any]:
    """Tên: uoc_thoi_gian_di — Ước lượng thời gian đi bộ (phút) giữa hai phân khu trong VinWonders Phú Quốc.
    Input: khu_a (str — mã hoặc tên phân khu xuất phát), khu_b (str — mã hoặc tên phân khu đích).
    Output: dict gồm khu_a, ten_khu_a, khu_b, ten_khu_b, thoi_gian_phut, ghi_chu.
    Tác động ra ngoài: Không (chỉ đọc ma trận đi bộ tĩnh trong data/park_zones.json)."""
    zones_data = _load_json("park_zones.json")
    zones_by_id = {z["id"]: z for z in zones_data["zones"]}
    matrix = zones_data["walking_matrix_min"]

    z_a = _resolve_zone_id(khu_a)
    z_b = _resolve_zone_id(khu_b)
    if z_a not in zones_by_id or z_b not in zones_by_id:
        valid = ", ".join("%s (%s)" % (z["id"], z["name"]) for z in zones_data["zones"])
        raise ValueError("Phân khu không hợp lệ (%r, %r). Các phân khu hợp lệ: %s" % (khu_a, khu_b, valid))

    walk_min = matrix[z_a][z_b]
    return {
        "khu_a": z_a,
        "ten_khu_a": zones_by_id[z_a]["name"],
        "khu_b": z_b,
        "ten_khu_b": zones_by_id[z_b]["name"],
        "thoi_gian_phut": walk_min,
        "ghi_chu": "Ước lượng đi bộ trung bình cho gia đình có trẻ nhỏ (tăng thêm 3–5 phút vào giờ cao điểm).",
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
) -> Dict[str, Any]:
    """Tên: tinh_chi_phi — Tính tổng chi phí vé, ăn uống, phụ phí (xe đẩy, tủ đồ, xe điện, fastpass…) và đối chiếu ngân sách.
    Input: so_nguoi_lon (int), so_tre_em_1m_1m4 (int), so_tre_duoi_1m (int), dich_vu (list[str] | None), so_nguoi_cao_tuoi (int), da_co_ve (bool), goi_an (str | None), ngan_sach_vnd (int | None).
    Output: dict gồm chi_phi_ve_vnd, chi_phi_an_vnd, chi_phi_dich_vu_vnd, tong_chi_phi_vnd, tien_coc_hoan_lai_vnd, chi_tiet, dich_vu_khong_ro, trong_ngan_sach, chenh_lech_ngan_sach_vnd.
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
    start_time = str(rang_buoc.get("gio_bat_dau", rang_buoc.get("start_time", "09:00")))
    end_time = str(rang_buoc.get("gio_ket_thuc", rang_buoc.get("end_time", "19:30")))
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
        gap_min = curr_it["s_min"] - prev_it["e_min"]
        if gap_min < walk_min:
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

    cost_summary = _compute_cost(
        so_nguoi_lon=gp["adults_for_pricing"],
        so_tre_em_1m_1m4=gp["children_100_140"],
        so_tre_duoi_1m=gp["children_under_100"],
        so_nguoi_cao_tuoi=gp["seniors"],
        da_co_ve=gp["da_co_ve"],
        goi_an=gp["goi_an"],
        dich_vu=gp["dich_vu"],
        ngan_sach_vnd=gp["ngan_sach_vnd"],
    )
    if gp["ngan_sach_vnd"] is not None and cost_summary["trong_ngan_sach"] is False:
        violations.append({
            "code": "BUDGET_EXCEEDED",
            "item_id": None,
            "message": "Tổng chi phí %sđ vượt ngân sách %sđ."
            % (f"{cost_summary['tong_chi_phi_vnd']:,}", f"{gp['ngan_sach_vnd']:,}"),
        })
        relaxations.extend(_build_budget_relaxations(cost_summary, gp["ngan_sach_vnd"], gp))

    indoor_alternatives: List[Dict[str, Any]] = []
    if rain_hit_windows:
        indoor_alternatives = _find_indoor_alternatives(
            attractions=attractions,
            min_child_height_cm=gp["min_child_height_cm"],
            rain_windows=rain_hit_windows,
            scheduled_ids=scheduled_ids,
            limit=5,
        )
        relaxations.append(
            "Chuyển các hoạt động ngoài trời trong khung mưa sang điểm trong nhà gợi ý (ưu tiên Cung điện Hải Vương Z6_SEASHELL hoặc khu trong nhà ở Z2_FAIRY / Z1_EURO)."
        )

    if height_violated_zones:
        alt_height = [
            "%s (%s, >=%dcm)" % (a["name"], a["id"], a["min_height_cm"])
            for a in attractions
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
        relaxations.append(
            "Lưu ý giờ mở cửa lệch nhau: Công viên nước (Z5_TYPHOON) & Cung điện Hải Vương (Z6_SEASHELL) chỉ mở 10:00–18:00; các khu còn lại mở 09:00–19:30."
        )
    if any(v["code"] == "SHOW_CANCELED" for v in violations):
        relaxations.append(
            "Khi show ngoài trời bị hủy, ưu tiên thay bằng show trong nhà tại Cung điện Hải Vương (Nàng tiên cá SH-MERMAID-1/2, Cho cá ăn SH-FEED-FISH)."
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


def search_example(query: str) -> list:
    """Hàm giữ tương thích tạm cho codebase/agent.py ở chế độ mẫu CP1/CP2 (không gắn @tool)."""
    return [
        {
            "code": "VW-COMPAT",
            "text": "Dữ liệu công viên VinWonders Phú Quốc đã sẵn sàng trong data/; agent.py sẽ nối 6 công cụ @tool chính thức.",
        }
    ]
