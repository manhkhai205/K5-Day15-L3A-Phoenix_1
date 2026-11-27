export const OPENFREEMAP_STYLE_URL = "https://tiles.openfreemap.org/styles/liberty";

export const MAP_FALLBACK_STYLE = {
  version: 8,
  name: "JoyPlan Offline Fallback",
  sources: {},
  layers: [
    {
      id: "offline-background",
      type: "background",
      paint: {
        "background-color": "#eef2f5",
      },
    },
  ],
};

export const FALLBACK_ZONES_GEOJSON = {
  type: "FeatureCollection",
  features: [
    {
      type: "Feature",
      id: "Z1_EURO",
      properties: {
        id: "Z1_EURO",
        venue_id: "vinwonders",
        name: "Đại lộ Châu Âu",
        open_time: "09:00",
        close_time: "19:30",
        color: "#c88a4b",
        center: [103.8535, 10.315],
      },
      geometry: {
        type: "Polygon",
        coordinates: [[[103.8515, 10.3136], [103.855, 10.3136], [103.855, 10.316], [103.8515, 10.316], [103.8515, 10.3136]]],
      },
    },
    {
      type: "Feature",
      id: "Z2_FAIRY",
      properties: {
        id: "Z2_FAIRY",
        venue_id: "vinwonders",
        name: "Thế giới diệu kỳ",
        open_time: "09:00",
        close_time: "19:30",
        color: "#9b7bd4",
        center: [103.8525, 10.3172],
      },
      geometry: {
        type: "Polygon",
        coordinates: [[[103.8515, 10.316], [103.854, 10.316], [103.854, 10.3186], [103.8515, 10.3186], [103.8515, 10.316]]],
      },
    },
    {
      type: "Feature",
      id: "Z3_ADVENTURE",
      properties: {
        id: "Z3_ADVENTURE",
        venue_id: "vinwonders",
        name: "Thế giới phiêu lưu",
        open_time: "09:00",
        close_time: "19:30",
        color: "#e07b3c",
        center: [103.8548, 10.3188],
      },
      geometry: {
        type: "Polygon",
        coordinates: [[[103.854, 10.3176], [103.8562, 10.3176], [103.8562, 10.32], [103.854, 10.32], [103.854, 10.3176]]],
      },
    },
    {
      type: "Feature",
      id: "Z4_VIKING",
      properties: {
        id: "Z4_VIKING",
        venue_id: "vinwonders",
        name: "Ngôi làng bí mật",
        open_time: "09:00",
        close_time: "19:30",
        color: "#5f8d4e",
        center: [103.857, 10.3182],
      },
      geometry: {
        type: "Polygon",
        coordinates: [[[103.8562, 10.317], [103.8582, 10.317], [103.8582, 10.3196], [103.8562, 10.3196], [103.8562, 10.317]]],
      },
    },
    {
      type: "Feature",
      id: "Z5_TYPHOON",
      properties: {
        id: "Z5_TYPHOON",
        venue_id: "vinwonders",
        name: "Thế giới lốc xoáy",
        open_time: "10:00",
        close_time: "18:00",
        color: "#2c82c9",
        center: [103.8568, 10.3156],
      },
      geometry: {
        type: "Polygon",
        coordinates: [[[103.8558, 10.314], [103.8582, 10.314], [103.8582, 10.317], [103.8558, 10.317], [103.8558, 10.314]]],
      },
    },
    {
      type: "Feature",
      id: "Z6_SEASHELL",
      properties: {
        id: "Z6_SEASHELL",
        venue_id: "vinwonders",
        name: "Cung điện Hải Vương",
        open_time: "10:00",
        close_time: "18:00",
        color: "#2e7d5b",
        center: [103.8552, 10.3162],
      },
      geometry: {
        type: "Polygon",
        coordinates: [[[103.8542, 10.3152], [103.856, 10.3152], [103.856, 10.3175], [103.8542, 10.3175], [103.8542, 10.3152]]],
      },
    },
    {
      type: "Feature",
      id: "Z7_SAFARI",
      properties: {
        id: "Z7_SAFARI",
        venue_id: "safari",
        name: "Vinpearl Safari Phú Quốc",
        open_time: "09:00",
        close_time: "16:00",
        color: "#4f9d69",
        center: [103.8741, 10.3342],
      },
      geometry: {
        type: "Polygon",
        coordinates: [[[103.8695, 10.3295], [103.8795, 10.3295], [103.8795, 10.3388], [103.8695, 10.3388], [103.8695, 10.3295]]],
      },
    },
    {
      type: "Feature",
      id: "Z8_GRANDWORLD",
      properties: {
        id: "Z8_GRANDWORLD",
        venue_id: "grandworld",
        name: "Grand World Phú Quốc",
        open_time: "08:00",
        close_time: "22:30",
        color: "#7b6fd6",
        center: [103.8529, 10.3237],
      },
      geometry: {
        type: "Polygon",
        coordinates: [[[103.8495, 10.3205], [103.8565, 10.3205], [103.8565, 10.3268], [103.8495, 10.3268], [103.8495, 10.3205]]],
      },
    },
  ],
};

export function formatVnd(amount) {
  if (amount == null || Number.isNaN(Number(amount))) return "—";
  return Number(amount).toLocaleString("vi-VN") + "đ";
}

export function buildGoogleMapsDirectionsUrl(items = []) {
  const pts = items.filter((it) => typeof it.lat === "number" && typeof it.lng === "number");
  if (pts.length === 0) return "";
  if (pts.length === 1) {
    return `https://www.google.com/maps/search/?api=1&query=${pts[0].lat},${pts[0].lng}`;
  }
  const origin = `${pts[0].lat},${pts[0].lng}`;
  const destination = `${pts[pts.length - 1].lat},${pts[pts.length - 1].lng}`;
  const mid = pts.slice(1, -1).slice(0, 8).map((p) => `${p.lat},${p.lng}`);
  const params = new URLSearchParams({
    api: "1",
    origin,
    destination,
    travelmode: "walking",
  });
  if (mid.length > 0) {
    params.set("waypoints", mid.join("|"));
  }
  return `https://www.google.com/maps/dir/?${params.toString()}`;
}

export function toYoutubeEmbedUrl(rawUrl) {
  if (!rawUrl || typeof rawUrl !== "string") return null;
  try {
    const u = new URL(rawUrl.trim());
    let videoId = "";
    if (u.hostname.includes("youtu.be")) {
      videoId = u.pathname.replace("/", "").trim();
    } else if (u.hostname.includes("youtube.com")) {
      if (u.pathname.startsWith("/embed/")) {
        videoId = u.pathname.split("/embed/")[1].split("/")[0];
      } else if (u.pathname.startsWith("/shorts/")) {
        videoId = u.pathname.split("/shorts/")[1].split("/")[0];
      } else {
        videoId = u.searchParams.get("v") || "";
      }
    }
    if (!videoId || !/^[a-zA-Z0-9_-]{6,20}$/.test(videoId)) return null;
    return `https://www.youtube.com/embed/${videoId}`;
  } catch {
    return null;
  }
}
