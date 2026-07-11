from datetime import datetime
import hashlib
from typing import List, Optional
from app.core.data_enum import Analysis_Status, Ticket_Status
#-----------------------------------------
#from app.models.ticket import TicketModel   //TODO:بعد از اتصال دیتا بیس از این مدل واقعی استفاده میکنیم
#-----------------------------------------

FAKE_TICKETS_DB :List[dict] = []
_id_counter = 777

class TicketRepository:
    # ساخت اثر انگشت مخصوص، بعدا بنظرم بهتهره زمان هم به متد هش اضافه کرد
    def _generate_fingerprint(self, title: str,
                              description: str,
                              requester: Optional[str]) -> str:
        req = requester or "nobody"
        raw_text = f"{title.lower()}{description.lower()}{req.lower()}"
        return hashlib.md5(raw_text.encode("utf-8")).hexdigest()
    
    # async def get_by_fingerprint(self, finger_print) -> Optional[str]:
    #     for T in FAKE_TICKETS_DB:
    #         if T.get("fingerprint") == finger_print:
    #             return T
            
    #     return None
    
    async def is_already_exist(self, title: str,
                              description: str,
                              requester: Optional[str]) -> Optional[dict]:
        finger_print = self._generate_fingerprint(title=title, description=description, requester=requester)

        for T in FAKE_TICKETS_DB:
            if T.get("fingerprint")==finger_print:
                return T
        return None
    
    async def get_by_id(self, target_ticket_id: int)-> Optional[dict]:

        for T in FAKE_TICKETS_DB:
            if T.get("ticket_id") == target_ticket_id:
                return T
        return None

    
    async def save_new_ticket(self, title: str, 
                        description: str, 
                        requester: Optional[str], 
                        department: Optional[str]) -> dict:
        
        # در آینده دیتابیس واقعی اینجا تزریق می‌شود:
        # def __init__(self, db_session): self.db = db_session
        global _id_counter

        FINGER_PRINT = self._generate_fingerprint(title=title, description=description, requester=requester)

        new_ticket = {
            "ticket_id": _id_counter,
            "title": title,
            "description": description,
            "requester": requester or "None",
            "department": department or "None",
            "ticket_status": Ticket_Status.OPEN,
            "analysis_status": Analysis_Status.PENDING,
            "source": "manual",
            "fingerprint": FINGER_PRINT,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),

            "ai_analysis" : None
        }

        _id_counter+= 1;
        FAKE_TICKETS_DB.append(new_ticket)

        return new_ticket
    
    async def update_ticket_analysis(self, 
                              ticket_id: int, 
                              new_analysis_status: Analysis_Status, 
                              new_analysis_data: Optional[dict] = None)-> None:
        
        for T in FAKE_TICKETS_DB:
            if T.get("ticket_id")== ticket_id:
                T["ai_analysis"] = new_analysis_data
                T["analysis_status"] = new_analysis_status
                T["updated_at"] = datetime.now()
                break

