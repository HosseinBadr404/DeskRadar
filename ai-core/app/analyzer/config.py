# config.py

# Map Persian labels to standard database-friendly English constants
CATEGORY_MAP = {
    "اتصال vpn و شبکه راه دور": "vpn",
    "مشکلات ایمیل و صندوق پستی": "email",
    "قطعی اینترنت و وای‌فای": "network",
    "خرابی پرینتر و صف چاپ": "printer",
    "حساب کاربری و رمز عبور": "account",
}

# Extract Persian labels required by the AI model for textual comprehension
CATEGORY_LABELS_FA = list(CATEGORY_MAP.keys())

# Confidence threshold for the zero-shot classifier (Taskbook Page 11, Section 8.12)
CATEGORY_THRESHOLD = 0.70