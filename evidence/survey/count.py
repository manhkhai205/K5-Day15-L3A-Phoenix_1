"""Đếm kết quả khảo sát từ evidence/survey/results.csv — chạy: python evidence/survey/count.py"""
import csv, collections, pathlib
import sys
sys.stdout.reconfigure(encoding="utf-8")
rows = list(csv.DictReader(open(pathlib.Path(__file__).with_name("results.csv"), encoding="utf-8")))
ok = [r for r in rows if r["q1_di_cung_tre_12_thang"] == "Có"]
clean = [r for r in ok if not r["canh_bao"]]
print("Tổng phiếu: %d · đúng đối tượng (câu 1 = Có): %d · không mâu thuẫn: %d" % (len(rows), len(ok), len(clean)))
for col in ["q2_noi_gan_nhat", "q4_cach_chuan_bi", "q5_thoi_gian_chuan_bi", "q6_chuyen_da_xay_ra",
            "q7_thoi_gian_quyet_lai", "q8_chi_so_voi_du_tinh", "q10_san_long_hoi_them"]:
    multi = col in ("q4_cach_chuan_bi", "q6_chuyen_da_xay_ra")
    for label, group in (("đúng đối tượng", ok), ("không mâu thuẫn", clean)):
        c = collections.Counter()
        for r in group:
            vals = [v.strip() for v in r[col].replace("(Facebook, Zalo…)", "(Facebook/Zalo)").split(",")] if multi else [r[col]]
            c.update(v for v in vals if v)
        print("\n%s — %s (n=%d)" % (col, label, len(group)))
        for k, v in c.most_common():
            print("  %d/%d  %s" % (v, len(group), k))
