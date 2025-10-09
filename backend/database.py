"""
Database module for conversation history and document management.
Uses SQLite for simplicity, can be upgraded to PostgreSQL for production.
"""
import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
import uuid


class Database:
    def __init__(self, db_path: str = "rag_chatbot.db"):
        self.db_path = db_path
        self.init_db()
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_db(self):
        """Initialize database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                title TEXT,
                metadata TEXT
            )
        """)
        
        # Messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                message_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                citations TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        """)
        
        # Documents table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                doc_id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                file_size INTEGER,
                file_type TEXT,
                chunks_count INTEGER,
                status TEXT DEFAULT 'processing',
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status)")
        
        conn.commit()
        conn.close()
    
    # Session Management
    def create_session(self, session_id: Optional[str] = None, title: Optional[str] = None) -> str:
        """Create a new conversation session"""
        if not session_id:
            session_id = str(uuid.uuid4())
        
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO sessions (session_id, title, metadata) VALUES (?, ?, ?)",
            (session_id, title or "New Conversation", json.dumps({}))
        )
        conn.commit()
        conn.close()
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session details"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def list_sessions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List all sessions"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM sessions ORDER BY updated_at DESC LIMIT ?",
            (limit,)
        )
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def delete_session(self, session_id: str):
        """Delete a session and all its messages"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
        cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
        conn.commit()
        conn.close()
    
    def update_session_title(self, session_id: str, title: str):
        """Update session title"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE sessions SET title = ?, updated_at = CURRENT_TIMESTAMP WHERE session_id = ?",
            (title, session_id)
        )
        conn.commit()
        conn.close()
    
    # Message Management
    def add_message(self, session_id: str, role: str, content: str, citations: Optional[List[Dict]] = None) -> str:
        """Add a message to a session"""
        message_id = str(uuid.uuid4())
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Ensure session exists
        cursor.execute("SELECT session_id FROM sessions WHERE session_id = ?", (session_id,))
        if not cursor.fetchone():
            self.create_session(session_id)
        
        cursor.execute(
            "INSERT INTO messages (message_id, session_id, role, content, citations) VALUES (?, ?, ?, ?, ?)",
            (message_id, session_id, role, content, json.dumps(citations or []))
        )
        
        # Update session timestamp
        cursor.execute(
            "UPDATE sessions SET updated_at = CURRENT_TIMESTAMP WHERE session_id = ?",
            (session_id,)
        )
        
        conn.commit()
        conn.close()
        return message_id
    
    def get_messages(self, session_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all messages for a session"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM messages WHERE session_id = ? ORDER BY created_at ASC LIMIT ?",
            (session_id, limit)
        )
        rows = cursor.fetchall()
        conn.close()
        
        messages = []
        for row in rows:
            msg = dict(row)
            msg['citations'] = json.loads(msg['citations']) if msg['citations'] else []
            messages.append(msg)
        return messages
    
    def get_conversation_context(self, session_id: str, max_messages: int = 10) -> str:
        """Get recent conversation context as formatted string"""
        messages = self.get_messages(session_id)[-max_messages:]
        context_parts = []
        for msg in messages:
            context_parts.append(f"{msg['role'].upper()}: {msg['content']}")
        return "\n".join(context_parts)
    
    # Document Management
    def add_document(self, doc_id: str, filename: str, file_size: int, file_type: str, 
                     chunks_count: int = 0, metadata: Optional[Dict] = None) -> str:
        """Add a document record"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO documents 
               (doc_id, filename, file_size, file_type, chunks_count, status, metadata) 
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (doc_id, filename, file_size, file_type, chunks_count, 'processing', json.dumps(metadata or {}))
        )
        conn.commit()
        conn.close()
        return doc_id
    
    def update_document_status(self, doc_id: str, status: str, chunks_count: Optional[int] = None):
        """Update document processing status"""
        conn = self.get_connection()
        cursor = conn.cursor()
        if chunks_count is not None:
            cursor.execute(
                "UPDATE documents SET status = ?, chunks_count = ? WHERE doc_id = ?",
                (status, chunks_count, doc_id)
            )
        else:
            cursor.execute(
                "UPDATE documents SET status = ? WHERE doc_id = ?",
                (status, doc_id)
            )
        conn.commit()
        conn.close()
    
    def list_documents(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all documents"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if status:
            cursor.execute(
                "SELECT * FROM documents WHERE status = ? ORDER BY uploaded_at DESC",
                (status,)
            )
        else:
            cursor.execute("SELECT * FROM documents ORDER BY uploaded_at DESC")
        
        rows = cursor.fetchall()
        conn.close()
        
        documents = []
        for row in rows:
            doc = dict(row)
            doc['metadata'] = json.loads(doc['metadata']) if doc['metadata'] else {}
            documents.append(doc)
        return documents
    
    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get document details"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM documents WHERE doc_id = ?", (doc_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            doc = dict(row)
            doc['metadata'] = json.loads(doc['metadata']) if doc['metadata'] else {}
            return doc
        return None
    
    def delete_document(self, doc_id: str):
        """Delete a document record"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
        conn.commit()
        conn.close()
    
    # Analytics
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as count FROM sessions")
        sessions_count = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM messages")
        messages_count = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM documents WHERE status = 'completed'")
        documents_count = cursor.fetchone()['count']
        
        conn.close()
        
        return {
            "sessions": sessions_count,
            "messages": messages_count,
            "documents": documents_count
        }


# Global database instance
_db_instance = None

def get_db() -> Database:
    """Get or create database instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance

