from fastapi import HTTPException, status, BackgroundTasks
from app.repositories.ticket_repository import TicketRepository
from app.core.data_enum import Analysis_Status, Ticket_Status
from app.services.analysis_service import AnalysisService
from typing import Optional

class TicketService:

    def __init__(self):

        self.ticket_repo = TicketRepository()
        self.analysis_serv = AnalysisService()

    async def create_ticket(
        self, 
        title: str, 
        description: str, 
        requester: Optional[str], 
        department: Optional[str], 
        background_tasks: BackgroundTasks,
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

        #ایجاد تسک در پس زمنیه برای ثبت خودکار خروجی تحلیل بخش 
        #Ai Core
        if auto_analyze:
            background_tasks.add_task(
                self.run_ai_analysis,
                ticket_id=ticket_data["ticket_id"],
                title=ticket_data["title"],
                description=ticket_data["description"]
            )

        return ticket_data
    
    async def run_ai_analysis(self, ticket_id: int,
                              title: str,
                              description: str) -> None:
        
        try:
            ai_raw_response = await self.analysis_serv.analyze_ticket(ticket_id=ticket_id, title=title, description=description)
            analysis_payload = ai_raw_response.get("analysis")

            await self.ticket_repo.update_ticket_analysis(ticket_id=ticket_id,
                                                   new_analysis_status= Analysis_Status.COMPLETED,
                                                   new_analysis_data= analysis_payload )
            
            print(f"Updating analysis for ticket id: {ticket_id} completed.")

        except Exception as e:
            await self.ticket_repo.update_ticket_analysis(
                ticket_id=ticket_id,
                analysis_status=Analysis_Status.FAILED
            )
            print(f"Background analysis failed for ticket {ticket_id}: {str(e)}")


    async def get_ticket_by_id(self, ticket_id: int ) -> dict:
            
            target_ticket = await self.ticket_repo.get_by_id(target_ticket_id= ticket_id)

            if target_ticket == None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Ticket Not found."
                )
            
            return target_ticket
            

