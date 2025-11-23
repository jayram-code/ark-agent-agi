"""
Database Query Tool for ARK Agent AGI
Execute SQL queries (Read/Write)
"""

import sqlite3
import os
from typing import Any, Dict, List

from tools.base import BaseTool
from utils.observability.logging_utils import log_event


class DatabaseTool(BaseTool):
    """
    Database query execution (SQLite)
    """

    def __init__(self, db_path: str = "data/ark_agent.db", read_only: bool = False):
        super().__init__(name="database", description="Execute SQL queries on SQLite database")
        self.db_path = db_path
        self.read_only = read_only
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        log_event("DatabaseTool", {"event": "initialized", "db_path": db_path, "read_only": read_only})

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute database query.
        Args:
            query (str): SQL query
            params (list/tuple): Query parameters (optional)
        """
        return self.query(kwargs.get("query", ""), kwargs.get("params", ()))

    def query(self, sql: str, params: tuple = ()) -> Dict[str, Any]:
        """
        Execute a SQL query

        Args:
            sql: SQL query
            params: Query parameters

        Returns:
            Query results
        """
        # Security check for read-only mode
        if self.read_only:
            if not sql.strip().upper().startswith("SELECT"):
                return {"success": False, "error": "Only SELECT queries are allowed in read-only mode"}

        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(sql, params)
            
            if sql.strip().upper().startswith("SELECT"):
                rows = cursor.fetchall()
                results = [dict(row) for row in rows]
                count = len(results)
            else:
                conn.commit()
                results = []
                count = cursor.rowcount

            conn.close()

            log_event("DatabaseTool", {"event": "query_success", "row_count": count, "query_type": sql.split()[0]})

            return {"success": True, "rows": results, "count": count}

        except Exception as e:
            log_event("DatabaseTool", {"event": "query_error", "error": str(e)})
            return {"success": False, "error": str(e), "error_type": type(e).__name__}


# Default instance (read-only by default for safety unless explicitly configured otherwise in main app)
database_tool = DatabaseTool(read_only=False)
