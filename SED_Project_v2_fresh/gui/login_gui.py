
import customtkinter as ctk, sys, pathlib
BASE_DIR = pathlib.Path(getattr(sys, "_MEIPASS", pathlib.Path(__file__).resolve().parents[1]))
sys.path.append(str(BASE_DIR / 'backend'))
from backend.login import login as backend_login
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
        user = backend_login(self.username.get(), self.password.get())
        if user: self.msg.configure(text="Berjaya"); self.after(200, lambda: (self.destroy(), self.on_success(user)))
        else: self.msg.configure(text="Username / Password salah.")
