
from ._helpers import rows_to_dicts
TABLE = 'profil_pk_wm'
def ensure_table(conn):
    cur = conn.cursor(); cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE} (
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
    """); conn.commit()
def create_profil(conn, data):
    cur = conn.cursor(); cur.execute(f"INSERT INTO {TABLE} (nama,no_kp,pangkat,unit,telefon,alamat,tarikh_masuk,status) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                (data.get('nama'),data.get('no_kp'),data.get('pangkat'),data.get('unit'),data.get('telefon'),data.get('alamat'),data.get('tarikh_masuk'),data.get('status') or 'aktif')); conn.commit(); return cur.lastrowid
def update_profil(conn, rec_id, data):
    fields = [k for k in ['nama','no_kp','pangkat','unit','telefon','alamat','tarikh_masuk','status'] if k in data]
    if not fields: return False
    set_clause = ','.join(f"{k}=%s" for k in fields)
    vals = [data[k] for k in fields] + [rec_id]
    cur = conn.cursor(); cur.execute(f"UPDATE {TABLE} SET {set_clause} WHERE id=%s", vals); conn.commit(); return cur.rowcount>0
def delete_profil(conn, rec_id):
    cur = conn.cursor(); cur.execute(f"DELETE FROM {TABLE} WHERE id=%s", (rec_id,)); conn.commit(); return cur.rowcount>0
def list_profils(conn, status=None):
    cur = conn.cursor()
    if status: cur.execute(f"SELECT * FROM {TABLE} WHERE status=%s ORDER BY id DESC", (status,))
    else: cur.execute(f"SELECT * FROM {TABLE} ORDER BY id DESC")
    return rows_to_dicts(cur)
