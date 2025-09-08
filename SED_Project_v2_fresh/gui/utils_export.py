
import csv
from tkinter import filedialog, messagebox
try:
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.pdfgen import canvas
except Exception:
    canvas = None
def export_csv(rows, default_name="export.csv"):
    if not rows: messagebox.showinfo("Export", "Tiada data untuk diexport."); return
    path = filedialog.asksaveasfilename(defaultextension=".csv", initialfile=default_name, filetypes=[("CSV","*.csv")])
    if not path: return
    keys = list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); w.writerows(rows)
    messagebox.showinfo("Export", f"CSV disimpan: {path}")
def export_pdf(rows, title="Laporan", default_name="export.pdf"):
    if canvas is None: messagebox.showerror("Export PDF", "reportlab tiada. Jalankan: pip install reportlab"); return
    if not rows: messagebox.showinfo("Export", "Tiada data untuk diexport."); return
    path = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile=default_name, filetypes=[("PDF","*.pdf")])
    if not path: return
    c = canvas.Canvas(path, pagesize=landscape(A4)); c.setFont("Helvetica", 12); c.drawString(50,560,title)
    y = 520; keys = list(rows[0].keys())
    for r in rows:
        x = 50
        for k in keys:
            c.drawString(x,y, str(r.get(k,""))[:30]); x += 180
        y -= 18
        if y < 50: c.showPage(); y = 560
    c.save(); messagebox.showinfo("Export", f"PDF disimpan: {path}")
