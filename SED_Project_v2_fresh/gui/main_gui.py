
import customtkinter as ctk, sys, pathlib
BASE_DIR = pathlib.Path(getattr(sys, "_MEIPASS", pathlib.Path(__file__).resolve().parents[1]))
sys.path.append(str(BASE_DIR / 'backend'))
from backend.user_roles import ROLE_PERMISSIONS
from backend import init_schema
from .crud_base import CrudFrame
from .module_wrappers import MODULE_SPECS, list_profil_records
from .utils_logger import get_logger
logger = get_logger("MainGUI")
class ReadOnlyList(ctk.CTkFrame):
    def __init__(self, master, fetch_fn, title="", filters=None):
        super().__init__(master); self.fetch_fn=fetch_fn; self.filters=filters or []
        ctk.CTkLabel(self, text=title, font=ctk.CTkFont(size=18, weight="bold")).grid(row=0,column=0,sticky="w",padx=8,pady=(8,4))
        self.filter_vars={}
        if self.filters:
            filt = ctk.CTkFrame(self); filt.grid(row=1,column=0,sticky="ew",padx=8,pady=4)
            for i,(k,label) in enumerate(self.filters):
                ctk.CTkLabel(filt, text=label).grid(row=0,column=2*i,sticky="e",padx=4)
                var = ctk.StringVar(); ent=ctk.CTkEntry(filt, textvariable=var, width=180); ent.grid(row=0,column=2*i+1,sticky="w",padx=4); self.filter_vars[k]=var
            ctk.CTkButton(filt, text="Cari", command=self.refresh).grid(row=0,column=2*len(self.filters)+1,padx=6)
        import tkinter.ttk as ttk, json
        self.tree = ttk.Treeview(self, columns=['data'], show='headings'); self.tree.heading('data', text='Rekod (JSON)'); self.tree.grid(row=2,column=0,sticky="nsew",padx=8,pady=8); self.grid_rowconfigure(2,weight=1); self.grid_columnconfigure(0,weight=1); self.refresh()
    def refresh(self):
        for r in self.tree.get_children(): self.tree.delete(r)
        kwargs = {k:v.get().strip() or None for k,v in self.filter_vars.items()}
        try: items = self.fetch_fn(**kwargs)
        except Exception as e: items = []
        import json
        for it in items or []: self.tree.insert('', 'end', values=[json.dumps(it, ensure_ascii=False)])
class MainApp(ctk.CTk):
    def __init__(self, user):
        super().__init__(); self.user=user; self.title("SED"); self.geometry("1100x700"); ctk.set_appearance_mode("System"); ctk.set_default_color_theme("blue")
        sidebar = ctk.CTkFrame(self, width=220, corner_radius=0); sidebar.pack(side='left', fill='y')
        ctk.CTkLabel(sidebar, text=f"👤 {user.get('username')} ({user.get('role')})").pack(padx=8,pady=(12,8))
        self.content = ctk.CTkFrame(self); self.content.pack(side='right', fill='both', expand=True)
        def add_btn(name, builder): b=ctk.CTkButton(sidebar, text=name, command=lambda: self.show(builder)); b.pack(fill='x',padx=8,pady=4)
        perms = ROLE_PERMISSIONS.get(user.get('role'), [])
        for key,spec in MODULE_SPECS.items():
            add_btn(spec['title'], lambda s=spec: self.build_crud_view(s))
        add_btn("Rekod Profil", lambda: ReadOnlyList(self.content, list_profil_records, title="Rekod Profil", filters=[('unit','Unit'),('name','Nama')]))
        buttons = [w for w in sidebar.winfo_children() if isinstance(w, ctk.CTkButton)]
        if buttons: buttons[0].invoke()
    def show(self, builder): 
        for w in self.content.winfo_children(): w.destroy()
        v = builder(); v.pack(fill='both', expand=True)
    def build_crud_view(self, spec):
        def builder(): return CrudFrame(self.content, api=spec['api'], fields=spec['fields'], title=spec['title'], combos=spec.get('combos',{}), required=spec.get('required', set()))
        return builder
