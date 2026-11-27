import React from "react";

const CONDITION_LABELS = [
  { key: "gio_mo_cua", label: "Giờ mở cửa phân khu & chuyến cuối (Safari 15:20 · Z5/Z6 18:00)" },
  { key: "chong_gio", label: "Không chồng giờ & đủ thời gian đi bộ / xe VinBus" },
  { key: "ngan_sach", label: "Tổng chi phí vé, ăn uống & phụ phí trong ngân sách" },
  { key: "chieu_cao", label: "Giới hạn chiều cao an toàn cho từng bé" },
  { key: "mua", label: "Tránh trò / show ngoài trời trong khung giờ mưa" },
];

export default function CheckModal({ dayNum, check, onClose }) {
  if (!check) return null;
  const conditions = check.dieu_kien || {};
  const violations = check.vi_pham || [];
  const warnings = check.canh_bao || [];

  return (
    <div className="modal-backdrop" onClick={onClose} role="dialog" aria-modal="true" aria-label="Bảng kiểm 5 điều kiện">
      <div className="modal-glass" onClick={(e) => e.stopPropagation()}>
        <div className="modal-head">
          <div>
            <h2 className="modal-title">Tự kiểm cứng Ngày {dayNum} · kiem_lich_trinh</h2>
            <div style={{ fontSize: 13, color: "var(--muted)", marginTop: 4 }}>
              {check.hop_le
                ? "Đạt 0 vi phạm cứng trên cả 5 điều kiện."
                : `Phát hiện ${check.so_vi_pham} vi phạm cần xử lý.`}
            </div>
          </div>
          <button type="button" className="modal-close" onClick={onClose} aria-label="Đóng">
            ×
          </button>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {CONDITION_LABELS.map((c) => {
            const ok = conditions[c.key] !== false;
            return (
              <div key={c.key} className="check-row">
                <span>{c.label}</span>
                <span className={`height-tag ${ok ? "height-tag--ok" : "height-tag--no"}`}>
                  {ok ? "Đạt ✓" : "Vi phạm ✗"}
                </span>
              </div>
            );
          })}
        </div>

        {violations.length > 0 && (
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: "var(--danger)" }}>Vi phạm chi tiết</div>
            {violations.map((v, i) => (
              <div key={i} className="alert-error">
                {v.message}
              </div>
            ))}
          </div>
        )}

        {warnings.length > 0 && (
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: "var(--warn)" }}>
              Lưu ý cho gia đình ({warnings.length})
            </div>
            {warnings.map((w, i) => (
              <div
                key={i}
                style={{
                  padding: "8px 11px",
                  borderRadius: 12,
                  background: "#fff6ef",
                  border: "1px solid #f5d2b8",
                  fontSize: 12.5,
                  color: "var(--ink)",
                }}
              >
                {w.message}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
