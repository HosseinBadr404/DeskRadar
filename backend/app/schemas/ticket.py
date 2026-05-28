from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class TicketCreate(BaseModel):

    title: str
    description: str
    requester: str
    department: str


class TicketRead(BaseModel):

    id: int
    title: str
    description: str
    requester: str
    department: str
    status: str
    created_at: datetime

class TicketUpdate(BaseModel):

    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None