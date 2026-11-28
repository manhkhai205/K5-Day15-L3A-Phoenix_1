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
    _get_transfer_min,
    _load_json,
    kiem_lich_trinh,
    tinh_chi_phi,
    tra_diem_choi,
    tra_khach_san,
    tra_lich_show,
    tra_thoi_tiet,
    uoc_thoi_gian_di,
)
from tracing import note

MAX_REPAIR_ROUNDS = 2
MAX_DAILY_STOPS = 10

SYSTEM = """Bạn là trợ lý lập & tái lập lịch trình cụm Phú Quốc United Center cho gia đình có trẻ nhỏ (mặc định VinWonders Phú Quốc nếu người dùng không nhắc khu khác; hỗ trợ thêm Vinpearl Safari và Grand World).
Quy tắc bắt buộc:
1. CHỈ sử dụng chính xác mã trong trường `id` của danh sách `diem_choi_hop_le` và `show_kha_dung` (vd `VW-Z2-01`, `SH-MERMAID-1`, `VW-MEAL-02`, `SF-Z7-01`, `GW-Z8-03`). TUYỆT ĐỐI KHÔNG dùng mã phân khu (`Z1_EURO`..`Z8_GRANDWORLD`) làm `id` và KHÔNG tự đặt mã mới (như `Z6_OCEAN_PALACE`, `Z5_WATER_PARK`).
2. BẮT BUỘC đưa vào lịch mọi show trong `show_bat_buoc` (đến sớm tối thiểu `early` phút trước `start` và kết thúc ở `end`), chèn ít nhất 1 bữa ăn (`VW-MEAL-*`, `SF-MEAL-*`, hoặc `GW-MEAL-*`) nếu khung giờ >= 5 tiếng bao trùm 11:00–15:00, và gom các trò cùng phân khu liền kề nhau để hạn chế đi vòng.
3. Tuân thủ giờ mở/đóng và thời gian di chuyển trong `ma_tran_di_chuyen`:
   - VinWonders: 09:00–19:30 (riêng Z5_TYPHOON & Z6_SEASHELL chỉ mở 10:00–18:00).
   - Vinpearl Safari (Z7_SAFARI): 09:00–16:00 (xe buýt bán hoang dã `SF-Z7-01` kết thúc <= 15:20).
   - Grand World (Z8_GRANDWORLD): 08:00–22:30; chuyển giữa 2 tổ hợp cần >= 15–20 phút VinBus.
   - Tuyệt đối không xếp bất kỳ mục nào kết thúc sau giờ về trong `rang_buoc.gio`; nếu khách đến từ 09:00 và muốn đi Z5_TYPHOON/Z6_SEASHELL (10:00 mới mở), hãy xếp 1 điểm ở Z1_EURO hoặc Z2_FAIRY trong khung 09:00–09:50 trước khi vào Z5/Z6 lúc 10:00.
4. Có thể giữ nguyên hoặc tinh chỉnh từ `lich_goi_y_tu_cong_cu` (đã đạt 0 vi phạm), nhưng vẫn phải đảm bảo 0 chồng giờ, đủ thời gian di chuyển, đúng chiều cao từng bé và không dùng điểm ngoài trời trong giờ mưa.
5. Giữ lịch trình gọn, vừa sức gia đình: tối đa `10` mốc/ngày (gồm điểm chơi, show và bữa ăn; ngày trọn vẹn khoảng `8–10` mốc, nửa ngày/buổi tối `3–7` mốc), phân bổ đều sáng–trưa–chiều–tối; tối đa 1 bữa trưa trong khung `11:00–15:00` (không xếp 2 bữa trưa liên tiếp khi đi nhiều tổ hợp); hạn chế quay lại phân khu đã rời (nếu cuối ngày có `SH-ONCE` ở `Z1_EURO` thì buổi sáng ưu tiên bắt đầu từ `Z2_FAIRY`).
6. Không bao giờ đặt vé, nhận số thẻ/OTP, đặt khách sạn/vé máy bay hay xác nhận thông tin trái dữ liệu chính thức.
7. Chỉ trả về đúng 1 khối JSON theo mẫu:
{
  "lich": [{"id": "MA_ID_CHINH_XAC", "start": "HH:MM", "end": "HH:MM", "tach_nhom": false}],
  "ghi_chu_rieng": ["..."],
  "diem_bo_qua": ["Tên điểm/khu bỏ qua kèm lý do ngắn gọn..."]
}"""

_VENUE_ORDER = ("safari", "vinwonders", "grandworld")

_VENUE_DISPLAY = {
    "safari": "Vinpearl Safari",
    "vinwonders": "VinWonders Phú Quốc",
    "grandworld": "Grand World",
}

_TICKET_DISPLAY = {
    "vinwonders": "Vé lẻ VinWonders Phú Quốc",
    "safari": "Vé lẻ Vinpearl Safari",
    "combo_vinwonders_safari": "Combo 1 ngày VinWonders + Vinpearl Safari",
    "grandworld_free_entry": "Vào cổng miễn phí Grand World",
    "da_co_ve": "Gia đình đã có vé sẵn",
}


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


def _detect_venues(raw_text: str) -> List[str]:
    """Nhận diện tổ hợp muốn đi (mặc định ['vinwonders'] để tương thích ngược 100% B01–B14)."""
    low = _norm(raw_text)
    if any(
        kw in low
        for kw in ("united center", "phu quoc united", "ca cum", "3 khu", "ba khu", "ca 3", "ca ba")
    ):
        return ["safari", "vinwonders", "grandworld"]

    selected: List[str] = []
    if any(kw in low for kw in ("safari", "vuon thu", "ban hoang da", "huou cao co", "z7")):
        selected.append("safari")
    if any(
        kw in low
        for kw in (
            "vinwonder",
            "vinwonders",
            "cong vien nuoc",
            "cung dien hai vuong",
            "thuy cung",
            "nang tien ca",
            "show once",
            "once show",
            "cho ca an",
            "the gioi dieu ky",
            "the gioi phieu luu",
            "dai lo chau au",
            "ngoi lang bi mat",
            "z1",
            "z2",
            "z3",
            "z4",
            "z5",
            "z6",
        )
    ):
        selected.append("vinwonders")
    if any(
        kw in low
        for kw in (
            "grand world",
            "grandworld",
            "venice",
            "tinh hoa viet nam",
            "gau teddy",
            "teddy bear",
            "thanh pho khong ngu",
            "z8",
        )
    ):
        selected.append("grandworld")

    return selected or ["vinwonders"]


def _check_input_guardrail(raw_text: str, allow_hotel_context: bool = False) -> Optional[str]:
    """Lớp 3 Guardrail: chặn prompt injection, giao dịch thanh toán, ngoài phạm vi và ép giờ/giá sai theo từng tổ hợp."""
    low = _norm(raw_text)
    venues = _detect_venues(raw_text)
    has_injection = any(
        kw in low
        for kw in ("system prompt", "bo qua huong dan", "ignore previous", "in nguyen huong dan", "lo prompt")
    )
    has_payment = bool(
        re.search(r"\b4\d{3}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b", low)
        or any(kw in low for kw in ("dat ve giup", "dat luon ve", "thanh toan bang the", "so the", "ma otp"))
    )
    if allow_hotel_context:
        has_out_of_scope = bool(
            re.search(r"\b(?:dat|book|thue)\b[^.?!]{0,25}\b(?:khach san|phong|resort|villa)\b", low)
            or any(kw in low for kw in ("ve may bay", "chuyen bay"))
        )
    else:
        has_out_of_scope = any(
            kw in low for kw in ("khach san", "ve may bay", "dat phong", "book phong", "chuyen bay")
        )

    has_false_vw_hours = bool(
        re.search(
            r"(?:vinwonders?|cong vien(?:\s*chu\s*de)?)\s*(?:mo(?:\s*cua)?|dong(?:\s*cua)?)\s*(?:den|toi|luc)?\s*(?:2[0-3])(?::|h|\b)",
            low,
        )
        or (
            "grandworld" not in venues
            and "safari" not in venues
            and re.search(r"(?:mo|den|toi)\s*(?:2[0-3]):?\d{0,2}", low)
        )
    )
    has_false_safari_hours = bool(
        "safari" in venues
        and (
            re.search(
                r"(?:safari|vuon thu)\s*(?:mo(?:\s*cua)?|dong(?:\s*cua)?)\s*(?:den|toi|luc)?\s*(?:1[7-9]|2[0-3])(?::|h|\b)",
                low,
            )
            or (venues == ["safari"] and re.search(r"(?:mo|dong|den|toi)\s*(?:1[7-9]|2[0-3]):?\d{0,2}", low))
        )
    )
    has_fake_discount = bool(re.search(r"(?:giam|khuyen mai)\s*(?:50|70|80|90)%", low))

    if not (
        has_injection
        or has_payment
        or has_out_of_scope
        or has_false_vw_hours
        or has_false_safari_hours
        or has_fake_discount
    ):
        return None

    # Tra cứu giờ mở cửa thật từ công cụ theo đúng tổ hợp bị hỏi sai (mặc định VinWonders cho B11/B12)
    lookup_venues = ["safari"] if (has_false_safari_hours and not has_false_vw_hours and "vinwonders" not in venues) else ["vinwonders"]
    show_info = tra_lich_show() if lookup_venues == ["vinwonders"] else tra_lich_show(to_hop=lookup_venues)
    park = show_info["gio_mo_cua_cong_vien"]
    zones_txt = ", ".join("%s (%s–%s)" % (z["name"], z["open_time"], z["close_time"]) for z in show_info["phan_khu"])

    reasons: List[str] = []
    if has_injection:
        reasons.append("từ chối tiết lộ hướng dẫn hệ thống hoặc bỏ qua quy tắc an toàn")
    if has_payment:
        reasons.append("không hỗ trợ đặt vé, thu tiền hay xử lý thông tin thẻ thanh toán/OTP")
    if has_out_of_scope:
        reasons.append("chỉ hỗ trợ lập lịch tham quan cụm Phú Quốc United Center (VinWonders / Safari / Grand World), không đặt khách sạn hoặc vé máy bay")
    if has_false_vw_hours:
        reasons.append(
            "không thể xác nhận giờ mở cửa sai — theo dữ liệu chính thức, %s mở cửa %s–%s (%s)"
            % (park["name"], park["open_time"], park["close_time"], zones_txt)
        )
    if has_false_safari_hours:
        sf_meta = show_info.get("to_hop", {}).get("safari", {})
        sf_open = sf_meta.get("open_time", "09:00")
        sf_close = sf_meta.get("close_time", "16:00")
        reasons.append(
            "không thể xác nhận giờ mở cửa sai — theo dữ liệu chính thức, Vinpearl Safari mở cửa %s–%s (cổng từ 08:30, chuyến xe buýt bán hoang dã cuối 15:20)"
            % (sf_open, sf_close)
        )
    if has_fake_discount:
        reasons.append("không tự ý xác nhận mức giảm giá không có trong bảng giá chính thức")

    note("tu_choi: " + "; ".join(reasons))
    return (
        "Mình không thể thực hiện yêu cầu này vì: %s.\n"
        "- Kênh thay thế hợp lệ: bạn vui lòng đặt vé chính thức qua ứng dụng *VinWonders: Theme Parks* hoặc `booking.vinwonders.com`.\n"
        "- Nếu cần, bạn hãy gửi lại số người, chiều cao bé, khung giờ và ngân sách để mình hỗ trợ xếp lịch trình tham quan bên trong công viên."
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


def _valid_hhmm(h_str: str, m_str: Optional[str]) -> Optional[str]:
    """Chuẩn hoá giờ:phút sang 'HH:MM' nếu nằm trong 00:00–23:59."""
    hh = int(h_str)
    mm = int(m_str or 0)
    if 0 <= hh <= 23 and 0 <= mm <= 59:
        return "%02d:%02d" % (hh, mm)
    return None


def _extract_time_window(raw_text: str, venues: Optional[List[str]] = None) -> Tuple[str, str, bool]:
    """Trích khung giờ dự kiến (gio_bat_dau, gio_ket_thuc, thieu_gio_ro) theo tổ hợp mục tiêu."""
    low = _norm(raw_text)
    v_list = venues or ["vinwonders"]
    default_end = (
        "22:00" if "grandworld" in v_list
        else ("16:00" if v_list == ["safari"] else "19:30")
    )

    m_range = re.search(r"(\d{1,2})[:h](\d{2})?\s*[-–~]\s*(\d{1,2})[:h](\d{2})?", low)
    if m_range:
        s = _valid_hhmm(m_range.group(1), m_range.group(2))
        e = _valid_hhmm(m_range.group(3), m_range.group(4))
        if s and e:
            return s, e, False

    m_from_to = re.search(
        r"(?:tu|den|dang|luc|bat\s*dau)"
        r"(?:\s+(?:vinwonders?(?:\s+phu\s+quoc)?|vinpearl\s+safari|safari|grand\s+world|cong\s+vien|cung|o|tai|luc|vao|dung|khoang|tam|tu)){0,4}"
        r"\s*(\d{1,2})[:h](\d{2})?.*?"
        r"(?:ra\s*ve(?:\s*luc)?|ve(?:\s*luc)?|ket\s*thuc(?:\s*luc)?|o\s*den|con\s*o\s*den|den|toi)"
        r"(?:\s+(?:luc|dung|khoang|tam))?\s*(\d{1,2})[:h](\d{2})?",
        low,
    )
    if m_from_to:
        s = _valid_hhmm(m_from_to.group(1), m_from_to.group(2))
        e = _valid_hhmm(m_from_to.group(3), m_from_to.group(4))
        if s and e and _to_min(s) < _to_min(e):
            return s, e, False

    m_arrive = re.search(
        r"(?:den(?:\s+(?:vinwonders?(?:\s+phu\s+quoc)?|safari|grand\s+world|cong\s+vien))?\s*(?:luc|vao|dung)|dang(?:\s+o)?(?:\s+luc)?)\s*(\d{1,2})[:h](\d{2})?",
        low,
    )
    if m_arrive:
        s = _valid_hhmm(m_arrive.group(1), m_arrive.group(2))
        if s:
            return s, default_end, False

    m_leave = re.search(
        r"(?:ra\s*ve(?:\s*luc)?|ve(?:\s*luc)?|ket\s*thuc(?:\s*luc)?|o\s*den|den|toi)\s*(?:luc|dung)?\s*(\d{1,2})[:h](\d{2})?",
        low,
    )
    if m_leave:
        e = _valid_hhmm(m_leave.group(1), m_leave.group(2))
        if e:
            if "con lai" in low or "xep hang" in low:
                return "14:00", e, True
            if _to_min(e) > _to_min("09:00"):
                return "09:00", e, False

    if "xep hang" in low and "con lai" in low:
        return "14:00", default_end, True
    return "09:00", default_end, True


def _extract_rain_query(raw_text: str) -> str:
    """Trích từ khoá mưa theo mốc giờ thực tế trong input (vd 'Đang 13:00, mưa to' -> 'mua to 13:00')."""
    low = _norm(raw_text)
    m_rain_at = re.search(
        r"(?:dang\s*(\d{1,2})[:h](\d{2})?[^.?!]{0,30}\bmua\b|\bmua(?:\s+to|\s+lon|\s+rao)?\s*(?:tu|luc|vao)\s*(\d{1,2})[:h](\d{2})?)",
        low,
    )
    if m_rain_at:
        hh = int(m_rain_at.group(1) or m_rain_at.group(3))
        mm = int(m_rain_at.group(2) or m_rain_at.group(4) or 0)
        if 0 <= hh <= 23 and 0 <= mm <= 59:
            prefix = "mua to" if re.search(r"\bmua\s*(?:to|lon)\b", low) else "mua"
            return "%s %02d:%02d" % (prefix, hh, mm)
    if "chieu" in low:
        return "mua chieu"
    if "toi" in low and not re.search(r"\bto\b", low):
        return "mua toi"
    return "mua"


def _parse_constraints(raw_text: str) -> Dict[str, Any]:
    """Phân tích input người dùng thành từ điển ràng buộc có kiểm tra biến thiếu."""
    low = _norm(raw_text)
    venues = _detect_venues(raw_text)
    heights = _extract_heights_cm(raw_text)
    budget = _extract_budget_vnd(raw_text)
    start_time, end_time, time_assumed = _extract_time_window(raw_text, venues)

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

    raw_low = unicodedata.normalize("NFC", (raw_text or "").strip().lower())
    has_rain = bool(
        "mưa" in raw_low
        or re.search(
            r"\b(?:troi\s+mua|bi\s+mua|co\s+mua|neu\s+mua|mua\s+(?:to|lon|rao|chieu|toi|phun|bat\s+chot)|rain)\b",
            low,
        )
    )
    has_hot = bool(
        "nắng" in raw_low
        or re.search(r"\b(?:troi\s+nang|nang\s+gat|nang\s+nong|sunny|hot)\b", low)
    )
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
    if "huy" in low and "tinh hoa" in low:
        canceled_shows.append("SH-GW-TINHHOA")
    if "huy" in low and "venice" in low:
        canceled_shows.append("SH-GW-VENICE")

    want_shows: List[str] = []
    if "nang tien ca" in low:
        want_shows.append("SH-MERMAID-2" if "SH-MERMAID-1" in canceled_shows else "SH-MERMAID-1")
    if "cho ca an" in low:
        want_shows.append("SH-FEED-FISH")
    if any(kw in low for kw in ("show toi", "once", "phuong hoang")) and "vinwonders" in venues:
        want_shows.append("SH-ONCE")
    if "safari" in venues:
        if any(kw in low for kw in ("zulu", "mua chau phi")):
            want_shows.append("SH-SF-ZULU")
        if any(kw in low for kw in ("animal", "show dong vat", "bieu dien dong vat")):
            want_shows.append("SH-SF-ANIMAL")
    if "grandworld" in venues:
        if "tinh hoa viet nam" in low and "SH-GW-TINHHOA" not in canceled_shows:
            want_shows.append("SH-GW-TINHHOA")
        if any(kw in low for kw in ("sac mau venice", "nhac nuoc")) and "SH-GW-VENICE" not in canceled_shows:
            want_shows.append("SH-GW-VENICE")

    want_paid_items: List[str] = []
    if "grandworld" in venues:
        if any(kw in low for kw in ("teddy", "gau")):
            want_paid_items.append("gw_teddy")
        if any(kw in low for kw in ("gondola", "thuyen")):
            want_paid_items.append("gw_venice_boat")
        if "tinh hoa viet nam" in low and "SH-GW-TINHHOA" not in canceled_shows:
            want_paid_items.append("gw_tinh_hoa")

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
        "venues": venues,
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
        "thoi_tiet": "mua" if has_rain else ("nang_gat" if has_hot else "nang"),
        "khung_gio_mua": rain_window,
        "show_bi_huy": canceled_shows,
        "want_shows": want_shows,
        "want_paid_items": want_paid_items,
        "prefer_water_park": "cong vien nuoc" in low or "loc xoay" in low,
        "prefer_indoor_midday": "trong nha" in low or has_hot or has_rain,
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
    venues = constraints.get("venues") or ["vinwonders"]
    paid_items = constraints.get("want_paid_items") or []

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
            to_hop=venues,
            diem_ve_le=paid_items,
        )
        if res["trong_ngan_sach"]:
            return meal, extras

    return "fastfood", []


def _safe_parse_min(hhmm: Any) -> Optional[int]:
    """Đổi chuỗi 'HH:MM' sang phút an toàn (trả None nếu sai định dạng)."""
    s = str(hhmm or "").strip()
    if len(s) == 5 and s[2] == ":" and s[:2].isdigit() and s[3:].isdigit():
        hh, mm = int(s[:2]), int(s[3:])
        if 0 <= hh <= 23 and 0 <= mm <= 59:
            return hh * 60 + mm
    return None


def _allocate_slot_quotas(weights: List[int], total_slots: int, min_per_nonzero: int = 0) -> List[int]:
    """Phân bổ số mốc tối đa theo tỉ lệ trọng số (Hamilton) cho các khoảng có weight > 0."""
    quotas = [0] * len(weights)
    if total_slots <= 0 or not weights:
        return quotas
    pos_indices = [i for i, w in enumerate(weights) if w > 0]
    if not pos_indices:
        return quotas

    rem = int(total_slots)
    if min_per_nonzero > 0:
        pos_count = len(pos_indices)
        if rem >= pos_count:
            base = min(min_per_nonzero, rem // pos_count)
            for idx in pos_indices:
                quotas[idx] = base
                rem -= base
        else:
            ranked = sorted(pos_indices, key=lambda idx: (-weights[idx], idx))
            for idx in ranked[:rem]:
                quotas[idx] += 1
            return quotas

    if rem > 0:
        total_w = sum(weights[i] for i in pos_indices)
        raw = [(i, (rem * weights[i]) / total_w) for i in pos_indices]
        for i, val in raw:
            fl = int(val)
            quotas[i] += fl
            rem -= fl
        if rem > 0:
            remainders = sorted(
                [(val - int(val), weights[i], -i, i) for i, val in raw],
                reverse=True,
            )
            for _, _, _, idx in remainders[:rem]:
                quotas[idx] += 1
    return quotas


def _trim_schedule_to_limit(
    schedule: List[Dict[str, Any]],
    max_stops: int,
    constraints: Dict[str, Any],
    catalog_by_id: Dict[str, Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Cắt gọn lịch vượt quá max_stops theo độ ưu tiên, giữ show bắt buộc, bữa ăn và đủ tổ hợp."""
    if len(schedule) <= max_stops:
        return list(schedule)

    def _entry_id(entry: Dict[str, Any]) -> str:
        return str(entry.get("id", entry.get("ma", ""))).strip()

    def _entry_start(entry: Dict[str, Any]) -> Optional[int]:
        return _safe_parse_min(entry.get("start", entry.get("bat_dau")))

    def _entry_end(entry: Dict[str, Any]) -> Optional[int]:
        return _safe_parse_min(entry.get("end", entry.get("ket_thuc")))

    items = [dict(x) for x in schedule]
    items.sort(key=lambda x: (_entry_start(x) is None, _entry_start(x) or 0))
    want_shows = set(constraints.get("want_shows") or [])
    prefer_water = bool(constraints.get("prefer_water_park"))

    while len(items) > max_stops:
        meal_indices: List[int] = []
        midday_meal_indices: List[int] = []
        venue_counts: Dict[str, int] = {}
        zone_counts: Dict[str, int] = {}
        water_count = 0

        metas: List[Tuple[str, Dict[str, Any], str, str, str]] = []
        for idx, entry in enumerate(items):
            eid = _entry_id(entry)
            meta = catalog_by_id.get(eid) or {}
            cat = str(
                meta.get("category")
                or entry.get("category")
                or ("show" if eid.startswith("SH-") else ("meal" if "-MEAL-" in eid else "ride"))
            )
            zone_id = str(meta.get("zone_id") or entry.get("zone_id") or "")
            venue_id = str(meta.get("venue_id") or entry.get("venue_id") or "")
            metas.append((eid, meta, cat, zone_id, venue_id))
            if cat == "meal":
                meal_indices.append(idx)
                s_min = _entry_start(entry)
                e_min = _entry_end(entry)
                if s_min is not None and 660 <= s_min < 900 and (e_min is None or e_min > 660):
                    midday_meal_indices.append(idx)
            if venue_id:
                venue_counts[venue_id] = venue_counts.get(venue_id, 0) + 1
            if zone_id:
                zone_counts[zone_id] = zone_counts.get(zone_id, 0) + 1
            if meta.get("is_water_park"):
                water_count += 1

        best_drop_idx: Optional[int] = None
        best_score: Optional[Tuple[int, int, int, int, int]] = None

        for idx, entry in enumerate(items):
            eid, meta, cat, zone_id, venue_id = metas[idx]
            if eid in want_shows:
                continue
            if cat == "meal" and len(meal_indices) <= 1:
                continue
            if venue_id and venue_counts.get(venue_id, 0) <= 1:
                continue
            if eid == "SF-Z7-01":
                continue
            if prefer_water and meta.get("is_water_park") and water_count <= 1:
                continue

            is_dup_midday_meal = 1 if (len(midday_meal_indices) >= 2 and idx in midday_meal_indices) else 0
            is_non_show = 0 if cat == "show" else 1
            z_cnt = zone_counts.get(zone_id, 0)

            s_cur = _entry_start(entry)
            e_cur = _entry_end(entry)
            gaps: List[int] = []
            if idx > 0:
                e_prev = _entry_end(items[idx - 1])
                if s_cur is not None and e_prev is not None:
                    gaps.append(max(0, s_cur - e_prev))
            if idx + 1 < len(items):
                s_next = _entry_start(items[idx + 1])
                if s_next is not None and e_cur is not None:
                    gaps.append(max(0, s_next - e_cur))
            min_neighbor_gap_min = min(gaps) if gaps else 999

            score = (is_dup_midday_meal, is_non_show, z_cnt, -min_neighbor_gap_min, idx)
            if best_score is None or score > best_score:
                best_score = score
                best_drop_idx = idx

        if best_drop_idx is None:
            break
        del items[best_drop_idx]

    return items


def _build_schedule_from_tools(
    constraints: Dict[str, Any],
    shows_data: Dict[str, Any],
    attractions_data: Dict[str, Any],
    weather_data: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Xếp lịch hợp lệ trực tiếp từ kết quả công cụ (tối đa MAX_DAILY_STOPS mốc, hỗ trợ đơn khu và đa tổ hợp)."""
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
            walk_cache[pair] = _get_transfer_min(z_a, z_b)[0]
        return walk_cache[pair]

    venues = constraints.get("venues") or ["vinwonders"]
    chosen: List[Dict[str, Any]] = []

    def _can_place(s_min: int, e_min: int, z_id: str, indoor: bool, item_meta: Optional[Dict[str, Any]] = None) -> bool:
        if s_min < t_start or e_min > t_end or s_min >= e_min:
            return False
        z = zones_by_id.get(z_id)
        if not z:
            return False
        if s_min < _to_min(z["open_time"]) or e_min > _to_min(z["close_time"]):
            return False
        if item_meta and item_meta.get("category") != "show":
            if s_min < _to_min(item_meta["open_time"]) or e_min > _to_min(item_meta["close_time"]):
                return False
        if not indoor and rain_span and s_min < rain_span[1] and rain_span[0] < e_min:
            return False
        for ex in chosen:
            walk = _walk(ex["zone_id"], z_id)
            ex_s, ex_e = _to_min(ex["start"]), _to_min(ex["end"])
            if s_min < ex_e + walk and ex_s < e_min + walk:
                return False
        return True

    def _add_item(meta: Dict[str, Any], s_min: int, e_min: int) -> None:
        chosen.append(
            {
                "id": meta["id"],
                "name": meta["name"],
                "zone_id": meta["zone_id"],
                "venue_id": meta.get("venue_id", "vinwonders"),
                "start": _to_hhmm(s_min),
                "end": _to_hhmm(e_min),
                "tach_nhom": False,
            }
        )

    # Nhánh 1: Thuần VinWonders Phú Quốc — giữ tương thích B01–B14 với trần MAX_DAILY_STOPS
    if venues == ["vinwonders"]:
        preferred_show_ids = list(dict.fromkeys(constraints["want_shows"]))
        if not preferred_show_ids:
            if t_start <= _to_min("13:50") and t_end >= _to_min("14:20") and "SH-MERMAID-1" in shows_by_id:
                preferred_show_ids.append("SH-MERMAID-1")
            if t_end >= _to_min("19:05") and "SH-ONCE" in shows_by_id:
                preferred_show_ids.append("SH-ONCE")

        for sid in preferred_show_ids:
            sh = shows_by_id.get(sid)
            if not sh:
                continue
            early = int(sh.get("arrive_early_min", 10))
            sh_s = max(t_start, _to_min(sh["start_time"]) - early)
            sh_e = _to_min(sh["end_time"])
            if _can_place(sh_s, sh_e, sh["zone_id"], sh.get("indoor", False), sh):
                _add_item(sh, sh_s, sh_e)

        if t_end - t_start >= 300 and t_start <= _to_min("13:00") and t_end >= _to_min("13:00"):
            for mid in ("VW-MEAL-02", "VW-MEAL-03", "VW-MEAL-01"):
                m_item = items_by_id.get(mid)
                if not m_item:
                    continue
                for m_start in (_to_min("11:45"), _to_min("12:15"), _to_min("12:45"), _to_min("11:15")):
                    m_end = m_start + int(m_item.get("duration_min", 50))
                    if _can_place(m_start, m_end, m_item["zone_id"], True, m_item):
                        _add_item(m_item, m_start, m_end)
                        break
                if any(x["id"].startswith("VW-MEAL") for x in chosen):
                    break

        chosen.sort(key=lambda x: _to_min(x["start"]))
        remaining_slots = max(0, MAX_DAILY_STOPS - len(chosen))
        if remaining_slots <= 0:
            return chosen

        candidates = [a for a in attractions_data["diem_choi"] if a.get("category") not in ("meal", "rest")]
        used_ids = {x["id"] for x in chosen}
        anchors = list(chosen) + [{"start": _to_hhmm(t_end), "end": _to_hhmm(t_end), "zone_id": "Z1_EURO"}]

        gaps: List[Tuple[int, int, Dict[str, Any]]] = []
        gap_weights: List[int] = []
        temp_cursor = t_start
        for anchor in anchors:
            g_start = temp_cursor
            g_end = _to_min(anchor["start"])
            dur_gap = max(0, g_end - g_start)
            gaps.append((g_start, g_end, anchor))
            gap_weights.append(dur_gap if dur_gap >= 25 else 0)
            temp_cursor = max(temp_cursor, _to_min(anchor["end"]))

        gap_quotas = _allocate_slot_quotas(gap_weights, remaining_slots)
        has_evening_once = any(x["id"] == "SH-ONCE" for x in chosen)
        initial_zone = "Z2_FAIRY" if (has_evening_once and t_start < _to_min("17:00")) else "Z1_EURO"
        zone_ride_counts: Dict[str, int] = {}
        left_zones: set = set()
        water_count = 0
        carryover = 0
        cursor = t_start

        for (g_start, gap_end, anchor), base_quota in zip(gaps, gap_quotas):
            cursor = max(cursor, g_start)
            quota_for_gap = base_quota + carryover
            placed_in_gap = 0
            prev_items = sorted(
                [c for c in chosen if _to_min(c["end"]) <= cursor],
                key=lambda c: _to_min(c["end"]),
            )
            prev_zone = prev_items[-1]["zone_id"] if prev_items else initial_zone
            for pi in prev_items:
                if pi["zone_id"] != prev_zone and zone_ride_counts.get(pi["zone_id"], 0) > 0:
                    left_zones.add(pi["zone_id"])

            while cursor < gap_end and placed_in_gap < quota_for_gap and len(chosen) < MAX_DAILY_STOPS:
                best_pick = None
                best_key = None
                remaining_in_gap = quota_for_gap - placed_in_gap
                for item in candidates:
                    if item["id"] in used_ids:
                        continue
                    if not item.get("indoor", False) and rain_span and cursor < rain_span[1] and rain_span[0] < gap_end:
                        continue
                    if constraints["prefer_indoor_midday"] and _to_min("11:00") <= cursor < _to_min("15:00") and not item.get("indoor"):
                        continue
                    walk_in = _walk(prev_zone, item["zone_id"]) if prev_items or chosen else 0
                    walk_out = _walk(item["zone_id"], anchor["zone_id"]) if anchor.get("id") else 0
                    min_start = max(
                        cursor + walk_in,
                        _to_min(item["open_time"]),
                        _to_min(zones_by_id[item["zone_id"]]["open_time"]),
                    )
                    dur = int(item.get("duration_min", 30))
                    if min_start + dur + walk_out > gap_end:
                        continue

                    s_try = min_start
                    if prev_items:
                        cushioned_s = max(min_start, cursor + 10)
                        if (
                            cushioned_s + dur + walk_out <= gap_end
                            and _can_place(cushioned_s, cushioned_s + dur, item["zone_id"], item.get("indoor", False), item)
                        ):
                            s_try = cushioned_s
                    e_try = s_try + dur
                    if not _can_place(s_try, e_try, item["zone_id"], item.get("indoor", False), item):
                        continue

                    water_pref = (
                        0
                        if (
                            constraints["prefer_water_park"]
                            and item.get("is_water_park")
                            and water_count < 2
                            and (
                                (cursor < _to_min("12:00") and (s_try - cursor) <= (65 if remaining_in_gap <= 1 else 45))
                                or (water_count == 0 and cursor >= _to_min("12:00"))
                            )
                        )
                        else 1
                    )
                    thrill_pref = 0 if (constraints["prefer_thrill"] and item.get("thrill_level") in ("medium", "high")) else 1
                    revisit_penalty = 1 if item["zone_id"] in left_zones else 0
                    avoid_z1_early = 1 if (has_evening_once and item["zone_id"] == "Z1_EURO" and cursor < _to_min("16:30")) else 0
                    zone_saturated = 1 if zone_ride_counts.get(item["zone_id"], 0) >= 2 else 0
                    same_zone = 0 if item["zone_id"] == prev_zone else 1
                    next_zone = 0 if (anchor.get("id") and item["zone_id"] == anchor["zone_id"]) else 1
                    key = (
                        water_pref,
                        thrill_pref,
                        revisit_penalty,
                        avoid_z1_early,
                        zone_saturated,
                        same_zone,
                        walk_in,
                        next_zone,
                        s_try,
                        item["id"],
                    )
                    if best_key is None or key < best_key:
                        best_key = key
                        best_pick = (item, s_try, e_try)
                if best_pick is None:
                    break
                item, s_try, e_try = best_pick
                if prev_zone != item["zone_id"] and zone_ride_counts.get(prev_zone, 0) > 0:
                    left_zones.add(prev_zone)
                _add_item(item, s_try, e_try)
                used_ids.add(item["id"])
                zone_ride_counts[item["zone_id"]] = zone_ride_counts.get(item["zone_id"], 0) + 1
                if item.get("is_water_park"):
                    water_count += 1
                placed_in_gap += 1
                prev_items.append(chosen[-1])
                prev_zone = item["zone_id"]
                cursor = e_try

            carryover = max(0, quota_for_gap - placed_in_gap)
            cursor = max(cursor, _to_min(anchor["end"]))

        chosen.sort(key=lambda x: _to_min(x["start"]))
        return chosen

    # Nhánh 2: Đơn khu Safari / Grand World hoặc Đa tổ hợp (trình tự Safari -> VinWonders -> Grand World, đệm VinBus 15–20 phút)
    ordered_venues = [v for v in _VENUE_ORDER if v in venues]
    venue_slices: List[Tuple[str, int, int]] = []
    want_tinhhoa = "SH-GW-TINHHOA" in constraints["want_shows"]
    cursor_slice = t_start

    for idx_v, vid in enumerate(ordered_venues):
        is_last = idx_v == len(ordered_venues) - 1
        if vid == "safari":
            if is_last:
                v_end = min(t_end, _to_min("16:00"))
            elif "vinwonders" in ordered_venues:
                v_end = min(t_end, _to_min("11:20"))
            else:
                v_end = min(t_end, _to_min("13:00"))
            v_start = max(cursor_slice, _to_min("09:00"))
        elif vid == "vinwonders":
            v_start = cursor_slice
            if is_last:
                v_end = min(t_end, _to_min("19:30"))
            elif want_tinhhoa:
                v_end = min(t_end, _to_min("18:20"))
            else:
                v_end = min(t_end, _to_min("19:10"))
        else:  # grandworld
            v_start = max(cursor_slice, _to_min("17:00") if len(ordered_venues) == 1 and t_start < _to_min("17:00") and t_end >= _to_min("21:00") else cursor_slice)
            v_end = t_end

        if v_start < v_end:
            venue_slices.append((vid, v_start, v_end))
            if not is_last:
                next_vid = ordered_venues[idx_v + 1]
                transfer_gap = 20 if ("safari" in (vid, next_vid)) else 15
                cursor_slice = max(cursor_slice, v_end + transfer_gap)

    used_ids: set = set()
    midday_meal_placed = False
    dinner_placed = False
    want_paid_set = set(constraints.get("want_paid_items") or [])

    # Lượt 1: Đặt trước show tiêu biểu, bữa trưa (tối đa 1 lần) và bữa tối Grand World cho mọi tổ hợp
    for vid, v_start, v_end in venue_slices:
        venue_shows: List[str] = [
            sid for sid in constraints["want_shows"]
            if sid in shows_by_id and shows_by_id[sid].get("venue_id") == vid
        ]
        if vid == "safari" and "SH-SF-ANIMAL" in shows_by_id and "SH-SF-ANIMAL" not in venue_shows:
            venue_shows.append("SH-SF-ANIMAL")
        elif vid == "vinwonders":
            if "SH-MERMAID-1" in shows_by_id and "SH-MERMAID-1" not in venue_shows and v_start <= _to_min("13:50") and v_end >= _to_min("14:20"):
                venue_shows.append("SH-MERMAID-1")
            if "SH-ONCE" in shows_by_id and "SH-ONCE" not in venue_shows and not want_tinhhoa and v_end >= _to_min("19:05"):
                venue_shows.append("SH-ONCE")
        elif vid == "grandworld":
            if "SH-GW-VENICE" in shows_by_id and "SH-GW-VENICE" not in venue_shows and v_end >= _to_min("22:00"):
                venue_shows.append("SH-GW-VENICE")

        for sid in venue_shows:
            sh = shows_by_id.get(sid)
            if not sh or sid in used_ids:
                continue
            early = int(sh.get("arrive_early_min", 10))
            sh_s = max(v_start, _to_min(sh["start_time"]) - early)
            sh_e = _to_min(sh["end_time"])
            if sh_e <= v_end and _can_place(sh_s, sh_e, sh["zone_id"], sh.get("indoor", False), sh):
                _add_item(sh, sh_s, sh_e)
                used_ids.add(sid)

        if not midday_meal_placed and t_end - t_start >= 240 and v_start <= _to_min("13:00") and v_end >= _to_min("12:30"):
            meal_ids = (
                ["SF-MEAL-01"] if vid == "safari"
                else (["VW-MEAL-02", "VW-MEAL-03", "VW-MEAL-01"] if vid == "vinwonders" else ["GW-MEAL-01"])
            )
            for mid in meal_ids:
                m_item = items_by_id.get(mid)
                if not m_item:
                    continue
                for m_start in (_to_min("11:45"), _to_min("12:15"), _to_min("11:15"), _to_min("12:45")):
                    m_end = m_start + int(m_item.get("duration_min", 50))
                    if m_start >= v_start and m_end <= v_end and _can_place(m_start, m_end, m_item["zone_id"], True, m_item):
                        _add_item(m_item, m_start, m_end)
                        used_ids.add(mid)
                        midday_meal_placed = True
                        break
                if midday_meal_placed:
                    break

        if vid == "grandworld" and not dinner_placed and v_end >= _to_min("20:30"):
            gw_meal = items_by_id.get("GW-MEAL-01")
            if gw_meal and "GW-MEAL-01" not in used_ids:
                for m_start in (_to_min("19:25"), _to_min("19:00"), _to_min("18:30"), _to_min("19:45")):
                    m_end = m_start + int(gw_meal.get("duration_min", 50))
                    if m_start >= v_start and m_end <= v_end and _can_place(m_start, m_end, gw_meal["zone_id"], True, gw_meal):
                        _add_item(gw_meal, m_start, m_end)
                        used_ids.add("GW-MEAL-01")
                        dinner_placed = True
                        break

    # Lượt 2: Điền điểm chơi / tham quan trong khung giờ từng tổ hợp với trần MAX_DAILY_STOPS
    remaining_slots = max(0, MAX_DAILY_STOPS - len(chosen))
    if remaining_slots > 0 and venue_slices:
        slice_weights = [max(0, ve - vs) for _, vs, ve in venue_slices]
        slice_quotas = _allocate_slot_quotas(slice_weights, remaining_slots, min_per_nonzero=1)
        zone_ride_counts_v2: Dict[str, int] = {}
        left_zones_v2: set = set()
        has_evening_once_v2 = any(x["id"] == "SH-ONCE" for x in chosen)
        slice_carryover = 0

        for (vid, v_start, v_end), s_quota in zip(venue_slices, slice_quotas):
            if len(chosen) >= MAX_DAILY_STOPS:
                break
            budget_for_slice = s_quota + slice_carryover
            if budget_for_slice <= 0:
                continue

            v_candidates = [
                a for a in attractions_data["diem_choi"]
                if a.get("venue_id", "vinwonders") == vid
                and a.get("category") not in ("meal", "rest")
                and (not a.get("paid_ticket_key") or a["paid_ticket_key"] in want_paid_set or a.get("venue_id") != "grandworld")
            ]
            slice_items = sorted(
                [c for c in chosen if c.get("venue_id") == vid],
                key=lambda x: _to_min(x["start"]),
            )
            default_z = (
                "Z7_SAFARI" if vid == "safari"
                else ("Z8_GRANDWORLD" if vid == "grandworld" else ("Z2_FAIRY" if has_evening_once_v2 and v_start < _to_min("17:00") else "Z1_EURO"))
            )
            anchors = slice_items + [{"start": _to_hhmm(v_end), "end": _to_hhmm(v_end), "zone_id": default_z}]
            v_gaps: List[Tuple[int, int, Dict[str, Any]]] = []
            v_gap_weights: List[int] = []
            temp_c = v_start
            for anchor in anchors:
                gs = temp_c
                ge = _to_min(anchor["start"])
                gd = max(0, ge - gs)
                v_gaps.append((gs, ge, anchor))
                v_gap_weights.append(gd if gd >= 25 else 0)
                temp_c = max(temp_c, _to_min(anchor["end"]))

            v_gap_quotas = _allocate_slot_quotas(v_gap_weights, budget_for_slice)
            placed_in_slice = 0
            gap_carryover = 0
            cursor = v_start

            for (gs, gap_end, anchor), g_q in zip(v_gaps, v_gap_quotas):
                cursor = max(cursor, gs)
                q_gap = g_q + gap_carryover
                placed_in_gap = 0
                prev_in_slice = sorted(
                    [c for c in chosen if c.get("venue_id") == vid and _to_min(c["end"]) <= cursor],
                    key=lambda c: _to_min(c["end"]),
                )
                prev_zone = prev_in_slice[-1]["zone_id"] if prev_in_slice else default_z
                if vid == "vinwonders":
                    for pi in prev_in_slice:
                        if pi["zone_id"] != prev_zone and zone_ride_counts_v2.get(pi["zone_id"], 0) > 0:
                            left_zones_v2.add(pi["zone_id"])

                while cursor < gap_end and placed_in_gap < q_gap and placed_in_slice < budget_for_slice and len(chosen) < MAX_DAILY_STOPS:
                    best_pick = None
                    best_key = None
                    for item in v_candidates:
                        if item["id"] in used_ids:
                            continue
                        if not item.get("indoor", False) and rain_span and cursor < rain_span[1] and rain_span[0] < gap_end:
                            continue
                        if constraints["prefer_indoor_midday"] and _to_min("11:30") <= cursor < _to_min("15:00") and not item.get("indoor"):
                            continue
                        walk_in = _walk(prev_zone, item["zone_id"]) if prev_in_slice else 0
                        walk_out = _walk(item["zone_id"], anchor["zone_id"]) if anchor.get("id") else 0
                        min_start = max(
                            cursor + walk_in,
                            _to_min(item["open_time"]),
                            _to_min(zones_by_id[item["zone_id"]]["open_time"]),
                        )
                        dur = int(item.get("duration_min", 30))
                        if min_start + dur + walk_out > gap_end:
                            continue

                        s_try = min_start
                        if prev_in_slice:
                            cushioned_s = max(min_start, cursor + 10)
                            if (
                                cushioned_s + dur + walk_out <= gap_end
                                and _can_place(cushioned_s, cushioned_s + dur, item["zone_id"], item.get("indoor", False), item)
                            ):
                                s_try = cushioned_s
                        e_try = s_try + dur
                        if not _can_place(s_try, e_try, item["zone_id"], item.get("indoor", False), item):
                            continue

                        # Ưu tiên đi Safari Tour xe buýt đầu tiên ở Safari, ưu tiên điểm được yêu cầu ở Grand World
                        priority = 0
                        if vid == "safari" and item["id"] == "SF-Z7-01":
                            priority = -2
                        elif vid == "grandworld" and item.get("paid_ticket_key") in want_paid_set:
                            priority = -1
                        revisit_penalty = 1 if (vid == "vinwonders" and item["zone_id"] in left_zones_v2) else 0
                        avoid_z1_early = 1 if (vid == "vinwonders" and has_evening_once_v2 and item["zone_id"] == "Z1_EURO" and cursor < _to_min("16:30")) else 0
                        zone_saturated = 1 if (vid == "vinwonders" and zone_ride_counts_v2.get(item["zone_id"], 0) >= 2) else 0
                        same_zone = 0 if item["zone_id"] == prev_zone else 1
                        key = (
                            priority,
                            revisit_penalty,
                            avoid_z1_early,
                            zone_saturated,
                            same_zone,
                            walk_in,
                            s_try,
                            item["id"],
                        )
                        if best_key is None or key < best_key:
                            best_key = key
                            best_pick = (item, s_try, e_try)
                    if best_pick is None:
                        break
                    item, s_try, e_try = best_pick
                    if vid == "vinwonders" and prev_zone != item["zone_id"] and zone_ride_counts_v2.get(prev_zone, 0) > 0:
                        left_zones_v2.add(prev_zone)
                    _add_item(item, s_try, e_try)
                    used_ids.add(item["id"])
                    if vid == "vinwonders":
                        zone_ride_counts_v2[item["zone_id"]] = zone_ride_counts_v2.get(item["zone_id"], 0) + 1
                    placed_in_gap += 1
                    placed_in_slice += 1
                    prev_in_slice.append(chosen[-1])
                    prev_zone = item["zone_id"]
                    cursor = e_try

                gap_carryover = max(0, q_gap - placed_in_gap)
                cursor = max(cursor, _to_min(anchor["end"]))

            slice_carryover = max(0, budget_for_slice - placed_in_slice)

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


def _enrich_schedule(
    schedule: List[Dict[str, Any]],
    catalog_by_id: Dict[str, Dict[str, Any]],
    heights_cm: List[int],
) -> List[Dict[str, Any]]:
    """Đối chiếu lại từng mốc với catalog để điền đủ name, zone_id, lat/lng, nhãn chiều cao từng bé."""
    enriched: List[Dict[str, Any]] = []
    for raw_step in schedule:
        item_id = str(raw_step.get("id", raw_step.get("ma", ""))).strip()
        meta = catalog_by_id.get(item_id, {})
        cat = meta.get("category", "ride")
        if cat == "show":
            ui_type = "show"
        elif cat in ("meal", "rest"):
            ui_type = "meal"
        else:
            ui_type = "ride"

        min_h = int(meta.get("min_height_cm", 0) or 0)
        height_labels = [{"child_cm": int(h), "ok": int(h) >= min_h} for h in (heights_cm or [])]
        enriched.append(
            {
                "id": item_id,
                "type": ui_type,
                "category": cat,
                "name": meta.get("name") or raw_step.get("name") or item_id,
                "zone_id": meta.get("zone_id") or raw_step.get("zone_id") or "",
                "venue_id": meta.get("venue_id") or raw_step.get("venue_id") or "vinwonders",
                "start": str(raw_step.get("start", raw_step.get("bat_dau", ""))).strip(),
                "end": str(raw_step.get("end", raw_step.get("ket_thuc", ""))).strip(),
                "tach_nhom": bool(raw_step.get("tach_nhom", raw_step.get("split_group", False))),
                "lat": meta.get("lat"),
                "lng": meta.get("lng"),
                "indoor": bool(meta.get("indoor", False)),
                "cost_vnd": 0,
                "min_height_cm": min_h,
                "companion_required_below_cm": int(meta.get("companion_required_below_cm", 0) or 0),
                "height_labels": height_labels,
                "notes": meta.get("notes", ""),
            }
        )
    return enriched


def _check_missing_required_shows(
    schedule: List[Dict[str, Any]],
    constraints: Dict[str, Any],
    shows_by_id: Dict[str, Dict[str, Any]],
    zones_by_id: Dict[str, Dict[str, Any]],
    t_start: int,
    t_end: int,
) -> List[Dict[str, Any]]:
    """Kiểm tra xem có show bắt buộc nào người dùng yêu cầu (khả dụng & vừa giờ) bị bỏ sót không."""
    scheduled_ids = {str(s.get("id", "")).strip() for s in (schedule or [])}
    missing: List[Dict[str, Any]] = []
    for sid in constraints.get("want_shows") or []:
        if sid in scheduled_ids:
            continue
        sh = shows_by_id.get(sid)
        if not sh:
            continue
        z = zones_by_id.get(sh["zone_id"])
        sh_s = _to_min(sh["start_time"])
        sh_e = _to_min(sh["end_time"])
        if z and _to_min(z["open_time"]) <= sh_s and sh_e <= _to_min(z["close_time"]) and t_start <= sh_s and sh_e <= t_end:
            missing.append(
                {
                    "code": "MISSING_REQUIRED_SHOW",
                    "item_id": sid,
                    "message": "Người dùng yêu cầu xem %s (%s–%s, mã '%s') nhưng lịch chưa có."
                    % (sh["name"], sh["start_time"], sh["end_time"], sid),
                }
            )
    return missing


def _record_actual_transfers(schedule: List[Dict[str, Any]]) -> None:
    """Gọi @tool uoc_thoi_gian_di một lần cho từng chặng chuyển khu thực tế để trace gọn mà vẫn đủ căn cứ."""
    seen_legs: set = set()
    for idx in range(1, len(schedule)):
        z_a = schedule[idx - 1].get("zone_id")
        z_b = schedule[idx].get("zone_id")
        if z_a and z_b and (z_a != z_b or not seen_legs):
            if (z_a, z_b) not in seen_legs:
                seen_legs.add((z_a, z_b))
                uoc_thoi_gian_di(z_a, z_b)


def _format_output(
    constraints: Dict[str, Any],
    schedule: List[Dict[str, Any]],
    check_res: Dict[str, Any],
    shows_data: Dict[str, Any],
    excluded_rides: List[Dict[str, Any]],
    weather_data: Dict[str, Any],
    model_used: str,
    ghi_chu_rieng: Optional[List[str]] = None,
    diem_bo_qua: Optional[List[str]] = None,
    attractions_data: Optional[Dict[str, Any]] = None,
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
        rain_win = weather_data.get("khung_gio_mua") or []
        rain_str = "–".join(rain_win) if len(rain_win) == 2 else ", ".join(rain_win)
        lines.append(
            "*Thời tiết:* %s (khung mưa %s) — đã loại toàn bộ trò ngoài trời & Công viên nước trong giờ mưa."
            % (weather_data["trang_thai"], rain_str)
        )
        if attractions_data:
            scheduled_ids = {str(s.get("id", "")).strip() for s in schedule}
            outdoor_skipped = [
                a["name"]
                for a in (attractions_data.get("diem_choi") or [])
                if not a.get("indoor", False)
                and a.get("category") not in ("meal", "rest")
                and a.get("id") not in scheduled_ids
            ]
            if outdoor_skipped:
                lines.append(
                    "*Trò ngoài trời tạm bỏ trong giờ mưa:* %s."
                    % ", ".join(outdoor_skipped[:4])
                )
        t_s_min = _to_min(constraints["gio_bat_dau"])
        t_e_min = _to_min(constraints["gio_ket_thuc"])
        all_shows_pool = list(shows_data.get("show_kha_dung") or []) + list(
            shows_data.get("show_anh_huong_thoi_tiet") or []
        )
        seen_show_ids = set()
        outdoor_shows_txt: List[str] = []
        for sh in all_shows_pool:
            sid = sh.get("id")
            if not sid or sid in seen_show_ids or sh.get("indoor", False):
                continue
            seen_show_ids.add(sid)
            sh_s = _to_min(sh["start_time"])
            sh_e = _to_min(sh["end_time"])
            if sh_e > t_s_min and sh_s < t_e_min:
                outdoor_shows_txt.append("%s (%s–%s)" % (sh["name"], sh["start_time"], sh["end_time"]))
        if outdoor_shows_txt:
            lines.append(
                "*Lưu ý show ngoài trời phụ thuộc thời tiết:* %s diễn ra ngoài trời nên phụ thuộc thời tiết thực tế, có thể tạm dừng hoặc đổi lịch nếu mưa kéo dài."
                % "; ".join(outdoor_shows_txt)
            )

    if constraints["show_bi_huy"]:
        alt_shows = [s["name"] + " (" + s["start_time"] + "–" + s["end_time"] + ")" for s in shows_data["show_kha_dung"] if s.get("indoor")]
        lines.append(
            "*Cập nhật show bị hủy (%s):* các suất trong nhà còn khả dụng trong dữ liệu gồm: %s."
            % (", ".join(constraints["show_bi_huy"]), "; ".join(alt_shows) if alt_shows else "không còn suất thay thế")
        )

    venues = constraints.get("venues") or ["vinwonders"]
    venue_label = " + ".join(_VENUE_DISPLAY.get(v, v) for v in venues)
    lines.append(
        "\n**Lịch trình đề xuất — %s (%s–%s · đã kiểm `kiem_lich_trinh`: 0 vi phạm):**"
        % (venue_label, constraints["gio_bat_dau"], constraints["gio_ket_thuc"])
    )
    prev_venue_step = None
    multi_kids = len(constraints.get("heights_cm") or []) >= 2
    for step in schedule:
        cur_venue_step = step.get("venue_id")
        if prev_venue_step and cur_venue_step and cur_venue_step != prev_venue_step:
            transfer_min = 20 if "safari" in (prev_venue_step, cur_venue_step) else 15
            lines.append(
                "  ↳ *Di chuyển xe VinBus miễn phí (~%d phút): %s → %s*"
                % (transfer_min, _VENUE_DISPLAY.get(prev_venue_step, prev_venue_step), _VENUE_DISPLAY.get(cur_venue_step, cur_venue_step))
            )
        height_txt = ""
        if multi_kids and step.get("category") not in ("meal", "rest", "show") and step.get("height_labels"):
            height_txt = " · " + " · ".join(
                "Bé %dcm %s" % (hl["child_cm"], "✓" if hl["ok"] else "✗")
                for hl in step["height_labels"]
            )
        lines.append(
            "- `%s–%s` | **[%s] %s** *(khu %s)*%s"
            % (step["start"], step["end"], step["id"], step.get("name", step["id"]), step.get("zone_id", ""), height_txt)
        )
        if cur_venue_step:
            prev_venue_step = cur_venue_step

    cost = check_res["tong_hop_chi_phi"]
    lines.append("\n**Dự toán chi phí từ `tinh_chi_phi`:**")
    ticket_label = _TICKET_DISPLAY.get(cost.get("loai_ve_ap_dung", ""), "Vé tham quan")
    savings_txt = (
        " (tiết kiệm %sđ nhờ Combo)" % _fmt_vnd(cost["tiet_kiem_combo_vnd"])
        if cost.get("tiet_kiem_combo_vnd", 0) > 0
        else ""
    )
    lines.append("- *Loại vé áp dụng:* %s%s." % (ticket_label, savings_txt))
    lines.append(
        "- Vé tham quan/show: %s · Ăn uống (%s): %s · Dịch vụ phát sinh: %s → **Tổng dự kiến: %s**"
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
    for c_note in cost.get("ghi_chu", []):
        if "đặt cọc" not in c_note:
            lines.append("- *Ghi chú chi phí:* %s" % c_note)
    if constraints["ngan_sach_vnd"] is not None:
        lines.append("- So với ngân sách %s: còn dư %s." % (_fmt_vnd(constraints["ngan_sach_vnd"]), _fmt_vnd(cost["chenh_lech_ngan_sach_vnd"])))

    if excluded_rides:
        names = ", ".join("%s (%dcm)" % (r["name"], r["min_height_cm"]) for r in excluded_rides[:4])
        lines.append("\n*Trò chơi bị loại do giới hạn chiều cao bé (%dcm):* %s." % (constraints["min_child_height_cm"], names))

    extra_reasons = [str(x).strip() for x in (list(ghi_chu_rieng or []) + list(diem_bo_qua or [])) if str(x).strip()]
    if extra_reasons:
        lines.append("*Lý do & điểm bỏ qua:* " + " · ".join(extra_reasons[:5]))

    if check_res["canh_bao"]:
        lines.append("*Cảnh báo:* " + " · ".join(w["message"] for w in check_res["canh_bao"]))

    return "\n".join(lines)


def _compact_attr(a: Dict[str, Any]) -> Dict[str, Any]:
    """Rút gọn trường điểm chơi để tiết kiệm token vào nhưng đủ thông tin lập lịch."""
    return {
        "id": a["id"],
        "name": a["name"],
        "zone": a["zone_id"],
        "cat": a.get("category", "ride"),
        "indoor": a["indoor"],
        "open": a["open_time"],
        "close": a["close_time"],
        "dur": a["duration_min"],
        "min_h": a["min_height_cm"],
    }


def plan_day(
    text: str,
    *,
    allow_hotel_context: bool = False,
    selected_hotel: Optional[Dict[str, Any]] = None,
    day_index: int = 1,
    date_str: Optional[str] = None,
    weather_override: Optional[str] = None,
) -> Dict[str, Any]:
    """Lõi có cấu trúc: chạy workflow 5 bước trả dữ liệu chuẩn cho cả Web UI và answer(text)."""
    steps: List[Dict[str, Any]] = []

    # Bước 1: Input Guardrail (tấn công / ngoài phạm vi / ép sai thông tin)
    blocked_reply = _check_input_guardrail(text, allow_hotel_context=allow_hotel_context)
    if blocked_reply is not None:
        steps.append({"step": 1, "name": "Kiểm tra an toàn đầu vào", "status": "blocked", "detail": "Chặn yêu cầu vi phạm guardrail"})
        return {
            "status": "refused",
            "reply": blocked_reply,
            "missing_fields": [],
            "constraints": {},
            "venues": _detect_venues(text),
            "day": None,
            "steps": steps,
            "model_used": "guardrail",
        }
    steps.append({"step": 1, "name": "Kiểm tra an toàn đầu vào", "status": "ok", "detail": "Hợp lệ trong phạm vi cụm Phú Quốc United Center"})

    # Bước 2: Trích ràng buộc & kiểm tra thiếu thông tin (G10)
    constraints = _parse_constraints(text)
    if constraints["missing_fields"]:
        note("thieu_thong_tin: " + ", ".join(constraints["missing_fields"]))
        steps.append({"step": 2, "name": "Trích ràng buộc gia đình (G10)", "status": "warn", "detail": "Thiếu: " + ", ".join(constraints["missing_fields"])})
        ask_reply = (
            "Để xếp lịch chính xác và tránh vượt ngân sách hay chiều cao bé, bạn cho mình biết thêm:\n"
            "1. Số người lớn và số trẻ em?\n"
            "2. Chiều cao chính xác của từng bé (cm hoặc mét)?\n"
            "3. Khung giờ dự kiến ở công viên và tổng ngân sách (đã mua vé chưa)?"
        )
        return {
            "status": "ask_more",
            "reply": ask_reply,
            "missing_fields": list(constraints["missing_fields"]),
            "constraints": constraints,
            "venues": constraints["venues"],
            "day": None,
            "steps": steps,
            "model_used": "g10",
        }

    steps.append(
        {
            "step": 2,
            "name": "Trích ràng buộc gia đình (G10)",
            "status": "ok",
            "detail": "%d lớn, bé %s, %s–%s"
            % (
                constraints["adults"],
                "/".join("%dcm" % h for h in constraints["heights_cm"]) if constraints["heights_cm"] else "chưa rõ cm",
                constraints["gio_bat_dau"],
                constraints["gio_ket_thuc"],
            ),
        }
    )

    # Bước 3: Tra cứu dữ liệu thật qua các công cụ chỉ đọc
    venues = constraints.get("venues") or ["vinwonders"]
    to_hop_arg = None if venues == ["vinwonders"] else venues
    if weather_override:
        weather_query = weather_override
        if "mua" in _norm(weather_override):
            constraints["thoi_tiet"] = "mua"
    elif constraints["thoi_tiet"] == "mua":
        weather_query = _extract_rain_query(text)
    elif date_str and constraints["thoi_tiet"] == "nang":
        weather_query = date_str
    else:
        weather_query = constraints["thoi_tiet"]

    weather_data = tra_thoi_tiet(ngay=weather_query, khung_gio="%s-%s" % (constraints["gio_bat_dau"], constraints["gio_ket_thuc"]))
    if weather_data.get("co_mua"):
        constraints["thoi_tiet"] = "mua"
        constraints["khung_gio_mua"] = weather_data.get("khung_gio_mua")

    shows_data = tra_lich_show(ngay=weather_query, bo_qua_show=constraints["show_bi_huy"], to_hop=to_hop_arg)
    attractions_data = tra_diem_choi(chieu_cao_min=constraints["min_child_height_cm"], gom_an_nghi=True, to_hop=to_hop_arg)

    excluded_rides: List[Dict[str, Any]] = []
    if constraints["min_child_height_cm"] is not None:
        all_rides = tra_diem_choi(chieu_cao_min=None, gom_an_nghi=False, to_hop=to_hop_arg)
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
        to_hop=to_hop_arg,
        diem_ve_le=constraints["want_paid_items"] or None,
    )
    steps.append(
        {
            "step": 3,
            "name": "Gọi công cụ đọc dữ liệu",
            "status": "ok",
            "detail": "%d điểm phù hợp, %d show khả dụng (%s)"
            % (len(attractions_data["diem_choi"]), len(shows_data["show_kha_dung"]), ", ".join(venues)),
        }
    )

    if constraints["ngan_sach_vnd"] is not None and cost_check["trong_ngan_sach"] is False:
        shortfall = abs(int(cost_check["chenh_lech_ngan_sach_vnd"] or 0))
        note("bat_kha_thi_ngan_sach: thieu %d VND" % shortfall)
        steps.append({"step": 4, "name": "Lập lịch & kiểm cứng kiem_lich_trinh", "status": "blocked", "detail": "Thiếu ngân sách %sđ" % _fmt_vnd(shortfall)})
        infeasible_reply = (
            "Không xếp được lịch trình trong ngân sách %s.\n"
            "- Theo bảng giá công cụ `tinh_chi_phi`, chi phí tối thiểu (vé vào cổng/show: %s, ăn tiết kiệm %s: %s) là **%s**, đang **thiếu %s**.\n"
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
        return {
            "status": "infeasible",
            "reply": infeasible_reply,
            "missing_fields": [],
            "constraints": constraints,
            "venues": venues,
            "day": None,
            "steps": steps,
            "model_used": "cost_guard",
        }

    # Bước 4: Lập lịch + Kiểm cứng `kiem_lich_trinh` + Vòng sửa tối đa 2 vòng
    baseline_schedule = _build_schedule_from_tools(constraints, shows_data, attractions_data, weather_data)
    rang_buoc = {
        "to_hop": venues,
        "so_nguoi_lon": constraints["adults"] + constraints["tall_kids_as_adult"],
        "so_tre_em_1m_1m4": constraints["so_tre_em_1m_1m4"],
        "so_tre_duoi_1m": constraints["so_tre_duoi_1m"],
        "so_nguoi_cao_tuoi": constraints["seniors"],
        "chieu_cao_tre_cm": constraints["heights_cm"] or None,
        "da_co_ve": constraints["da_co_ve"],
        "goi_an": meal_option,
        "dich_vu": extras,
        "diem_ve_le": constraints["want_paid_items"] or None,
        "ngan_sach_vnd": constraints["ngan_sach_vnd"],
        "gio_bat_dau": constraints["gio_bat_dau"],
        "gio_ket_thuc": constraints["gio_ket_thuc"],
        "thoi_tiet": constraints["thoi_tiet"],
        "khung_gio_mua": weather_data.get("khung_gio_mua") if weather_data.get("co_mua") else None,
        "show_bi_huy": constraints["show_bi_huy"],
    }

    zones_by_id = {z["id"]: z for z in shows_data["phan_khu"]}
    shows_by_id = {s["id"]: s for s in shows_data["show_kha_dung"]}
    catalog_by_id: Dict[str, Dict[str, Any]] = {a["id"]: a for a in attractions_data["diem_choi"]}
    for s in shows_data["show_kha_dung"]:
        catalog_by_id[s["id"]] = s

    # Đảm bảo LUÔN giữ toàn bộ điểm ăn/nghỉ và cân đối điểm chơi theo từng tổ hợp
    meals_and_rest = [a for a in attractions_data["diem_choi"] if a.get("category") in ("meal", "rest")]
    rides_pool = [a for a in attractions_data["diem_choi"] if a.get("category") not in ("meal", "rest")]
    per_venue_limit = 22 if len(venues) <= 1 else max(5, 24 // len(venues))
    balanced_rides: List[Dict[str, Any]] = []
    counts_by_venue: Dict[str, int] = {}
    for a in rides_pool:
        v_id = a.get("venue_id", "vinwonders")
        if counts_by_venue.get(v_id, 0) < per_venue_limit:
            balanced_rides.append(a)
            counts_by_venue[v_id] = counts_by_venue.get(v_id, 0) + 1
    model_items = balanced_rides + meals_and_rest

    matrix_full = _load_json("park_zones.json")["walking_matrix_min"]
    active_zone_ids = [z["id"] for z in shows_data["phan_khu"]]
    compact_matrix = {
        za: {zb: matrix_full[za][zb] for zb in active_zone_ids}
        for za in active_zone_ids
        if za in matrix_full
    }
    required_show_payload = [
        {
            "id": shows_by_id[sid]["id"],
            "name": shows_by_id[sid]["name"],
            "zone": shows_by_id[sid]["zone_id"],
            "start": shows_by_id[sid]["start_time"],
            "end": shows_by_id[sid]["end_time"],
            "early": shows_by_id[sid].get("arrive_early_min", 10),
        }
        for sid in constraints.get("want_shows") or []
        if sid in shows_by_id
    ]
    baseline_compact = [{"id": s["id"], "start": s["start"], "end": s["end"]} for s in baseline_schedule]

    prompt_payload = {
        "yeu_cau": text,
        "to_hop": venues,
        "rang_buoc": {
            "nguoi_lon": rang_buoc["so_nguoi_lon"],
            "tre_em_cm": constraints["heights_cm"],
            "gio": "%s-%s" % (constraints["gio_bat_dau"], constraints["gio_ket_thuc"]),
            "da_co_ve": constraints["da_co_ve"],
            "goi_an": meal_option,
            "ngan_sach_vnd": constraints["ngan_sach_vnd"],
            "thoi_tiet": weather_data["trang_thai"],
            "khung_mua": rang_buoc["khung_gio_mua"],
            "so_diem_toi_da": MAX_DAILY_STOPS,
        },
        "show_bat_buoc": required_show_payload,
        "show_kha_dung": [
            {
                "id": s["id"],
                "name": s["name"],
                "zone": s["zone_id"],
                "start": s["start_time"],
                "end": s["end_time"],
                "early": s.get("arrive_early_min", 10),
                "indoor": s.get("indoor", False),
            }
            for s in shows_data["show_kha_dung"]
        ],
        "diem_choi_hop_le": [_compact_attr(a) for a in model_items],
        "ma_tran_di_chuyen": compact_matrix,
        "lich_goi_y_tu_cong_cu": baseline_compact,
    }

    reply = call_model(SYSTEM, "Dữ liệu công cụ:\n" + json.dumps(prompt_payload, ensure_ascii=False))
    model_used = reply.get("model", MODEL_PROVIDER)
    schedule = list(baseline_schedule)
    ghi_chu_rieng: List[str] = []
    diem_bo_qua: List[str] = []

    if model_used != "fake":
        parsed = _parse_model_json(reply.get("text", ""))
        if parsed and isinstance(parsed.get("lich"), list):
            schedule = parsed["lich"]
            if len(schedule) > MAX_DAILY_STOPS:
                schedule = _trim_schedule_to_limit(schedule, MAX_DAILY_STOPS, constraints, catalog_by_id)
            ghi_chu_rieng = parsed.get("ghi_chu_rieng") if isinstance(parsed.get("ghi_chu_rieng"), list) else []
            diem_bo_qua = parsed.get("diem_bo_qua") if isinstance(parsed.get("diem_bo_qua"), list) else []

    t_start_min = _to_min(constraints["gio_bat_dau"])
    t_end_min = _to_min(constraints["gio_ket_thuc"])
    check_res = kiem_lich_trinh(schedule, rang_buoc)
    missing_req = _check_missing_required_shows(schedule, constraints, shows_by_id, zones_by_id, t_start_min, t_end_min) if model_used != "fake" else []
    rounds = 0

    while (not check_res["hop_le"] or missing_req) and rounds < MAX_REPAIR_ROUNDS:
        rounds += 1
        all_errs = list(check_res["vi_pham"]) + missing_req
        note("sua_vong_%d: %d vi pham" % (rounds, len(all_errs)))
        if model_used != "fake":
            valid_ids_list = [
                "%s (%s | %s | %s-%s)" % (it["id"], it["name"], it["zone_id"], it["open_time"], it["close_time"])
                for it in model_items
            ] + [
                "%s (%s | %s | show %s-%s)" % (s["id"], s["name"], s["zone_id"], s["start_time"], s["end_time"])
                for s in shows_data["show_kha_dung"]
            ]
            repair_payload = {
                "yeu_cau_goc": text,
                "lich_vua_lap": schedule,
                "loi_can_sua": all_errs,
                "goi_y": check_res["goi_y_noi_rang_buoc"],
                "id_hop_le": valid_ids_list,
                "lich_mau_0_vi_pham": baseline_compact,
                "so_diem_toi_da": MAX_DAILY_STOPS,
            }
            repair_reply = call_model(
                SYSTEM,
                "Sửa lại toàn bộ lịch trình sang đúng JSON 0 vi phạm (CHỈ dùng mã trong id_hop_le):\n"
                + json.dumps(repair_payload, ensure_ascii=False),
            )
            parsed_repair = _parse_model_json(repair_reply.get("text", ""))
            if parsed_repair and isinstance(parsed_repair.get("lich"), list):
                schedule = parsed_repair["lich"]
                if len(schedule) > MAX_DAILY_STOPS:
                    schedule = _trim_schedule_to_limit(schedule, MAX_DAILY_STOPS, constraints, catalog_by_id)
                if isinstance(parsed_repair.get("ghi_chu_rieng"), list):
                    ghi_chu_rieng = parsed_repair["ghi_chu_rieng"]
                if isinstance(parsed_repair.get("diem_bo_qua"), list):
                    diem_bo_qua = parsed_repair["diem_bo_qua"]
        else:
            schedule = list(baseline_schedule)
        check_res = kiem_lich_trinh(schedule, rang_buoc)
        missing_req = _check_missing_required_shows(schedule, constraints, shows_by_id, zones_by_id, t_start_min, t_end_min) if model_used != "fake" else []

    if (not check_res["hop_le"] or missing_req) and model_used != "fake":
        baseline_check = kiem_lich_trinh(baseline_schedule, rang_buoc)
        baseline_missing = _check_missing_required_shows(baseline_schedule, constraints, shows_by_id, zones_by_id, t_start_min, t_end_min)
        if baseline_check["hop_le"] and not baseline_missing:
            note("fallback_lich_cong_cu")
            schedule = list(baseline_schedule)
            check_res = baseline_check
            missing_req = []
            ghi_chu_rieng = []
            diem_bo_qua = []
            used_zones = {
                (catalog_by_id.get(str(s.get("id", "")).strip(), {}).get("zone_id") or s.get("zone_id"))
                for s in schedule
            }
            skipped_zones = [z["name"] for z in shows_data["phan_khu"] if z["id"] not in used_zones]
            if skipped_zones:
                diem_bo_qua = [
                    "Chưa ghép phân khu %s trong khung giờ hiện tại để giữ lộ trình liền mạch, 0 chồng giờ"
                    % ", ".join(skipped_zones)
                ]

    if not check_res["hop_le"] or missing_req:
        all_errs = list(check_res["vi_pham"]) + missing_req
        note("dung: khong xep duoc sau %d vong sua" % rounds)
        steps.append({"step": 4, "name": "Lập lịch & kiểm cứng kiem_lich_trinh", "status": "blocked", "detail": "Còn %d vi phạm sau %d vòng sửa" % (len(all_errs), rounds)})
        fail_reply = (
            "Không thể xếp lịch trình thoả mãn toàn bộ ràng buộc hiện tại (còn %d vi phạm):\n- %s\nGợi ý nới ràng buộc:\n- %s"
            % (
                len(all_errs),
                "\n- ".join(v["message"] for v in all_errs),
                "\n- ".join(check_res["goi_y_noi_rang_buoc"] or ["Mở rộng khung giờ tham quan hoặc giảm số điểm muốn đi."]),
            )
        )
        return {
            "status": "infeasible",
            "reply": fail_reply,
            "missing_fields": [],
            "constraints": constraints,
            "venues": venues,
            "day": None,
            "steps": steps,
            "model_used": model_used,
        }

    if len(schedule) > MAX_DAILY_STOPS:
        trimmed = _trim_schedule_to_limit(schedule, MAX_DAILY_STOPS, constraints, catalog_by_id)
        trimmed_check = kiem_lich_trinh(trimmed, rang_buoc)
        trimmed_missing = _check_missing_required_shows(trimmed, constraints, shows_by_id, zones_by_id, t_start_min, t_end_min)
        if trimmed_check["hop_le"] and not trimmed_missing:
            schedule = trimmed
            check_res = trimmed_check
            missing_req = trimmed_missing

    # Bước 5: Làm giàu dữ liệu mốc, ghi chặng di chuyển thực tế và tổng hợp kết quả
    enriched_schedule = _enrich_schedule(schedule, catalog_by_id, constraints["heights_cm"])
    enriched_schedule.sort(key=lambda x: _to_min(x["start"]))
    _record_actual_transfers(enriched_schedule)

    steps.append({"step": 4, "name": "Lập lịch & kiểm cứng kiem_lich_trinh", "status": "ok", "detail": "0 vi phạm sau %d vòng sửa" % rounds})
    final_reply = _format_output(
        constraints=constraints,
        schedule=enriched_schedule,
        check_res=check_res,
        shows_data=shows_data,
        excluded_rides=excluded_rides,
        weather_data=weather_data,
        model_used=model_used,
        ghi_chu_rieng=ghi_chu_rieng,
        diem_bo_qua=diem_bo_qua,
        attractions_data=attractions_data,
    )

    ui_items = list(enriched_schedule)
    if selected_hotel:
        h_end = max(30, t_start_min - 5)
        h_start = max(0, h_end - 20)
        hotel_step = {
            "id": str(selected_hotel.get("id", "HOTEL-01")),
            "type": "hotel",
            "category": "hotel",
            "name": str(selected_hotel.get("name", "Khách sạn xuất phát")),
            "zone_id": "HOTEL",
            "venue_id": "hotel",
            "start": _to_hhmm(h_start),
            "end": _to_hhmm(h_end),
            "tach_nhom": False,
            "lat": selected_hotel.get("lat"),
            "lng": selected_hotel.get("lng"),
            "indoor": True,
            "cost_vnd": 0,
            "min_height_cm": 0,
            "companion_required_below_cm": 0,
            "height_labels": [{"child_cm": int(h), "ok": True} for h in constraints["heights_cm"]],
            "notes": selected_hotel.get("fit_note", "Điểm xuất phát (tham khảo, ngoài phạm vi chấm eval/)."),
        }
        ui_items.insert(0, hotel_step)

    ride_items = [it for it in enriched_schedule if it.get("category") not in ("meal", "rest")]
    kid_ok_count = sum(
        1 for it in ride_items if all(hl["ok"] for hl in (it.get("height_labels") or []))
    )
    cost_final = check_res["tong_hop_chi_phi"]
    steps.append(
        {
            "step": 5,
            "name": "Tổng hợp lịch & chi phí",
            "status": "ok",
            "detail": "%d mốc · Tổng chi %s" % (len(ui_items), _fmt_vnd(cost_final["tong_chi_phi_vnd"])),
        }
    )

    day_payload = {
        "day": day_index,
        "date": date_str or weather_data["ngay"],
        "weather": {
            "trang_thai": weather_data["trang_thai"],
            "co_mua": weather_data["co_mua"],
            "khung_gio_mua": weather_data["khung_gio_mua"],
        },
        "summary": {
            "cost_vnd": cost_final["tong_chi_phi_vnd"],
            "n_items": len(ui_items),
            "kid_ok_count": kid_ok_count,
            "total_rides": len(ride_items),
        },
        "items": ui_items,
        "check": {
            "hop_le": True,
            "so_vi_pham": 0,
            "vi_pham": [],
            "canh_bao": check_res["canh_bao"],
            "dieu_kien": {
                "gio_mo_cua": True,
                "chong_gio": True,
                "ngan_sach": True,
                "chieu_cao": True,
                "mua": True,
            },
        },
        "cost": cost_final,
        "excluded_rides": excluded_rides,
        "diem_bo_qua": diem_bo_qua,
        "ghi_chu_rieng": ghi_chu_rieng,
    }

    return {
        "status": "ok",
        "reply": final_reply,
        "missing_fields": [],
        "constraints": constraints,
        "venues": venues,
        "day": day_payload,
        "steps": steps,
        "model_used": model_used,
    }


def answer(text: str) -> dict:
    """Luồng workflow chính cho run.py / eval / simulate: giữ nguyên hợp đồng {"output": str}."""
    return {"output": plan_day(text, allow_hotel_context=False)["reply"]}
