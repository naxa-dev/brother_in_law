"""
Lightweight SQLite database access module.

This module provides helper functions to open database connections and
initialize the schema. It does not rely on SQLAlchemy and instead
uses Python's built-in sqlite3 module. Each connection uses a row
factory so that query results can be accessed as dictionaries.
"""

import os
import sqlite3
from datetime import datetime

# Path to the SQLite database file. Stored under the db directory.
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'db', 'ax.db')
DB_PATH = os.path.normpath(DB_PATH)


def get_connection() -> sqlite3.Connection:
    """Return a connection to the SQLite database.

    The connection uses row_factory so rows behave like dictionaries.  To
    support FastAPI's async view handlers running on thread pool executors,
    the SQLite connection is opened with `check_same_thread=False`. Without
    this flag, using a connection across different threads raises
    `sqlite3.ProgrammingError`. Setting the flag disables SQLite's
    single‑thread check and allows the same connection object to be used
    by the FastAPI request handlers across threads. Because each request
    obtains its own connection via dependency injection, this trade‑off
    is acceptable and does not share a connection between concurrent
    requests.
    """
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Initialize database tables if they do not exist."""
    # Ensure directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with get_connection() as conn:
        c = conn.cursor()
        # snapshots table
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS snapshots (
                snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_date TEXT UNIQUE NOT NULL,
                uploaded_at TEXT NOT NULL,
                source_filename TEXT NOT NULL
            )
            """
        )
        # champions
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS champions (
                champion_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                is_active INTEGER DEFAULT 1
            )
            """
        )
        # strategy_categories
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS strategy_categories (
                strategy_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                is_active INTEGER DEFAULT 1
            )
            """
        )
        # projects
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS projects (
                snapshot_id INTEGER NOT NULL,
                project_id TEXT NOT NULL,
                project_name TEXT NOT NULL,
                champion_id INTEGER,
                strategy_id INTEGER,
                org_unit TEXT,
                current_status TEXT NOT NULL,
                proposed_month TEXT,
                approved_month TEXT,
                PRIMARY KEY (snapshot_id, project_id),
                FOREIGN KEY (snapshot_id) REFERENCES snapshots(snapshot_id),
                FOREIGN KEY (champion_id) REFERENCES champions(champion_id),
                FOREIGN KEY (strategy_id) REFERENCES strategy_categories(strategy_id)
            )
            """
        )
        # project_monthly_events
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS project_monthly_events (
                snapshot_id INTEGER NOT NULL,
                month_key TEXT NOT NULL,
                project_id TEXT NOT NULL,
                champion_id INTEGER,
                is_new_proposal INTEGER DEFAULT 0,
                is_approved INTEGER DEFAULT 0,
                note TEXT,
                PRIMARY KEY (snapshot_id, month_key, project_id),
                FOREIGN KEY (snapshot_id) REFERENCES snapshots(snapshot_id),
                FOREIGN KEY (project_id) REFERENCES projects(project_id),
                FOREIGN KEY (champion_id) REFERENCES champions(champion_id)
            )
            """
        )
        # audit_logs
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_logs (
                audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_id INTEGER NOT NULL,
                entity_type TEXT NOT NULL,
                entity_key TEXT NOT NULL,
                action TEXT NOT NULL,
                changed_fields TEXT,
                before_json TEXT,
                after_json TEXT,
                actor TEXT NOT NULL,
                acted_at TEXT NOT NULL DEFAULT (DATETIME('now')),
                FOREIGN KEY (snapshot_id) REFERENCES snapshots(snapshot_id)
            )
            """
        )
        conn.commit()