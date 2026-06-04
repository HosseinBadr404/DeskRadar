from intent_config import INTENT_RULES


def detect_intent(normalized_text, category):
    # Check if the category exists in our configuration
    if category not in INTENT_RULES:
        return f"unknown_{category}_issue"

    # Loop through each intent and its keywords for this category
    for intent, keywords in INTENT_RULES[category].items():
        for keyword in keywords:
            if keyword in normalized_text:
                return intent

    # Fallback if no keywords match
    return f"general_{category}_issue"


if __name__ == "__main__":

    ticket_a = "سلام وی پی ان من قطع شده و ارور میده"
    cat_a = "vpn"

    ticket_b = "لطفا فضا یا حجم ایمیل من رو ارتقا بدید"
    cat_b = "email"

    ticket_c = "تیکت نمونه بدون هیچ کلمه خاصی"
    cat_c = "network"

    print("Result A:", detect_intent(ticket_a, cat_a))
    print("Result B:", detect_intent(ticket_b, cat_b))
    print("Result C:", detect_intent(ticket_c, cat_c))
