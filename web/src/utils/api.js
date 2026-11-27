async function requestJson(url, options = {}) {
  const res = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  let data = null;
  try {
    data = await res.json();
  } catch {
    data = null;
  }

  if (!res.ok) {
    const detail = data && data.detail;
    const msg =
      (detail && typeof detail === "object" && detail.message) ||
      (typeof detail === "string" && detail) ||
      (data && data.message) ||
      `Lỗi máy chủ (HTTP ${res.status})`;
    const err = new Error(msg);
    err.status = res.status;
    err.detail = detail;
    throw err;
  }

  return data;
}

export function fetchZones() {
  return requestJson("/api/zones");
}

export function fetchHotels({ ngayDen, ngayVe, soNguoi, nganSachVnd, soTreEm } = {}) {
  const params = new URLSearchParams();
  if (ngayDen) params.set("ngay_den", ngayDen);
  if (ngayVe) params.set("ngay_ve", ngayVe);
  if (soNguoi != null) params.set("so_nguoi", String(soNguoi));
  if (nganSachVnd != null) params.set("ngan_sach_vnd", String(nganSachVnd));
  if (soTreEm != null) params.set("so_tre_em", String(soTreEm));
  const qs = params.toString();
  return requestJson(`/api/hotels${qs ? `?${qs}` : ""}`);
}

export function sendChat(sessionId, message) {
  return requestJson("/api/chat", {
    method: "POST",
    body: JSON.stringify({
      session_id: sessionId || null,
      message,
    }),
  });
}

export function selectHotel(sessionId, hotelId) {
  return requestJson(`/api/sessions/${encodeURIComponent(sessionId)}/hotel`, {
    method: "POST",
    body: JSON.stringify({ hotel_id: hotelId }),
  });
}

export function fetchAttractionDetail(itemId, heights = []) {
  const params = new URLSearchParams();
  if (Array.isArray(heights) && heights.length > 0) {
    params.set("heights", heights.join(","));
  }
  const qs = params.toString();
  return requestJson(`/api/attractions/${encodeURIComponent(itemId)}${qs ? `?${qs}` : ""}`);
}

export function fetchAlternatives(sessionId, dayNum, itemId) {
  const params = new URLSearchParams({ item_id: itemId });
  return requestJson(
    `/api/sessions/${encodeURIComponent(sessionId)}/days/${dayNum}/alternatives?${params.toString()}`
  );
}

export function swapItem(sessionId, dayNum, itemId, newId) {
  return requestJson(`/api/sessions/${encodeURIComponent(sessionId)}/days/${dayNum}/swap`, {
    method: "POST",
    body: JSON.stringify({ item_id: itemId, new_id: newId }),
  });
}

export function removeItem(sessionId, dayNum, itemId) {
  return requestJson(`/api/sessions/${encodeURIComponent(sessionId)}/days/${dayNum}/remove`, {
    method: "POST",
    body: JSON.stringify({ item_id: itemId }),
  });
}

export function undoSession(sessionId) {
  return requestJson(`/api/sessions/${encodeURIComponent(sessionId)}/undo`, {
    method: "POST",
    body: JSON.stringify({}),
  });
}
