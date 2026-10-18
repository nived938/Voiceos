import sqlite3
import json
import uuid
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger("VoiceOS.Database")

class DatabaseManager:
    """
    SQLite persistence layer mirroring the investigated VoiceOS schema.
    """
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_schema()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def init_schema(self):
        """Initializes tables and indexes."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Voice sessions
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS voice_sessions (
                id TEXT PRIMARY KEY,
                transcript TEXT,
                generated_text TEXT,
                app_name TEXT,
                window_title TEXT,
                duration_seconds REAL,
                word_count INTEGER,
                mode INTEGER DEFAULT 0,
                chat_history TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """)

            # Agent turns
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_turns (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                sequence INTEGER DEFAULT 0,
                user_message TEXT,
                assistant_response TEXT,
                duration_ms INTEGER,
                created_at TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES voice_sessions (id) ON DELETE CASCADE
            );
            """)

            # Agent tool calls
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_tool_calls (
                id TEXT PRIMARY KEY,
                turn_id TEXT NOT NULL,
                tool_name TEXT NOT NULL,
                status TEXT,
                input_json TEXT,
                output_summary TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (turn_id) REFERENCES agent_turns (id) ON DELETE CASCADE
            );
            """)

            # Custom vocabulary dictionary
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS dictionary (
                id TEXT PRIMARY KEY,
                text TEXT NOT NULL UNIQUE,
                description TEXT,
                auto_added INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """)

            # Custom app instructions
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS custom_instructions (
                id TEXT PRIMARY KEY,
                app_identifier TEXT NOT NULL,
                instruction TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """)

            # Productivity insights
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS voice_session_insights (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL UNIQUE,
                time_saved_seconds REAL DEFAULT 0,
                words INTEGER DEFAULT 0,
                duration_seconds REAL DEFAULT 0,
                prompts INTEGER DEFAULT 1,
                tool_runs INTEGER DEFAULT 0,
                created_at TEXT NOT NULL
            );
            """)

            conn.commit()

    # --- Session Operations ---
    def create_session(self, transcript: str, generated_text: str = "",
                       app_name: Optional[str] = None, window_title: Optional[str] = None,
                       duration_seconds: float = 0.0, mode: int = 0,
                       chat_history: Optional[List[Dict[str, str]]] = None) -> str:
        session_id = str(uuid.uuid4())
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        word_count = len(transcript.strip().split()) if transcript else 0
        history_str = json.dumps(chat_history or [], ensure_ascii=False)

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO voice_sessions (
                    id, transcript, generated_text, app_name, window_title,
                    duration_seconds, word_count, mode, chat_history, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (session_id, transcript, generated_text, app_name, window_title,
                  duration_seconds, word_count, mode, history_str, now, now))

            # Record insights (approx 130 words/min typing speed vs 150 words/min speaking)
            time_saved = max(0.0, (word_count / 30.0) * 60.0 - duration_seconds) if word_count > 0 else 0.5
            insight_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO voice_session_insights (
                    id, session_id, time_saved_seconds, words, duration_seconds, prompts, tool_runs, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (insight_id, session_id, round(time_saved, 1), word_count, duration_seconds, 1, 0, now))

            conn.commit()
        return session_id

    def get_sessions(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM voice_sessions ORDER BY created_at DESC LIMIT ? OFFSET ?
            """, (limit, offset))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def delete_session(self, session_id: str):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM voice_sessions WHERE id = ?", (session_id,))
            cursor.execute("DELETE FROM voice_session_insights WHERE session_id = ?", (session_id,))
            conn.commit()

    # --- Turn & Tool Operations ---
    def record_turn(self, session_id: str, user_message: str, assistant_response: str,
                    duration_ms: int = 0, tool_calls: Optional[List[Dict[str, Any]]] = None) -> str:
        turn_id = str(uuid.uuid4())
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO agent_turns (
                    id, session_id, sequence, user_message, assistant_response, duration_ms, created_at
                ) VALUES (?, ?, 0, ?, ?, ?, ?)
            """, (turn_id, session_id, user_message, assistant_response, duration_ms, now))

            if tool_calls:
                for tc in tool_calls:
                    tc_id = str(uuid.uuid4())
                    cursor.execute("""
                        INSERT INTO agent_tool_calls (
                            id, turn_id, tool_name, status, input_json, output_summary, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (tc_id, turn_id, tc.get("tool_name", "unknown"),
                          tc.get("status", "completed"), json.dumps(tc.get("input", {})),
                          tc.get("output", ""), now))

                cursor.execute("""
                    UPDATE voice_session_insights
                    SET tool_runs = tool_runs + ?
                    WHERE session_id = ?
                """, (len(tool_calls), session_id))

            conn.commit()
        return turn_id

    # --- Dictionary Operations ---
    def add_dictionary_word(self, text: str, description: Optional[str] = None, auto_added: bool = False) -> bool:
        clean_text = text.strip()
        if not clean_text:
            return False
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO dictionary (id, text, description, auto_added, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (str(uuid.uuid4()), clean_text, description, 1 if auto_added else 0, now, now))
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False

    def get_dictionary_words(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM dictionary ORDER BY created_at DESC")
            return [dict(r) for r in cursor.fetchall()]

    def delete_dictionary_word(self, word_id: str):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM dictionary WHERE id = ?", (word_id,))
            conn.commit()

    # --- Insights Operations ---
    def get_total_insights(self) -> Dict[str, Any]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    COUNT(*) as total_sessions,
                    COALESCE(SUM(time_saved_seconds), 0) as total_time_saved,
                    COALESCE(SUM(words), 0) as total_words,
                    COALESCE(SUM(tool_runs), 0) as total_tools
                FROM voice_session_insights
            """)
            row = cursor.fetchone()
            return {
                "total_sessions": row["total_sessions"] or 0,
                "total_time_saved_seconds": row["total_time_saved"] or 0,
                "total_words": row["total_words"] or 0,
                "total_tools": row["total_tools"] or 0
            }
