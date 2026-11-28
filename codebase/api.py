"""Backend HTTP FastAPI cho JoyPlan AI (9 endpoint + quản lý phiên / undo + luật xoá mốc).

Lưu ý tách lớp:
- Giữ nguyên 100% hợp đồng `answer(text) -> {"output": str}` cho `run.py`, `eval/` và `simulate`.
- Các thao tác tương tác trên Web UI (`swap`, `remove`, `undo`) luôn kiểm lại bằng `kiem_lich_trinh`.
- Không tự đặt phòng / thanh toán; `hotels.json` & `media.json` được đọc an toàn (fallback nếu chưa có).
"""
import copy
import datetime
import json
import os
import re
import sys
import unicodedata
import uuid
from typing import Any, Dict, List, Optional, Tuple

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

_CODEBASE_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT_DIR = os.path.dirname(_CODEBASE_DIR)
_DATA_DIR = os.path.join(_ROOT_DIR, "data")
if _CODEBASE_DIR not in sys.path:
    sys.path.insert(0, _CODEBASE_DIR)

from agent import (  # noqa: E402
    _check_input_guardrail,
    _fmt_vnd,
    _norm,
    _parse_constraints,
    _pick_meal_option,
    _to_hhmm,
    _to_min,
    plan_day,
)
from tools import (  # noqa: E402
    _get_transfer_min,
    _load_json,
    kiem_lich_trinh,
    tra_khach_san,
)

MAX_UNDO = 20
SESSIONS: Dict[str, Dict[str, Any]] = {}

app = FastAPI(
    title="JoyPlan AI API",
    description="API lập & tái lập lịch trình gia đình cụm Phú Quốc United Center (0 vi phạm qua kiem_lich_trinh).",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str


class SelectHotelRequest(BaseModel):
    hotel_id: Optional[str] = None


class SwapItemRequest(BaseModel):
    item_id: str
    new_id: str


class RemoveItemRequest(BaseModel):
    item_id: str


# ---------------------------------------------------------------------------
# Helpers đọc dữ liệu & định dạng dùng chung
# ---------------------------------------------------------------------------


def _load_optional_json(filename: str, default: Any) -> Any:
    path = os.path.join(_DATA_DIR, filename)
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _load_catalog() -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    zones_data = _load_json("park_zones.json")
    attractions = _load_json("attractions.json")
    shows = _load_json("shows.json")
    zones_by_id = {z["id"]: z for z in zones_data["zones"]}
    catalog: Dict[str, Dict[str, Any]] = {a["id"]: a for a in attractions}
    for s in shows:
        catalog[s["id"]] = s
    return catalog, zones_by_id, attractions, shows


def _load_media_store() -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    raw = _load_optional_json("media.json", {})
    mapping: Dict[str, Dict[str, Any]] = {}
    zone_fallbacks: Dict[str, Dict[str, Any]] = {}
    if isinstance(raw, dict):
        items = raw.get("items") if isinstance(raw.get("items"), list) else None
        if items is not None:
            for row in items:
                if isinstance(row, dict) and row.get("item_id"):
                    mapping[str(row["item_id"])] = row
        else:
            for k, v in raw.items():
                if k not in ("_meta", "zone_fallbacks") and isinstance(v, dict):
                    mapping[str(v.get("item_id") or k)] = v
        raw_zf = raw.get("zone_fallbacks")
        if isinstance(raw_zf, dict):
            for zk, zv in raw_zf.items():
                if isinstance(zv, dict):
                    zone_fallbacks[str(zk)] = zv
    elif isinstance(raw, list):
        for row in raw:
            if isinstance(row, dict) and row.get("item_id"):
                mapping[str(row["item_id"])] = row
    return mapping, zone_fallbacks


def _load_media_map() -> Dict[str, Dict[str, Any]]:
    return _load_media_store()[0]


def _get_media_payload(
    item_id: str,
    media_map: Optional[Dict[str, Dict[str, Any]]] = None,
    zone_id: Optional[str] = None,
) -> Dict[str, Any]:
    mmap, zone_fallbacks = _load_media_store()
    if media_map is not None:
        mmap = media_map
    entry = mmap.get(item_id) or {}
    img = (entry.get("image_url") or "").strip() or None
    yt = (entry.get("youtube_url") or "").strip() or None
    is_zone_fallback = False
    if not img and not yt and zone_id and zone_id in zone_fallbacks:
        entry = zone_fallbacks[zone_id] or {}
        img = (entry.get("image_url") or "").strip() or None
        yt = (entry.get("youtube_url") or "").strip() or None
        is_zone_fallback = bool(img or yt)
    return {
        "has_media": bool(img or yt),
        "image_url": img,
        "youtube_url": yt,
        "source_url": (entry.get("source_url") or "").strip() or None,
        "caption": entry.get("caption") or None,
        "verified_date": entry.get("verified_date") or None,
        "license_note": entry.get("license_note") or None,
        "is_zone_fallback": is_zone_fallback,
        "fallback_text": "Chưa có media",
    }


def _ui_type_from_meta(meta: Dict[str, Any]) -> str:
    cat = meta.get("category", "ride")
    if cat == "show":
        return "show"
    if cat in ("meal", "rest"):
        return "meal"
    return "ride"


def _make_ui_item(
    meta: Dict[str, Any],
    start: str,
    end: str,
    heights_cm: List[int],
    tach_nhom: bool = False,
) -> Dict[str, Any]:
    min_h = int(meta.get("min_height_cm", 0) or 0)
    return {
        "id": meta["id"],
        "type": _ui_type_from_meta(meta),
        "category": meta.get("category", "ride"),
        "name": meta["name"],
        "zone_id": meta["zone_id"],
        "venue_id": meta.get("venue_id", "vinwonders"),
        "start": start,
        "end": end,
        "tach_nhom": bool(tach_nhom),
        "lat": meta.get("lat"),
        "lng": meta.get("lng"),
        "indoor": bool(meta.get("indoor", False)),
        "cost_vnd": 0,
        "min_height_cm": min_h,
        "companion_required_below_cm": int(meta.get("companion_required_below_cm", 0) or 0),
        "height_labels": [{"child_cm": int(h), "ok": int(h) >= min_h} for h in (heights_cm or [])],
        "notes": meta.get("notes", ""),
    }


def _extract_park_schedule(ui_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Lọc bỏ khách sạn & khoảng nghỉ tự do trước khi gửi qua `kiem_lich_trinh`."""
    return [
        {
            "id": str(it["id"]),
            "start": str(it["start"]),
            "end": str(it["end"]),
            "tach_nhom": bool(it.get("tach_nhom", False)),
        }
        for it in ui_items
        if it.get("type") != "hotel" and not it.get("is_free_rest")
    ]


def _build_check_payload(check_res: Dict[str, Any]) -> Dict[str, Any]:
    codes = {v.get("code") for v in (check_res.get("vi_pham") or [])}
    return {
        "hop_le": bool(check_res.get("hop_le")),
        "so_vi_pham": int(check_res.get("so_vi_pham", 0)),
        "vi_pham": list(check_res.get("vi_pham") or []),
        "canh_bao": list(check_res.get("canh_bao") or []),
        "dieu_kien": {
            "gio_mo_cua": not bool(codes & {"OUTSIDE_OPENING_HOURS", "OUTSIDE_TRIP_WINDOW"}),
            "chong_gio": not bool(
                codes & {"TIME_OVERLAP", "INSUFFICIENT_WALK_TIME", "INSUFFICIENT_TRANSFER_TIME", "INVALID_TIME", "SHOW_TIME_MISMATCH"}
            ),
            "ngan_sach": "BUDGET_EXCEEDED" not in codes,
            "chieu_cao": not bool(codes & {"HEIGHT_RESTRICTION", "INVALID_SPLIT_GROUP"}),
            "mua": not bool(codes & {"WEATHER_RAIN_OUTDOOR", "SHOW_CANCELED"}),
        },
    }


def _recompute_day_summary(day_obj: Dict[str, Any], check_res: Dict[str, Any]) -> None:
    ui_items = day_obj.get("items") or []
    ride_items = [
        it for it in ui_items
        if it.get("type") not in ("hotel",) and not it.get("is_free_rest") and it.get("category") not in ("meal", "rest")
    ]
    kid_ok_count = sum(1 for it in ride_items if all(hl.get("ok", True) for hl in (it.get("height_labels") or [])))
    cost_final = check_res["tong_hop_chi_phi"]
    day_obj["summary"] = {
        "cost_vnd": cost_final["tong_chi_phi_vnd"],
        "n_items": len(ui_items),
        "kid_ok_count": kid_ok_count,
        "total_rides": len(ride_items),
    }
    day_obj["cost"] = cost_final
    day_obj["check"] = _build_check_payload(check_res)


def _new_session(session_id: Optional[str] = None) -> Dict[str, Any]:
    sid = (session_id or "").strip() or ("sess_" + uuid.uuid4().hex[:8])
    session = {
        "session_id": sid,
        "base_prompt": "",
        "ask_more_attempts": 0,
        "constraints": {},
        "rang_buoc_by_day": {},
        "num_days": 1,
        "start_date": None,
        "end_date": None,
        "hotels": [],
        "selected_hotel_id": None,
        "days": [],
        "steps": [],
        "messages": [],
        "undo_stack": [],
    }
    SESSIONS[sid] = session
    return session


def _push_undo(session: Dict[str, Any]) -> None:
    snap = {
        "constraints": copy.deepcopy(session.get("constraints")),
        "rang_buoc_by_day": copy.deepcopy(session.get("rang_buoc_by_day")),
        "selected_hotel_id": session.get("selected_hotel_id"),
        "days": copy.deepcopy(session.get("days")),
        "steps": copy.deepcopy(session.get("steps")),
    }
    stack: List[Dict[str, Any]] = session.setdefault("undo_stack", [])
    stack.append(snap)
    if len(stack) > MAX_UNDO:
        del stack[0]


def _get_session_and_day(session_id: str, day_num: int) -> Tuple[Dict[str, Any], Dict[str, Any], int]:
    session = SESSIONS.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail={"message": f"Không tìm thấy phiên '{session_id}'."})
    for idx, day_obj in enumerate(session.get("days") or []):
        if int(day_obj.get("day", -1)) == int(day_num):
            return session, day_obj, idx
    raise HTTPException(status_code=404, detail={"message": f"Không tìm thấy Ngày {day_num} trong phiên '{session_id}'."})


def _rang_buoc_for_day(session: Dict[str, Any], day_num: int, day_obj: Dict[str, Any], for_ui_edit: bool = False) -> Dict[str, Any]:
    saved = session.get("rang_buoc_by_day", {}).get(int(day_num))
    if saved:
        rb = copy.deepcopy(saved)
        if for_ui_edit:
            rb["diem_ve_le"] = None
        return rb

    constraints = session.get("constraints") or {}
    meal_option, extras = _pick_meal_option(constraints) if constraints else ("a_la_carte", [])
    cost_obj = day_obj.get("cost") or {}
    weather_obj = day_obj.get("weather") or {}
    return {
        "to_hop": constraints.get("venues") or ["vinwonders"],
        "so_nguoi_lon": (constraints.get("adults", 2) + constraints.get("tall_kids_as_adult", 0)),
        "so_tre_em_1m_1m4": constraints.get("so_tre_em_1m_1m4", 0),
        "so_tre_duoi_1m": constraints.get("so_tre_duoi_1m", 0),
        "so_nguoi_cao_tuoi": constraints.get("seniors", 0),
        "chieu_cao_tre_cm": constraints.get("heights_cm") or None,
        "da_co_ve": bool(constraints.get("da_co_ve", False)),
        "goi_an": cost_obj.get("goi_an") or meal_option,
        "dich_vu": extras,
        "diem_ve_le": None if for_ui_edit else (constraints.get("want_paid_items") or None),
        "ngan_sach_vnd": constraints.get("ngan_sach_vnd"),
        "gio_bat_dau": constraints.get("gio_bat_dau", "09:00"),
        "gio_ket_thuc": constraints.get("gio_ket_thuc", "19:30"),
        "thoi_tiet": constraints.get("thoi_tiet", "nang"),
        "khung_gio_mua": weather_obj.get("khung_gio_mua") if weather_obj.get("co_mua") else None,
        "show_bi_huy": constraints.get("show_bi_huy") or [],
    }


def _build_plan_response(
    session: Dict[str, Any],
    reply: str,
    status: str,
    missing_fields: Optional[List[str]] = None,
) -> Dict[str, Any]:
    return {
        "session_id": session["session_id"],
        "reply": reply,
        "status": status,
        "missing_fields": list(missing_fields or []),
        "hotels": list(session.get("hotels") or []),
        "selected_hotel_id": session.get("selected_hotel_id"),
        "days": list(session.get("days") or []),
        "steps": list(session.get("steps") or []),
        "can_undo": bool(session.get("undo_stack")),
    }


def _parse_trip_meta(text: str) -> Tuple[int, Optional[str], Optional[str]]:
    low = _norm(text)
    dates = re.findall(r"\b(20\d{2}-\d{2}-\d{2})\b", text or "")
    start_date = dates[0] if len(dates) >= 1 else None
    end_date = dates[1] if len(dates) >= 2 else None

    num_days = 1
    m_nday = re.search(r"\b([1-3])\s*(?:ngay|n\d+d?)\b", low)
    if m_nday:
        num_days = max(1, min(3, int(m_nday.group(1))))
    elif start_date and end_date:
        try:
            d0 = datetime.date.fromisoformat(start_date)
            d1 = datetime.date.fromisoformat(end_date)
            if d1 >= d0:
                num_days = max(1, min(3, (d1 - d0).days + 1))
        except ValueError:
            pass

    if start_date and not end_date:
        try:
            d0 = datetime.date.fromisoformat(start_date)
            end_date = (d0 + datetime.timedelta(days=max(1, num_days - 1))).isoformat()
        except ValueError:
            pass
    return num_days, start_date, end_date


def _format_day_prompt_for_index(base_prompt: str, day_idx: int, num_days: int, venues: List[str]) -> str:
    if num_days <= 1:
        return base_prompt
    # Tách tổ hợp tự nhiên khi người dùng đi 2–3 ngày tại cụm Phú Quốc United Center
    cleaned = re.sub(
        r"(?:ca\s*cum|phu\s*quoc\s*united\s*center|united\s*center|3\s*khu|ba\s*khu)",
        "",
        base_prompt,
        flags=re.IGNORECASE,
    )
    if len(venues) >= 2:
        if day_idx == 1:
            return base_prompt if "vinwonders" not in venues else (cleaned + " đi VinWonders Phú Quốc 09:00-19:30")
        if day_idx == 2 and "safari" in venues:
            return cleaned + " đi Vinpearl Safari 09:00-16:00" + (" và Grand World 17:00-22:00" if num_days == 2 and "grandworld" in venues else "")
        if day_idx == 3 and "grandworld" in venues:
            return cleaned + " đi Grand World 09:30-22:00"
    return base_prompt


def _generate_days_for_session(session: Dict[str, Any], hotel_obj: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    base_prompt = session["base_prompt"]
    constraints = session["constraints"]
    num_days = int(session.get("num_days", 1) or 1)
    start_date = session.get("start_date")
    venues = constraints.get("venues") or ["vinwonders"]

    days: List[Dict[str, Any]] = []
    rang_buoc_by_day: Dict[int, Dict[str, Any]] = {}
    last_steps: List[Dict[str, Any]] = []
    first_reply = ""

    for d in range(1, num_days + 1):
        d_date = None
        if start_date:
            try:
                d_date = (datetime.date.fromisoformat(start_date) + datetime.timedelta(days=d - 1)).isoformat()
            except ValueError:
                d_date = None
        d_prompt = _format_day_prompt_for_index(base_prompt, d, num_days, venues)
        res = plan_day(
            d_prompt,
            allow_hotel_context=True,
            selected_hotel=hotel_obj,
            day_index=d,
            date_str=d_date,
        )
        last_steps = res.get("steps") or []
        if d == 1:
            first_reply = res.get("reply", "")
        if res.get("status") != "ok" or not res.get("day"):
            return {
                "status": res.get("status", "infeasible"),
                "reply": res.get("reply", "Không thể lập lịch trình với ràng buộc hiện tại."),
                "missing_fields": res.get("missing_fields") or [],
                "steps": last_steps,
                "days": [],
                "rang_buoc_by_day": {},
            }
        day_payload = res["day"]
        d_cons = res["constraints"]
        meal_option, extras = _pick_meal_option(d_cons)
        day_weather = day_payload.get("weather") or {}
        rang_buoc_by_day[d] = {
            "to_hop": d_cons.get("venues") or ["vinwonders"],
            "so_nguoi_lon": d_cons["adults"] + d_cons["tall_kids_as_adult"],
            "so_tre_em_1m_1m4": d_cons["so_tre_em_1m_1m4"],
            "so_tre_duoi_1m": d_cons["so_tre_duoi_1m"],
            "so_nguoi_cao_tuoi": d_cons["seniors"],
            "chieu_cao_tre_cm": d_cons["heights_cm"] or None,
            "da_co_ve": d_cons["da_co_ve"],
            "goi_an": (day_payload.get("cost") or {}).get("goi_an") or meal_option,
            "dich_vu": extras,
            "diem_ve_le": d_cons.get("want_paid_items") or None,
            "ngan_sach_vnd": d_cons.get("ngan_sach_vnd"),
            "gio_bat_dau": d_cons["gio_bat_dau"],
            "gio_ket_thuc": d_cons["gio_ket_thuc"],
            "thoi_tiet": d_cons["thoi_tiet"],
            "khung_gio_mua": day_weather.get("khung_gio_mua") if day_weather.get("co_mua") else None,
            "show_bi_huy": d_cons.get("show_bi_huy") or [],
        }
        days.append(day_payload)

    hotel_prefix = ""
    if hotel_obj:
        hotel_prefix = "Mình đã xếp lịch %d ngày xuất phát từ **%s** (`0 vi phạm` qua `kiem_lich_trinh`).\n\n" % (
            len(days),
            hotel_obj.get("name", "khách sạn đã chọn"),
        )
    return {
        "status": "ok",
        "reply": (hotel_prefix + first_reply).strip(),
        "missing_fields": [],
        "steps": last_steps,
        "days": days,
        "rang_buoc_by_day": rang_buoc_by_day,
    }


def _apply_followup_edit(
    session: Dict[str, Any],
    day_num: int,
    message: str,
) -> Dict[str, Any]:
    target_day_obj = next((d for d in session["days"] if int(d["day"]) == day_num), None)
    if target_day_obj is None:
        target_day_obj = session["days"][0]
        day_num = int(target_day_obj["day"])

    low = _norm(message)
    rb = _rang_buoc_for_day(session, day_num, target_day_obj, for_ui_edit=False)
    old_budget = rb.get("ngan_sach_vnd")
    edited_prompt = session["base_prompt"]

    # Điều chỉnh ngân sách nếu người dùng nói "bớt/giảm X triệu/k" hoặc đặt ngân sách mới
    m_dec = re.search(r"(?:bot|giam)\s*(\d+(?:[.,]\d+)?)\s*(?:trieu|tr|k|nghin|ngan)?", low)
    new_budget: Optional[int] = None
    if m_dec and old_budget is not None:
        raw_val = float(m_dec.group(1).replace(",", "."))
        unit_txt = low[m_dec.start():m_dec.end()]
        delta = int(round(raw_val * 1_000)) if ("k" in unit_txt or "nghin" in unit_txt or "ngan" in unit_txt) else int(round(raw_val * 1_000_000))
        new_budget = max(0, int(old_budget) - delta)
    elif re.search(r"(?:ngan sach|tong chi|chi phi)\s*(\d+(?:[.,]\d+)?)\s*(?:trieu|tr)\b", low):
        m_b = re.search(r"(?:ngan sach|tong chi|chi phi)\s*(\d+(?:[.,]\d+)?)\s*(?:trieu|tr)\b", low)
        if m_b:
            new_budget = int(round(float(m_b.group(1).replace(",", ".")) * 1_000_000))

    if new_budget is not None:
        budget_fmt = f"ngân sách {new_budget:,}đ".replace(",", ".")
        budget_pat = (
            r"(?:ngân\s*sách|ngan\s*sach|tối\s*đa|toi\s*da|chi\s*phí|chi\s*phi)?\s*"
            r"(?:\d+(?:[.,]\d+)?\s*(?:triệu|trieu|tr|k|nghìn|nghin|ngàn|ngan)\b"
            r"|\d{1,3}(?:[.,]\d{3})+\s*(?:đ|d|vnd|đồng|dong)?\b)"
        )
        edited_prompt, n_subs = re.subn(budget_pat, budget_fmt, edited_prompt, count=1, flags=re.IGNORECASE)
        if n_subs == 0:
            edited_prompt = f"{edited_prompt} {budget_fmt}".strip()

    weather_override = None
    raw_low = unicodedata.normalize("NFC", message.lower())
    has_rain_edit = bool(
        "mưa" in raw_low
        or re.search(r"\b(?:troi\s+mua|bi\s+mua|co\s+mua|neu\s+mua|mua\s+(?:to|lon|rao|chieu|toi|phun)|rain)\b", low)
    )
    has_sun_edit = bool(
        "nắng" in raw_low
        or re.search(r"\b(?:troi\s+nang|nang\s+gat|nang\s+nong|sunny)\b", low)
    )
    if has_rain_edit:
        if "chieu" in low:
            weather_override = "mua chieu"
        elif "toi" in low:
            weather_override = "mua toi"
        else:
            weather_override = "mua"
    elif has_sun_edit:
        weather_override = "nang"
    elif (target_day_obj.get("weather") or {}).get("co_mua"):
        prev_win = (target_day_obj.get("weather") or {}).get("khung_gio_mua") or []
        if prev_win and str(prev_win[0]).startswith(("18", "19")):
            weather_override = "mua toi"
        elif prev_win and str(prev_win[0]).startswith(("13", "14", "15", "16")):
            weather_override = "mua chieu"
        else:
            weather_override = "mua"

    if "huy" in low:
        edited_prompt = edited_prompt + " " + message

    hotel_obj = next((h for h in (session.get("hotels") or []) if h.get("id") == session.get("selected_hotel_id")), None)
    res = plan_day(
        _format_day_prompt_for_index(edited_prompt, day_num, session.get("num_days", 1), session["constraints"].get("venues") or ["vinwonders"]),
        allow_hotel_context=True,
        selected_hotel=hotel_obj,
        day_index=day_num,
        date_str=target_day_obj.get("date"),
        weather_override=weather_override,
    )
    if res.get("status") != "ok" or not res.get("day"):
        session["steps"] = res.get("steps") or session["steps"]
        return _build_plan_response(session, res.get("reply", "Không thể cập nhật lịch với điều kiện mới."), res.get("status", "infeasible"), res.get("missing_fields"))

    _push_undo(session)
    if new_budget is not None:
        session["base_prompt"] = edited_prompt
        session["constraints"]["ngan_sach_vnd"] = new_budget
    new_day = res["day"]
    d_cons = res["constraints"]
    meal_option, extras = _pick_meal_option(d_cons)
    day_weather = new_day.get("weather") or {}
    session["rang_buoc_by_day"][day_num] = {
        "to_hop": d_cons.get("venues") or ["vinwonders"],
        "so_nguoi_lon": d_cons["adults"] + d_cons["tall_kids_as_adult"],
        "so_tre_em_1m_1m4": d_cons["so_tre_em_1m_1m4"],
        "so_tre_duoi_1m": d_cons["so_tre_duoi_1m"],
        "so_nguoi_cao_tuoi": d_cons["seniors"],
        "chieu_cao_tre_cm": d_cons["heights_cm"] or None,
        "da_co_ve": d_cons["da_co_ve"],
        "goi_an": (new_day.get("cost") or {}).get("goi_an") or meal_option,
        "dich_vu": extras,
        "diem_ve_le": d_cons.get("want_paid_items") or None,
        "ngan_sach_vnd": d_cons.get("ngan_sach_vnd"),
        "gio_bat_dau": d_cons["gio_bat_dau"],
        "gio_ket_thuc": d_cons["gio_ket_thuc"],
        "thoi_tiet": d_cons["thoi_tiet"],
        "khung_gio_mua": day_weather.get("khung_gio_mua") if day_weather.get("co_mua") else None,
        "show_bi_huy": d_cons.get("show_bi_huy") or [],
    }
    for i, d_existing in enumerate(session["days"]):
        if int(d_existing["day"]) == day_num:
            session["days"][i] = new_day
            break
    session["steps"] = res.get("steps") or session["steps"]
    return _build_plan_response(session, res["reply"], "ok")


def _compute_candidate_window(
    ui_items: List[Dict[str, Any]],
    replace_idx: int,
    cand_meta: Dict[str, Any],
    zones_by_id: Dict[str, Dict[str, Any]],
) -> Tuple[str, str, int]:
    """Tính khung giờ (start, end, walk_from_prev_min) thống nhất giữa /alternatives và /swap."""
    old_item = ui_items[replace_idx]
    prev_park = None
    for j in range(replace_idx - 1, -1, -1):
        if ui_items[j].get("type") != "hotel" and not ui_items[j].get("is_free_rest"):
            prev_park = ui_items[j]
            break

    walk_prev = 0
    if prev_park and prev_park.get("zone_id") in zones_by_id:
        walk_prev, _ = _get_transfer_min(prev_park["zone_id"], cand_meta["zone_id"])

    if cand_meta.get("category") == "show":
        early = int(cand_meta.get("arrive_early_min", 10) or 10)
        s_min = max(0, _to_min(cand_meta["start_time"]) - early)
        e_min = _to_min(cand_meta["end_time"])
        return _to_hhmm(s_min), _to_hhmm(e_min), walk_prev

    old_s = _to_min(old_item["start"])
    s_min = max(old_s, (_to_min(prev_park["end"]) + walk_prev) if prev_park else old_s)
    dur = int(cand_meta.get("duration_min", 30) or 30)
    return _to_hhmm(s_min), _to_hhmm(s_min + dur), walk_prev


# ---------------------------------------------------------------------------
# 9 Endpoint chính thức
# ---------------------------------------------------------------------------


@app.get("/api/zones")
def get_zones() -> Dict[str, Any]:
    """1. Trả GeoJSON FeatureCollection 8 phân khu cụm Phú Quốc United Center (dự phòng mất mạng)."""
    zones_data = _load_json("park_zones.json")
    features = [
        {
            "type": "Feature",
            "id": z["id"],
            "properties": {
                "id": z["id"],
                "venue_id": z.get("venue_id", "vinwonders"),
                "name": z["name"],
                "english_name": z.get("english_name", ""),
                "open_time": z["open_time"],
                "close_time": z["close_time"],
                "indoor_ratio": z.get("indoor_ratio", "mixed"),
                "color": z.get("color", "#2c6ab0"),
                "center": z.get("center"),
                "description": z.get("description", ""),
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": z["polygon"],
            },
        }
        for z in zones_data["zones"]
    ]
    return {
        "type": "FeatureCollection",
        "park": zones_data.get("park", {}),
        "venues": zones_data.get("venues", {}),
        "features": features,
    }


@app.get("/api/hotels")
def get_hotels(
    ngay_den: Optional[str] = Query(default=None),
    ngay_ve: Optional[str] = Query(default=None),
    so_nguoi: int = Query(default=2, ge=1),
    ngan_sach_vnd: Optional[int] = Query(default=None),
    so_tre_em: int = Query(default=0, ge=0),
) -> Dict[str, Any]:
    """2. Gọi tool chỉ đọc tra_khach_san trả danh sách khách sạn tham khảo (ngoài phạm vi eval/)."""
    return tra_khach_san(
        ngay_den=ngay_den,
        ngay_ve=ngay_ve,
        so_nguoi=so_nguoi,
        ngan_sach_vnd=ngan_sach_vnd,
        so_tre_em=so_tre_em,
    )


@app.post("/api/chat")
def post_chat(req: ChatRequest) -> Dict[str, Any]:
    """3. Endpoint trò chuyện chính: Guardrail → G10 → tra_khach_san → plan_day() nhiều ngày & chỉnh sửa nối tiếp."""
    msg = (req.message or "").strip()
    if not msg:
        raise HTTPException(status_code=400, detail={"message": "Tin nhắn không được để trống."})

    session = SESSIONS.get(req.session_id) if req.session_id else None
    if session is None:
        session = _new_session(req.session_id)
    session["messages"].append({"role": "user", "content": msg})

    blocked_reply = _check_input_guardrail(msg, allow_hotel_context=True)
    if blocked_reply is not None:
        session["steps"] = [{"step": 1, "name": "Kiểm tra an toàn đầu vào", "status": "blocked", "detail": "Chặn yêu cầu vi phạm guardrail"}]
        session["messages"].append({"role": "assistant", "content": blocked_reply})
        return _build_plan_response(session, blocked_reply, "refused")

    # Nếu phiên đã có lịch -> xử lý câu chỉnh sửa nối tiếp (vd mưa chiều, bớt 1 triệu, huỷ show)
    if session.get("days"):
        m_day = re.search(r"ngay\s*([1-3])\b", _norm(msg))
        target_day = int(m_day.group(1)) if m_day else 1
        resp = _apply_followup_edit(session, target_day, msg)
        session["messages"].append({"role": "assistant", "content": resp["reply"]})
        return resp

    combined = (session["base_prompt"] + " " + msg).strip() if session.get("base_prompt") else msg
    constraints = _parse_constraints(combined)
    num_days, start_date, end_date = _parse_trip_meta(combined)

    if constraints["missing_fields"]:
        session["base_prompt"] = combined
        session["constraints"] = constraints
        session["ask_more_attempts"] += 1
        session["steps"] = [
            {"step": 1, "name": "Kiểm tra an toàn đầu vào", "status": "ok", "detail": "Hợp lệ"},
            {"step": 2, "name": "Trích ràng buộc gia đình (G10)", "status": "warn", "detail": "Thiếu: " + ", ".join(constraints["missing_fields"])},
        ]
        if session["ask_more_attempts"] >= 2:
            ask_reply = (
                "Thông tin vẫn còn thiếu (%s), nên hệ thống chưa thể tự đoán để lập lịch chính xác. "
                "Bạn vui lòng bổ sung đầy đủ để mình xếp lịch ngay nhé."
                % ", ".join(constraints["missing_fields"])
            )
        else:
            ask_reply = plan_day(combined, allow_hotel_context=True)["reply"]
        session["messages"].append({"role": "assistant", "content": ask_reply})
        return _build_plan_response(session, ask_reply, "ask_more", constraints["missing_fields"])

    session["base_prompt"] = combined
    session["constraints"] = constraints
    session["num_days"] = num_days
    session["start_date"] = start_date
    session["end_date"] = end_date

    total_people = constraints["adults"] + constraints["tall_kids_as_adult"] + constraints["so_tre_em_1m_1m4"] + constraints["so_tre_duoi_1m"] + constraints["seniors"]
    num_kids = len(constraints.get("heights_cm") or [])
    hotel_res = tra_khach_san(
        ngay_den=start_date,
        ngay_ve=end_date,
        so_nguoi=total_people,
        ngan_sach_vnd=constraints.get("ngan_sach_vnd"),
        so_tre_em=num_kids,
    )
    session["hotels"] = hotel_res.get("hotels") or []

    # Nếu đã có dữ liệu khách sạn và người dùng chưa chọn -> trả Bước 1 thẻ khách sạn tham khảo
    if session["hotels"] and not session.get("selected_hotel_id"):
        session["steps"] = [
            {"step": 1, "name": "Kiểm tra an toàn đầu vào", "status": "ok", "detail": "Hợp lệ"},
            {"step": 2, "name": "Trích ràng buộc gia đình (G10)", "status": "ok", "detail": f"{total_people} người · {num_days} ngày"},
            {"step": 3, "name": "Gợi ý khách sạn tham khảo", "status": "ok", "detail": f"{len(session['hotels'])} khách sạn gần cổng (dữ liệu phòng mô phỏng)"},
        ]
        need_hotel_reply = (
            "Đã nắm đủ thông số gia đình (%d người, %d ngày). Mình gợi ý %d khách sạn gần cổng bên dưới "
            "(số phòng trống là *dữ liệu mô phỏng*, đặt phòng mở trang chính thức). "
            "Hãy bấm chọn 1 khách sạn để mình lập lộ trình xuất phát từ nơi ở cho từng ngày nhé."
            % (total_people, num_days, len(session["hotels"]))
        )
        session["messages"].append({"role": "assistant", "content": need_hotel_reply})
        return _build_plan_response(session, need_hotel_reply, "need_hotel")

    # Chưa có data/hotels.json -> lập lịch thẳng không kẹt luồng
    gen = _generate_days_for_session(session, hotel_obj=None)
    session["steps"] = gen["steps"]
    session["days"] = gen["days"]
    session["rang_buoc_by_day"] = gen["rang_buoc_by_day"]
    session["messages"].append({"role": "assistant", "content": gen["reply"]})
    return _build_plan_response(session, gen["reply"], gen["status"], gen["missing_fields"])


@app.post("/api/sessions/{session_id}/hotel")
def select_session_hotel(session_id: str, req: SelectHotelRequest) -> Dict[str, Any]:
    """4. Chọn khách sạn xuất phát → chạy plan_day cho Ngày 1..N → trả PlanResponse."""
    session = SESSIONS.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail={"message": f"Không tìm thấy phiên '{session_id}'."})
    if not session.get("base_prompt"):
        raise HTTPException(status_code=400, detail={"message": "Phiên chưa có yêu cầu tham quan để lập lịch."})

    hotel_id = (req.hotel_id or "").strip()
    hotel_obj = None
    if hotel_id and hotel_id.lower() != "none":
        hotels = session.get("hotels") or tra_khach_san().get("hotels") or []
        hotel_obj = next((h for h in hotels if h.get("id") == hotel_id), None)
        if hotel_obj is None:
            raise HTTPException(status_code=404, detail={"message": f"Không tìm thấy khách sạn '{hotel_id}'."})
        session["hotels"] = hotels

    if session.get("days"):
        _push_undo(session)

    session["selected_hotel_id"] = hotel_obj["id"] if hotel_obj else None
    gen = _generate_days_for_session(session, hotel_obj=hotel_obj)
    session["steps"] = gen["steps"]
    session["days"] = gen["days"]
    session["rang_buoc_by_day"] = gen["rang_buoc_by_day"]
    session["messages"].append({"role": "assistant", "content": gen["reply"]})
    return _build_plan_response(session, gen["reply"], gen["status"], gen["missing_fields"])


@app.get("/api/attractions/{item_id}")
def get_attraction_detail(item_id: str, heights: Optional[str] = Query(default=None)) -> Dict[str, Any]:
    """5. Trả chi tiết điểm/show + media chính thức (hoặc 'Chưa có media') + nhãn chiều cao từng bé."""
    catalog, zones_by_id, _, _ = _load_catalog()
    item = catalog.get(item_id)
    if item is None:
        raw_hotels = _load_optional_json("hotels.json", {})
        h_rows = raw_hotels.get("hotels", raw_hotels) if isinstance(raw_hotels, dict) else raw_hotels
        hotel = next((h for h in (h_rows or []) if isinstance(h, dict) and h.get("id") == item_id), None)
        if hotel is None:
            raise HTTPException(status_code=404, detail={"message": f"Không tìm thấy điểm '{item_id}'."})
        return {
            "id": hotel["id"],
            "type": "hotel",
            "category": "hotel",
            "name": hotel["name"],
            "lat": hotel.get("lat"),
            "lng": hotel.get("lng"),
            "detail": hotel,
            "media": _get_media_payload(item_id, zone_id="HOTEL"),
            "height_labels": [],
        }

    parsed_heights: List[int] = []
    if heights:
        for tok in str(heights).split(","):
            tok = tok.strip()
            if tok.isdigit():
                parsed_heights.append(int(tok))

    min_h = int(item.get("min_height_cm", 0) or 0)
    return {
        "id": item["id"],
        "type": _ui_type_from_meta(item),
        "category": item.get("category", "ride"),
        "name": item["name"],
        "zone": zones_by_id.get(item["zone_id"], {}),
        "venue_id": item.get("venue_id", "vinwonders"),
        "indoor": bool(item.get("indoor", False)),
        "open_time": item.get("open_time") or item.get("start_time"),
        "close_time": item.get("close_time") or item.get("end_time"),
        "duration_min": item.get("duration_min"),
        "min_height_cm": min_h,
        "companion_required_below_cm": int(item.get("companion_required_below_cm", 0) or 0),
        "height_labels": [{"child_cm": h, "ok": h >= min_h} for h in parsed_heights],
        "lat": item.get("lat"),
        "lng": item.get("lng"),
        "notes": item.get("notes", ""),
        "media": _get_media_payload(item["id"], zone_id=item.get("zone_id")),
    }


@app.get("/api/sessions/{session_id}/days/{day_num}/alternatives")
def get_day_alternatives(session_id: str, day_num: int, item_id: str = Query(...)) -> Dict[str, Any]:
    """6. Gợi ý các điểm thay thế vừa khít khung giờ (qua chiều cao, thời tiết & kiem_lich_trinh)."""
    session, day_obj, _ = _get_session_and_day(session_id, day_num)
    ui_items = day_obj.get("items") or []
    rep_idx = next((i for i, it in enumerate(ui_items) if it.get("id") == item_id), None)
    if rep_idx is None:
        raise HTTPException(status_code=404, detail={"message": f"Không tìm thấy mốc '{item_id}' trong Ngày {day_num}."})

    old_item = ui_items[rep_idx]
    if old_item.get("type") == "hotel" or old_item.get("is_free_rest"):
        raise HTTPException(status_code=400, detail={"message": "Không hỗ trợ tìm thay thế cho mốc khách sạn hoặc nghỉ tự do."})

    catalog, zones_by_id, attractions, shows = _load_catalog()
    rang_buoc = _rang_buoc_for_day(session, day_num, day_obj, for_ui_edit=True)
    active_venues = set(rang_buoc.get("to_hop") or ["vinwonders"])
    existing_ids = {it.get("id") for it in ui_items}
    heights_cm = (session.get("constraints") or {}).get("heights_cm") or []
    min_child_h = min(heights_cm) if heights_cm else None

    candidates_pool = list(attractions) + list(shows)
    valid_alternatives: List[Dict[str, Any]] = []

    for cand in candidates_pool:
        cid = cand["id"]
        if cid in existing_ids or cand.get("category") == "rest":
            continue
        if cand.get("venue_id", "vinwonders") not in active_venues:
            continue
        if min_child_h is not None and int(cand.get("min_height_cm", 0) or 0) > min_child_h:
            continue

        cand_s, cand_e, walk_prev = _compute_candidate_window(ui_items, rep_idx, cand, zones_by_id)
        trial_items = list(ui_items)
        trial_items[rep_idx] = _make_ui_item(cand, cand_s, cand_e, heights_cm)
        chk = kiem_lich_trinh(_extract_park_schedule(trial_items), rang_buoc)
        if not chk["hop_le"]:
            continue

        same_zone = 0 if cand["zone_id"] == old_item.get("zone_id") else 1
        valid_alternatives.append(
            {
                "id": cid,
                "name": cand["name"],
                "type": _ui_type_from_meta(cand),
                "category": cand.get("category", "ride"),
                "zone_id": cand["zone_id"],
                "zone_name": zones_by_id.get(cand["zone_id"], {}).get("name", cand["zone_id"]),
                "venue_id": cand.get("venue_id", "vinwonders"),
                "start": cand_s,
                "end": cand_e,
                "duration_min": cand.get("duration_min"),
                "min_height_cm": int(cand.get("min_height_cm", 0) or 0),
                "indoor": bool(cand.get("indoor", False)),
                "walk_from_prev_min": walk_prev,
                "height_labels": [{"child_cm": int(h), "ok": int(h) >= int(cand.get("min_height_cm", 0) or 0)} for h in heights_cm],
                "notes": cand.get("notes", ""),
                "_sort_key": (same_zone, walk_prev, 0 if cand.get("indoor") else 1, cid),
            }
        )

    valid_alternatives.sort(key=lambda x: x.pop("_sort_key"))
    return {
        "session_id": session_id,
        "day": day_num,
        "replacing_item_id": item_id,
        "count": len(valid_alternatives),
        "items": valid_alternatives[:12],
    }


@app.post("/api/sessions/{session_id}/days/{day_num}/swap")
def swap_day_item(session_id: str, day_num: int, req: SwapItemRequest) -> Dict[str, Any]:
    """7. Đổi item_id -> new_id rồi BẮT BUỘC kiểm lại bằng kiem_lich_trinh (vi phạm thì hoàn nguyên & báo lỗi)."""
    session, day_obj, _ = _get_session_and_day(session_id, day_num)
    ui_items = day_obj.get("items") or []
    rep_idx = next((i for i, it in enumerate(ui_items) if it.get("id") == req.item_id), None)
    if rep_idx is None:
        raise HTTPException(status_code=404, detail={"message": f"Không tìm thấy mốc '{req.item_id}' trong Ngày {day_num}."})

    old_item = ui_items[rep_idx]
    if old_item.get("type") == "hotel" or old_item.get("is_free_rest"):
        raise HTTPException(status_code=400, detail={"message": "Không thể đổi mốc khách sạn hoặc khoảng nghỉ tự do."})

    catalog, zones_by_id, _, _ = _load_catalog()
    new_meta = catalog.get(req.new_id)
    if new_meta is None:
        raise HTTPException(status_code=404, detail={"message": f"Không tìm thấy điểm mới '{req.new_id}'."})
    if any(i != rep_idx and it.get("id") == req.new_id for i, it in enumerate(ui_items)):
        raise HTTPException(status_code=400, detail={"message": f"'{new_meta['name']}' đã có sẵn trong lịch Ngày {day_num}."})

    heights_cm = (session.get("constraints") or {}).get("heights_cm") or []
    rang_buoc = _rang_buoc_for_day(session, day_num, day_obj, for_ui_edit=True)
    new_s, new_e, _ = _compute_candidate_window(ui_items, rep_idx, new_meta, zones_by_id)

    trial_items = copy.deepcopy(ui_items)
    trial_items[rep_idx] = _make_ui_item(new_meta, new_s, new_e, heights_cm)
    check_res = kiem_lich_trinh(_extract_park_schedule(trial_items), rang_buoc)
    if not check_res["hop_le"]:
        reasons = "; ".join(v["message"] for v in check_res["vi_pham"])
        raise HTTPException(
            status_code=400,
            detail={
                "message": f"Không thể đổi sang '{new_meta['name']}' vì vi phạm: {reasons}",
                "vi_pham": check_res["vi_pham"],
                "goi_y": check_res["goi_y_noi_rang_buoc"],
            },
        )

    _push_undo(session)
    day_obj["items"] = trial_items
    _recompute_day_summary(day_obj, check_res)
    reply_msg = "Đã đổi **%s** → **%s** (`%s–%s`) ở Ngày %d — đã kiểm `kiem_lich_trinh`: `0 vi phạm`, tổng chi %s." % (
        old_item["name"],
        new_meta["name"],
        new_s,
        new_e,
        day_num,
        _fmt_vnd(check_res["tong_hop_chi_phi"]["tong_chi_phi_vnd"]),
    )
    session["steps"] = [
        {"step": 1, "name": "Kiểm tra thao tác đổi mốc", "status": "ok", "detail": f"{req.item_id} → {req.new_id}"},
        {"step": 2, "name": "Kiểm cứng kiem_lich_trinh", "status": "ok", "detail": "0 vi phạm"},
    ]
    session["messages"].append({"role": "assistant", "content": reply_msg})
    return _build_plan_response(session, reply_msg, "ok")


@app.post("/api/sessions/{session_id}/days/{day_num}/remove")
def remove_day_item(session_id: str, day_num: int, req: RemoveItemRequest) -> Dict[str, Any]:
    """8. Xoá mốc theo Luật xoá mốc (nhường giờ cho prev_item hoặc chuyển thành thời gian nghỉ) + kiểm kiem_lich_trinh."""
    session, day_obj, _ = _get_session_and_day(session_id, day_num)
    ui_items = day_obj.get("items") or []
    rem_idx = next((i for i, it in enumerate(ui_items) if it.get("id") == req.item_id), None)
    if rem_idx is None:
        raise HTTPException(status_code=404, detail={"message": f"Không tìm thấy mốc '{req.item_id}' trong Ngày {day_num}."})

    removed_item = ui_items[rem_idx]
    if removed_item.get("type") == "hotel" or removed_item.get("is_free_rest"):
        raise HTTPException(status_code=400, detail={"message": "Không thể xoá mốc khách sạn hoặc khoảng nghỉ tự do."})

    park_indices = [i for i, it in enumerate(ui_items) if it.get("type") != "hotel" and not it.get("is_free_rest")]
    if len(park_indices) <= 1:
        raise HTTPException(status_code=400, detail={"message": "Không thể xoá mốc công viên duy nhất còn lại trong ngày."})

    rang_buoc = _rang_buoc_for_day(session, day_num, day_obj, for_ui_edit=True)
    catalog, zones_by_id, _, _ = _load_catalog()

    def _build_free_rest_trial() -> List[Dict[str, Any]]:
        trial = copy.deepcopy(ui_items)
        # Nếu liền trước là khoảng nghỉ tự do sẵn thì gộp giờ lại cho gọn UI
        if rem_idx > 0 and trial[rem_idx - 1].get("is_free_rest"):
            trial[rem_idx - 1]["end"] = removed_item["end"]
            del trial[rem_idx]
            return trial
        trial[rem_idx] = {
            "id": f"REST-FREE-{day_num}-{rem_idx}",
            "type": "meal",
            "category": "rest",
            "is_free_rest": True,
            "name": "Thời gian nghỉ / di chuyển tự do",
            "zone_id": removed_item.get("zone_id", ""),
            "venue_id": removed_item.get("venue_id", "vinwonders"),
            "start": removed_item["start"],
            "end": removed_item["end"],
            "tach_nhom": False,
            "lat": removed_item.get("lat"),
            "lng": removed_item.get("lng"),
            "indoor": True,
            "cost_vnd": 0,
            "min_height_cm": 0,
            "companion_required_below_cm": 0,
            "height_labels": list(removed_item.get("height_labels") or []),
            "notes": f"Khoảng trống sau khi bỏ {removed_item['name']}.",
        }
        return trial

    prev_item = ui_items[rem_idx - 1] if rem_idx > 0 else None
    can_try_extend = bool(
        prev_item
        and prev_item.get("type") not in ("hotel", "show")
        and not prev_item.get("is_free_rest")
        and prev_item.get("id") in catalog
    )

    chosen_trial: Optional[List[Dict[str, Any]]] = None
    chosen_check: Optional[Dict[str, Any]] = None
    action_note = ""

    if can_try_extend and prev_item is not None:
        ext_trial = copy.deepcopy(ui_items)
        ext_trial[rem_idx - 1]["end"] = removed_item["end"]
        del ext_trial[rem_idx]
        ext_check = kiem_lich_trinh(_extract_park_schedule(ext_trial), rang_buoc)
        if ext_check["hop_le"]:
            chosen_trial = ext_trial
            chosen_check = ext_check
            action_note = "đã nhường khoảng trống để **%s** kéo dài đến `%s`" % (prev_item["name"], removed_item["end"])

    if chosen_trial is None:
        rest_trial = _build_free_rest_trial()
        rest_check = kiem_lich_trinh(_extract_park_schedule(rest_trial), rang_buoc)
        if not rest_check["hop_le"]:
            reasons = "; ".join(v["message"] for v in rest_check["vi_pham"])
            raise HTTPException(
                status_code=400,
                detail={
                    "message": f"Không thể xoá '{removed_item['name']}' vì phát sinh vi phạm: {reasons}",
                    "vi_pham": rest_check["vi_pham"],
                },
            )
        chosen_trial = rest_trial
        chosen_check = rest_check
        action_note = "đã chuyển `%s–%s` thành **Thời gian nghỉ / di chuyển tự do**" % (removed_item["start"], removed_item["end"])

    assert chosen_check is not None
    _push_undo(session)
    day_obj["items"] = chosen_trial
    _recompute_day_summary(day_obj, chosen_check)
    reply_msg = "Đã xoá **%s** ở Ngày %d — %s (đã kiểm `kiem_lich_trinh`: `0 vi phạm`)." % (
        removed_item["name"],
        day_num,
        action_note,
    )
    session["steps"] = [
        {"step": 1, "name": "Áp dụng luật xoá mốc", "status": "ok", "detail": action_note.replace("**", "").replace("`", "")},
        {"step": 2, "name": "Kiểm cứng kiem_lich_trinh", "status": "ok", "detail": "0 vi phạm"},
    ]
    session["messages"].append({"role": "assistant", "content": reply_msg})
    return _build_plan_response(session, reply_msg, "ok")


@app.post("/api/sessions/{session_id}/undo")
def undo_session(session_id: str) -> Dict[str, Any]:
    """9. Khôi phục trạng thái gần nhất trong undo stack của phiên."""
    session = SESSIONS.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail={"message": f"Không tìm thấy phiên '{session_id}'."})
    stack: List[Dict[str, Any]] = session.get("undo_stack") or []
    if not stack:
        raise HTTPException(status_code=400, detail={"message": "Chưa có thao tác nào trước đó để hoàn tác."})

    snap = stack.pop()
    session["constraints"] = snap["constraints"]
    session["rang_buoc_by_day"] = snap["rang_buoc_by_day"]
    session["selected_hotel_id"] = snap["selected_hotel_id"]
    session["days"] = snap["days"]
    session["steps"] = snap["steps"]
    reply_msg = "Đã hoàn tác về bước trước đó (giữ nguyên kết quả kiểm `0 vi phạm`)."
    session["messages"].append({"role": "assistant", "content": reply_msg})
    return _build_plan_response(session, reply_msg, "ok")
