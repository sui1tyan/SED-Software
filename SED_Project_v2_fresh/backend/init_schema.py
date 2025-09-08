
import mysql.connector
from .db import DB_CONFIG, get_db_connection

def _create_database_if_missing():
    cfg = dict(DB_CONFIG)
    dbname = cfg.pop("database", None)
    try:
        conn = mysql.connector.connect(**{k: cfg[k] for k in ("host","port","user","password")})
        cur = conn.cursor()
        cur.execute(f"CREATE DATABASE IF NOT EXISTS `{dbname}` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        conn.commit()
    finally:
        try: conn.close()
        except: pass

def _ensure_users(conn):
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            password VARCHAR(128) NOT NULL,
            role ENUM('host','admin','user') DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)
    conn.commit()
    import hashlib
    def hpw(p): return hashlib.sha256(p.encode('utf-8')).hexdigest()
    for u,pw,role in [("admin","admin123","admin"), ("alif","alif123","host")]:
        try:
            cur.execute("INSERT IGNORE INTO users (username, password, role) VALUES (%s,%s,%s)", (u, hpw(pw), role))
        except Exception:
            pass
    conn.commit()

def _ensure_module_tables(conn):
    from .modules import (carta_organisasi, profil_pk_wm_input, bkl_input, laporan_jenayah,
                          ganjaran_pk_wm, rekod_ganjaran, jurnal_sed)
    for mod in (carta_organisasi, profil_pk_wm_input, bkl_input, laporan_jenayah,
                ganjaran_pk_wm, rekod_ganjaran, jurnal_sed):
        try:
            if hasattr(mod, "ensure_table"):
                mod.ensure_table(conn)
        except Exception as e:
            print("Warning: ensure_table failed for", mod, e)

def main():
    try:
        _create_database_if_missing()
        conn = get_db_connection()
        if not conn:
            print("Failed to connect to DB using settings in config.json")
            return False
        try:
            _ensure_users(conn)
            _ensure_module_tables(conn)
        finally:
            conn.close()
        print("Database schema ensured and default users seeded.")
        return True
    except Exception as e:
        print("init_schema error:", e)
        return False

if __name__ == "__main__":
    main()
