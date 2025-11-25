"""
Conversation Logger
Logs all voice interactions for context and system improvement
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
import json
import sqlite3
import os
from pathlib import Path


@dataclass
class ConversationLog:
    """Structure for logging a conversation turn"""
    session_id: str
    user_id: str
    turn_number: int
    user_input: str
    assistant_response: str
    intent: str
    extracted_parameters: Dict[str, Any] = field(default_factory=dict)
    command_type: str = ""
    success: bool = True
    error_message: str = ""
    response_time_ms: float = 0.0
    audio_duration_ms: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class ConversationLogger:
    """
    Logs all voice interactions to SQLite database
    Enables analysis and improvement of voice assistant
    """
    
    def __init__(self, db_path: str = ".config/voice_conversations.db"):
        self.db_path = db_path
        self._ensure_database_exists()
    
    def _ensure_database_exists(self) -> None:
        """Create database and tables if they don't exist"""
        os.makedirs(os.path.dirname(self.db_path) or '.config', exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Conversations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                turn_number INTEGER NOT NULL,
                user_input TEXT NOT NULL,
                assistant_response TEXT NOT NULL,
                intent TEXT,
                command_type TEXT,
                extracted_parameters JSON,
                success BOOLEAN DEFAULT 1,
                error_message TEXT,
                response_time_ms REAL DEFAULT 0.0,
                audio_duration_ms REAL DEFAULT 0.0,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            )
        """)
        
        # Sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                end_time DATETIME,
                device TEXT,
                notes TEXT
            )
        """)
        
        # Intents summary table (for quick stats)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS intent_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                intent TEXT NOT NULL,
                count INTEGER DEFAULT 1,
                success_count INTEGER DEFAULT 0,
                avg_response_time_ms REAL DEFAULT 0.0,
                date DATE DEFAULT CURRENT_DATE
            )
        """)
        
        # Create indexes for better query performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_session_user 
            ON conversations(session_id, user_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_timestamp 
            ON conversations(user_id, timestamp)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_intent 
            ON conversations(intent)
        """)
        
        conn.commit()
        conn.close()
    
    def start_session(self, session_id: str, user_id: str, device: str = "web") -> None:
        """Start a new conversation session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO sessions (id, user_id, device)
            VALUES (?, ?, ?)
        """, (session_id, user_id, device))
        
        conn.commit()
        conn.close()
    
    def end_session(self, session_id: str, notes: str = "") -> None:
        """End a conversation session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE sessions
            SET end_time = CURRENT_TIMESTAMP, notes = ?
            WHERE id = ?
        """, (notes, session_id))
        
        conn.commit()
        conn.close()
    
    def log_turn(self, log: ConversationLog) -> int:
        """
        Log a conversation turn
        
        Args:
            log: ConversationLog object
            
        Returns:
            ID of logged entry
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO conversations (
                session_id, user_id, turn_number, user_input, 
                assistant_response, intent, command_type, extracted_parameters,
                success, error_message, response_time_ms, audio_duration_ms,
                timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            log.session_id,
            log.user_id,
            log.turn_number,
            log.user_input,
            log.assistant_response,
            log.intent,
            log.command_type,
            json.dumps(log.extracted_parameters),
            log.success,
            log.error_message,
            log.response_time_ms,
            log.audio_duration_ms,
            log.timestamp
        ))
        
        entry_id = cursor.lastrowid
        
        # Update intent stats
        self._update_intent_stats(cursor, log.user_id, log.intent, log.success, log.response_time_ms)
        
        conn.commit()
        conn.close()
        
        return entry_id
    
    def _update_intent_stats(
        self, 
        cursor: sqlite3.Cursor, 
        user_id: str, 
        intent: str, 
        success: bool,
        response_time_ms: float
    ) -> None:
        """Update intent statistics"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        cursor.execute("""
            INSERT INTO intent_stats (user_id, intent, count, success_count, avg_response_time_ms, date)
            VALUES (?, ?, 1, ?, ?, ?)
            ON CONFLICT(user_id, intent, date) DO UPDATE SET
                count = count + 1,
                success_count = success_count + ?,
                avg_response_time_ms = (avg_response_time_ms * (count - 1) + ?) / count
        """, (
            user_id, intent, 1 if success else 0, response_time_ms, today,
            1 if success else 0, response_time_ms
        ))
    
    def get_session_history(self, session_id: str) -> list:
        """Get all turns in a session"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM conversations
            WHERE session_id = ?
            ORDER BY turn_number ASC
        """, (session_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_user_statistics(self, user_id: str, days: int = 7) -> Dict[str, Any]:
        """Get usage statistics for a user"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Total turns
        cursor.execute("""
            SELECT COUNT(*) as total_turns FROM conversations
            WHERE user_id = ? AND timestamp > datetime('now', '-' || ? || ' days')
        """, (user_id, days))
        total_turns = cursor.fetchone()['total_turns']
        
        # Success rate
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful
            FROM conversations
            WHERE user_id = ? AND timestamp > datetime('now', '-' || ? || ' days')
        """, (user_id, days))
        result = cursor.fetchone()
        success_rate = (result['successful'] / result['total'] * 100) if result['total'] > 0 else 0
        
        # Intent breakdown
        cursor.execute("""
            SELECT intent, COUNT(*) as count
            FROM conversations
            WHERE user_id = ? AND timestamp > datetime('now', '-' || ? || ' days')
            GROUP BY intent
            ORDER BY count DESC
        """, (user_id, days))
        intent_breakdown = [dict(row) for row in cursor.fetchall()]
        
        # Average response time
        cursor.execute("""
            SELECT AVG(response_time_ms) as avg_response_time
            FROM conversations
            WHERE user_id = ? AND timestamp > datetime('now', '-' || ? || ' days')
        """, (user_id, days))
        avg_response = cursor.fetchone()['avg_response_time'] or 0
        
        conn.close()
        
        return {
            'user_id': user_id,
            'period_days': days,
            'total_turns': total_turns,
            'success_rate': round(success_rate, 2),
            'average_response_time_ms': round(avg_response, 2),
            'intent_breakdown': intent_breakdown
        }
    
    def get_common_errors(self, user_id: str, limit: int = 10) -> list:
        """Get most common errors for a user"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                error_message, 
                COUNT(*) as count,
                intent
            FROM conversations
            WHERE user_id = ? AND success = 0 AND error_message != ''
            GROUP BY error_message
            ORDER BY count DESC
            LIMIT ?
        """, (user_id, limit))
        
        errors = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return errors
    
    def export_session_transcript(self, session_id: str, format: str = "json") -> str:
        """
        Export session as readable transcript
        
        Args:
            session_id: Session ID to export
            format: Output format ('json' or 'text')
            
        Returns:
            Formatted transcript
        """
        history = self.get_session_history(session_id)
        
        if format == "json":
            return json.dumps(history, indent=2, default=str)
        
        elif format == "text":
            lines = []
            for turn in history:
                lines.append(f"[{turn['timestamp']}] User: {turn['user_input']}")
                lines.append(f"Assistant: {turn['assistant_response']}")
                if turn['intent']:
                    lines.append(f"Intent: {turn['intent']}")
                lines.append("")
            return "\n".join(lines)
        
        else:
            raise ValueError(f"Unknown format: {format}")
    
    def cleanup_old_data(self, days_to_keep: int = 90) -> int:
        """
        Delete old conversation logs beyond retention period
        
        Args:
            days_to_keep: Number of days to keep
            
        Returns:
            Number of rows deleted
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM conversations
            WHERE timestamp < datetime('now', '-' || ? || ' days')
        """, (days_to_keep,))
        
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        return deleted_count
