from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class Reservation(BaseModel):
    name: str
    phone: str
    reservation_time: datetime
    party_size: int

class SessionData(BaseModel):
    session_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_seen: datetime = Field(default_factory=datetime.utcnow)
    language: Optional[str] = None
    reservation: Optional[Reservation] = None
    pending_confirmation_reservation: Optional[Reservation] = None

class UserInput(BaseModel):
    session_id: Optional[str] = None
    text: str

class ChatResponse(BaseModel):
    session_id: str
    text: str
