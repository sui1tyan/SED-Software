
import tkinter as tk, tkinter.ttk as ttk, customtkinter as ctk
from tkinter import messagebox
from .utils_export import export_csv, export_pdf
from .utils_logger import get_logger
logger = get_logger("CRUD")
class CrudFrame(ctk.CTkFrame):
    def __init__(self, master, api, fields, title="", combos=None, required=None):
        super().__init__(master)
        self.api = api; self.fields = fields; self.combos = combos or {}; self.required = required or set()
        ctk.CTkLabel(self, text=title, font=ctk.CTkFont(size=18, weight="bold")).grid(row=0, column=0, sticky="w", padx=8, pady=(10,0))
        toolbar = ctk.CTkFrame(self); toolbar.grid(row=1, column=0, sticky="ew", padx=8, pady=6)
        self.search_var = tk.StringVar()
        ctk.CTkEntry(toolbar, textvariable=self.search_var, placeholder_text="Cari...").pack(side="left", padx=4)
        ctk.CTkButton(toolbar, text="Cari", command=self.refresh).pack(side="left", padx=4)
        ctk.CTkButton(toolbar, text="Tambah", command=self.open_add).pack(side="left", padx=4)
        ctk.CTkButton(toolbar, text="Edit", command=self.open_edit).pack(side="left", padx=4)
        ctk.CTkButton(toolbar, text="Padam", command=self.delete_selected).pack(side="left", padx=4)
        ctk.CTkButton(toolbar, text="Export CSV", command=lambda: export_csv(self._all_rows)).pack(side="right", padx=4)
        ctk.CTkButton(toolbar, text="Export PDF", command=lambda: export_pdf(self._all_rows, title)).pack(side="right", padx=4)
        self.tree = ttk.Treeview(self, columns=[f['name'] for f in self.fields], show='headings')
        for f in self.fields:
            self.tree.heading(f['name'], text=f['label'])
            self.tree.column(f['name'], width=140, anchor="w")
        self.tree.grid(row=2, column=0, sticky="nsew", padx=8, pady=8)
        self.grid_rowconfigure(2, weight=1); self.grid_columnconfigure(0, weight=1)
        self._all_rows = []; self.refresh()
    def refresh(self):
        for r in self.tree.get_children(): self.tree.delete(r)
        query = (self.search_var.get() or "").strip().lower()
        try: rows = self.api['list']()
        except Exception as e: logger.exception("List failed"); rows = []
        if query: rows = [r for r in rows if any(query in str(v).lower() for v in r.values())]
        self._all_rows = rows
        for r in rows: self.tree.insert('', 'end', iid=str(r.get('id','')), values=[r.get(f['name'],"") for f in self.fields])
    def _collect_form(self, win, entries):
        data = {}
        for k,w in entries.items():
            val = w.get().strip()
            if k in self.required and not val: messagebox.showerror("Validasi", f"Medan {k} wajib"); return None
            data[k] = val if val != "" else None
        return data
    def open_add(self): self._open_form(mode="add")
    def open_edit(self):
        sel = self.tree.selection()
        if not sel: messagebox.showinfo("Info","Sila pilih rekod"); return
        self._open_form(mode="edit", rec_id=int(sel[0]))
    def _open_form(self, mode="add", rec_id=None):
        win = ctk.CTkToplevel(self); frm = ctk.CTkFrame(win); frm.pack(padx=10,pady=10)
        entries = {}
        for i,f in enumerate(self.fields):
            ctk.CTkLabel(frm, text=f['label']).grid(row=i,column=0,sticky="e",padx=6,pady=4)
            ent = ctk.CTkEntry(frm, width=240); ent.grid(row=i,column=1,sticky="w",padx=6,pady=4); entries[f['name']]=ent
        def save():
            data = self._collect_form(win, entries)
            if data is None: return
            try:
                if mode=="add": self.api['create'](data)
                else: self.api['update'](rec_id, data)
                win.destroy(); self.refresh()
            except Exception as e: messagebox.showerror("Ralat", f"Gagal simpan: {e}")
        frm_btn = ctk.CTkFrame(win); frm_btn.pack(fill="x",padx=10,pady=(0,10))
        ctk.CTkButton(frm_btn, text="Simpan", command=save).pack(side="left",padx=6); ctk.CTkButton(frm_btn, text="Batal", command=win.destroy).pack(side="left",padx=6)
    def delete_selected(self):
        sel = self.tree.selection(); 
        if not sel: messagebox.showinfo("Info","Sila pilih rekod"); return
        if not messagebox.askyesno("Pasti","Padam?"): return
        try: self.api['delete'](int(sel[0])); self.refresh()
        except Exception as e: messagebox.showerror("Ralat", f"Gagal padam: {e}")
