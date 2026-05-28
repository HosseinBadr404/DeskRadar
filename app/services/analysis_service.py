# چون فعلا ای آی نداریم از یه فیک لاجیک ای آی اینحا استفاده کردم
#  تا بعدا که ای آی اوکی شد جایگزین اش می کنیم 
from app.models.ticket_analysis import TicketAnalysis


class AnalysisService:

    def analyze_ticket(self, title: str, description: str):

        text = f"{title} {description}".lower()

        category = "general"
        urgency = "low"

        # Simple keyword analysis
        if "vpn" in text:
            category = "network"

        if "server" in text:
            category = "infrastructure"

        if "urgent" in text:
            urgency = "high"

        if "critical" in text:
            urgency = "critical"

        summary = f"Issue related to {category}"

        reply = "Our technical team is investigating the issue."

        confidence = 0.91

        raw_ai_response = "Simulated AI response"

        analysis = TicketAnalysis(
            category=category,
            intent="issue_detection",
            urgency=urgency,
            summary=summary,
            reply=reply,
            confidence=confidence,
            raw_ai_response=raw_ai_response
        )

        return analysis