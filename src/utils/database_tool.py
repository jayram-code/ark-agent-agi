"""
Database Query Tool for ARK Agent AGI
Execute safe read-only SQL queries
"""

import sqlite3
from typing import Dict, Any, List
from utils.logging_utils import log_event


class DatabaseTool:
    """
    Safe read-only database query execution
    """

    def __init__(self, db_path: str = "data/ark_agent.db"):
        self.db_path = db_path
        log_event("DatabaseTool", {"event": "initialized", "db_path": db_path})

    def query(self, sql: str, params: tuple = ()) -> Dict[str, Any]:
        """
        Execute a read-only SQL query

        Args:
            sql: SQL query (SELECT only)
            params: Query parameters

        Returns:
            Query results
        """
        # Security: Only allow SELECT statements
        if not sql.strip().upper().startswith("SELECT"):
            return {"success": False, "error": "Only SELECT queries are allowed for safety"}

        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(sql, params)
            rows = cursor.fetchall()

            # Convert to list of dicts
            results = [dict(row) for row in rows]

            conn.close()

            log_event("DatabaseTool", {"event": "query_success", "row_count": len(results)})

            return {"success": True, "rows": results, "count": len(results)}

        except Exception as e:
            log_event("DatabaseTool", {"event": "query_error", "error": str(e)})
            return {"success": False, "error": str(e), "error_type": type(e).__name__}


database_tool = DatabaseTool()
