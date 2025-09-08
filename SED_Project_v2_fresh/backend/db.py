
import mysql.connector, json, pathlib, sys

BASE_DIR = pathlib.Path(getattr(sys, "_MEIPASS", pathlib.Path(__file__).resolve().parents[1]))
CONFIG_PATH = BASE_DIR / "config.json"

DEFAULT_DB = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "",
    "database": "sed_db",
    "autocommit": True
}

def load_config():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        db = cfg.get("db", {})
        result = {
            "host": db.get("host", DEFAULT_DB["host"]),
            "port": int(db.get("port", DEFAULT_DB["port"])),
            "user": db.get("user", DEFAULT_DB["user"]),
            "password": db.get("password", DEFAULT_DB["password"]),
            "database": db.get("database", DEFAULT_DB["database"]),
            "autocommit": True
        }
        return result
    except Exception as e:
        print("Warning: could not read config.json, using defaults.", e)
        return dict(DEFAULT_DB)

DB_CONFIG = load_config()

def get_db_connection():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Exception as e:
        print("DB connection error:", e)
        return None
