"""
Session Logger for ARK Agent AGI
Logs all messages for session replay and debugging
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Any


class SessionLogger:
    """
    Log messages for each session to enable replay and debugging
    """

    def __init__(self, sessions_dir: str = "data/sessions"):
        self.sessions_dir = sessions_dir
        os.makedirs(self.sessions_dir, exist_ok=True)

    def log_message(self, session_id: str, message: Dict[str, Any]):
        """Log a message to the session file"""
        session_file = os.path.join(self.sessions_dir, f"{session_id}.json")
        
        # Load existing messages
        messages = []
        if os.path.exists(session_file):
            try:
                with open(session_file, "r") as f:
                    messages = json.load(f)
            except (json.JSONDecodeError, IOError):
                messages = []
        
        # Append new message
        message_copy = message.copy()
        message_copy["logged_at"] = datetime.utcnow().isoformat()
        messages.append(message_copy)
        
        # Save
        try:
            with open(session_file, "w") as f:
                json.dump(messages, f, indent=2)
        except IOError:
            pass

    def get_session(self, session_id: str) -> List[Dict[str, Any]]:
        """Retrieve all messages for a session"""
        session_file = os.path.join(self.sessions_dir, f"{session_id}.json")
        
        if not os.path.exists(session_file):
            return []
        
        try:
            with open(session_file, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []

    def list_sessions(self) -> List[str]:
        """List all session IDs"""
        if not os.path.exists(self.sessions_dir):
            return []
        
        sessions = []
        for filename in os.listdir(self.sessions_dir):
            if filename.endswith(".json"):
                sessions.append(filename[:-5])  # Remove .json extension
        
        return sorted(sessions)


# Global instance
session_logger = SessionLogger()
