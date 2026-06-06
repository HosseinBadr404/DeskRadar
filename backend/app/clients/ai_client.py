import httpx
from app.core.config import settings

class AIClient:

    def analyze_ticket(
        self,
        title: str,
        description: str
    ):

        response = httpx.post(
            # request to POST/analyze in AI Core
            f"{settings.AI_CORE_URL}/analyze",
            json={
                "title": title,
                "description": description
            }
        )

        return response.json()


ai_client = AIClient()