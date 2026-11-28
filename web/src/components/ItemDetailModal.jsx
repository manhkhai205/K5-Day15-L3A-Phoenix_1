import React, { useEffect, useId, useRef, useState } from "react";
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
  const [mediaTab, setMediaTab] = useState("image");
  const [actionError, setActionError] = useState("");

  const tabBaseId = useId();
  const imageTabId = `${tabBaseId}-tab-image`;
  const videoTabId = `${tabBaseId}-tab-video`;
  const imageTabRef = useRef(null);
  const videoTabRef = useRef(null);

  useEffect(() => {
    if (!item) return undefined;
    let cancelled = false;
    setImgFailed(false);
    setMediaTab("image");
    setActionError("");
    setDetail(null);
    setAlternatives([]);

    if (item.is_free_rest) {
      setLoadingInfo(false);
      return undefined;
    }

    const heights = (item.height_labels || []).map((hl) => hl.child_cm);

    if (isMockMode) {
      if (item.media) {
        setDetail({ media: item.media, notes: item.notes });
        setLoadingInfo(false);
        return undefined;
      }
      setLoadingInfo(true);
      fetchAttractionDetail(item.id, heights)
        .catch(() => null)
        .then((det) => {
          if (cancelled) return;
          setDetail(det);
          setLoadingInfo(false);
        });
      return () => {
        cancelled = true;
      };
    }

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

  const media = detail?.media || item?.media || {};
  const embedUrl = toYoutubeEmbedUrl(media.youtube_url);
  const hasWorkingImage = Boolean(media.image_url) && !imgFailed;
  const hasBoth = hasWorkingImage && Boolean(embedUrl);
  const activeTab = hasBoth ? mediaTab : hasWorkingImage ? "image" : embedUrl ? "video" : "none";

  const openHours =
    detail?.open_time && detail?.close_time
      ? `${detail.open_time}–${detail.close_time}`
      : `${item.start}–${item.end}`;
  const canModify = !isMockMode && Boolean(sessionId) && item.type !== "hotel" && !item.is_free_rest;
  const canRemove = canModify && parkItemCount > 1;

  function handleTabKeyDown(e, currentKey) {
    if (e.key === "ArrowRight" || e.key === "ArrowLeft" || e.key === "Home" || e.key === "End") {
      e.preventDefault();
      const targetKey =
        e.key === "Home"
          ? "image"
          : e.key === "End"
          ? "video"
          : currentKey === "image"
          ? "video"
          : "image";
      const targetRef = targetKey === "image" ? imageTabRef : videoTabRef;
      targetRef.current?.focus();
    }
  }

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

        {/* Media Hybrid (tab Ảnh / Video youtube-nocookie + ảnh link chính thức + onError fallback) */}
        <div className="media-box">
          {loadingInfo ? (
            <div className="media-empty">
              <span>Đang tải media...</span>
            </div>
          ) : (
            <>
              {hasBoth && (
                <div className="media-tabs" role="tablist" aria-label="Loại media">
                  <button
                    ref={imageTabRef}
                    type="button"
                    role="tab"
                    id={imageTabId}
                    className="media-tab"
                    aria-selected={activeTab === "image"}
                    tabIndex={activeTab === "image" ? 0 : -1}
                    onClick={() => setMediaTab("image")}
                    onKeyDown={(e) => handleTabKeyDown(e, "image")}
                  >
                    Ảnh
                  </button>
                  <button
                    ref={videoTabRef}
                    type="button"
                    role="tab"
                    id={videoTabId}
                    className="media-tab"
                    aria-selected={activeTab === "video"}
                    tabIndex={activeTab === "video" ? 0 : -1}
                    onClick={() => setMediaTab("video")}
                    onKeyDown={(e) => handleTabKeyDown(e, "video")}
                  >
                    Video
                  </button>
                </div>
              )}

              {hasBoth ? (
                <>
                  <div role="tabpanel" aria-labelledby={imageTabId} hidden={activeTab !== "image"}>
                    {activeTab === "image" && (
                      <img
                        className="media-img"
                        src={media.image_url}
                        alt={media.caption || item.name}
                        referrerPolicy="no-referrer"
                        onError={() => setImgFailed(true)}
                      />
                    )}
                  </div>
                  <div role="tabpanel" aria-labelledby={videoTabId} hidden={activeTab !== "video"}>
                    {activeTab === "video" && embedUrl && (
                      <iframe
                        className="media-frame"
                        src={embedUrl}
                        title={`Video giới thiệu ${item.name}`}
                        loading="lazy"
                        referrerPolicy="strict-origin-when-cross-origin"
                        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                        allowFullScreen
                      />
                    )}
                  </div>
                </>
              ) : activeTab === "image" ? (
                <img
                  className="media-img"
                  src={media.image_url}
                  alt={media.caption || item.name}
                  referrerPolicy="no-referrer"
                  onError={() => setImgFailed(true)}
                />
              ) : activeTab === "video" && embedUrl ? (
                <iframe
                  className="media-frame"
                  src={embedUrl}
                  title={`Video giới thiệu ${item.name}`}
                  loading="lazy"
                  referrerPolicy="strict-origin-when-cross-origin"
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                  allowFullScreen
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

              {(activeTab === "image" || activeTab === "video") && (media.caption || media.source_url) && (
                <div className="media-caption">
                  <span>{media.caption || item.name}</span>
                  {media.source_url && (
                    <a
                      href={media.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{ color: "var(--brand)", fontWeight: 600, whiteSpace: "nowrap" }}
                    >
                      Nguồn chính thức ↗
                    </a>
                  )}
                </div>
              )}
            </>
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
