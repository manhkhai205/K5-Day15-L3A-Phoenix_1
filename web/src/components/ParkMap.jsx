import React, { useEffect, useMemo, useRef, useState } from "react";
import maplibregl from "maplibre-gl";
import {
  buildGoogleMapsDirectionsUrl,
  FALLBACK_ZONES_GEOJSON,
  MAP_FALLBACK_STYLE,
  OPENFREEMAP_STYLE_URL,
} from "../utils/mapFallbackStyle.js";

function shortenName(name) {
  const s = String(name || "").split("(")[0].split("—")[0].trim();
  return s.length > 22 ? s.slice(0, 21) + "…" : s;
}

export default function ParkMap({
  zonesData,
  dayItems,
  hotels,
  dayCheck,
  selectedItemId,
  onSelectItem,
  onOpenCheck,
}) {
  const containerRef = useRef(null);
  const mapRef = useRef(null);
  const itemMarkersRef = useRef([]);
  const zoneMarkersRef = useRef([]);
  const hotelMarkersRef = useRef([]);
  const libertyLoadedRef = useRef(false);
  const fallbackTriggeredRef = useRef(false);
  const lastFitSigRef = useRef("");

  const [isOfflineFallback, setIsOfflineFallback] = useState(false);
  const [styleReadyTick, setStyleReadyTick] = useState(0);
  const [is3D, setIs3D] = useState(false);
  const [glassExpanded, setGlassExpanded] = useState(false);

  const effectiveZones = useMemo(() => {
    if (zonesData && Array.isArray(zonesData.features) && zonesData.features.length > 0) {
      return zonesData;
    }
    return FALLBACK_ZONES_GEOJSON;
  }, [zonesData]);

  const gmapsUrl = useMemo(() => buildGoogleMapsDirectionsUrl(dayItems), [dayItems]);

  // Khởi tạo MapLibre GL JS + OpenFreeMap Liberty + dự phòng ngoại tuyến
  useEffect(() => {
    if (!containerRef.current) return undefined;

    const map = new maplibregl.Map({
      container: containerRef.current,
      style: OPENFREEMAP_STYLE_URL,
      center: [103.858, 10.324],
      zoom: 14.2,
      attributionControl: { compact: true },
    });

    map.addControl(new maplibregl.NavigationControl({ visualizePitch: false, showZoom: true }), "bottom-right");
    mapRef.current = map;

    const triggerFallback = () => {
      if (fallbackTriggeredRef.current) return;
      fallbackTriggeredRef.current = true;
      setIsOfflineFallback(true);
      try {
        map.setStyle(MAP_FALLBACK_STYLE);
      } catch {
        // Bỏ qua nếu map đã hủy
      }
    };

    const timerId = window.setTimeout(() => {
      if (!libertyLoadedRef.current) {
        triggerFallback();
      }
    }, 3000);

    map.on("style.load", () => {
      if (!fallbackTriggeredRef.current) {
        libertyLoadedRef.current = true;
        window.clearTimeout(timerId);
      }
      setStyleReadyTick((t) => t + 1);
    });

    map.on("error", (ev) => {
      const msg = String(ev?.error?.message || ev?.message || "");
      const looksNetwork =
        !libertyLoadedRef.current ||
        ev?.sourceId === "openmaptiles" ||
        msg.toLowerCase().includes("fetch") ||
        msg.toLowerCase().includes("network") ||
        msg.toLowerCase().includes("openfreemap");
      if (looksNetwork) {
        triggerFallback();
      }
    });

    return () => {
      window.clearTimeout(timerId);
      itemMarkersRef.current.forEach((m) => m.remove());
      zoneMarkersRef.current.forEach((m) => m.remove());
      hotelMarkersRef.current.forEach((m) => m.remove());
      itemMarkersRef.current = [];
      zoneMarkersRef.current = [];
      hotelMarkersRef.current = [];
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // Chuyển đổi góc nhìn 2D / 3D
  function handleToggle3D() {
    const map = mapRef.current;
    const next = !is3D;
    setIs3D(next);
    if (map) {
      map.easeTo({
        pitch: next ? 45 : 0,
        bearing: next ? -12 : 0,
        duration: 500,
      });
    }
  }

  // Đồng bộ GeoJSON 8 phân khu + tuyến LineString + HTML markers
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded()) return;

    const zonesSource = map.getSource("zones-geojson");
    if (zonesSource) {
      zonesSource.setData(effectiveZones);
    } else {
      map.addSource("zones-geojson", {
        type: "geojson",
        data: effectiveZones,
      });
      map.addLayer({
        id: "zones-fill",
        type: "fill",
        source: "zones-geojson",
        paint: {
          "fill-color": ["coalesce", ["get", "color"], "#2c6ab0"],
          "fill-opacity": 0.22,
        },
      });
      map.addLayer({
        id: "zones-line",
        type: "line",
        source: "zones-geojson",
        paint: {
          "line-color": ["coalesce", ["get", "color"], "#2c6ab0"],
          "line-width": 1.6,
          "line-opacity": 0.85,
        },
      });
    }

    const coords = (dayItems || [])
      .filter((it) => typeof it.lng === "number" && typeof it.lat === "number")
      .map((it) => [it.lng, it.lat]);

    const routeGeoJson = {
      type: "FeatureCollection",
      features:
        coords.length >= 2
          ? [
              {
                type: "Feature",
                geometry: { type: "LineString", coordinates: coords },
                properties: {},
              },
            ]
          : [],
    };

    const routeSource = map.getSource("route-line");
    if (routeSource) {
      routeSource.setData(routeGeoJson);
    } else {
      map.addSource("route-line", {
        type: "geojson",
        data: routeGeoJson,
      });
      map.addLayer({
        id: "route-line-layer",
        type: "line",
        source: "route-line",
        layout: {
          "line-join": "round",
          "line-cap": "round",
        },
        paint: {
          "line-color": "#2c6ab0",
          "line-width": 3.5,
          "line-opacity": 0.85,
          "line-dasharray": [2, 1.2],
        },
      });
    }

    zoneMarkersRef.current.forEach((m) => m.remove());
    zoneMarkersRef.current = [];
    (effectiveZones.features || []).forEach((feat) => {
      const center = feat?.properties?.center;
      const name = feat?.properties?.name;
      if (!Array.isArray(center) || center.length !== 2 || !name) return;
      const el = document.createElement("div");
      el.className = "jp-zone-label";
      el.textContent = name;
      const marker = new maplibregl.Marker({ element: el, anchor: "center" }).setLngLat(center).addTo(map);
      zoneMarkersRef.current.push(marker);
    });

    itemMarkersRef.current.forEach((m) => m.remove());
    itemMarkersRef.current = [];
    (dayItems || []).forEach((it, idx) => {
      if (typeof it.lng !== "number" || typeof it.lat !== "number") return;
      const pinType = ["hotel", "ride", "show", "meal"].includes(it.type) ? it.type : "ride";
      const isActive = it.id === selectedItemId;

      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = `jp-pin jp-pin--${pinType}${isActive ? " jp-pin--active" : ""}`;
      btn.title = `${idx + 1}. ${it.name} (${it.start}–${it.end})`;
      btn.textContent = `${idx + 1} · ${shortenName(it.name)} · ${it.start}`;
      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        onSelectItem(it);
      });

      const marker = new maplibregl.Marker({ element: btn, anchor: "center" })
        .setLngLat([it.lng, it.lat])
        .addTo(map);
      itemMarkersRef.current.push(marker);
    });

    hotelMarkersRef.current.forEach((m) => m.remove());
    hotelMarkersRef.current = [];
    if (!dayItems || dayItems.length === 0) {
      (hotels || []).forEach((h) => {
        if (typeof h.lng !== "number" || typeof h.lat !== "number") return;
        const badge = document.createElement("div");
        badge.className = "jp-pin jp-pin--hotel";
        badge.textContent = `KS · ${shortenName(h.name)}`;
        const marker = new maplibregl.Marker({ element: badge, anchor: "center" })
          .setLngLat([h.lng, h.lat])
          .addTo(map);
        hotelMarkersRef.current.push(marker);
      });
    }

    const fitSig =
      coords.length > 0
        ? coords.map((c) => `${c[0].toFixed(4)},${c[1].toFixed(4)}`).join("|")
        : `hotels:${(hotels || []).map((h) => h.id).join(",")}`;

    if (fitSig !== lastFitSigRef.current) {
      lastFitSigRef.current = fitSig;
      const boundsCoords =
        coords.length > 0
          ? coords
          : (hotels || [])
              .filter((h) => typeof h.lng === "number" && typeof h.lat === "number")
              .map((h) => [h.lng, h.lat]);

      if (boundsCoords.length >= 2) {
        const bounds = boundsCoords.reduce(
          (b, c) => b.extend(c),
          new maplibregl.LngLatBounds(boundsCoords[0], boundsCoords[0])
        );
        map.fitBounds(bounds, {
          padding: { top: 76, bottom: 92, left: 48, right: 48 },
          maxZoom: 16.2,
          duration: 600,
        });
      } else if (boundsCoords.length === 1) {
        map.easeTo({ center: boundsCoords[0], zoom: 15.2, duration: 500 });
      }
    }
  }, [effectiveZones, dayItems, hotels, selectedItemId, styleReadyTick, onSelectItem]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !selectedItemId) return;
    const target = (dayItems || []).find((it) => it.id === selectedItemId);
    if (target && typeof target.lng === "number" && typeof target.lat === "number") {
      map.easeTo({ center: [target.lng, target.lat], duration: 400 });
    }
  }, [selectedItemId, dayItems]);

  const violationsCount = dayCheck?.so_vi_pham ?? 0;
  const warnings = dayCheck?.canh_bao || [];

  return (
    <div className="map-wrap">
      <div ref={containerRef} className="map-canvas" />

      <div className="map-overlay-top-left">
        {isOfflineFallback && <div className="offline-badge">Chế độ bản đồ ngoại tuyến</div>}
        <div className="map-legend">
          <span className="legend-item">
            <span className="legend-dot" style={{ background: "var(--pin-hotel)" }} />
            Khách sạn
          </span>
          <span className="legend-item">
            <span className="legend-dot" style={{ background: "var(--pin-ride)" }} />
            Điểm chơi
          </span>
          <span className="legend-item">
            <span className="legend-dot" style={{ background: "var(--pin-show)" }} />
            Show
          </span>
          <span className="legend-item">
            <span className="legend-dot" style={{ background: "var(--pin-meal)" }} />
            Ăn / Nghỉ
          </span>
        </div>
      </div>

      <div className="map-overlay-top-right">
        <button type="button" className="glass-pill" onClick={handleToggle3D} title="Chuyển góc nhìn 2D / 3D">
          {is3D ? "3D" : "2D"}
        </button>
        {gmapsUrl && (
          <a className="glass-pill" href={gmapsUrl} target="_blank" rel="noopener noreferrer">
            Google Maps ↗
          </a>
        )}
      </div>

      <div className="map-overlay-bottom-left">
        {dayCheck ? (
          <div className="map-glass-card">
            <div className="map-glass-head">
              <button
                type="button"
                onClick={onOpenCheck}
                style={{
                  border: "none",
                  background: "transparent",
                  padding: 0,
                  display: "inline-flex",
                  alignItems: "center",
                  gap: 6,
                }}
              >
                <span className={`jp-dot ${violationsCount > 0 ? "jp-dot--danger" : ""}`} />
                <span className="lbl" style={{ color: violationsCount > 0 ? "var(--danger)" : "var(--brand)" }}>
                  Kiểm cứng · {violationsCount} vi phạm
                </span>
              </button>
              <button
                type="button"
                className="icon-circle-btn"
                style={{ width: 26, height: 26, fontSize: 12 }}
                onClick={() => setGlassExpanded((v) => !v)}
                aria-label="Mở rộng lưu ý"
              >
                {glassExpanded ? "▴" : "▾"}
              </button>
            </div>

            {glassExpanded ? (
              <div className="map-glass-body">
                <div className="glass-bullet">
                  <span className="glass-bullet-dot" style={{ background: "var(--go)" }} />
                  <span>Đạt 5/5 điều kiện: giờ mở cửa, chồng giờ, ngân sách, chiều cao, thời tiết.</span>
                </div>
                {warnings.length > 0 && (
                  <>
                    <div className="lbl" style={{ color: "var(--rust)", marginTop: 2 }}>
                      Lưu ý ({warnings.length})
                    </div>
                    {warnings.slice(0, 2).map((w, i) => (
                      <div key={i} className="glass-bullet">
                        <span className="glass-bullet-dot" style={{ background: "var(--warn)" }} />
                        <span>{w.message}</span>
                      </div>
                    ))}
                  </>
                )}
              </div>
            ) : (
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: 12.5, color: "var(--muted)" }}>
                <span>{warnings.length > 0 ? `${warnings.length} lưu ý cho bé` : "5/5 điều kiện hợp lệ"}</span>
                <button
                  type="button"
                  onClick={onOpenCheck}
                  style={{ border: "none", background: "transparent", color: "var(--brand)", fontWeight: 600, padding: 0 }}
                >
                  Chi tiết →
                </button>
              </div>
            )}
          </div>
        ) : (
          <div className="map-glass-card">
            <div className="lbl">Kết quả sẽ hiển thị tại đây</div>
            <div style={{ fontSize: 13.5, lineHeight: 1.45, color: "var(--ink)" }}>
              Chọn một câu gợi ý hoặc mô tả nhu cầu gia đình. JoyPlan AI sẽ vẽ tuyến qua 8 phân khu, lọc chiều cao từng bé và tính chi phí dự kiến.
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
