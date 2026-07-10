from enum import Enum

class Analysis_Status(str, Enum):
    PENDING   = "pending"
    COMPLETED = "completed"
    FAILED    = "failed"

class Ticket_Status(str, Enum):
    IN_PROGRESS = "in_progress"
    OPEN        = "open"
    RESOLVED    = "resolved"
    CLOSED      = "closed"