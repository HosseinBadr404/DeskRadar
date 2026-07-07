import httpx
from app.core.config import settings


# این کلاینت تنها نقطه‌ی تماس Backend با AI Core است (طبق قرارداد §3.2).
# هیچ فایل دیگری نباید مستقیم به AI Core درخواست بزند.
class AIClient:

    # مهلت پاسخ AI Core؛ مدل embedding ممکن است در فراخوانی‌های اول کند باشد.
    TIMEOUT_SECONDS = 30.0

    def analyze_ticket(
        self,
        ticket_id: int,
        title: str,
        description: str,
        category: str | None = None,
        old_tickets: list | None = None,
    ) -> dict:

        # بدنه‌ی درخواست باید دقیقاً با InfrastructureRequest در AI Core یکی باشد:
        # ticket_id (اجباری و >۰)، title (غیرخالی)، description، category (اختیاری)،
        # و old_tickets (استخر تیکت‌های قبلی که باید در هر درخواست فرستاده شود).
        payload = {
            "ticket_id": ticket_id,
            "title": title,
            "description": description,
            "category": category,
            "old_tickets": old_tickets or [],
        }

        try:
            response = httpx.post(
                # endpoint درست در AI Core؛ نه /analyze
                f"{settings.AI_CORE_URL}/analyze-ticket",
                json=payload,
                timeout=self.TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            return response.json()

        except httpx.HTTPError as exc:
            # اگر AI Core خاموش بود یا خطا داد، Backend نباید crash کند (§6.8).
            # یک نتیجه‌ی امن با فیلد error برمی‌گردانیم تا لایه‌ی سرویس بتواند
            # analysis_status = "failed" را ذخیره کند.
            return {
                "error": f"ai_core_unavailable: {exc}",
                "similar_tickets": [],
                "related_article": None,
                "incident": {"possible_incident": False},
            }


ai_client = AIClient()