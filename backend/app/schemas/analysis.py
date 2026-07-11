from pydantic import BaseModel,Field
from typing import Optional, List

class AISimilarTicket(BaseModel):
    ticket_id: int
    similarity_dgree: float

class AIRelatedArticle(BaseModel):
    article_id: int
    title: str
    score: float

class AIAnalysisDetails(BaseModel):
    category: str
    category_label_fa: str
    category_score: float
    intent: str
    intent_label_fa: str
    urgency: str
    urgency_score: int
    sentiment: str
    summary_fa: str
    suggested_reply_fa: str
    confidence: float
    reasons_fa: List[str]

class AIIntelligenceDetails(BaseModel):
    similar_tickets: List[AISimilarTicket]
    related_article: Optional[AIRelatedArticle] = None
    possible_incident: bool
    incident_title_fa: Optional[str] = None

# فرمت خروجی از 
# AI Core
# طبق مستندات پروژه
class AICoreResponse(BaseModel):
    ticket_id: int
    analysis: AIAnalysisDetails
    intelligence: AIIntelligenceDetails



class Ai_Analysis(BaseModel):
    #استخراج فیلد های مورد نیاز از پاسخ  تحلیل هوش مصنوعی برای ارسال به یوز
    category: str
    category_label_fa: str
    category_score: float = Field( ge=0.0, le=1.0, description="Category Score in range of [0.0,1.0]")
    
    intent : str
    intent_label_fa: str

    urgency: str

    summary_fa: str
    suggested_reply_fa: str

    reasons_fa: List[str]