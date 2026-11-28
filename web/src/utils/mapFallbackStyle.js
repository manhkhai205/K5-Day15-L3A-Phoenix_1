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
        center: [103.85495, 10.33645],
      },
      geometry: {
        type: "Polygon",
        coordinates: [[[103.8542, 10.3357], [103.8555, 10.3357], [103.8559, 10.3372], [103.8542, 10.3372], [103.8542, 10.3357]]],
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
        center: [103.8535, 10.3364],
      },
      geometry: {
        type: "Polygon",
        coordinates: [[[103.8528, 10.3355], [103.8542, 10.3357], [103.8542, 10.3372], [103.8528, 10.3372], [103.8528, 10.3355]]],
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
        center: [103.8538, 10.3397],
      },
      geometry: {
        type: "Polygon",
        coordinates: [[[103.8529, 10.3389], [103.8544, 10.3389], [103.8544, 10.3405], [103.8534, 10.3405], [103.8529, 10.3389]]],
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
        center: [103.8551, 10.3398],
      },
      geometry: {
        type: "Polygon",
        coordinates: [[[103.8544, 10.3389], [103.856, 10.3389], [103.8556, 10.3409], [103.8544, 10.3405], [103.8544, 10.3389]]],
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
        center: [103.8552, 10.33805],
      },
      geometry: {
        type: "Polygon",
        coordinates: [[[103.8543, 10.3372], [103.8562, 10.3372], [103.856, 10.3389], [103.8543, 10.3389], [103.8543, 10.3372]]],
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
        center: [103.85355, 10.33805],
      },
      geometry: {
        type: "Polygon",
        coordinates: [[[103.8528, 10.3372], [103.8543, 10.3372], [103.8543, 10.3389], [103.8529, 10.3389], [103.8528, 10.3372]]],
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
        center: [103.89501, 10.3394],
      },
      geometry: {
        type: "Polygon",
        coordinates: [[[103.87954, 10.33694], [103.88331, 10.33055], [103.88914, 10.32613], [103.89565, 10.33015], [103.90046, 10.33839], [103.90583, 10.33744], [103.91157, 10.34063], [103.91013, 10.34622], [103.90039, 10.35378], [103.89015, 10.34311], [103.88323, 10.34135], [103.87954, 10.33694]]],
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
        center: [103.85814, 10.32494],
      },
      geometry: {
        type: "Polygon",
        coordinates: [[[103.85143, 10.32581], [103.85285, 10.32279], [103.85363, 10.32114], [103.85943, 10.32407], [103.86334, 10.32332], [103.86552, 10.32653], [103.86601, 10.32756], [103.86119, 10.32973], [103.85143, 10.32581]]],
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
    } else if (u.hostname.includes("youtube.com") || u.hostname.includes("youtube-nocookie.com")) {
      if (u.pathname.startsWith("/embed/")) {
        videoId = u.pathname.split("/embed/")[1].split("/")[0];
      } else if (u.pathname.startsWith("/shorts/")) {
        videoId = u.pathname.split("/shorts/")[1].split("/")[0];
      } else if (u.pathname.startsWith("/live/")) {
        videoId = u.pathname.split("/live/")[1].split("/")[0];
      } else {
        videoId = u.searchParams.get("v") || "";
      }
    }
    if (!videoId || !/^[a-zA-Z0-9_-]{6,20}$/.test(videoId)) return null;
    return `https://www.youtube-nocookie.com/embed/${videoId}`;
  } catch {
    return null;
  }
}
