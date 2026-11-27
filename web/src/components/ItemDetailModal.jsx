import React, { useEffect, useState } from "react";
import { fetchAlternatives, fetchAttractionDetail } from "../utils/api.js";
import { toYoutubeEmbedUrl } from "../utils/mapFallbackStyle.js";

export default function ItemDetailModal({
  item,
  sessionId,
  activeDay,
  parkItemCount,
  isMockMode,
  busy,
  onClose,
  onSwap,
  onRemove,
}) {
  const [detail, setDetail] = useState(null);
  const [alternatives, setAlternatives] = useState([]);
  const [loadingInfo, setLoadingInfo] = useState(false);
  const [imgFailed, setImgFailed] = useState(false);
  const [actionError, setActionError] = useState("");

  useEffect(() => {
    if (!item) return undefined;
    let cancelled = false;
    setImgFailed(false);
    setActionError("");
    setDetail(null);
    setAlternatives([]);

    if (isMockMode || item.is_free_rest) {
      return undefined;
    }

    const heights = (item.height_labels || []).map((hl) => hl.child_cm);
    setLoadingInfo(true);

    const detailPromise = fetchAttractionDetail(item.id, heights).catch(() => null);
    const altPromise =
      sessionId && item.type !== "hotel"
        ? fetchAlternatives(sessionId, activeDay, item.id).catch(() => ({ items: [] }))
        : Promise.resolve({ items: [] });

    Promise.all([detailPromise, altPromise]).then(([det, altRes]) => {
      if (cancelled) return;
      setDetail(det);
      setAlternatives(altRes?.items || []);
      setLoadingInfo(false);
    });

    return () => {
      cancelled = true;
    };
  }, [item, sessionId, activeDay, isMockMode]);

  if (!item) return null;

  const media = detail?.media || {};
  const embedUrl = toYoutubeEmbedUrl(media.youtube_url);
  const hasWorkingImage = Boolean(media.image_url) && !imgFailed;
  const openHours =
    detail?.open_time && detail?.close_time
      ? `${detail.open_time}–${detail.close_time}`
      : `${item.start}–${item.end}`;
  const canModify = !isMockMode && Boolean(sessionId) && item.type !== "hotel" && !item.is_free_rest;
  const canRemove = canModify && parkItemCount > 1;

  async function handleSwapClick(newId) {
    setActionError("");
    try {
      await onSwap(item.id, newId);
    } catch (err) {
      setActionError(err.message || "Không thể đổi điểm này.");
    }
  }

  async function handleRemoveClick() {
    setActionError("");
    try {
      await onRemove(item.id);
    } catch (err) {
      setActionError(err.message || "Không thể xoá mốc này.");
    }
  }

  return (
    <div className="modal-backdrop" onClick={onClose} role="dialog" aria-modal="true" aria-label={item.name}>
      <div className="modal-glass" onClick={(e) => e.stopPropagation()}>
        <div className="modal-head">
          <div>
            <div style={{ fontSize: 12, fontWeight: 700, color: "var(--brand)" }}>
              {item.start}–{item.end} · {detail?.zone?.name || item.zone_id}
            </div>
            <h2 className="modal-title">{item.name}</h2>
          </div>
          <button type="button" className="modal-close" onClick={onClose} aria-label="Đóng">
            ×
          </button>
        </div>

        {/* Media Hybrid (YouTube embed hoặc ảnh link chính thức + onError fallback) */}
        <div className="media-box">
          {embedUrl ? (
            <iframe
              className="media-frame"
              src={embedUrl}
              title={item.name}
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowFullScreen
            />
          ) : hasWorkingImage ? (
            <img
              className="media-img"
              src={media.image_url}
              alt={media.caption || item.name}
              loading="lazy"
              referrerPolicy="no-referrer"
              onError={() => setImgFailed(true)}
            />
          ) : (
            <div className="media-empty">
              <span>Chưa có media</span>
              {media.source_url && (
                <a className="btn-outline-sm" href={media.source_url} target="_blank" rel="noopener noreferrer">
                  Xem trang chính thức ↗
                </a>
              )}
            </div>
          )}
        </div>

        <div style={{ display: "flex", flexWrap: "wrap", gap: 6, fontSize: 12.5 }}>
          <span className="summary-pill">Giờ hoạt động: {openHours}</span>
          {item.type !== "hotel" && (
            <span className="summary-pill">{item.indoor ? "Trong nhà / có mái che" : "Ngoài trời"}</span>
          )}
          {item.min_height_cm > 0 && <span className="summary-pill">Yêu cầu ≥ {item.min_height_cm}cm</span>}
        </div>

        {Array.isArray(item.height_labels) && item.height_labels.length > 0 && item.type !== "hotel" && (
          <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
            {item.height_labels.map((hl) => (
              <span
                key={hl.child_cm}
                className={`height-tag ${hl.ok ? "height-tag--ok" : "height-tag--no"}`}
              >
                Bé {hl.child_cm}cm {hl.ok ? "✓ Chơi được" : "✗ Chưa đủ chiều cao"}
              </span>
            ))}
          </div>
        )}

        {(detail?.notes || item.notes) && (
          <div style={{ fontSize: 13.5, lineHeight: 1.5, color: "var(--muted)" }}>
            {detail?.notes || item.notes}
          </div>
        )}

        {actionError && <div className="alert-error">{actionError}</div>}

        {canModify && (
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: "var(--ink)" }}>
              Đổi sang điểm khác cùng khung giờ (qua kiểm cứng)
            </div>
            {loadingInfo ? (
              <div style={{ fontSize: 12.5, color: "var(--subtle)" }}>Đang lọc điểm thay thế phù hợp...</div>
            ) : alternatives.length === 0 ? (
              <div style={{ fontSize: 12.5, color: "var(--subtle)" }}>
                Không có điểm thay thế khác vừa khít khung giờ này.
              </div>
            ) : (
              <div className="alt-list">
                {alternatives.slice(0, 6).map((alt) => (
                  <div key={alt.id} className="alt-item">
                    <div style={{ minWidth: 0 }}>
                      <div style={{ fontSize: 13, fontWeight: 700, color: "var(--ink)" }}>{alt.name}</div>
                      <div style={{ fontSize: 12, color: "var(--muted)" }}>
                        {alt.start}–{alt.end} · {alt.zone_name} ·{" "}
                        {alt.indoor ? "Trong nhà" : "Ngoài trời"}
                        {alt.min_height_cm > 0 ? ` · ≥${alt.min_height_cm}cm` : ""}
                      </div>
                    </div>
                    <button
                      type="button"
                      className="btn-primary-sm"
                      style={{ flex: "0 0 auto" }}
                      disabled={busy}
                      onClick={() => handleSwapClick(alt.id)}
                    >
                      Đổi
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 8 }}>
          {item.type !== "hotel" && !item.is_free_rest ? (
            <button
              type="button"
              className="btn-danger-sm"
              disabled={!canRemove || busy}
              onClick={handleRemoveClick}
              title={
                isMockMode
                  ? "Chế độ xem mẫu không gọi API xoá"
                  : parkItemCount <= 1
                  ? "Không thể xoá mốc duy nhất còn lại"
                  : "Xoá mốc và nhường giờ / nghỉ tự do"
              }
            >
              Xoá mốc này
            </button>
          ) : (
            <span />
          )}

          {isMockMode && (
            <span style={{ fontSize: 12, color: "var(--subtle)" }}>
              Đang xem dữ liệu mẫu — chat với API thật để Đổi / Xoá
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
