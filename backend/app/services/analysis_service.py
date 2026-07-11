# چون فعلا ای آی نداریم از یه فیک لاجیک ای آی اینحا استفاده کردم
#  تا بعدا که ای آی اوکی شد جایگزین اش می کنیم 
from app.models.ticket_analysis import TicketAnalysis


class AnalysisService:

    async def analyze_ticket(self, ticket_id: int, title: str, description: str) -> dict:

        text = f"{title} {description}".lower()

        category = "general"
        category_label_fa = "عمومی" 
        urgency = "low"

        # Simple keyword analysis
        if "vpn" in text:
            category = "network"
            category_label_fa = "شبکه و اینترنت"

        elif "server" in text:
            category = "server"
            category_label_fa = "سرور"

        if "urgent" in text:
            urgency = "mediume"

        elif "critical" in text:
            urgency = "high"

        confidence = 0.91

        analysis_respo = {
            "category": category,
            "category_label_fa": category_label_fa,
            "category_score": 0.5,
            "intent": "Problem",
            "intent_label_fa": "مشکل",
            "urgency": urgency,
            "urgency_score": 50,
            "sentiment": "fucking angree",
            "summary_fa": "وحشی",
            "suggested_reply_fa": "از چت جی پی تی بپرس",
            "confidence": confidence,
            "reasons_fa": ["کار بلد نیستی", "هنوز خیلی نوبی"]
        }

        result = {
            "ticket_id" : ticket_id,
            "intelligence" : "Coming soon...",
            "analysis" : analysis_respo
        }
            
        

        return result