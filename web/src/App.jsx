import React, { useEffect, useState } from "react";
import ChatPanel from "./components/ChatPanel.jsx";
import ItineraryPanel from "./components/ItineraryPanel.jsx";
import mockPlan from "./mock/plan.json";
import {
  fetchHotels,
  fetchZones,
  removeItem,
  selectHotel,
  sendChat,
  swapItem,
  undoSession,
} from "./utils/api.js";
import { FALLBACK_ZONES_GEOJSON } from "./utils/mapFallbackStyle.js";
import { deleteSavedPlan, downloadPlanJson, loadSavedPlans, savePlanToStorage } from "./utils/storage.js";

export default function App() {
  const [zonesData, setZonesData] = useState(FALLBACK_ZONES_GEOJSON);
  const [apiOnline, setApiOnline] = useState(null);
  const [isMockMode, setIsMockMode] = useState(false);

  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [plan, setPlan] = useState(null);
  const [previewHotels, setPreviewHotels] = useState([]);

  const [activeDay, setActiveDay] = useState(1);
  const [selectedItem, setSelectedItem] = useState(null);
  const [showCheckModal, setShowCheckModal] = useState(false);

  const [loading, setLoading] = useState(false);
  const [latencySec, setLatencySec] = useState(null);
  const [mobileTab, setMobileTab] = useState("chat");
  const [savedPlans, setSavedPlans] = useState(() => loadSavedPlans());
  const [showSavedModal, setShowSavedModal] = useState(false);
  const [saveNotice, setSaveNotice] = useState("");

  useEffect(() => {
    let active = true;
    fetchZones()
      .then((res) => {
        if (!active) return;
        setZonesData(res);
        setApiOnline(true);
      })
      .catch(() => {
        if (!active) return;
        setApiOnline(false);
      });

    fetchHotels()
      .then((res) => {
        if (!active) return;
        if (Array.isArray(res?.hotels)) {
          setPreviewHotels(res.hotels);
        }
      })
      .catch(() => {});

    return () => {
      active = false;
    };
  }, []);

  const hasConversation = messages.length > 0 || Boolean(plan);

  function applyPlanResponse(res, appendMessage = true) {
    setSessionId(res.session_id || sessionId);
    setPlan(res);
    setIsMockMode(false);
    if (appendMessage && res.reply) {
      setMessages((prev) => [...prev, { role: "assistant", content: res.reply }]);
    }
    const days = res.days || [];
    if (days.length > 0) {
      setActiveDay((prev) => (days.some((d) => Number(d.day) === Number(prev)) ? prev : days[0].day));
      setMobileTab("result");
    }
    setSelectedItem(null);
  }

  async function handleSendMessage(text) {
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setLoading(true);
    const t0 = performance.now();
    try {
      const res = await sendChat(isMockMode ? null : sessionId, text);
      setApiOnline(true);
      setLatencySec((performance.now() - t0) / 1000);
      applyPlanResponse(res, true);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `Không kết nối được backend API (${err.message}). Hãy chắc chắn đã chạy \`uvicorn codebase.api:app --port 8000\`, hoặc bấm **Xem mẫu UI** ở góc phải trên để xem trước giao diện.`,
        },
      ]);
      setApiOnline(false);
    } finally {
      setLoading(false);
    }
  }

  async function handleSelectHotel(hotelId) {
    if (isMockMode) {
      setPlan((prev) => (prev ? { ...prev, selected_hotel_id: hotelId } : prev));
      return;
    }
    if (!sessionId) return;
    setLoading(true);
    const t0 = performance.now();
    try {
      const res = await selectHotel(sessionId, hotelId);
      setLatencySec((performance.now() - t0) / 1000);
      applyPlanResponse(res, true);
    } catch (err) {
      setMessages((prev) => [...prev, { role: "assistant", content: `Lỗi chọn khách sạn: ${err.message}` }]);
    } finally {
      setLoading(false);
    }
  }

  async function handleSwapItem(oldId, newId) {
    if (!sessionId || isMockMode) return;
    setLoading(true);
    const t0 = performance.now();
    try {
      const res = await swapItem(sessionId, activeDay, oldId, newId);
      setLatencySec((performance.now() - t0) / 1000);
      applyPlanResponse(res, true);
    } finally {
      setLoading(false);
    }
  }

  async function handleRemoveItem(itemId) {
    if (!sessionId || isMockMode) return;
    setLoading(true);
    const t0 = performance.now();
    try {
      const res = await removeItem(sessionId, activeDay, itemId);
      setLatencySec((performance.now() - t0) / 1000);
      applyPlanResponse(res, true);
    } finally {
      setLoading(false);
    }
  }

  async function handleUndo() {
    if (!sessionId || isMockMode) return;
    setLoading(true);
    const t0 = performance.now();
    try {
      const res = await undoSession(sessionId);
      setLatencySec((performance.now() - t0) / 1000);
      applyPlanResponse(res, true);
    } catch (err) {
      setMessages((prev) => [...prev, { role: "assistant", content: `Không thể hoàn tác: ${err.message}` }]);
    } finally {
      setLoading(false);
    }
  }

  function handleLoadMock() {
    setIsMockMode(true);
    setSessionId(mockPlan.session_id);
    setPlan(mockPlan);
    setActiveDay(1);
    setSelectedItem(null);
    setShowCheckModal(false);
    setLatencySec(0.4);
    setMessages([
      {
        role: "user",
        content: "2 người lớn, 2 bé cao 1m1 và 95cm đi VinWonders và Vinpearl Safari 2 ngày 2026-12-12, ngân sách 10 triệu",
      },
      { role: "assistant", content: mockPlan.reply },
    ]);
    setMobileTab("result");
  }

  function handleReset() {
    setIsMockMode(false);
    setSessionId(null);
    setPlan(null);
    setMessages([]);
    setSelectedItem(null);
    setShowCheckModal(false);
    setLatencySec(null);
    setActiveDay(1);
    setMobileTab("chat");
  }

  function handleSavePlan() {
    if (!plan || !plan.days?.length) return;
    const next = savePlanToStorage(plan);
    setSavedPlans(next);
    setSaveNotice("Đã lưu ✓");
    window.setTimeout(() => setSaveNotice(""), 2000);
  }

  const activeDayObj =
    (plan?.days || []).find((d) => Number(d.day) === Number(activeDay)) || plan?.days?.[0] || null;
  const effectiveHotels = plan?.hotels?.length ? plan.hotels : previewHotels;

  const statusText = isMockMode
    ? "Đang xem dữ liệu mẫu"
    : apiOnline === true
    ? "Đang trực tuyến"
    : apiOnline === false
    ? "Chưa nối backend :8000"
    : "Đang kiểm tra kết nối...";

  return (
    <>
      <header className="jp-header">
        <div className="jp-brand">
          <div className="jp-logo" aria-hidden="true">
            <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
              <path d="M12 21s-6-5.2-6-10a6 6 0 1 1 12 0c0 4.8-6 10-6 10z" />
              <circle cx="12" cy="11" r="2.2" />
            </svg>
          </div>
          <div className="jp-brand-title">
            <span>JOYPLAN</span>
            <span className="jp-brand-slash">/</span>
            <span className="jp-brand-slash">AI</span>
          </div>
        </div>

        <nav className="jp-nav" aria-label="Điều hướng nhanh">
          <button type="button" className="jp-nav-link" onClick={() => setShowSavedModal(true)}>
            Lịch đã lưu ({savedPlans.length})
          </button>
          <button type="button" className="jp-nav-link" onClick={handleReset}>
            Phiên mới
          </button>
          <button type="button" className="jp-nav-link jp-nav-link--brand" onClick={handleLoadMock}>
            Xem mẫu UI
          </button>
        </nav>
      </header>

      <div className="mobile-tabs" role="tablist" aria-label="Chuyển khung hiển thị">
        <button
          type="button"
          role="tab"
          aria-selected={mobileTab === "chat"}
          className={`mobile-tab ${mobileTab === "chat" ? "mobile-tab--active" : ""}`}
          onClick={() => setMobileTab("chat")}
        >
          Trò chuyện
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={mobileTab === "result"}
          className={`mobile-tab ${mobileTab === "result" ? "mobile-tab--active" : ""}`}
          onClick={() => setMobileTab("result")}
        >
          Kết quả ({plan?.days?.length || 0} ngày)
        </button>
      </div>

      <main className={`stage ${hasConversation ? "stage--active" : ""}`}>
        <div className={`stage-col ${mobileTab !== "chat" ? "panel--hidden-mobile" : ""}`}>
          <ChatPanel
            messages={messages}
            hotels={plan?.hotels || []}
            selectedHotelId={plan?.selected_hotel_id || null}
            steps={plan?.steps || []}
            canUndo={Boolean(plan?.can_undo) && !isMockMode}
            loading={loading}
            latencySec={latencySec}
            activeDayItems={activeDayObj?.items || []}
            selectedItemId={selectedItem?.id || null}
            statusText={statusText}
            apiOnline={apiOnline}
            onSendMessage={handleSendMessage}
            onSelectHotel={handleSelectHotel}
            onSelectItem={setSelectedItem}
            onUndo={handleUndo}
            onReset={handleReset}
            onLoadMock={handleLoadMock}
          />
        </div>

        <div className={`stage-col ${mobileTab !== "result" ? "panel--hidden-mobile" : ""}`}>
          <ItineraryPanel
            zonesData={zonesData}
            plan={plan ? { ...plan, hotels: effectiveHotels } : { hotels: effectiveHotels, days: [] }}
            activeDay={activeDay}
            selectedItem={selectedItem}
            showCheckModal={showCheckModal}
            isMockMode={isMockMode}
            loading={loading}
            saveNotice={saveNotice}
            onChangeDay={(d) => {
              setActiveDay(d);
              setSelectedItem(null);
            }}
            onSelectItem={setSelectedItem}
            onOpenCheck={() => setShowCheckModal(true)}
            onCloseCheck={() => setShowCheckModal(false)}
            onSwapItem={handleSwapItem}
            onRemoveItem={handleRemoveItem}
            onSavePlan={handleSavePlan}
            onDownloadPlan={() => plan && downloadPlanJson(plan)}
          />
        </div>
      </main>

      {showSavedModal && (
        <div
          className="modal-backdrop"
          onClick={() => setShowSavedModal(false)}
          role="dialog"
          aria-modal="true"
          aria-label="Lịch trình đã lưu"
        >
          <div className="modal-glass" onClick={(e) => e.stopPropagation()}>
            <div className="modal-head">
              <h2 className="modal-title">Lịch trình đã lưu trên trình duyệt</h2>
              <button type="button" className="modal-close" onClick={() => setShowSavedModal(false)}>
                ×
              </button>
            </div>
            {savedPlans.length === 0 ? (
              <div style={{ fontSize: 13.5, color: "var(--muted)" }}>
                Chưa có lịch trình nào được lưu. Khi có lịch, bấm nút <strong>Lưu lịch</strong> để giữ lại trên trình duyệt.
              </div>
            ) : (
              <div className="alt-list">
                {savedPlans.map((entry) => (
                  <div key={entry.saved_id} className="alt-item">
                    <div>
                      <div style={{ fontSize: 13.5, fontWeight: 600 }}>{entry.label}</div>
                      <div style={{ fontSize: 12, color: "var(--muted)" }}>
                        Lưu lúc {new Date(entry.saved_at).toLocaleString("vi-VN")}
                      </div>
                    </div>
                    <div style={{ display: "flex", gap: 6 }}>
                      <button
                        type="button"
                        className="btn-primary-sm"
                        onClick={() => {
                          setIsMockMode(true);
                          setPlan(entry.plan);
                          setSessionId(entry.plan.session_id || "saved");
                          setActiveDay(entry.plan.days?.[0]?.day || 1);
                          setMessages([{ role: "assistant", content: entry.plan.reply || entry.label }]);
                          setShowSavedModal(false);
                          setMobileTab("result");
                        }}
                      >
                        Mở
                      </button>
                      <button
                        type="button"
                        className="btn-danger-sm"
                        onClick={() => setSavedPlans(deleteSavedPlan(entry.saved_id))}
                      >
                        Xoá
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
}
