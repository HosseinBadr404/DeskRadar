from datetime import datetime


class TicketAnalysis:

    def __init__(
        self,
        category: str,
        intent: str,
        urgency: str,
        summary: str,
        reply: str,
        confidence: float,
        raw_ai_response: str
    ):

        self.category = category
        self.intent = intent
        self.urgency = urgency
        self.summary = summary
        self.reply = reply
        self.confidence = confidence
        self.raw_ai_response = raw_ai_response

        self.created_at = datetime.now()