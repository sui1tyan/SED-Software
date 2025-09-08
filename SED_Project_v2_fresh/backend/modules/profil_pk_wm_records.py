
from ._helpers import rows_to_dicts
TABLE='profil_pk_wm'
def list_by_unit(conn, unit): cur=conn.cursor(); cur.execute(f"SELECT * FROM {TABLE} WHERE unit=%s ORDER BY id DESC",(unit,)); return rows_to_dicts(cur)
def search_by_name(conn, name): cur=conn.cursor(); cur.execute(f"SELECT * FROM {TABLE} WHERE nama LIKE %s ORDER BY id DESC",(f"%{name}%",)); return rows_to_dicts(cur)
def list_inactive(conn): cur=conn.cursor(); cur.execute(f"SELECT * FROM {TABLE} WHERE status='tidak_aktif' ORDER BY id DESC"); return rows_to_dicts(cur)
