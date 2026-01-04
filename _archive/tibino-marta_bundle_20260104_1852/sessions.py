import uuid
from datetime import datetime
from typing import Optional

from models import SessionData
from config import SESSION_TTL

# In-memory storage for sessions
sessions = {}

def get_session(session_id: Optional[str] = None) -> SessionData:
    """Gets an existing session or creates a new one."""
    # Clean up expired sessions first
    cleanup_expired_sessions()

    if session_id and session_id in sessions:
        session = sessions[session_id]
        session.last_seen = datetime.utcnow()
        return session
    
    new_session_id = str(uuid.uuid4())
    session = SessionData(session_id=new_session_id)
    sessions[new_session_id] = session
    return session

def cleanup_expired_sessions():
    """Removes sessions that have expired."""
    now = datetime.utcnow()
    expired_sessions = [
        sid for sid, session in sessions.items() 
        if now - session.last_seen > SESSION_TTL
    ]
    for sid in expired_sessions:
        del sessions[sid]
