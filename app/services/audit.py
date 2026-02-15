"""
Audit logging service using sqlite backend.

Provides a helper function to record CRUD operations into the
audit_logs table. Accepts a raw sqlite3 connection.
"""

import json
import sqlite3
from typing import Dict, Any, Optional


def record_audit(conn: sqlite3.Connection, snapshot_id: int, entity_type: str, entity_key: str,
                 action: str, before: Optional[Dict[str, Any]], after: Optional[Dict[str, Any]],
                 actor: str = 'admin') -> None:
    changed_fields = None
    if before is not None and after is not None:
        before_keys = set(before.keys())
        after_keys = set(after.keys())
        changed_fields = ','.join(sorted(list(before_keys.union(after_keys))))
    conn.execute(
        """
        INSERT INTO audit_logs (snapshot_id, entity_type, entity_key, action, changed_fields, before_json, after_json, actor)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            snapshot_id,
            entity_type,
            entity_key,
            action,
            changed_fields,
            json.dumps(before) if before is not None else None,
            json.dumps(after) if after is not None else None,
            actor,
        )
    )
    conn.commit()