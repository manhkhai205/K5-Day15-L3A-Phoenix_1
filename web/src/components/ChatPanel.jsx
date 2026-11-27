import React, { useEffect, useRef, useState } from "react";
import { formatVnd } from "../utils/mapFallbackStyle.js";

const STARTER_PROMPTS = [
  "2 người lớn, 2 bé cao 1m1 và 95cm đi VinWonders và Vinpearl Safari 2 ngày 2026-12-12, ngân sách 10 triệu",
  "Nhà mình 2 người lớn, 1 bé cao 1,1m, ở VinWonders Phú Quốc 9:00–19:30, ngân sách 4 triệu (đã có vé), muốn xem show Nàng tiên cá và show tối",
  "Đang 13:00, trời mưa to, các trò ngoài trời tạm dừng. Nhà mình 2 người lớn, 1 bé 1,1m ở đến 19:30, ngân sách 2 triệu (đã có vé). Xếp lại lịch buổi chiều giúp",
];

const FOLLOWUP_PROMPTS = [
  "Nếu chiều 14:00 trời mưa to thì xếp lại lịch thế nào?",
  "Giảm ngân sách bớt 1 triệu giúp mình",
  "Show Nàng tiên cá suất 14:00 bị hủy thì thay bằng gì?",
];

const PREFERENCE_CHIPS = [
  { id: "vinwonders", label: "VinWonders" },
  { id: "safari", label: "Vinpearl Safari" },
  { id: "grandworld", label: "Grand World" },
  { id: "has_ticket", label: "Đã có vé" },
  { id: "evening_show", label: "Ưu tiên show tối" },
  { id: "avoid_noon_sun", label: "Tránh nắng trưa" },
];

function renderInlineFormatting(line) {
  const tokens = line.split(/(\*\*[^*]+\*\*|`[^`]+`)/g);
  return tokens.map((part, idx) => {
    if (part.startsWith("**") && part.endsWith("**") && part.length > 4) {
      return <strong key={idx}>{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith("`") && part.endsWith("`") && part.length > 2) {
      return (
        <code key={idx} className="msg-code">
          {part.slice(1, -1)}
        </code>
      );
    }
    return <React.Fragment key={idx}>{part}</React.Fragment>;
  });
}

function FormattedText({ text }) {
  const lines = String(text || "").split("\n");
  return (
    <>
      {lines.map((line, idx) => {
        if (!line.trim()) {
          return <div key={idx} style={{ height: 4 }} />;
        }
        return (
          <p key={idx} className="msg-line">
            {renderInlineFormatting(line)}
          </p>
        );
      })}
    </>
  );
}

function buildQuickPrompt({ adults, heightsInput, numDays, startDate, budgetMil, prefs }) {
  const heights = String(heightsInput || "")
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
  const venues = [];
  if (prefs.includes("vinwonders")) venues.push("VinWonders Phú Quốc");
  if (prefs.includes("safari")) venues.push("Vinpearl Safari");
  if (prefs.includes("grandworld")) venues.push("Grand World");
  if (venues.length === 0) venues.push("VinWonders Phú Quốc");

  return [
    `${adults} người lớn`,
    heights.length > 0 ? `${heights.length} bé cao ${heights.map((h) => `${h}cm`).join(" và ")}` : "không có trẻ nhỏ",
    `đi ${venues.join(", ")} ${numDays} ngày`,
    startDate ? `từ ${startDate}` : "",
    `ngân sách ${budgetMil} triệu${prefs.includes("has_ticket") ? " (đã có vé)" : ""}`,
    prefs.includes("evening_show") ? "ưu tiên xem show tối" : "",
    prefs.includes("avoid_noon_sun") ? "tránh nắng gắt 11:00–15:00" : "",
  ]
    .filter(Boolean)
    .join(", ");
}

export default function ChatPanel({
  messages,
  hotels,
  selectedHotelId,
  steps,
  canUndo,
  loading,
  latencySec,
  activeDayItems,
  selectedItemId,
  statusText,
  apiOnline,
  onSendMessage,
  onSelectHotel,
  onSelectItem,
  onUndo,
  onReset,
  onLoadMock,
}) {
  const [input, setInput] = useState("");
  const [showSteps, setShowSteps] = useState(false);
  const [showQuick, setShowQuick] = useState(false);

  const [adults, setAdults] = useState(2);
  const [heightsInput, setHeightsInput] = useState("110, 95");
  const [numDays, setNumDays] = useState(2);
  const [budgetMil, setBudgetMil] = useState(10);
  const [startDate, setStartDate] = useState("2026-12-12");
  const [prefs, setPrefs] = useState(["vinwonders", "safari", "evening_show"]);
  const [quickTouched, setQuickTouched] = useState(false);

  const scrollRef = useRef(null);
  const textareaRef = useRef(null);

  const isWelcome = messages.length === 0;
  const hasPlan = Array.isArray(activeDayItems) && activeDayItems.length > 0;
  const activeFilterCount = quickTouched ? prefs.length + (heightsInput.trim() ? 1 : 0) : 0;

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, hotels, loading, steps]);

  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 110)}px`;
  }, [input]);

  function applyLiveQuick(nextState) {
    setQuickTouched(true);
    setInput(buildQuickPrompt(nextState));
  }

  function handleResetQuick() {
    setAdults(2);
    setHeightsInput("110, 95");
    setNumDays(2);
    setBudgetMil(10);
    setStartDate("2026-12-12");
    setPrefs(["vinwonders", "safari", "evening_show"]);
    setQuickTouched(false);
    setInput("");
  }

  function submitCurrentInput() {
    const trimmed = input.trim();
    if (!trimmed || loading) return;
    setInput("");
    setShowQuick(false);
    setQuickTouched(false);
    onSendMessage(trimmed);
  }

  function handleFormSubmit(e) {
    e.preventDefault();
    submitCurrentInput();
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submitCurrentInput();
    }
  }

  function togglePref(id) {
    const nextPrefs = prefs.includes(id) ? prefs.filter((p) => p !== id) : [...prefs, id];
    setPrefs(nextPrefs);
    applyLiveQuick({ adults, heightsInput, numDays, startDate, budgetMil, prefs: nextPrefs });
  }

  const quickDrawerNode = showQuick ? (
    <div className="quick-drawer" aria-label="Bộ lọc tìm nhanh">
      <div className="quick-head">
        <div style={{ display: "flex", alignItems: "center", gap: 7 }}>
          <span className="quick-badge-icon">≡</span>
          <span className="lbl" style={{ letterSpacing: "0.1em" }}>
            Bộ lọc nhanh
          </span>
          {activeFilterCount > 0 && <span className="count-badge">{activeFilterCount}</span>}
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          {quickTouched && (
            <button type="button" className="ghost-tool-btn" onClick={handleResetQuick}>
              Đặt lại
            </button>
          )}
          <button
            type="button"
            className="ghost-tool-btn"
            style={{ padding: "0 6px" }}
            onClick={() => setShowQuick(false)}
            aria-label="Đóng bộ lọc"
          >
            ×
          </button>
        </div>
      </div>

      <div className="quick-grid">
        <label className="quick-field">
          Số người lớn
          <input
            type="number"
            min={1}
            max={12}
            value={adults}
            onChange={(e) => {
              const v = Math.max(1, Number(e.target.value) || 1);
              setAdults(v);
              applyLiveQuick({ adults: v, heightsInput, numDays, startDate, budgetMil, prefs });
            }}
          />
        </label>
        <label className="quick-field">
          Chiều cao các bé (cm)
          <input
            type="text"
            value={heightsInput}
            placeholder="vd: 110, 95"
            onChange={(e) => {
              const v = e.target.value;
              setHeightsInput(v);
              applyLiveQuick({ adults, heightsInput: v, numDays, startDate, budgetMil, prefs });
            }}
          />
        </label>
        <label className="quick-field">
          Số ngày &amp; ngày đi
          <div style={{ display: "flex", gap: 6 }}>
            <select
              value={numDays}
              onChange={(e) => {
                const v = Number(e.target.value);
                setNumDays(v);
                applyLiveQuick({ adults, heightsInput, numDays: v, startDate, budgetMil, prefs });
              }}
            >
              <option value={1}>1 ngày</option>
              <option value={2}>2 ngày</option>
              <option value={3}>3 ngày</option>
            </select>
            <input
              type="date"
              value={startDate}
              style={{ flex: 1, minWidth: 0 }}
              onChange={(e) => {
                const v = e.target.value;
                setStartDate(v);
                applyLiveQuick({ adults, heightsInput, numDays, startDate: v, budgetMil, prefs });
              }}
            />
          </div>
        </label>
        <label className="quick-field">
          Ngân sách (triệu VND)
          <input
            type="number"
            min={0.5}
            step={0.5}
            value={budgetMil}
            onChange={(e) => {
              const v = Number(e.target.value) || 1;
              setBudgetMil(v);
              applyLiveQuick({ adults, heightsInput, numDays, startDate, budgetMil: v, prefs });
            }}
          />
        </label>
      </div>

      <div className="chip-row">
        {PREFERENCE_CHIPS.map((c) => {
          const on = prefs.includes(c.id);
          return (
            <button
              key={c.id}
              type="button"
              className={`filter-chip ${on ? "filter-chip--on" : ""}`}
              onClick={() => togglePref(c.id)}
            >
              {c.label}
            </button>
          );
        })}
      </div>

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 8 }}>
        <span style={{ fontSize: 11.5, color: "var(--subtle)" }}>
          Câu lệnh tự điền vào ô chat để bạn chỉnh hoặc gửi
        </span>
        <button
          type="button"
          className="btn-primary-sm"
          style={{ flex: "0 0 auto" }}
          onClick={() => {
            const promptText = input.trim() || buildQuickPrompt({ adults, heightsInput, numDays, startDate, budgetMil, prefs });
            setInput("");
            setShowQuick(false);
            setQuickTouched(false);
            onSendMessage(promptText);
          }}
        >
          Gửi ngay →
        </button>
      </div>
    </div>
  ) : null;

  const composerForm = (
    <form className={`gm-input-shell ${loading ? "gm-input-shell--streaming" : ""}`} onSubmit={handleFormSubmit}>
      <div className="gm-input">
        <textarea
          ref={textareaRef}
          rows={1}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ví dụ: 2 người lớn, 1 bé cao 1m1 đi VinWonders từ 9:00–19:30, ngân sách 4 triệu..."
          disabled={loading}
          aria-label="Nhập yêu cầu lịch trình"
        />
        <div className="send-wrap">
          {loading && <span className="send-ring" aria-hidden="true" />}
          <button
            type="submit"
            className={`send-btn ${loading ? "send-btn--busy" : ""}`}
            disabled={loading || !input.trim()}
            aria-label={loading ? "Đang xử lý" : "Gửi yêu cầu"}
          >
            {loading ? "■" : "↑"}
          </button>
        </div>
      </div>
    </form>
  );

  const toolbarRow = (
    <div className="composer-toolbar">
      <button
        type="button"
        className={`ghost-tool-btn ${showQuick ? "ghost-tool-btn--active" : ""}`}
        onClick={() => setShowQuick((v) => !v)}
        disabled={loading}
      >
        <span>≡ Tìm nhanh</span>
        {activeFilterCount > 0 && <span className="count-badge">{activeFilterCount}</span>}
        <span>{showQuick ? "▴" : "▾"}</span>
      </button>
      {quickTouched && (
        <button type="button" className="ghost-tool-btn" onClick={handleResetQuick} disabled={loading}>
          Xoá lọc
        </button>
      )}
      {isWelcome && (
        <button type="button" className="ghost-tool-btn" onClick={onLoadMock} disabled={loading}>
          Xem mẫu UI ↗
        </button>
      )}
      {!isWelcome && canUndo && (
        <button type="button" className="ghost-tool-btn" onClick={onUndo} disabled={loading}>
          ↶ Hoàn tác
        </button>
      )}
    </div>
  );

  return (
    <section className="panel chat-panel" aria-label="Trò chuyện lập lịch trình">
      <div className="chat-head">
        <div>
          <div className="chat-head-title">Trợ lý lịch trình</div>
          <div className="chat-head-status">
            <span className={`jp-dot ${apiOnline === false ? "jp-dot--warn" : ""}`} />
            <span>{statusText}</span>
          </div>
        </div>
        <div className="chat-head-actions">
          {canUndo && (
            <button
              type="button"
              className="icon-circle-btn"
              onClick={onUndo}
              disabled={loading}
              title="Hoàn tác thao tác gần nhất"
              aria-label="Hoàn tác"
            >
              ↶
            </button>
          )}
          <button
            type="button"
            className="icon-circle-btn"
            onClick={onReset}
            disabled={loading}
            title="Phiên trò chuyện mới"
            aria-label="Phiên mới"
          >
            ✎
          </button>
        </div>
      </div>

      {isWelcome ? (
        <div className="welcome-hero">
          <h1 className="welcome-title">Gia đình bạn định đi đâu, trong mấy ngày?</h1>
          <p className="welcome-desc">
            Nhập số người, chiều cao từng bé, khung giờ và ngân sách. Hệ thống tra dữ liệu thật và tự kiểm cứng 5 điều kiện đạt 0 vi phạm.
          </p>

          <div className="welcome-composer">
            {composerForm}
            {toolbarRow}
            {quickDrawerNode}
          </div>

          <div className="starter-wrap">
            <div className="lbl">Gợi ý để bắt đầu</div>
            <div className="starter-list">
              {STARTER_PROMPTS.map((text) => (
                <button
                  key={text}
                  type="button"
                  className="starter-row"
                  onClick={() => onSendMessage(text)}
                  disabled={loading}
                >
                  <span className="starter-arrow">→</span>
                  <span>{text}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      ) : (
        <>
          <div className="chat-scroll" ref={scrollRef}>
            <div className="msg-list">
              {messages.map((m, idx) => {
                const isLastBot = m.role === "assistant" && idx === messages.length - 1;
                return (
                  <React.Fragment key={idx}>
                    <div className={`msg ${m.role === "user" ? "msg-user" : "msg-bot"}`}>
                      <FormattedText text={m.content} />
                      {isLastBot && hasPlan && (
                        <div className="inline-items-list">
                          {activeDayItems.slice(0, 5).map((it, iIdx) => {
                            const active = it.id === selectedItemId;
                            return (
                              <button
                                key={`${it.id}-${iIdx}`}
                                type="button"
                                className={`inline-item-row ${active ? "inline-item-row--active" : ""}`}
                                onClick={() => onSelectItem(it)}
                              >
                                <span className="inline-idx">{String(iIdx + 1).padStart(2, "0")}</span>
                                <span className="inline-name">{it.name}</span>
                                <span className="inline-time">
                                  {it.start}–{it.end}
                                </span>
                              </button>
                            );
                          })}
                        </div>
                      )}
                    </div>
                  </React.Fragment>
                );
              })}
            </div>

            {hotels.length > 0 && (
              <div className="hotel-section" aria-label="Khách sạn tham khảo gần cổng">
                <div className="hotel-header">
                  <span>Khách sạn gợi ý làm điểm xuất phát</span>
                  <span className="hotel-sim-tag">Số phòng: dữ liệu mô phỏng</span>
                </div>
                {hotels.map((h) => {
                  const isSelected = h.id === selectedHotelId;
                  const priceLabel =
                    h.price_ref_vnd != null && Number(h.price_ref_vnd) > 0
                      ? `${formatVnd(h.price_ref_vnd)}/đêm`
                      : "Xem giá tại trang đặt phòng";
                  const locationLabel =
                    typeof h.distance_to_gate_m === "number"
                      ? `Cách cổng ${h.distance_to_gate_m}m`
                      : h.address || h.location_note || "";
                  const extraNote = h.family_room_note || h.price_note || "";
                  return (
                    <div key={h.id} className={`hotel-card ${isSelected ? "hotel-card--selected" : ""}`}>
                      <div className="hotel-top">
                        <span className="hotel-name">{h.name}</span>
                        {h.fit_score != null && <span className="hotel-fit">Phù hợp {h.fit_score}%</span>}
                      </div>
                      <div className="hotel-meta">
                        <span>{priceLabel}</span>
                        {locationLabel && <span>• {locationLabel}</span>}
                        {h.rooms_left != null && (
                          <span>
                            • Còn {h.rooms_left} phòng <em>(mô phỏng)</em>
                          </span>
                        )}
                      </div>
                      {extraNote && (
                        <div style={{ fontSize: 12, color: "var(--subtle)", lineHeight: 1.4 }}>{extraNote}</div>
                      )}
                      <div className="hotel-actions">
                        <button
                          type="button"
                          className="btn-primary-sm"
                          onClick={() => onSelectHotel(h.id)}
                          disabled={loading}
                        >
                          {isSelected ? "Đang chọn · Lập lại" : "Chọn & lập lịch từ đây"}
                        </button>
                        {h.booking_url && (
                          <a
                            className="btn-outline-sm"
                            href={h.booking_url}
                            target="_blank"
                            rel="noopener noreferrer"
                          >
                            Đặt phòng ↗
                          </a>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            {loading && (
              <div className="steps-live-card" aria-live="polite">
                <div className="steps-live-banner">
                  <span>JoyPlan Core · 5 bước</span>
                  <span style={{ fontSize: 11, color: "var(--muted)" }}>0 vi phạm</span>
                </div>
                <div className="steps-list">
                  {[
                    "Kiểm tra an toàn đầu vào",
                    "Trích ràng buộc gia đình (G10)",
                    "Tra dữ liệu & kiểm kiem_lich_trinh",
                    "Tổng hợp lịch & chi phí",
                  ].map((label, idx) => (
                    <div key={label} className="step-row" style={{ opacity: idx > 2 ? 0.45 : 1 }}>
                      {idx === 2 ? (
                        <span className="live-spinner" />
                      ) : (
                        <span className={`step-badge ${idx > 2 ? "step-badge--pending" : ""}`}>{idx + 1}</span>
                      )}
                      <span className={idx === 2 ? "gm-shimmer-text" : ""} style={{ color: idx === 2 ? undefined : "var(--ink)" }}>
                        {label}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {!loading && steps.length > 0 && (
              <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                <button
                  type="button"
                  className="steps-pill"
                  onClick={() => setShowSteps((v) => !v)}
                  aria-expanded={showSteps}
                >
                  <span style={{ display: "inline-block", transform: showSteps ? "rotate(90deg)" : "none", transition: "transform 150ms ease" }}>
                    ›
                  </span>
                  <span>
                    Quá trình xử lý · {steps.length} bước
                    {latencySec != null ? ` · ${latencySec.toFixed(1)} s` : ""}
                  </span>
                </button>
                {showSteps && (
                  <div className="steps-card">
                    <div className="steps-list">
                      {steps.map((s, sIdx) => {
                        const cls =
                          s.status === "warn"
                            ? "step-badge--warn"
                            : s.status === "blocked"
                            ? "step-badge--blocked"
                            : "";
                        const pct = sIdx === 2 || sIdx === 3 ? 82 : 42;
                        return (
                          <div key={s.step} className="step-row" style={{ justifyContent: "space-between" }}>
                            <div style={{ display: "flex", alignItems: "center", gap: 8, minWidth: 0 }}>
                              <span className={`step-badge ${cls}`}>{s.step}</span>
                              <span
                                style={{
                                  color: "var(--ink)",
                                  overflow: "hidden",
                                  textOverflow: "ellipsis",
                                  whiteSpace: "nowrap",
                                }}
                                title={s.detail}
                              >
                                {s.name}
                              </span>
                            </div>
                            <div className="step-bar-track">
                              <div className="step-bar-fill" style={{ width: `${pct}%` }} />
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            )}

            {!loading && hasPlan && (
              <div className="followup-row" aria-label="Gợi ý chỉnh sửa nhanh">
                {FOLLOWUP_PROMPTS.map((q) => (
                  <button
                    key={q}
                    type="button"
                    className="followup-chip"
                    onClick={() => onSendMessage(q)}
                  >
                    {q}
                  </button>
                ))}
              </div>
            )}
          </div>

          <div className="chat-footer">
            {quickDrawerNode}
            {toolbarRow}
            {composerForm}
          </div>
        </>
      )}
    </section>
  );
}
