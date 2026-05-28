from datetime import datetime


class Incident:

    def __init__(
        self,
        title: str,
        description: str,
        severity: str,
        status: str = "open"
    ):

        self.title = title
        self.description = description
        self.severity = severity
        self.status = status

        self.created_at = datetime.now()
        self.updated_at = datetime.now()