from fastapi import HTTPException, status
from app.repositories.ticket_repository import TicketRepository
from app.core.data_enum import Analysis_Status, Ticket_Status
from app.services.analysis_service import AnalysisService
from typing import Optional

class TicketService:

    def __init__(self):

        self.ticket_repo = TicketRepository()
        self.analysis_serv = AnalysisService()

    async def creat_ticket(
        self, 
        title: str, 
        description: str, 
        requester: Optional[str], 
        department: Optional[str], 
        auto_analyze: bool = True
    ) -> dict:
        
        ALREADY_EXIST = await self.ticket_repo.is_already_exist(title=title, description=description, requester=requester)
        
        if ALREADY_EXIST:
            raise HTTPException(
                status_code= status.HTTP_400_BAD_REQUEST,
                detail= "Ticket has already been submitted and it is in progress."
            )
        
        ticket_data = await self.ticket_repo.save_new_ticket(
            title=title,
            description=description,
            requester=requester,
            department=department
        )

        return ticket_data