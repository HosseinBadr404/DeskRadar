from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.core.data_enum import Ticket_Status, Analysis_Status
from app.schemas.analysis import Ai_Analysis


class TicketCreateRequest(BaseModel):

    title: str
    description: str
    requester: Optional[str] = None
    department: Optional[str] = None


class TicketResponse(BaseModel):

    id: int
    title: str
    description: str
    requester: str
    department: str
    analysis_status: Analysis_Status = Analysis_Status.PENDING
    ticket_status: Ticket_Status = Ticket_Status.OPEN
    created_at: datetime

    ai_analysis: Optional[Ai_Analysis] = None


class TicketUpdateRequest(BaseModel):

    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None