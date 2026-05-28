from datetime import datetime
from typing import Optional


class Ticket:

    def __init__(
        self,
        title: str,
        description: str,
        requester: str,
        department: str,
        status: str = "open"
    ):

        self.title = title
        self.description = description
        self.requester = requester
        self.department = department
        self.status = status

        self.created_at = datetime.now()
        self.updated_at = datetime.now()