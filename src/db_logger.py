"""
Database logging system for scan operations
"""
import json
import logging
from typing import Dict, Any, Optional
from src.database import db

class DatabaseLogger:
    """Logger that writes to database instead of files."""
    
    def __init__(self, session_id: str, component: str = "file_scanner"):
        self.session_id = session_id
        self.component = component
        self._error_count = 0
        self._warning_count = 0
    
    def get_error_count(self) -> int:
        """Get current error count."""
        return self._error_count
    
    def get_warning_count(self) -> int:
        """Get current warning count."""
        return self._warning_count
    
    def log(self, level: str, message: str, file_path: Optional[str] = None, 
            error_details: Optional[Dict[str, Any]] = None):
        """Log message to database."""
        try:
            with db.get_cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO scan_logs 
                    (session_id, log_level, component, message, file_path, error_details)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        self.session_id,
                        level.upper(),
                        self.component,
                        message,
                        file_path,
                        json.dumps(error_details) if error_details else None
                    )
                )
        except Exception as e:
            # Fallback to standard logging if DB fails
            logging.getLogger().error(f"Database logging failed: {e}")
    
    def info(self, message: str, file_path: Optional[str] = None):
        self.log("INFO", message, file_path)
    
    def warning(self, message: str, file_path: Optional[str] = None):
        self.log("WARNING", message, file_path)
    
    def error(self, message: str, file_path: Optional[str] = None, 
              error_details: Optional[Dict[str, Any]] = None):
        self.log("ERROR", message, file_path, error_details)
    
    def debug(self, message: str, file_path: Optional[str] = None):
        # Only log debug in verbose mode
        pass  # Skip debug for performance 