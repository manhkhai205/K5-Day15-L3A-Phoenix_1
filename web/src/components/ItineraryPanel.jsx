import React from "react";
import { formatVnd } from "../utils/mapFallbackStyle.js";
import ParkMap from "./ParkMap.jsx";
import TimelineStrip from "./TimelineStrip.jsx";
import CheckModal from "./CheckModal.jsx";
import ItemDetailModal from "./ItemDetailModal.jsx";

export default function ItineraryPanel({
  zonesData,
  plan,
  activeDay,
  selectedItem,
  showCheckModal,
  isMockMode,
  loading,
  saveNotice,
  onChangeDay,
  onSelectItem,
  onOpenCheck,
  onCloseCheck,
  onSwapItem,
  onRemoveItem,
  onSavePlan,
  onDownloadPlan,
}) {
  const days = plan?.days || [];
  const currentDay = days.find((d) => Number(d.day) === Number(activeDay)) || days[0] || null;
  const dayItems = currentDay?.items || [];
  const summary = currentDay?.summary;
  const hotels = plan?.hotels || [];
  const selectedHotel = hotels.find((h) => h.id === plan?.selected_hotel_id) || null;
  const parkItemCount = dayItems.filter((it) => it.type !== "hotel" && !it.is_free_rest).length;

  return (
    <section className="panel itinerary-panel" aria-label="Bản đồ và lịch trình">
      <div className="itin-header-row">
        <div className="itin-title-block">
          <div className="lbl">
            {currentDay
              ? `Phú Quốc United Center · Ngày ${currentDay.day} / ${days.length}`
              : "Tổng quan 8 phân khu · Phú Quốc United Center"}
          </div>
          {days.length > 0 && (
            <div className="day-tabs">
              {days.map((d) => {
                const isAct = Number(d.day) === Number(currentDay?.day);
                return (
                  <button
                    key={d.day}
                    type="button"
                    className={`day-tab ${isAct ? "day-tab--active" : ""}`}
                    onClick={() => onChangeDay(d.day)}
                  >
                    <span>Ngày {d.day}</span>
                    {d.date && <span style={{ opacity: 0.78, fontWeight: 400 }}>{d.date}</span>}
                    {d.weather?.co_mua && <span>🌧️</span>}
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {currentDay && (
          <div className="itin-cta-group">
            {selectedHotel?.booking_url && (
              <a
                className="pill-cta-ghost"
                href={selectedHotel.booking_url}
                target="_blank"
                rel="noopener noreferrer"
              >
                Đặt phòng ↗
              </a>
            )}
            <button type="button" className="pill-cta-ghost" onClick={onDownloadPlan}>
              Tải JSON
            </button>
            <button type="button" className="pill-cta-ink" onClick={onSavePlan}>
              {saveNotice || "Lưu lịch"}
            </button>
            <button type="button" className="pill-cta-brand" onClick={onOpenCheck}>
              Bảng kiểm ^
            </button>
          </div>
        )}
      </div>

      {currentDay && (
        <div className="kpi-strip">
          <div className="kpi-cell">
            <span className="lbl">Dự kiến chi phí</span>
            <span className="num kpi-value">{formatVnd(summary?.cost_vnd)}</span>
          </div>
          <div className="kpi-cell">
            <span className="lbl">Lộ trình Ngày {currentDay.day}</span>
            <span className="num kpi-value">{summary?.n_items ?? dayItems.length} mốc</span>
          </div>
          <div className="kpi-cell">
            <span className="lbl">Hợp chiều cao bé</span>
            <span className="num kpi-value">
              {summary?.kid_ok_count ?? 0}/{summary?.total_rides ?? 0} trò
            </span>
          </div>
        </div>
      )}

      <ParkMap
        zonesData={zonesData}
        dayItems={dayItems}
        hotels={hotels}
        dayCheck={currentDay?.check || null}
        selectedItemId={selectedItem?.id || null}
        onSelectItem={onSelectItem}
        onOpenCheck={onOpenCheck}
      />

      {dayItems.length > 0 && (
        <TimelineStrip
          items={dayItems}
          selectedItemId={selectedItem?.id || null}
          onSelectItem={onSelectItem}
        />
      )}

      {showCheckModal && currentDay?.check && (
        <CheckModal dayNum={currentDay.day} check={currentDay.check} onClose={onCloseCheck} />
      )}

      {selectedItem && (
        <ItemDetailModal
          item={selectedItem}
          sessionId={plan?.session_id}
          activeDay={currentDay?.day || 1}
          parkItemCount={parkItemCount}
          isMockMode={isMockMode}
          busy={loading}
          onClose={() => onSelectItem(null)}
          onSwap={onSwapItem}
          onRemove={onRemoveItem}
        />
      )}
    </section>
  );
}
