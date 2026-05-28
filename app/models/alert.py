from datetime import datetime


class Alert:

    def __init__(
        self,
        urgent_ticket: bool,
        incident_candidate: bool,
        sla_risk: bool,
        message: str
    ):

        self.urgent_ticket = urgent_ticket
        self.incident_candidate = incident_candidate
        self.sla_risk = sla_risk
        self.message = message

        self.created_at = datetime.now()