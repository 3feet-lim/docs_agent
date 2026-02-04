"""
SQLite 데이터베이스 모듈

대화 히스토리를 SQLite에 저장하고 관리합니다.
"""

import sqlite3
import json
from datetime import datetime, timezone
from typing import List, Optional
from pathlib import Path
from contextlib import contextmanager

from ..config import get_settings
from ..utils.logger import get_logger


logger = get_logger(__name__)


# 데이터베이스 파일 경로
DB_PATH = Path("data/chat_history.db")


def get_db_path() -> Path:
    """데이터베이스 파일 경로를 반환합니다."""
    settings = get_settings()
    db_path = Path(getattr(settings, 'db_path', 'data/chat_history.db'))
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return db_path


@contextmanager
def get_connection():
    """데이터베이스 연결을 반환하는 컨텍스트 매니저."""
    conn = sqlite3.connect(get_db_path(), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    """데이터베이스 테이블을 초기화합니다."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # 세션 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        # 메시지 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id TEXT UNIQUE NOT NULL,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                sources TEXT,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        """)
        
        # 인덱스 생성
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_session 
            ON messages(session_id)
        """)
        
        conn.commit()
        logger.info("데이터베이스 초기화 완료")


def create_session(session_id: str) -> None:
    """새 세션을 생성합니다."""
    now = datetime.now(timezone.utc).isoformat()
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO sessions (session_id, created_at, updated_at)
            VALUES (?, ?, ?)
        """, (session_id, now, now))
        conn.commit()


def save_message(
    message_id: str,
    session_id: str,
    role: str,
    content: str,
    sources: Optional[List[dict]] = None,
    timestamp: Optional[str] = None
) -> None:
    """메시지를 저장합니다."""
    if timestamp is None:
        timestamp = datetime.now(timezone.utc).isoformat()
    
    sources_json = json.dumps(sources, ensure_ascii=False) if sources else None
    
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # 세션이 없으면 생성
        create_session(session_id)
        
        # 메시지 저장
        cursor.execute("""
            INSERT OR REPLACE INTO messages 
            (message_id, session_id, role, content, sources, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (message_id, session_id, role, content, sources_json, timestamp))
        
        # 세션 업데이트 시간 갱신
        cursor.execute("""
            UPDATE sessions SET updated_at = ? WHERE session_id = ?
        """, (timestamp, session_id))
        
        conn.commit()


def get_session_messages(session_id: str) -> List[dict]:
    """세션의 모든 메시지를 조회합니다."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT message_id, role, content, sources, timestamp
            FROM messages
            WHERE session_id = ?
            ORDER BY id ASC
        """, (session_id,))
        
        messages = []
        for row in cursor.fetchall():
            msg = {
                "message_id": row["message_id"],
                "role": row["role"],
                "content": row["content"],
                "timestamp": row["timestamp"],
            }
            if row["sources"]:
                msg["sources"] = json.loads(row["sources"])
            messages.append(msg)
        
        return messages


def get_session_history(session_id: str) -> List[dict]:
    """세션의 대화 히스토리를 반환합니다 (role, content만)."""
    messages = get_session_messages(session_id)
    return [{"role": m["role"], "content": m["content"]} for m in messages]


def delete_session(session_id: str) -> bool:
    """세션과 관련 메시지를 삭제합니다."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
        cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
        
        conn.commit()
        deleted = cursor.rowcount > 0
        
        if deleted:
            logger.info(f"세션 삭제: {session_id}")
        
        return deleted


def get_all_sessions() -> List[dict]:
    """모든 세션 목록을 조회합니다."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.session_id, s.created_at, s.updated_at,
                   COUNT(m.id) as message_count,
                   (SELECT content FROM messages 
                    WHERE session_id = s.session_id AND role = 'user' 
                    ORDER BY id ASC LIMIT 1) as first_message
            FROM sessions s
            LEFT JOIN messages m ON s.session_id = m.session_id
            GROUP BY s.session_id
            ORDER BY s.updated_at DESC
        """)
        
        return [dict(row) for row in cursor.fetchall()]


# 앱 시작 시 DB 초기화
init_db()
