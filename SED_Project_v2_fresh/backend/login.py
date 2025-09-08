diff --git a/SED_Project_v2_fresh/backend/login.py b/SED_Project_v2_fresh/backend/login.py
index c5a6b3361049b234cde90922af8aa0e69d566a34..94baab1b699ba9399901438d8c798e4afcda6663 100644
--- a/SED_Project_v2_fresh/backend/login.py
+++ b/SED_Project_v2_fresh/backend/login.py
@@ -1,54 +1,55 @@
 
import bcrypt
 from .db import get_db_connection
 
 def _hpw(pw: str) -> str:
     return bcrypt.hashpw(pw.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
 
 def login(username: str, password: str):
     conn = get_db_connection()
     if not conn:
         return None
     try:
         cur = conn.cursor(dictionary=True)
         cur.execute("SELECT id, username, password, role FROM users WHERE username=%s", (username,))
         row = cur.fetchone()
         if not row:
             return None
             if bcrypt.checkpw(password.encode("utf-8"), row["password"].encode("utf-8")):
             return {"id": row["id"], "username": row["username"], "role": row["role"]}
         return None
     finally:
         conn.close()
 
 def create_user(username: str, password: str, role: str = "user"):
     conn = get_db_connection()
     if not conn:
         return False
     try:
         cur = conn.cursor()
         hashed_pw = _hpw(password)
         cur.execute("INSERT IGNORE INTO users (username, password, role) VALUES (%s,%s,%s)",
                    (username, hashed_pw, role))
         conn.commit()
         return cur.rowcount > 0
     finally:
         conn.close()
 
 def delete_user(requestor_username: str, username: str):
     """Delete a user if the requestor is host/admin and not deleting themselves."""
     conn = get_db_connection()
     if not conn:
         return False
     try:
         cur = conn.cursor(dictionary=True)
         cur.execute("SELECT role FROM users WHERE username=%s", (requestor_username,))
         r = cur.fetchone()
         if not r or r["role"] not in ("host","admin"):
             return False
         if requestor_username == username:
             return False
         cur.execute("DELETE FROM users WHERE username=%s", (username,))
         conn.commit()
         return cur.rowcount > 0
     finally:
         conn.close()
