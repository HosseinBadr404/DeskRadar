from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from enum import Enum

class Ticket_Status(str, Enum):
    PENDING   = "pending"
    COMPLETED = "completed"
    FAILED    = "failed"


class TicketCreateRequest(BaseModel):

    title: str
    description: str
    requester: str
    department: str


class TicketResponse(BaseModel):

    id: int
    title: str
    description: str
    requester: str
    department: str
    status: Ticket_Status = Ticket_Status.PENDING
    created_at: datetime


class TicketUpdateRequest(BaseModel):

    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None