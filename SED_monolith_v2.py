#!/usr/bin/env python3
# SED Monolith v2 — single-file app (backend + frontend)
# Dependencies: customtkinter, mysql-connector-python, (optional) reportlab
# Run: python SED_monolith_v2.py

import os, sys, json, csv, hashlib, logging
from logging.handlers import RotatingFileHandler
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox, filedialog
from datetime import datetime
from typing import Dict, Any, List, Optional

# ---- Third-party (install via pip) ----
try:
    import customtkinter as ctk
except Exception as e:
    raise RuntimeError("customtkinter required. Install: pip install customtkinter") from e

try:
    import mysql.connector
except Exception as e:
    raise RuntimeError("mysql-connector-python required. Install: pip install mysql-connector-python") from e

# reportlab is optional (for PDF export)
try:
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.pdfgen import canvas as pdf_canvas
except Exception:
    pdf_canvas = None

# ---------------- Paths & constants ----------------
BASE_DIR = Path(os.path.abspath(os.path.dirname(__file__)))
CONFIG_PATH = BASE_DIR / "config.json"
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "app.log"

DEFAULT_DB = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "",
    "database": "sed_db",
    "autocommit": True
}

# ---------------- Logging ----------------
def get_logger(name="SED"):
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = RotatingFileHandler(LOG_FILE, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
        fmt = logging.Formatter("%(asctime)s | %(name)s | %(levelname)s | %(message)s")
        handler.setFormatter(fmt)
        logger.addHandler(handler)
    return logger

log = get_logger("SED")

# ---------------- DB helpers ----------------
def load_config() -> Dict[str, Any]:
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            db = cfg.get("db", {})
            return {
                "host": db.get("host", DEFAULT_DB["host"]),
                "port": int(db.get("port", DEFAULT_DB["port"])),
                "user": db.get("user", DEFAULT_DB["user"]),
                "password": db.get("password", DEFAULT_DB["password"]),
                "database": db.get("database", DEFAULT_DB["database"]),
                "autocommit": True
            }
        except Exception as e:
            log.exception("Failed reading config.json; using defaults: %s", e)
    return dict(DEFAULT_DB)

DB_CONFIG = load_config()

def get_db_connection():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Exception as e:
        log.exception("DB connection error: %s", e)
        return None

def _create_database_if_missing():
    cfg = dict(DB_CONFIG)
    dbname = cfg.pop("database", None)
    try:
        conn = mysql.connector.connect(**{k: cfg[k] for k in ("host","port","user","password")})
        cur = conn.cursor()
        cur.execute(f"CREATE DATABASE IF NOT EXISTS `{dbname}` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        conn.commit()
    finally:
        try: conn.close()
        except: pass

# ---------------- Modules (data layer) ----------------
def rows_to_dicts(cur) -> List[Dict[str, Any]]:
    cols = [c[0] for c in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]

# Carta Organisasi
def carta_ensure_table(conn):
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS carta_organisasi (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nama VARCHAR(100) NOT NULL,
            jawatan VARCHAR(100) NOT NULL,
            unit VARCHAR(100),
            supervisor_id INT NULL,
            telefon VARCHAR(30),
            email VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)
    conn.commit()

def carta_create(conn, data):
    cur = conn.cursor()
    cur.execute("INSERT INTO carta_organisasi (nama,jawatan,unit,supervisor_id,telefon,email) VALUES (%s,%s,%s,%s,%s,%s)",
                (data.get('nama'),data.get('jawatan'),data.get('unit'),data.get('supervisor_id'),data.get('telefon'),data.get('email')))
    conn.commit(); return cur.lastrowid

def carta_update(conn, rec_id, data):
    fields = [k for k in ['nama','jawatan','unit','supervisor_id','telefon','email'] if k in data]
    if not fields: return False
    set_clause = ','.join(f"{k}=%s" for k in fields)
    vals = [data[k] for k in fields] + [rec_id]
    cur = conn.cursor(); cur.execute(f"UPDATE carta_organisasi SET {set_clause} WHERE id=%s", vals); conn.commit(); return cur.rowcount>0

def carta_delete(conn, rec_id):
    cur = conn.cursor(); cur.execute("DELETE FROM carta_organisasi WHERE id=%s", (rec_id,)); conn.commit(); return cur.rowcount>0

def carta_list(conn):
    cur = conn.cursor(); cur.execute("SELECT * FROM carta_organisasi ORDER BY id DESC"); return rows_to_dicts(cur)

# Profil PK/WM
def profil_ensure_table(conn):
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS profil_pk_wm (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nama VARCHAR(120) NOT NULL,
            no_kp VARCHAR(30) UNIQUE NOT NULL,
            pangkat VARCHAR(60),
            unit VARCHAR(60),
            telefon VARCHAR(30),
            alamat TEXT,
            tarikh_masuk DATE,
            status ENUM('aktif','tidak_aktif') DEFAULT 'aktif',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)
    conn.commit()

def profil_create(conn, data):
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO profil_pk_wm (nama,no_kp,pangkat,unit,telefon,alamat,tarikh_masuk,status)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
    """, (data.get('nama'),data.get('no_kp'),data.get('pangkat'),data.get('unit'),
          data.get('telefon'),data.get('alamat'),data.get('tarikh_masuk'),data.get('status') or 'aktif'))
    conn.commit(); return cur.lastrowid

def profil_update(conn, rec_id, data):
    fields = [k for k in ['nama','no_kp','pangkat','unit','telefon','alamat','tarikh_masuk','status'] if k in data]
    if not fields: return False
    set_clause = ','.join(f"{k}=%s" for k in fields)
    vals = [data[k] for k in fields] + [rec_id]
    cur = conn.cursor(); cur.execute(f"UPDATE profil_pk_wm SET {set_clause} WHERE id=%s", vals); conn.commit(); return cur.rowcount>0

def profil_delete(conn, rec_id):
    cur = conn.cursor(); cur.execute("DELETE FROM profil_pk_wm WHERE id=%s", (rec_id,)); conn.commit(); return cur.rowcount>0

def profil_list(conn, status=None):
    cur = conn.cursor()
    if status:
        cur.execute("SELECT * FROM profil_pk_wm WHERE status=%s ORDER BY id DESC", (status,))
    else:
        cur.execute("SELECT * FROM profil_pk_wm ORDER BY id DESC")
    return rows_to_dicts(cur)

def profil_list_by_unit(conn, unit):
    cur = conn.cursor(); cur.execute("SELECT * FROM profil_pk_wm WHERE unit=%s ORDER BY id DESC",(unit,)); return rows_to_dicts(cur)

def profil_search_by_name(conn, name):
    cur = conn.cursor(); cur.execute("SELECT * FROM profil_pk_wm WHERE nama LIKE %s ORDER BY id DESC",(f"%{name}%",)); return rows_to_dicts(cur)

def profil_list_inactive(conn):
    cur = conn.cursor(); cur.execute("SELECT * FROM profil_pk_wm WHERE status='tidak_aktif' ORDER BY id DESC"); return rows_to_dicts(cur)

# Placeholder modules (tables only)
def _ensure_simple_table(conn, table_name: str):
    cur = conn.cursor()
    cur.execute(f"CREATE TABLE IF NOT EXISTS {table_name} (id INT AUTO_INCREMENT PRIMARY KEY) ENGINE=InnoDB;")
    conn.commit()

def simple_list(conn, table_name: str):
    cur = conn.cursor(); cur.execute(f"SELECT * FROM {table_name}"); return rows_to_dicts(cur)

# ---------------- Users / Roles ----------------
ROLE_PERMISSIONS = {
    'host': [
        'carta_organisasi','profil_pk_wm_input','bkl_input','laporan_jenayah',
        'ganjaran_pk_wm','rekod_ganjaran','jurnal_sed',
        'profil_pk_wm_records','bkl_records','manage_users'
    ],
    'admin': [
        'carta_organisasi','profil_pk_wm_input','bkl_input','laporan_jenayah',
        'ganjaran_pk_wm','rekod_ganjaran','jurnal_sed',
        'profil_pk_wm_records','bkl_records','manage_users'
    ],
    'user': [
        'carta_organisasi','profil_pk_wm_input','bkl_input','laporan_jenayah',
        'ganjaran_pk_wm','rekod_ganjaran','jurnal_sed'
    ],
}

def _hpw(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()

def ensure_users_table(conn):
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            password VARCHAR(128) NOT NULL,
            role ENUM('host','admin','user') DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)
    conn.commit()
    # seed
    for u,pw,role in [("admin","admin123","admin"), ("alif","alif123","host")]:
        try:
            cur.execute("INSERT IGNORE INTO users (username, password, role) VALUES (%s,%s,%s)", (u, _hpw(pw), role))
        except Exception:
            pass
    conn.commit()

def login_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id, username, password, role FROM users WHERE username=%s", (username,))
        row = cur.fetchone()
        if row and row["password"] == _hpw(password):
            return {"id": row["id"], "username": row["username"], "role": row["role"]}
        return None
    finally:
        conn.close()

def create_user(username: str, password: str, role: str = "user") -> bool:
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cur = conn.cursor()
        cur.execute("INSERT IGNORE INTO users (username, password, role) VALUES (%s,%s,%s)",
                    (username, _hpw(password), role))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()

def delete_user(requestor_username: str, username: str) -> bool:
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT role FROM users WHERE username=%s", (requestor_username,))
        r = cur.fetchone()
        if not r or r["role"] not in ("host","admin"):
            return False
        if requestor_username == username:
            return False
        cur.execute("DELETE FROM users WHERE username=%s", (username,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()

# ---------------- Schema bootstrapping ----------------
def ensure_schema():
    _create_database_if_missing()
    conn = get_db_connection()
    if not conn:
        log.error("Could not connect to DB (ensure_schema)")
        return False
    try:
        ensure_users_table(conn)
        carta_ensure_table(conn)
        profil_ensure_table(conn)
        for t in ["bkl_input_table","laporan_jenayah_table","ganjaran_pk_wm_table","rekod_ganjaran_table","jurnal_sed_table"]:
            _ensure_simple_table(conn, t)
    finally:
        conn.close()
    return True

# ---------------- GUI utils ----------------
def export_csv(rows: List[Dict[str, Any]], default_name="export.csv"):
    if not rows:
        messagebox.showinfo("Export", "Tiada data untuk diexport.")
        return
    path = filedialog.asksaveasfilename(defaultextension=".csv", initialfile=default_name, filetypes=[("CSV","*.csv")])
    if not path:
        return
    keys = list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)
    messagebox.showinfo("Export", f"CSV disimpan: {path}")

def export_pdf(rows: List[Dict[str, Any]], title="Laporan", default_name="export.pdf"):
    if pdf_canvas is None:
        messagebox.showerror("Export PDF", "reportlab tiada. Jalankan: pip install reportlab")
        return
    if not rows:
        messagebox.showinfo("Export", "Tiada data untuk diexport.")
        return
    path = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile=default_name, filetypes=[("PDF","*.pdf")])
    if not path: return
    c = pdf_canvas.Canvas(path, pagesize=landscape(A4))
    c.setFont("Helvetica", 12)
    c.drawString(50,560,title)
    y = 520; keys = list(rows[0].keys())
    for r in rows:
        x = 50
        for k in keys:
            c.drawString(x,y, str(r.get(k,""))[:30]); x += 180
        y -= 18
        if y < 50: c.showPage(); y = 560
    c.save(); messagebox.showinfo("Export", f"PDF disimpan: {path}")

# ---------------- GUI components ----------------
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
        try:
            rows = self.api['list']()
        except Exception as e:
            get_logger("CRUD").exception("List failed")
            rows = []
        if query:
            rows = [r for r in rows if any(query in str(v).lower() for v in r.values())]
        self._all_rows = rows
        for r in rows:
            self.tree.insert('', 'end', iid=str(r.get('id','')), values=[r.get(f['name'],"") for f in self.fields])

    def _collect_form(self, win, entries):
        data = {}
        for k,w in entries.items():
            val = w.get().strip()
            if k in self.required and not val:
                messagebox.showerror("Validasi", f"Medan {k} wajib"); return None
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

class ReadOnlyList(ctk.CTkFrame):
    def __init__(self, master, fetch_fn, title="", filters=None):
        super().__init__(master); self.fetch_fn=fetch_fn; self.filters=filters or []
        ctk.CTkLabel(self, text=title, font=ctk.CTkFont(size=18, weight="bold")).grid(row=0,column=0,sticky="w",padx=8,pady=(8,4))
        self.filter_vars={}
        if self.filters:
            filt = ctk.CTkFrame(self); filt.grid(row=1,column=0,sticky="ew",padx=8,pady=4)
            for i,(k,label) in enumerate(self.filters):
                ctk.CTkLabel(filt, text=label).grid(row=0,column=2*i,sticky="e",padx=4)
                var = tk.StringVar(); ent=ctk.CTkEntry(filt, textvariable=var, width=180); ent.grid(row=0,column=2*i+1,sticky="w",padx=4); self.filter_vars[k]=var
            ctk.CTkButton(filt, text="Cari", command=self.refresh).grid(row=0,column=2*len(self.filters)+1,padx=6)
        self.tree = ttk.Treeview(self, columns=['data'], show='headings'); self.tree.heading('data', text='Rekod (JSON)')
        self.tree.grid(row=2,column=0,sticky="nsew",padx=8,pady=8); self.grid_rowconfigure(2,weight=1); self.grid_columnconfigure(0,weight=1)
        self.refresh()

    def refresh(self):
        for r in self.tree.get_children(): self.tree.delete(r)
        kwargs = {k:v.get().strip() or None for k,v in self.filter_vars.items()}
        try:
            items = self.fetch_fn(**kwargs)
        except Exception as e:
            items = []
        import json as _json
        for it in items or []: self.tree.insert('', 'end', values=[_json.dumps(it, ensure_ascii=False)])

# ---------------- APIs (wrappers to call with new connections) ----------------
def _with_conn(fn, *args, **kwargs):
    conn = get_db_connection()
    if not conn: raise RuntimeError("Cannot connect to DB")
    try: return fn(conn, *args, **kwargs)
    finally: conn.close()

def api_carta():
    return {
        "list": lambda: _with_conn(carta_list),
        "create": lambda data: _with_conn(carta_create, data),
        "update": lambda rec_id, data: _with_conn(carta_update, rec_id, data),
        "delete": lambda rec_id: _with_conn(carta_delete, rec_id),
    }

def api_profil():
    return {
        "list": lambda: _with_conn(profil_list),
        "create": lambda data: _with_conn(profil_create, data),
        "update": lambda rec_id, data: _with_conn(profil_update, rec_id, data),
        "delete": lambda rec_id: _with_conn(profil_delete, rec_id),
    }

def list_profil_records(unit=None,name=None,status=None):
    if unit: return _with_conn(profil_list_by_unit, unit)
    if name: return _with_conn(profil_search_by_name, name)
    if status == "tidak_aktif": return _with_conn(profil_list_inactive)
    return _with_conn(profil_list)

MODULE_SPECS = {
    "carta": {
        "title":"Carta Organisasi",
        "api": api_carta(),
        "fields":[
            {"name":"id","label":"ID"},
            {"name":"nama","label":"Nama"},
            {"name":"jawatan","label":"Jawatan"},
            {"name":"unit","label":"Unit"}
        ],
        "required":{"nama","jawatan"}
    },
    "profil": {
        "title":"Profil PK/WM",
        "api": api_profil(),
        "fields":[
            {"name":"id","label":"ID"},
            {"name":"nama","label":"Nama"},
            {"name":"no_kp","label":"No KP"}
        ],
        "required":{"nama","no_kp"}
    }
}

# ---------------- Setup / Login / Main GUI ----------------
class SetupWindow(ctk.CTkToplevel):
    def __init__(self, master, on_success=None):
        super().__init__(master)
        self.on_success = on_success
        self.title("Setup Database — First Run")
        self.geometry("460x320")
        ctk.set_appearance_mode("System"); ctk.set_default_color_theme("blue")
        cfg = {"db": dict(DEFAULT_DB)}
        try:
            if CONFIG_PATH.exists():
                with open(CONFIG_PATH, "r", encoding="utf-8") as f: cfg = json.load(f)
        except Exception: pass
        db = cfg.get("db", cfg)
        frm = ctk.CTkFrame(self); frm.pack(fill="both", expand=True, padx=12, pady=12)
        labels = [("Host","host"),("Port","port"),("User","user"),("Password","password"),("Database","database")]
        self.vars = {}
        for i,(lbl,key) in enumerate(labels):
            ctk.CTkLabel(frm, text=lbl).grid(row=i, column=0, sticky="e", padx=6, pady=6)
            ent = ctk.CTkEntry(frm, width=280, show="*" if key=="password" else None)
            ent.grid(row=i, column=1, sticky="w", padx=6, pady=6)
            ent.insert(0, str(db.get(key, "")))
            self.vars[key] = ent
        btnfrm = ctk.CTkFrame(self); btnfrm.pack(fill="x", padx=12, pady=(6,12))
        ctk.CTkButton(btnfrm, text="Test Connection", command=self.test_connection).pack(side="left", padx=6)
        ctk.CTkButton(btnfrm, text="Save & Continue", command=self.save_and_continue).pack(side="left", padx=6)
        ctk.CTkButton(btnfrm, text="Cancel", command=self.destroy).pack(side="left", padx=6)

    def _collect(self):
        try: port = int(self.vars["port"].get().strip() or 3306)
        except: port = 3306
        return {
            "host": self.vars["host"].get().strip() or "localhost",
            "port": port,
            "user": self.vars["user"].get().strip() or "root",
            "password": self.vars["password"].get(),
            "database": self.vars["database"].get().strip() or "sed_db"
        }

    def test_connection(self):
        cfg = self._collect()
        try:
            conn = mysql.connector.connect(host=cfg["host"], port=cfg["port"], user=cfg["user"], password=cfg["password"])
            conn.close()
            messagebox.showinfo("OK", "Berjaya sambung ke MySQL server.")
        except Exception as e:
            messagebox.showerror("Gagal", f"Tidak dapat sambung: {e}")

    def save_and_continue(self):
        cfg = self._collect()
        try:
            conn = mysql.connector.connect(host=cfg["host"], port=cfg["port"], user=cfg["user"], password=cfg["password"])
            cur = conn.cursor(); cur.execute(f"CREATE DATABASE IF NOT EXISTS `{cfg['database']}` DEFAULT CHARACTER SET utf8mb4;"); conn.commit(); conn.close()
        except Exception as e:
            messagebox.showerror("Gagal", f"Tidak dapat sambung/anda tidak ada kebenaran untuk buat DB: {e}"); return
        data = {"db": cfg}
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f: json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            messagebox.showerror("Gagal Simpan", f"Tidak dapat tulis config.json: {e}"); return
        global DB_CONFIG
        DB_CONFIG = load_config()
        messagebox.showinfo("Simpan", "Konfigurasi disimpan. Teruskan ke aplikasi.")
        if callable(self.on_success): self.destroy(); self.on_success()

class LoginWindow(ctk.CTkToplevel):
    def __init__(self, master, on_success):
        super().__init__(master); self.on_success = on_success; self.title("SED Login"); self.geometry("380x260"); self.resizable(False,False)
        ctk.set_appearance_mode("System"); ctk.set_default_color_theme("blue")
        ctk.CTkLabel(self, text="Log Masuk", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=(16,8))
        frm = ctk.CTkFrame(self); frm.pack(fill="x", padx=16, pady=8)
        ctk.CTkLabel(frm, text="Username").grid(row=0,column=0,sticky="e",padx=6,pady=6); self.username = ctk.CTkEntry(frm); self.username.grid(row=0,column=1,sticky="ew",padx=6,pady=6); frm.grid_columnconfigure(1,weight=1)
        ctk.CTkLabel(frm, text="Password").grid(row=1,column=0,sticky="e",padx=6,pady=6); self.password = ctk.CTkEntry(frm, show="*"); self.password.grid(row=1,column=1,sticky="ew",padx=6,pady=6)
        self.msg = ctk.CTkLabel(self, text="", text_color="red"); self.msg.pack(pady=4)
        btn = ctk.CTkButton(self, text="Masuk", command=self.try_login); btn.pack(pady=8)
        self.bind('<Return>', lambda e: self.try_login())

    def try_login(self):
        user = login_user(self.username.get(), self.password.get())
        if user: self.msg.configure(text="Berjaya"); self.after(200, lambda: (self.destroy(), self.on_success(user)))
        else: self.msg.configure(text="Username / Password salah.")

class MainApp(ctk.CTk):
    def __init__(self, user):
        super().__init__(); self.user=user; self.title("SED"); self.geometry("1100x700"); ctk.set_appearance_mode("System"); ctk.set_default_color_theme("blue")
        sidebar = ctk.CTkFrame(self, width=220, corner_radius=0); sidebar.pack(side='left', fill='y')
        ctk.CTkLabel(sidebar, text=f"👤 {user.get('username')} ({user.get('role')})").pack(padx=8,pady=(12,8))

        # Manage users (host/admin)
        if user.get("role") in ("host","admin"):
            manage = ctk.CTkFrame(sidebar); manage.pack(fill="x", padx=8, pady=(8,8))
            ctk.CTkLabel(manage, text="Manage Users").pack()
            ufrm = ctk.CTkFrame(manage); ufrm.pack(fill="x", pady=4)
            self.new_user = ctk.CTkEntry(ufrm, placeholder_text="username"); self.new_user.pack(fill="x", pady=2)
            self.new_pw = ctk.CTkEntry(ufrm, placeholder_text="password"); self.new_pw.pack(fill="x", pady=2)
            self.new_role = ctk.CTkEntry(ufrm, placeholder_text="role (host/admin/user)"); self.new_role.pack(fill="x", pady=2)
            ctk.CTkButton(manage, text="Add User", command=self._add_user).pack(fill="x", pady=2)
            self.del_user = ctk.CTkEntry(manage, placeholder_text="username to delete"); self.del_user.pack(fill="x", pady=2)
            ctk.CTkButton(manage, text="Delete User", command=self._del_user).pack(fill="x", pady=2)

        self.content = ctk.CTkFrame(self); self.content.pack(side='right', fill='both', expand=True)

        def add_btn(name, builder): b=ctk.CTkButton(sidebar, text=name, command=lambda: self.show(builder)); b.pack(fill='x',padx=8,pady=4)

        perms = ROLE_PERMISSIONS.get(user.get('role'), [])
        # Show modules (we don't filter by perms in this lightweight UI, add if needed)
        for key,spec in MODULE_SPECS.items():
            add_btn(spec['title'], lambda s=spec: self.build_crud_view(s))

        add_btn("Rekod Profil", lambda: ReadOnlyList(self.content, list_profil_records, title="Rekod Profil", filters=[('unit','Unit'),('name','Nama')]))

        buttons = [w for w in sidebar.winfo_children() if isinstance(w, ctk.CTkButton)]
        if buttons: buttons[0].invoke()

    def _add_user(self):
        u = (self.new_user.get() or "").strip()
        p = (self.new_pw.get() or "").strip()
        r = (self.new_role.get() or "user").strip()
        if not u or not p: messagebox.showerror("Err","username/password required"); return
        ok = create_user(u,p,r)
        messagebox.showinfo("Create", "OK" if ok else "Failed or duplicate")

    def _del_user(self):
        target = (self.del_user.get() or "").strip()
        if not target: return
        ok = delete_user(self.user.get("username"), target)
        messagebox.showinfo("Delete", "OK" if ok else "Not allowed / not found")

    def show(self, builder): 
        for w in self.content.winfo_children(): w.destroy()
        v = builder(); v.pack(fill='both', expand=True)

    def build_crud_view(self, spec):
        def builder(): return CrudFrame(self.content, api=spec['api'], fields=spec['fields'], title=spec['title'], combos=spec.get('combos',{}), required=spec.get('required', set()))
        return builder

# ---------------- App entry ----------------
def run():
    # Setup first-run
    ctk.set_appearance_mode("System"); ctk.set_default_color_theme("blue")
    root = ctk.CTk()
    root.withdraw()

    # Decide if setup is needed
    need_setup = False
    if not CONFIG_PATH.exists():
        need_setup = True
    else:
        try:
            conn = get_db_connection()
            if not conn:
                need_setup = True
            else:
                conn.close()
        except Exception:
            need_setup = True

    # Show setup
    if need_setup:
        done = {"ok": False}
        def after_setup(): done["ok"] = True
        sw = SetupWindow(root, on_success=after_setup)
        root.wait_window(sw)
        if not done["ok"]:
            log.info("User cancelled setup. Exiting.")
            return

    # Ensure schema (DB + tables + seed users)
    try:
        ensure_schema()
    except Exception as e:
        log.exception("Auto-init failed: %s", e)

    def on_success(user):
        app = MainApp(user); app.mainloop()

    lw = LoginWindow(root, on_success)
    root.deiconify()
    root.mainloop()

if __name__ == "__main__":
    run()
