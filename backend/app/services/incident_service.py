from app.models.incident import Incident
from app.models.ticket_analysis import TicketAnalysis


class IncidentService:

    def detect_incident(self, analysis: TicketAnalysis):

        if analysis.urgency == "critical":

            incident = Incident(
                title="Critical Infrastructure Issue",
                description=analysis.summary,
                severity="critical"
            )

            return incident

        return None