
import customtkinter as ctk, sys, pathlib
from .login_gui import LoginWindow
from .main_gui import MainApp
from .setup_gui import SetupWindow
from .utils_logger import get_logger
logger = get_logger("Start")
BASE_DIR = pathlib.Path(getattr(sys, "_MEIPASS", pathlib.Path(__file__).resolve().parents[1]))
CONFIG_PATH = BASE_DIR / "config.json"
def run():
    ctk.set_appearance_mode("System"); ctk.set_default_color_theme("blue")
    root = ctk.CTk()
    root.withdraw()
    need_setup = False
    if not CONFIG_PATH.exists():
        need_setup = True
    else:
        try:
            sys.path.append(str(BASE_DIR / "backend"))
            from backend.db import get_db_connection
            conn = get_db_connection()
            if not conn:
                need_setup = True
            else:
                conn.close()
        except Exception:
            need_setup = True
    setup_ok = True
    if need_setup:
        done = {"ok": False}
        def after_setup():
            done["ok"] = True
        sw = SetupWindow(root, on_success=after_setup)
        root.wait_window(sw)
        setup_ok = done["ok"]
        if not setup_ok:
            logger.info("User cancelled setup. Exiting.")
            return
    try:
        sys.path.append(str(BASE_DIR / "backend"))
        from backend import init_schema
        init_schema.main()
    except Exception as e:
        logger.exception("Auto-init failed: %s", e)
    def on_success(user):
        app = MainApp(user); app.mainloop()
    lw = LoginWindow(root, on_success)
    root.deiconify()
    root.mainloop()
if __name__ == "__main__": run()
