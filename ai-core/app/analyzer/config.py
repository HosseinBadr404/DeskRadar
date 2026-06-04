# config.py

CATEGORY_MAP = {
    "اتصال vpn و شبکه راه دور": "vpn",
    "مشکلات ایمیل و صندوق پستی": "email",
    "قطعی اینترنت و وای‌فای": "network",
    "خرابی پرینتر و صف چاپ": "printer",
    "حساب کاربری و رمز عبور": "account",
    "خرابی سخت‌افزار و تجهیزات": "hardware",
    "نصب و بروزرسانی نرم‌افزار": "software",
    "دسترسی به فایل و پوشه اشتراکی": "permission",
}

CATEGORY_LABELS_FA = list(CATEGORY_MAP.keys())
CATEGORY_THRESHOLD = 0.70
