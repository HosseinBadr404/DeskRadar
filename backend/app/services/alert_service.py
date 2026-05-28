from app.models.alert import Alert
from app.models.ticket_analysis import TicketAnalysis


class AlertService:

    def generate_alert(self, analysis: TicketAnalysis):

        urgent = analysis.urgency in ["high", "critical"]

        incident_candidate = analysis.urgency == "critical"

        sla_risk = analysis.urgency == "critical"

        message = "System operating normally"

        if urgent:
            message = "Urgent ticket detected"

        if incident_candidate:
            message = "Critical incident candidate detected"

        alert = Alert(
            urgent_ticket=urgent,
            incident_candidate=incident_candidate,
            sla_risk=sla_risk,
            message=message
        )

        return alert