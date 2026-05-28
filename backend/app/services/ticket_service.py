from app.models.ticket import Ticket
from app.services.analysis_service import AnalysisService
from app.services.incident_service import IncidentService
from app.services.alert_service import AlertService


class TicketService:

    def __init__(self):

        self.analysis_service = AnalysisService()
        self.incident_service = IncidentService()
        self.alert_service = AlertService()

    def create_ticket(
        self,
        title: str,
        description: str,
        requester: str,
        department: str
    ):

        ticket = Ticket(
            title=title,
            description=description,
            requester=requester,
            department=department
        )

        analysis = self.analysis_service.analyze_ticket(
            title=title,
            description=description
        )

        
        incident = self.incident_service.detect_incident(
            analysis
        )

        alert = self.alert_service.generate_alert(
            analysis
        )

        return {
            "ticket": ticket,
            "analysis": analysis,
            "incident": incident,
            "alert": alert
        }