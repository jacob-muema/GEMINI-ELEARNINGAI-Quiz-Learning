import os
import json
from datetime import datetime
import mysql.connector as mysql_connector

# Load .env file from the same directory as this script
_env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
if os.path.exists(_env_file):
    with open(_env_file) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith('#') and '=' in _line:
                _k, _v = _line.split('=', 1)
                os.environ.setdefault(_k.strip(), _v.strip())

# MySQL connection parameters
MYSQL_HOST     = os.getenv('MYSQL_HOST', 'localhost')
MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'elitorsa_jm')
MYSQL_USER     = os.getenv('MYSQL_USER', 'elitorsa_jm')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')


def get_db():
    """Return a fresh MySQL connection."""
    conn = mysql_connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE,
        charset='utf8mb4'
    )
    return conn


def dict_cursor(conn):
    """Return a cursor that yields rows as dicts (mimics sqlite3.Row behaviour)."""
    return conn.cursor(dictionary=True)


def init_db():
    """Create all required tables in MySQL if they don't already exist."""
    conn = get_db()
    cursor = conn.cursor()

    # ── Users ─────────────────────────────────────────────────────────────────
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id               INT          PRIMARY KEY AUTO_INCREMENT,
        username         VARCHAR(255) UNIQUE NOT NULL,
        email            VARCHAR(255) UNIQUE NOT NULL,
        password_hash    VARCHAR(512) NOT NULL,
        display_name     VARCHAR(255),
        accepted_terms   TINYINT      DEFAULT 1,
        terms_accepted_at TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
        created_at       TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
    ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ''')

    # ── Per-topic progress (JSON blob) ────────────────────────────────────────
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_progress (
        id            INT          PRIMARY KEY AUTO_INCREMENT,
        user_id       INT          NOT NULL,
        topic_id      VARCHAR(255) NOT NULL,
        progress_data TEXT         NOT NULL,
        updated_at    TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
                                   ON UPDATE CURRENT_TIMESTAMP,
        UNIQUE KEY uq_user_topic (user_id, topic_id),
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ''')

    # ── Quiz history ──────────────────────────────────────────────────────────
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS quiz_history (
        id              INT          PRIMARY KEY AUTO_INCREMENT,
        user_id         INT          NOT NULL,
        quiz_id         VARCHAR(255),
        topic_id        VARCHAR(255) NOT NULL,
        topic_name      VARCHAR(255) NOT NULL,
        score           FLOAT        NOT NULL,
        correct_answers INT          NOT NULL,
        total_questions INT          NOT NULL,
        results_json    TEXT,
        created_at      TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ''')

    conn.commit()
    cursor.close()
    conn.close()
    print("MySQL database initialised successfully.")


if __name__ == '__main__':
    init_db()
