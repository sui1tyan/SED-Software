
import sys, pathlib
BASE_DIR = pathlib.Path(getattr(sys, "_MEIPASS", pathlib.Path(__file__).resolve().parents[1]))
sys.path.append(str(BASE_DIR / "backend"))
from backend.db import get_db_connection
from backend.modules import carta_organisasi as mod_carta, profil_pk_wm_input as mod_profil_input, profil_pk_wm_records as mod_profil_records
def _with_conn(fn, *args, **kwargs):
    conn = get_db_connection()
    if not conn: raise RuntimeError("Cannot connect to DB")
    try: return fn(conn, *args, **kwargs)
    finally: conn.close()
def api_carta(): return {"list": lambda: _with_conn(mod_carta.list_members), "create": lambda data: _with_conn(mod_carta.create_member, data), "update": lambda rec_id,data: _with_conn(mod_carta.update_member, rec_id, data), "delete": lambda rec_id: _with_conn(mod_carta.delete_member, rec_id)}
def api_profil(): return {"list": lambda: _with_conn(mod_profil_input.list_profils), "create": lambda data: _with_conn(mod_profil_input.create_profil, data), "update": lambda rec_id,data: _with_conn(mod_profil_input.update_profil, rec_id, data), "delete": lambda rec_id: _with_conn(mod_profil_input.delete_profil, rec_id)}
MODULE_SPECS = {"carta":{"title":"Carta Organisasi","api":api_carta(),"fields":[{"name":"id","label":"ID"},{"name":"nama","label":"Nama"},{"name":"jawatan","label":"Jawatan"},{"name":"unit","label":"Unit"}],"required":{"nama","jawatan"}},"profil":{"title":"Profil PK/WM","api":api_profil(),"fields":[{"name":"id","label":"ID"},{"name":"nama","label":"Nama"},{"name":"no_kp","label":"No KP"}],"required":{"nama","no_kp"}}}
def list_profil_records(unit=None,name=None,status=None):
    if unit: return _with_conn(mod_profil_records.list_by_unit, unit)
    if name: return _with_conn(mod_profil_records.search_by_name, name)
    if status == "tidak_aktif": return _with_conn(mod_profil_records.list_inactive)
    return _with_conn(mod_profil_input.list_profils)
