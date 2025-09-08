
from ._helpers import rows_to_dicts
TABLE = 'rekod_ganjaran_table'
def ensure_table(conn):
    cur = conn.cursor()
    cur.execute(f"CREATE TABLE IF NOT EXISTS {TABLE} (id INT AUTO_INCREMENT PRIMARY KEY) ENGINE=InnoDB;")
    conn.commit()
def list_func(conn): cur=conn.cursor(); cur.execute(f"SELECT * FROM {TABLE}"); return rows_to_dicts(cur)
