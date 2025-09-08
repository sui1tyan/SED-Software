
import PyInstaller.__main__, pathlib, os
root = pathlib.Path(__file__).resolve().parents[0]
entry = root / "gui" / "start.py"
sep = ";" if os.name=="nt" else ":"
PyInstaller.__main__.run([
    str(entry),
    "--name=SED_App_v2",
    "--onefile",
    "--windowed",
    "--add-data", f"{root / 'config.json'}{sep}config.json",
    "--add-data", f"{root / 'backend'}{sep}backend",
    "--add-data", f"{root / 'gui'}{sep}gui",
    "--hidden-import", "customtkinter",
    "--hidden-import", "mysql.connector",
])
