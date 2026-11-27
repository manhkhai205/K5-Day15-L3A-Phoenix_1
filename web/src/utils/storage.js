const STORAGE_KEY = "joyplan_saved_plans_v1";

export function loadSavedPlans() {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export function savePlanToStorage(plan, label) {
  const list = loadSavedPlans();
  const days = plan?.days || [];
  const firstDate = days[0]?.date || new Date().toISOString().slice(0, 10);
  const entry = {
    saved_id: "save_" + Date.now(),
    saved_at: new Date().toISOString(),
    label: label || `Lịch ${days.length} ngày (${firstDate})`,
    plan,
  };
  const next = [entry, ...list].slice(0, 12);
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
  return next;
}

export function deleteSavedPlan(savedId) {
  const next = loadSavedPlans().filter((x) => x.saved_id !== savedId);
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
  return next;
}

export function downloadPlanJson(plan) {
  const payload = JSON.stringify(plan, null, 2);
  const blob = new Blob([payload], { type: "application/json;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `joyplan-${plan?.session_id || "itinerary"}.json`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
