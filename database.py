"""
database.py
------------
SQLite persistence layer for visitor records.

All queries use parameterized statements (the sqlite3 "?" placeholder
style). User-controlled values are NEVER concatenated into SQL strings.
"""

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

from config import Config

SCHEMA = """
CREATE TABLE IF NOT EXISTS visitors (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_name   TEXT    NOT NULL,
    ip_address  TEXT    NOT NULL,
    country     TEXT,
    region      TEXT,
    state       TEXT,
    city        TEXT,
    timezone    TEXT,
    created_at  TEXT    NOT NULL
);
"""


@contextmanager
def get_connection():
    """Yield a SQLite connection, always closed afterwards."""
    conn = sqlite3.connect(Config.DATABASE_PATH)
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    """Create the database file and the visitors table if missing."""
    with get_connection() as conn:
        conn.execute(SCHEMA)
        conn.commit()


def insert_visitor(user_name, ip_address, location):
    """
    Insert a new visitor record.

    `location` is a dict with keys: country, region, state, city, timezone.
    Any missing keys default to "Unknown". Returns the new row id.
    """
    created_at = datetime.now(timezone.utc).isoformat()

    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO visitors
                (user_name, ip_address, country, region, state, city, timezone, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_name,
                ip_address,
                location.get("country", "Unknown"),
                location.get("region", "Unknown"),
                location.get("state", "Unknown"),
                location.get("city", "Unknown"),
                location.get("timezone", "Unknown"),
                created_at,
            ),
        )
        conn.commit()
        return cursor.lastrowid, created_at


def get_all_visitors():
    """
    Retrieve all visitor records from the database, ordered by creation date (newest first).
    
    Returns a list of dictionaries with visitor data.
    """
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(
            "SELECT * FROM visitors ORDER BY created_at DESC"
        )
        return [dict(row) for row in cursor.fetchall()]


def get_visitor_count():
    """Get the total number of visitor records."""
    with get_connection() as conn:
        result = conn.execute("SELECT COUNT(*) as count FROM visitors").fetchone()
        return result[0]


def get_visitor_stats():
    """
    Get aggregated statistics about visitors.
    
    Returns a dict with stats like top countries, regions, etc.
    """
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        stats = {}
        
        # Count by country
        cursor = conn.execute(
            """
            SELECT country, COUNT(*) as count 
            FROM visitors 
            GROUP BY country 
            ORDER BY count DESC 
            LIMIT 10
            """
        )
        stats["by_country"] = [dict(row) for row in cursor.fetchall()]
        
        # Count by city
        cursor = conn.execute(
            """
            SELECT city, COUNT(*) as count 
            FROM visitors 
            GROUP BY city 
            ORDER BY count DESC 
            LIMIT 10
            """
        )
        stats["by_city"] = [dict(row) for row in cursor.fetchall()]
        
        # Count by state/region
        cursor = conn.execute(
            """
            SELECT state, COUNT(*) as count 
            FROM visitors 
            GROUP BY state 
            ORDER BY count DESC 
            LIMIT 10
            """
        )
        stats["by_state"] = [dict(row) for row in cursor.fetchall()]
        
        return stats
