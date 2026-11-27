import React, { useEffect, useRef } from "react";

const TYPE_META = {
  hotel: { label: "Xuất phát", color: "var(--pin-hotel)" },
  ride: { label: "Điểm chơi", color: "var(--pin-ride)" },
  show: { label: "Show", color: "var(--pin-show)" },
  meal: { label: "Ăn / Nghỉ", color: "var(--pin-meal)" },
};

export default function TimelineStrip({ items, selectedItemId, onSelectItem }) {
  const cardRefs = useRef({});

  useEffect(() => {
    if (selectedItemId && cardRefs.current[selectedItemId]) {
      cardRefs.current[selectedItemId].scrollIntoView({
        behavior: "smooth",
        inline: "center",
        block: "nearest",
      });
    }
  }, [selectedItemId]);

  if (!items || items.length === 0) {
    return (
      <div className="timeline-strip">
        <div className="timeline-empty">
          Chưa có mốc lịch trình — hãy gửi yêu cầu hoặc chọn khách sạn ở khung trò chuyện bên trái.
        </div>
      </div>
    );
  }

  return (
    <div className="timeline-strip" aria-label="Dải mốc lịch trình trong ngày">
      {items.map((it, idx) => {
        const meta = TYPE_META[it.type] || TYPE_META.ride;
        const isActive = it.id === selectedItemId;
        return (
          <button
            key={`${it.id}-${idx}`}
            ref={(el) => {
              cardRefs.current[it.id] = el;
            }}
            type="button"
            className={`tl-card ${isActive ? "tl-card--active" : ""}`}
            onClick={() => onSelectItem(it)}
          >
            <div className="tl-top">
              <span>
                #{idx + 1} · {it.start}–{it.end}
              </span>
              <span className="tl-type-badge" style={{ background: meta.color }}>
                {meta.label}
              </span>
            </div>
            <div className="tl-name">{it.name}</div>
            {Array.isArray(it.height_labels) && it.height_labels.length > 0 && it.type !== "hotel" && (
              <div className="tl-heights">
                {it.height_labels.map((hl) => (
                  <span
                    key={hl.child_cm}
                    className={`height-tag ${hl.ok ? "height-tag--ok" : "height-tag--no"}`}
                  >
                    Bé {hl.child_cm}cm {hl.ok ? "✓" : "✗"}
                  </span>
                ))}
              </div>
            )}
          </button>
        );
      })}
    </div>
  );
}
