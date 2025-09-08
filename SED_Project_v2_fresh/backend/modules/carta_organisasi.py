
from ._helpers import rows_to_dicts
TABLE = 'carta_organisasi'
def ensure_table(conn):
    cur = conn.cursor()
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE} (
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
def create_member(conn, data):
    cur = conn.cursor()
    cur.execute(f"INSERT INTO {TABLE} (nama,jawatan,unit,supervisor_id,telefon,email) VALUES (%s,%s,%s,%s,%s,%s)",
                (data.get('nama'),data.get('jawatan'),data.get('unit'),data.get('supervisor_id'),data.get('telefon'),data.get('email')))
    conn.commit(); return cur.lastrowid
def update_member(conn, rec_id, data):
    fields = [k for k in ['nama','jawatan','unit','supervisor_id','telefon','email'] if k in data]
    if not fields: return False
    set_clause = ','.join(f"{k}=%s" for k in fields)
    vals = [data[k] for k in fields] + [rec_id]
    cur = conn.cursor(); cur.execute(f"UPDATE {TABLE} SET {set_clause} WHERE id=%s", vals); conn.commit(); return cur.rowcount>0
def delete_member(conn, rec_id):
    cur = conn.cursor(); cur.execute(f"DELETE FROM {TABLE} WHERE id=%s", (rec_id,)); conn.commit(); return cur.rowcount>0
def list_members(conn):
    cur = conn.cursor(); cur.execute(f"SELECT * FROM {TABLE} ORDER BY id DESC"); return rows_to_dicts(cur)
