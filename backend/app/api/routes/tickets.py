from fastapi import APIRouter, status, HTTPException, BackgroundTasks
from app.schemas.ticket import TicketCreateRequest, TicketResponse
from app.services.ticket_service import TicketService
from datetime import datetime

router = APIRouter(prefix="/tickets", tags=["Tickets"])

ticket_service = TicketService()

@router.post("/", response_model=TicketResponse, status_code=status.HTTP_201_CREATED) #ریکوئست ایجاد تیکت جدید
async def create_ticket(ticket_in: TicketCreateRequest, api_background_tasks: BackgroundTasks):
    
    try:

        response = await ticket_service.create_ticket(
            **ticket_in.model_dump(),
            background_tasks = api_background_tasks,
            auto_analyze=True
            )
        return response;

    except HTTPException as http_ex:
        raise http_ex
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail= f"Unknow internal error occurred: {str(e)}"
        )


@router.get("/", status_code=status.HTTP_200_OK) #//TODO: ریکوئست دریافت لیست تیکت ها با فیلتر
async def get_all_tickets():
    return ["t1", "t2", "t3"]

@router.get("/{ticket_id}",response_model=TicketResponse, status_code=status.HTTP_200_OK) # //TODO: ریکوئست دریافت پاسخ یک تیکت خاص
async def get_ticket_detail(ticket_id: int):

    try:

        response = await ticket_service.get_ticket_by_id(ticket_id=ticket_id)
        return response
    
    except HTTPException as http_ex:
        raise http_ex
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail= f"Unknow internal error occurred: {str(e)}"
        )

    
    

@router.post("/import", status_code=status.HTTP_200_OK)
async def import_tickets_csv():
    return {"message": "tickets uploaded successfully"}

@router.post("/{ticket_id}/analyze", status_code=status.HTTP_200_OK)
async def analyze_ticket_by_id(ticket_id: int):
    return {"ticket_id": ticket_id, "status": "analyzed_by_ai"}