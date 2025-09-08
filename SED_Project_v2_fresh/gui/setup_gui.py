
import customtkinter as ctk, json, pathlib, sys
from tkinter import messagebox
import mysql.connector
BASE_DIR = pathlib.Path(getattr(sys, "_MEIPASS", pathlib.Path(__file__).resolve().parents[1]))
CONFIG_PATH = BASE_DIR / "config.json"
class SetupWindow(ctk.CTkToplevel):
    def __init__(self, master, on_success=None):
        super().__init__(master)
        self.on_success = on_success
        self.title("Setup Database — First Run")
        self.geometry("460x320")
        ctk.set_appearance_mode("System"); ctk.set_default_color_theme("blue")
        cfg = {"db": {"host":"localhost","port":3306,"user":"root","password":"","database":"sed_db"}}
        try:
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
        try:
            port = int(self.vars["port"].get().strip() or 3306)
        except:
            port = 3306
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
        messagebox.showinfo("Simpan", "Konfigurasi disimpan. Teruskan ke aplikasi.")
        if callable(self.on_success): self.destroy(); self.on_success()
