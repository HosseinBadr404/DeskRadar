from intent_config import (
    GENERAL_INTENT_TEMPLATE,
    INTENT_LABELS_FA,
    INTENT_RULES,
    UNKNOWN_INTENT,
)
from normalizer import normalize_persian_text


def normalize_category(category: str) -> str:
    if not category:
        return ""

    return str(category).strip().lower()


def normalize_keyword(keyword: str) -> str:
    return normalize_persian_text(str(keyword))


def get_general_intent(category: str) -> str:
    category_code = normalize_category(category)

    if not category_code or category_code == "unknown":
        return UNKNOWN_INTENT

    return GENERAL_INTENT_TEMPLATE.format(category=category_code)


def get_intent_label_fa(intent: str) -> str:
    return INTENT_LABELS_FA.get(intent, intent)


def find_keyword_matches(text: str, keywords: list) -> list:
    matches = []
    seen = set()

    for keyword in keywords:
        clean_keyword = normalize_keyword(keyword)

        if clean_keyword and clean_keyword in text and clean_keyword not in seen:
            matches.append(clean_keyword)
            seen.add(clean_keyword)

    return matches


def analyze_intent(text: str, category: str) -> dict:
    clean_text = normalize_persian_text(text)
    category_code = normalize_category(category)

    if not clean_text:
        return {
            "intent": UNKNOWN_INTENT,
            "intent_label_fa": get_intent_label_fa(UNKNOWN_INTENT),
            "intent_score": 0.0,
            "matched_keywords": [],
            "reason": "متن تیکت خالی است.",
        }

    if not category_code or category_code == "unknown":
        return {
            "intent": UNKNOWN_INTENT,
            "intent_label_fa": get_intent_label_fa(UNKNOWN_INTENT),
            "intent_score": 0.0,
            "matched_keywords": [],
            "reason": "دسته‌بندی تیکت مشخص نیست.",
        }

    category_rules = INTENT_RULES.get(category_code)

    if not category_rules:
        general_intent = get_general_intent(category_code)

        return {
            "intent": general_intent,
            "intent_label_fa": get_intent_label_fa(general_intent),
            "intent_score": 0.3,
            "matched_keywords": [],
            "reason": "برای این دسته‌بندی قانون intent تعریف نشده است.",
        }

    best_intent = None
    best_matches = []
    best_score = 0.0

    for intent, keywords in category_rules.items():
        matches = find_keyword_matches(clean_text, keywords)

        if not matches:
            continue

        score = min(1.0, 0.55 + (len(matches) * 0.15))

        if score > best_score:
            best_intent = intent
            best_matches = matches
            best_score = score

    if best_intent:
        return {
            "intent": best_intent,
            "intent_label_fa": get_intent_label_fa(best_intent),
            "intent_score": round(best_score, 2),
            "matched_keywords": best_matches,
            "reason": f"intent با کلمات کلیدی {', '.join(best_matches)} تشخیص داده شد.",
        }

    general_intent = get_general_intent(category_code)

    return {
        "intent": general_intent,
        "intent_label_fa": get_intent_label_fa(general_intent),
        "intent_score": 0.4,
        "matched_keywords": [],
        "reason": "هیچ کلمه کلیدی مشخصی برای intent پیدا نشد.",
    }


def detect_intent(text: str, category: str) -> str:
    return analyze_intent(text, category)["intent"]


if __name__ == "__main__":
    tickets = [
        {
            "text": "سلام وی پی ان من قطع شده و ارور میده",
            "category": "vpn",
        },
        {
            "text": "لطفا فضا یا حجم ایمیل من رو ارتقا بدید",
            "category": "email",
        },
        {
            "text": "تیکت نمونه بدون هیچ کلمه خاصی",
            "category": "network",
        },
    ]

    for ticket in tickets:
        print(analyze_intent(ticket["text"], ticket["category"]))
