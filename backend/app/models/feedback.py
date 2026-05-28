from datetime import datetime


class Feedback:

    def __init__(
        self,
        ticket_id: int,
        rating: int,
        comment: str
    ):

        self.ticket_id = ticket_id
        self.rating = rating
        self.comment = comment

        self.created_at = datetime.now()