from datetime import datetime
from typing import Optional
from app.core.data_enum import Analysis_Status, Ticket_Status
from app.core.database import Base
from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum

class TicketModel(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(150), nullable=False)
    description = Column(String, nullable=False)
    departement = Column(String(100), nullable=True)
    requester_name = Column(String(100), nullable=True)

    ticket_status = Column(SQLEnum(Ticket_Status), default=Ticket_Status.OPEN, nullable=False)
    analysis_status = Column(SQLEnum(Analysis_Status), default=Analysis_Status.PENDING, nullable=False)

    source = Column(String(20), default="manual", nullable=False) # manual یا csv
    fingerprint = Column(String(255), nullable=True, unique=True) # برای چلوگیری از ثبت تیکت تکراری
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)