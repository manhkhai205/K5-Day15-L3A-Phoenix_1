"""Sinh file demo-slides.pdf (8 trang 16:9) từ slides/slides.html.

Cách dùng:
  python slides/build_slides.py
      Xuất demo-slides.pdf ở thư mục gốc repo từ slides/slides.html hiện tại.

  python slides/build_slides.py --sync-docs
      (Chạy sau khi đã hoàn thành eval/run-2.csv và cost/simulate-1-summary.md trên máy có .env):
      Đọc số đo thật từ run-2.csv (dùng eval/run_eval.py grade()) và simulate-N-summary.md,
      cập nhật tự động vào spec.md (§7, §8), eval/README.md (mục 5), eval/report.md (mục 1, 3),
      cost/cost-estimate.md (mục 1, 2, 3) và slides/slides.html, rồi xuất lại demo-slides.pdf.
"""
import argparse
import html
import os
import re
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SLIDES_HTML = os.path.join(ROOT, "slides", "slides.html")
OUTPUT_PDF = os.path.join(ROOT, "demo-slides.pdf")


def find_browser() -> str:
    """Tìm Edge hoặc Chrome đã cài trên Windows/Linux/macOS để in PDF headless."""
    candidates = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    for cmd in ("msedge", "google-chrome", "chromium", "chrome"):
        found = shutil.which(cmd)
        if found:
            return found
    raise FileNotFoundError("Không tìm thấy Microsoft Edge hoặc Google Chrome để xuất PDF.")


def _replace_block(text: str, tag: str, new_inner: str) -> str:
    pattern = re.compile(
        r"(<!--SYNC:%s-->)(.*?)(<!--/SYNC:%s-->)" % (re.escape(tag), re.escape(tag)),
        re.DOTALL,
    )
    if not pattern.search(text):
        return text
    return pattern.sub(lambda m: m.group(1) + "\n          " + new_inner.strip() + "\n          " + m.group(3), text, count=1)


def _latest_simulate_summary() -> tuple[str | None, str | None]:
    cost_dir = os.path.join(ROOT, "cost")
    nums = []
    for fname in os.listdir(cost_dir):
        m = re.fullmatch(r"simulate-(\d+)-summary\.md", fname)
        if m:
            nums.append((int(m.group(1)), os.path.join(cost_dir, fname)))
    if not nums:
        return None, None
    n, path = max(nums)
    return f"simulate-{n}", path


def _parse_simulate_summary(md_text: str) -> dict:
    m_rid = re.search(r"#\s*Tóm tắt mô phỏng\s+(\S+)", md_text)
    run_id = m_rid.group(1) if m_rid else ""
    m_rate = re.search(r"Tỉ lệ đạt dùng để tính:\s*(.+)", md_text)
    rate_line = m_rate.group(1).strip() if m_rate else ""

    cost_rows = []
    in_cost_tbl = False
    for line in md_text.splitlines():
        if line.startswith("| Model (giá) |"):
            in_cost_tbl = True
            continue
        if in_cost_tbl:
            if not line.startswith("|"):
                if cost_rows:
                    break
                continue
            if set(line.replace("|", "").replace("-", "").replace(":", "").strip()) == set():
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) >= 8:
                cost_rows.append(
                    {
                        "label": cells[0],
                        "per_session": cells[1],
                        "per_task": cells[2],
                        "per_q": cells[3],
                        "low": cells[4],
                        "base": cells[5],
                        "high": cells[6],
                        "per_user": cells[7],
                    }
                )
    return {"run_id": run_id, "rate_line": rate_line, "rows": cost_rows}


def sync_docs_and_slides() -> None:
    """Đọc eval/run-2.csv và cost/simulate-N-summary.md rồi đồng bộ vào các file tài liệu & HTML slide."""
    sys.path.insert(0, os.path.join(ROOT, "eval"))
    import run_eval as ev  # noqa: E402

    run2_path = os.path.join(ROOT, "eval", "run-2.csv")
    run2_info = None
    if os.path.exists(run2_path):
        g = ev.grade(run2_path)
        if isinstance(g, dict):
            pct = round(100 * g["passed"] / g["total"])
            bt = g["by_type"]
            t_str = "%d/%d" % bt.get("thuong", (0, 0))
            k_str = "%d/%d" % bt.get("kho", (0, 0))
            tc_str = "%d/%d" % bt.get("tu_choi", (0, 0))
            run2_info = {
                "run_id": g["run_id"],
                "model": g["model"] or "gemini-3.5-flash-lite",
                "passed": g["passed"],
                "total": g["total"],
                "pct": pct,
                "thuong": t_str,
                "kho": k_str,
                "tu_choi": tc_str,
                "pass_verdict": "Đạt" if pct >= 80 and bt.get("tu_choi", (0, 1))[0] == bt.get("tu_choi", (0, 1))[1] else "Chưa đạt",
            }
        else:
            print("⚠️ Chưa đọc được eval/run-2.csv (%s) — bỏ qua đồng bộ Lượt 2." % g)

    sim_stem, sim_summary_path = _latest_simulate_summary()
    sim_info = None
    if sim_summary_path:
        with open(sim_summary_path, encoding="utf-8") as f:
            sim_info = _parse_simulate_summary(f.read())
        sim_info["stem"] = sim_stem

    # 1. Cập nhật eval/report.md
    if run2_info:
        rep_path = os.path.join(ROOT, "eval", "report.md")
        with open(rep_path, encoding="utf-8") as f:
            rep = f.read()
        rep = re.sub(
            r"\| 2 \|[^\n]*",
            f"| 2 | `{run2_info['run_id']}` | {run2_info['passed']}/{run2_info['total']} | {run2_info['pct']}% | {run2_info['thuong']} | {run2_info['kho']} | {run2_info['tu_choi']} | **{run2_info['pass_verdict']}** |",
            rep,
            count=1,
        )
        rep = re.sub(
            r"tổng `88%` → `[^`]+`.*",
            f"tổng `88%` → `{run2_info['pct']}%` (`{run2_info['passed']}/{run2_info['total']}`, run ID `{run2_info['run_id']}`).",
            rep,
        )
        with open(rep_path, "w", encoding="utf-8") as f:
            f.write(rep)

        # 2. Cập nhật eval/README.md
        er_path = os.path.join(ROOT, "eval", "README.md")
        with open(er_path, encoding="utf-8") as f:
            er = f.read()
        er = re.sub(
            r"\| 2 \|[^\n]*",
            f"| 2 | `{run2_info['run_id']}` | `{run2_info['model']}` | Sau 1 lần cải tiến Nhóm lỗi 1 (`B06`, `B16`): mở rộng `_extract_time_window`, `_extract_rain_query` & cảnh báo show ngoài trời | {run2_info['passed']}/{run2_info['total']} | {run2_info['pct']}% (thuong {run2_info['thuong']} · kho {run2_info['kho']} · tu_choi {run2_info['tu_choi']}) | **{run2_info['pass_verdict']}** |",
            er,
            count=1,
        )
        with open(er_path, "w", encoding="utf-8") as f:
            f.write(er)

    # 3. Cập nhật cost/cost-estimate.md & spec.md
    spec_path = os.path.join(ROOT, "spec.md")
    with open(spec_path, encoding="utf-8") as f:
        spec_txt = f.read()

    if run2_info:
        spec_txt = spec_txt.replace("lượt 2 `__/__ (__%)`", f"lượt 2 `{run2_info['passed']}/{run2_info['total']} ({run2_info['pct']}%)`")
        spec_txt = spec_txt.replace("(model `gemini-3.5-flash-lite`) / `__`", f"(model `gemini-3.5-flash-lite`) / `{run2_info['run_id']}` (model `{run2_info['model']}`)")

    if sim_info and sim_info["rows"]:
        ce_path = os.path.join(ROOT, "cost", "cost-estimate.md")
        with open(ce_path, encoding="utf-8") as f:
            ce = f.read()
        r0 = sim_info["rows"][0]
        r_mid = sim_info["rows"][1] if len(sim_info["rows"]) > 2 else None
        r_high = sim_info["rows"][-1] if len(sim_info["rows"]) > 1 else r0
        m0 = r0["label"].split(" ", 1)[0]
        m_mid = r_mid["label"].split(" ", 1)[0] if r_mid else ""
        m_high = r_high["label"].split(" ", 1)[0]
        ce = re.sub(
            r"Lượt mô phỏng:.*",
            "Lượt mô phỏng: `cost/%s.csv` · run ID `%s` · `50` phiên · `seed 42` · tỉ lệ đạt: %s"
            % (sim_info["stem"], sim_info["run_id"], sim_info["rate_line"]),
            ce,
        )
        tbl_rows = "\n".join(
            "| %s | %s | %s | %s | %s | %s | %s | %s |"
            % (row["label"], row["per_session"], row["per_task"], row["per_q"], row["low"], row["base"], row["high"], row["per_user"])
            for row in sim_info["rows"]
        )
        ce = re.sub(
            r"(\| Model \(giá\) \|[^\n]+\n\|[-:| ]+\n)(?:\|.*\n)+",
            lambda m: m.group(1) + tbl_rows + "\n",
            ce,
        )
        ce = re.sub(
            r"- \*\*Chi phí / người / tháng \(cơ sở, model `[^`]+`\):\*\*.*",
            "- **Chi phí / người / tháng (cơ sở, model `%s`):** %s (%s / task thành công)"
            % (m0, r0["per_user"], r0["per_task"]),
            ce,
        )
        ce = re.sub(
            r"- \*\*Kết luận một dòng — đáng làm không:\*\*.*",
            "- **Kết luận một dòng — đáng làm không:** **Rất đáng làm** — chi phí %s/gia đình/tháng nhỏ hơn rất nhiều so với giá trị ~75 phút tiết kiệm và chi tiêu 3,5–5 triệu đ/ngày."
            % r0["per_user"],
            ce,
        )
        if run2_info:
            ce = ce.replace("Lượt 2 (`run-2`): **`__/__ (__%)`**", "Lượt 2 (`run-2`): **`%d/%d (%d%%)`**" % (run2_info["passed"], run2_info["total"], run2_info["pct"]))
        with open(ce_path, "w", encoding="utf-8") as f:
            f.write(ce)

        spec_txt = re.sub(
            r"- Persona \+ giá:.*",
            "- Persona + giá: `cost/personas.yaml` (`3` persona, bình quân `2,4` phiên/gia đình/tháng) · lượt mô phỏng: `cost/%s.csv` (`50` phiên, `seed 42`, run ID `%s`)"
            % (sim_info["stem"], sim_info["run_id"]),
            spec_txt,
        )
        task_parts = [f"{r0['per_task']} (`{m0}`)"]
        if r_mid:
            task_parts.append(f"{r_mid['per_task']} (`{m_mid}`)")
        if r_high is not r0:
            task_parts.append(f"{r_high['per_task']} (`{m_high}`)")
        spec_txt = re.sub(
            r"- Chi phí / task thành công:.*",
            "- Chi phí / task thành công: " + " · ".join(task_parts),
            spec_txt,
        )
        spec_txt = re.sub(
            r"- Chi phí / tháng ở quy mô thật:.*",
            "- Chi phí / tháng ở quy mô thật (`%s`): thấp `1.425` gđ %s · cơ sở `4.275` gđ %s (%s/người/tháng) · cao `14.250` gđ %s → chi tiết `cost/cost-estimate.md`"
            % (m0, r0["low"], r0["base"], r0["per_user"], r0["high"]),
            spec_txt,
        )
        spec_txt = re.sub(
            r"- So với impact / người / tháng \(§2\): đáng làm không, vì sao:.*",
            "- So với impact / người / tháng (§2): đáng làm không, vì sao: **Rất đáng làm** — chỉ tốn %s/người/tháng để tiết kiệm ~75 phút ghép lịch/chuyến và hạn chế vỡ ngân sách 3,5–5 triệu đ/ngày."
            % r0["per_user"],
            spec_txt,
        )

    with open(spec_path, "w", encoding="utf-8") as f:
        f.write(spec_txt)

    # 4. Cập nhật slides/slides.html
    with open(SLIDES_HTML, encoding="utf-8") as f:
        html_txt = f.read()

    if run2_info:
        kpi_html = (
            '<span class="kpi-val kpi-val--go">%d/%d (%d%%)</span>\n'
            '          <span class="kpi-note"><code>%s</code> (%s · thuong %s · kho %s · tu_choi %s)</span>'
            % (
                run2_info["passed"], run2_info["total"], run2_info["pct"],
                html.escape(run2_info["run_id"]), html.escape(run2_info["pass_verdict"]),
                html.escape(run2_info["thuong"]), html.escape(run2_info["kho"]), html.escape(run2_info["tu_choi"]),
            )
        )
        html_txt = _replace_block(html_txt, "SLIDE5_RUN2_KPI", kpi_html)
        html_txt = _replace_block(
            html_txt,
            "SLIDE7_EVAL_KPI",
            '<div class="kpi-val kpi-val--go" style="font-size: 28px;">%d/%d (%d%%)</div>'
            % (run2_info["passed"], run2_info["total"], run2_info["pct"]),
        )

    if sim_info and sim_info["rows"]:
        html_txt = _replace_block(
            html_txt,
            "SLIDE6_RATE_TAG",
            '<span class="pill pill--go">%s · %s</span>'
            % (html.escape(sim_info["run_id"]), html.escape(sim_info["rate_line"])),
        )
        rows_html = []
        for idx, r in enumerate(sim_info["rows"]):
            cls = ' class="row-hi"' if idx == 0 else ""
            rows_html.append(
                f"<tr{cls}>"
                f"<td><code>{html.escape(r['label'])}</code></td>"
                f'<td class="num-cell">{html.escape(r["per_session"])}</td>'
                f'<td class="num-cell">{html.escape(r["per_task"])}</td>'
                f'<td class="num-cell">{html.escape(r["low"])}</td>'
                f'<td class="num-cell">{html.escape(r["base"])}</td>'
                f'<td class="num-cell">{html.escape(r["high"])}</td>'
                f'<td class="num-cell"><strong>{html.escape(r["per_user"])}</strong></td>'
                "</tr>"
            )
        tbl_html = (
            '<table class="tbl">\n'
            '          <thead>\n'
            '            <tr>\n'
            '              <th>Model (Paid Standard · $/1M tok)</th>\n'
            '              <th class="num-cell">/ phiên</th>\n'
            '              <th class="num-cell">/ task thành công</th>\n'
            '              <th class="num-cell">/ tháng — Thấp</th>\n'
            '              <th class="num-cell">/ tháng — Cơ sở</th>\n'
            '              <th class="num-cell">/ tháng — Cao</th>\n'
            '              <th class="num-cell">/ người / tháng</th>\n'
            '            </tr>\n'
            '          </thead>\n'
            '          <tbody>\n'
            + "\n".join("            " + ln for ln in rows_html)
            + "\n          </tbody>\n        </table>"
        )
        html_txt = _replace_block(html_txt, "SLIDE6_COST_TABLE", tbl_html)

    with open(SLIDES_HTML, "w", encoding="utf-8") as f:
        f.write(html_txt)
    print("Đã đồng bộ số liệu thật vào tài liệu & slides/slides.html.")


def export_pdf() -> None:
    browser = find_browser()
    file_url = "file:///" + SLIDES_HTML.replace("\\", "/")
    cmd = [
        browser,
        "--headless",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={OUTPUT_PDF}",
        file_url,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0 or not os.path.exists(OUTPUT_PDF):
        raise RuntimeError(f"Xuất PDF thất bại (code {proc.returncode}): {proc.stderr or proc.stdout}")
    print(f"Đã xuất {OUTPUT_PDF} thành công qua {os.path.basename(browser)}.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Xuất demo-slides.pdf từ slides/slides.html")
    parser.add_argument("--sync-docs", action="store_true", help="Đồng bộ số liệu từ run-2.csv và simulate-N-summary.md trước khi xuất PDF")
    args = parser.parse_args()
    if args.sync_docs:
        sync_docs_and_slides()
    export_pdf()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
