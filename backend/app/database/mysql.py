"""MySQL database operations — drop-in replacement for sqlite.py.

Uses PyMySQL (pure Python, no C deps) with autocommit.
All function signatures are identical to the SQLite version.
"""

import json
import uuid
import time
import threading
from datetime import datetime
from typing import Optional, Any

import pymysql
import pymysql.cursors

from app.config import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE

# --- Connection ---

_connection: pymysql.Connection | None = None
_lock = threading.Lock()


def _get_conn() -> pymysql.Connection:
    """Get (or create) the MySQL connection. Auto-reconnects if dropped."""
    global _connection
    if _connection is None:
        _connection = pymysql.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True,
            connect_timeout=10,
        )
    else:
        # Ping to detect dead connections (MySQL wait_timeout)
        try:
            _connection.ping(reconnect=True)
        except pymysql.err.OperationalError:
            _connection = pymysql.connect(
                host=MYSQL_HOST, port=MYSQL_PORT,
                user=MYSQL_USER, password=MYSQL_PASSWORD,
                database=MYSQL_DATABASE, charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=True, connect_timeout=10,
            )
    return _connection


def get_db() -> pymysql.Connection:
    """Get a database connection. (Public, same signature as sqlite.py)"""
    return _get_conn()


# --- Init ---

def init_db():
    """Initialize database tables. Waits for MySQL to be ready, then creates tables idempotently."""
    # Wait for MySQL container to be ready
    for attempt in range(10):
        try:
            conn = _get_conn()
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
            break
        except pymysql.err.OperationalError as e:
            if attempt == 9:
                raise RuntimeError(f"MySQL not ready after 10 attempts: {e}")
            print(f"[mysql] Waiting for MySQL... (attempt {attempt + 1}/10)")
            time.sleep(3)

    conn = _get_conn()
    with conn.cursor() as cursor:
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id VARCHAR(12) PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                username VARCHAR(100) NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(20) DEFAULT 'participant',
                contact_info TEXT,
                tags TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        # Scenarios table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scenarios (
                id VARCHAR(12) PRIMARY KEY,
                creator_id VARCHAR(12) DEFAULT 'anonymous',
                name VARCHAR(255) NOT NULL,
                description TEXT,
                form_schema TEXT NOT NULL,
                match_config TEXT NOT NULL,
                ui_config TEXT NOT NULL,
                status VARCHAR(20) DEFAULT 'draft',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        # Submissions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS submissions (
                id VARCHAR(12) PRIMARY KEY,
                scenario_id VARCHAR(12) NOT NULL,
                user_id VARCHAR(12) DEFAULT 'anonymous',
                form_data TEXT NOT NULL,
                embedding_vector TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (scenario_id) REFERENCES scenarios(id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        # Match results table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS match_results (
                id VARCHAR(12) PRIMARY KEY,
                submission_id VARCHAR(12) NOT NULL,
                matched_submission_id VARCHAR(12) NOT NULL,
                similarity_score DOUBLE NOT NULL,
                explanation TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (submission_id) REFERENCES submissions(id),
                FOREIGN KEY (matched_submission_id) REFERENCES submissions(id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

    print(f"[mysql] Database initialized — {MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}")


def generate_id() -> str:
    return uuid.uuid4().hex[:12]


# --- Scenario CRUD ---

def scenario_create(scenario_data: dict) -> str:
    conn = _get_conn()
    sid = generate_id()
    with conn.cursor() as cursor:
        cursor.execute(
            """INSERT INTO scenarios (id, creator_id, name, description, form_schema, match_config, ui_config, status)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
            (
                sid,
                scenario_data.get("creator_id", "anonymous"),
                scenario_data["name"],
                scenario_data.get("description", ""),
                json.dumps(scenario_data["form_schema"], ensure_ascii=False),
                json.dumps(scenario_data["match_config"], ensure_ascii=False),
                json.dumps(scenario_data["ui_config"], ensure_ascii=False),
                scenario_data.get("status", "draft"),
            ),
        )
    return sid


def scenario_get_all(status: Optional[str] = None) -> list[dict]:
    conn = _get_conn()
    with conn.cursor() as cursor:
        if status:
            cursor.execute(
                "SELECT * FROM scenarios WHERE status = %s ORDER BY created_at DESC", (status,)
            )
        else:
            cursor.execute("SELECT * FROM scenarios ORDER BY created_at DESC")
        rows = cursor.fetchall()
    return [_row_to_scenario(r) for r in rows]


def scenario_get_by_id(sid: str) -> Optional[dict]:
    conn = _get_conn()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM scenarios WHERE id = %s", (sid,))
        row = cursor.fetchone()
    return _row_to_scenario(row) if row else None


def scenario_update(sid: str, update_data: dict) -> bool:
    conn = _get_conn()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM scenarios WHERE id = %s", (sid,))
        if not cursor.fetchone():
            return False

        fields = []
        values = []
        for key in ["name", "description", "status"]:
            if key in update_data and update_data[key] is not None:
                fields.append(f"{key} = %s")
                values.append(update_data[key])
        for key in ["form_schema", "match_config", "ui_config"]:
            if key in update_data and update_data[key] is not None:
                fields.append(f"{key} = %s")
                values.append(json.dumps(update_data[key], ensure_ascii=False))

        if fields:
            values.append(sid)
            cursor.execute(f"UPDATE scenarios SET {', '.join(fields)} WHERE id = %s", values)

    return True


def scenario_delete(sid: str) -> bool:
    conn = _get_conn()
    with _lock:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM scenarios WHERE id = %s", (sid,))
            if not cursor.fetchone():
                return False
            # Manual cascade
            cursor.execute(
                "DELETE FROM match_results WHERE submission_id IN "
                "(SELECT id FROM submissions WHERE scenario_id = %s)", (sid,)
            )
            cursor.execute(
                "DELETE FROM match_results WHERE matched_submission_id IN "
                "(SELECT id FROM submissions WHERE scenario_id = %s)", (sid,)
            )
            cursor.execute("DELETE FROM submissions WHERE scenario_id = %s", (sid,))
            cursor.execute("DELETE FROM scenarios WHERE id = %s", (sid,))
    return True


def scenario_get_submission_count(sid: str) -> int:
    conn = _get_conn()
    with conn.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) as cnt FROM submissions WHERE scenario_id = %s", (sid,))
        row = cursor.fetchone()
    return row["cnt"]


# --- Submission CRUD ---

def submission_create(sub_data: dict) -> str:
    conn = _get_conn()
    sub_id = generate_id()
    with conn.cursor() as cursor:
        cursor.execute(
            """INSERT INTO submissions (id, scenario_id, user_id, form_data, embedding_vector)
               VALUES (%s, %s, %s, %s, %s)""",
            (
                sub_id,
                sub_data["scenario_id"],
                sub_data.get("user_id", "anonymous"),
                json.dumps(sub_data["form_data"], ensure_ascii=False),
                sub_data.get("embedding_vector"),
            ),
        )
    return sub_id


def submission_get_by_scenario(scenario_id: str) -> list[dict]:
    conn = _get_conn()
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT * FROM submissions WHERE scenario_id = %s ORDER BY created_at DESC",
            (scenario_id,),
        )
        rows = cursor.fetchall()
    return [_row_to_submission(r) for r in rows]


def submission_get_by_id(sub_id: str) -> Optional[dict]:
    conn = _get_conn()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM submissions WHERE id = %s", (sub_id,))
        row = cursor.fetchone()
    return _row_to_submission(row) if row else None


def submission_update_embedding(sub_id: str, vector: list[float]) -> bool:
    conn = _get_conn()
    with conn.cursor() as cursor:
        cursor.execute(
            "UPDATE submissions SET embedding_vector = %s WHERE id = %s",
            (json.dumps(vector), sub_id),
        )
    return True


def submission_get_all_with_embeddings(scenario_id: str) -> list[dict]:
    conn = _get_conn()
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT * FROM submissions WHERE scenario_id = %s AND embedding_vector IS NOT NULL",
            (scenario_id,),
        )
        rows = cursor.fetchall()
    return [_row_to_submission(r) for r in rows]


# --- Match Result CRUD ---

def match_result_save(
    submission_id: str,
    matched_submission_id: str,
    similarity_score: float,
    explanation: str = "",
) -> str:
    conn = _get_conn()
    mid = generate_id()
    with conn.cursor() as cursor:
        cursor.execute(
            """INSERT INTO match_results (id, submission_id, matched_submission_id, similarity_score, explanation)
               VALUES (%s, %s, %s, %s, %s)""",
            (mid, submission_id, matched_submission_id, similarity_score, explanation),
        )
    return mid


def match_result_get_by_submission(submission_id: str) -> list[dict]:
    conn = _get_conn()
    with conn.cursor() as cursor:
        cursor.execute(
            """SELECT mr.*, s.form_data as matched_form_data
               FROM match_results mr
               JOIN submissions s ON mr.matched_submission_id = s.id
               WHERE mr.submission_id = %s
               ORDER BY mr.similarity_score DESC""",
            (submission_id,),
        )
        rows = cursor.fetchall()
    return [_row_to_match(r) for r in rows]


# --- User CRUD ---

def user_create(email: str, username: str, password_hash: str, role: str = "participant",
                contact_info: str = "", tags: list = None) -> str:
    conn = _get_conn()
    uid = generate_id()
    with conn.cursor() as cursor:
        cursor.execute(
            "INSERT INTO users (id, email, username, password_hash, role, contact_info, tags) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (uid, email, username, password_hash, role, contact_info,
             json.dumps(tags or [], ensure_ascii=False)),
        )
    return uid


def user_get_by_email(email: str) -> dict | None:
    conn = _get_conn()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        row = cursor.fetchone()
    return _row_to_user(row) if row else None


def user_get_by_id(uid: str) -> dict | None:
    conn = _get_conn()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM users WHERE id = %s", (uid,))
        row = cursor.fetchone()
    return _row_to_user(row) if row else None


def user_get_all(page: int = 1, limit: int = 20, role_filter: str = "") -> tuple[list[dict], int]:
    conn = _get_conn()
    with conn.cursor() as cursor:
        if role_filter:
            cursor.execute("SELECT COUNT(*) FROM users WHERE role = %s", (role_filter,))
            total = cursor.fetchone()["COUNT(*)"]
            offset = (page - 1) * limit
            cursor.execute(
                "SELECT * FROM users WHERE role = %s ORDER BY created_at DESC LIMIT %s OFFSET %s",
                (role_filter, limit, offset),
            )
        else:
            cursor.execute("SELECT COUNT(*) FROM users")
            total = cursor.fetchone()["COUNT(*)"]
            offset = (page - 1) * limit
            cursor.execute(
                "SELECT * FROM users ORDER BY created_at DESC LIMIT %s OFFSET %s",
                (limit, offset),
            )
        rows = cursor.fetchall()
    return [_row_to_user(r) for r in rows], total


def user_update_role(uid: str, role: str) -> bool:
    conn = _get_conn()
    with conn.cursor() as cursor:
        cursor.execute("UPDATE users SET role = %s WHERE id = %s", (role, uid))
    return True


def user_update_profile(uid: str, update_data: dict) -> bool:
    conn = _get_conn()
    with conn.cursor() as cursor:
        fields = []
        values = []
        for key in ["username", "contact_info"]:
            if key in update_data and update_data[key] is not None:
                fields.append(f"{key} = %s")
                values.append(update_data[key])
        if "tags" in update_data and update_data["tags"] is not None:
            fields.append("tags = %s")
            values.append(json.dumps(update_data["tags"], ensure_ascii=False))
        if fields:
            values.append(uid)
            cursor.execute(f"UPDATE users SET {', '.join(fields)} WHERE id = %s", values)
    return True


def user_count() -> int:
    conn = _get_conn()
    with conn.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM users")
        row = cursor.fetchone()
    return row["COUNT(*)"] if row else 0


def user_count_by_role(role: str) -> int:
    conn = _get_conn()
    with conn.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM users WHERE role = %s", (role,))
        row = cursor.fetchone()
    return row["COUNT(*)"] if row else 0


# --- Submission user-scoped queries ---

def submission_get_by_user(user_id: str) -> list[dict]:
    conn = _get_conn()
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT * FROM submissions WHERE user_id = %s ORDER BY created_at DESC",
            (user_id,),
        )
        rows = cursor.fetchall()
    return [_row_to_submission(r) for r in rows]


def match_result_get_by_user(user_id: str) -> list[dict]:
    conn = _get_conn()
    with conn.cursor() as cursor:
        cursor.execute(
            """SELECT mr.*, s.form_data as matched_form_data, u.username as matched_user_name
               FROM match_results mr
               JOIN submissions s ON mr.matched_submission_id = s.id
               LEFT JOIN users u ON s.user_id = u.id
               WHERE mr.submission_id IN (SELECT id FROM submissions WHERE user_id = %s)
               ORDER BY mr.similarity_score DESC""",
            (user_id,),
        )
        rows = cursor.fetchall()
    return [_row_to_match(r) for r in rows]


# --- Admin stats ---

def admin_get_stats() -> dict:
    conn = _get_conn()
    with conn.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM scenarios")
        total_scenarios = cursor.fetchone()["COUNT(*)"]

        cursor.execute("SELECT COUNT(*) FROM scenarios WHERE status='active'")
        active_scenarios = cursor.fetchone()["COUNT(*)"]

        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()["COUNT(*)"]

        cursor.execute("SELECT COUNT(*) FROM users WHERE role='participant'")
        participant_count = cursor.fetchone()["COUNT(*)"]

        cursor.execute("SELECT COUNT(*) FROM users WHERE role='designer'")
        designer_count = cursor.fetchone()["COUNT(*)"]

        cursor.execute("SELECT COUNT(*) FROM users WHERE role='admin'")
        admin_count = cursor.fetchone()["COUNT(*)"]

        cursor.execute("SELECT COUNT(*) FROM submissions")
        total_submissions = cursor.fetchone()["COUNT(*)"]

        cursor.execute("SELECT COUNT(*) FROM match_results")
        total_matches = cursor.fetchone()["COUNT(*)"]

        cursor.execute(
            "SELECT COUNT(*) FROM users WHERE created_at >= NOW() - INTERVAL 7 DAY"
        )
        recent_users = cursor.fetchone()["COUNT(*)"]

        cursor.execute(
            "SELECT COUNT(*) FROM submissions WHERE created_at >= NOW() - INTERVAL 7 DAY"
        )
        recent_submissions = cursor.fetchone()["COUNT(*)"]

    return {
        "total_scenarios": total_scenarios,
        "active_scenarios": active_scenarios,
        "total_users": total_users,
        "users_by_role": {
            "participant": participant_count,
            "designer": designer_count,
            "admin": admin_count,
        },
        "total_submissions": total_submissions,
        "total_matches": total_matches,
        "recent_users_7d": recent_users,
        "recent_submissions_7d": recent_submissions,
    }


# --- Row helpers ---

def _dt_to_str(val) -> str:
    """Convert DATETIME from MySQL to ISO string (same format as SQLite output)."""
    if val is None:
        return ""
    if isinstance(val, datetime):
        return val.strftime("%Y-%m-%d %H:%M:%S")
    return str(val)


def _row_to_user(row) -> dict:
    return {
        "id": row["id"],
        "email": row["email"],
        "username": row["username"],
        "password_hash": row["password_hash"],
        "role": row["role"],
        "contact_info": row.get("contact_info", "") or "",
        "tags": json.loads(row["tags"]) if row.get("tags") else [],
        "created_at": _dt_to_str(row["created_at"]),
    }


def _row_to_scenario(row) -> dict:
    return {
        "id": row["id"],
        "creator_id": row["creator_id"],
        "name": row["name"],
        "description": row["description"],
        "form_schema": json.loads(row["form_schema"]),
        "match_config": json.loads(row["match_config"]),
        "ui_config": json.loads(row["ui_config"]),
        "status": row["status"],
        "created_at": _dt_to_str(row["created_at"]),
    }


def _row_to_submission(row) -> dict:
    return {
        "id": row["id"],
        "scenario_id": row["scenario_id"],
        "user_id": row["user_id"],
        "form_data": json.loads(row["form_data"]),
        "embedding_vector": json.loads(row["embedding_vector"]) if row["embedding_vector"] else None,
        "created_at": _dt_to_str(row["created_at"]),
    }


def _row_to_match(row) -> dict:
    result = {
        "id": row["id"],
        "submission_id": row["submission_id"],
        "matched_submission_id": row["matched_submission_id"],
        "similarity_score": row["similarity_score"],
        "explanation": row["explanation"] or "",
        "created_at": _dt_to_str(row["created_at"]),
    }
    if "matched_form_data" in row and row["matched_form_data"]:
        result["matched_form_data"] = json.loads(row["matched_form_data"])
    if "matched_user_name" in row and row["matched_user_name"]:
        result["matched_user_name"] = row["matched_user_name"]
    return result
