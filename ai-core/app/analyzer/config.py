CATEGORY_MAP = {
    "اتصال VPN و شبکه راه دور": "vpn",
    "مشکلات ایمیل و صندوق پستی": "email",
    "قطعی اینترنت و وای‌فای": "network",
    "خرابی پرینتر و صف چاپ": "printer",
    "حساب کاربری و رمز عبور": "account",
    "خرابی سخت‌افزار و تجهیزات": "hardware",
    "نصب و بروزرسانی نرم‌افزار": "software",
    "دسترسی به فایل و پوشه اشتراکی": "permission",
}

CATEGORY_LABELS_FA = list(CATEGORY_MAP.keys())
CATEGORY_CODES = list(CATEGORY_MAP.values())
CATEGORY_LABEL_BY_CODE = {code: label for label, code in CATEGORY_MAP.items()}

CATEGORY_THRESHOLD = 0.70
CATEGORY_FALLBACK_THRESHOLD = 0.55
CATEGORY_TOP_K = 3

ZERO_SHOT_MODEL_NAME = "MoritzLaurer/multilingual-MiniLMv2-L6-mnli-xnli"
ZERO_SHOT_HYPOTHESIS_TEMPLATE = "موضوع این تیکت مربوط به {} است."
ANALYZER_MODEL_VERSION = "ai-analyzer-fa-v1"
UNKNOWN_CATEGORY = "unknown"

CATEGORY_KEYWORDS = {
    "vpn": [
        "vpn",
        "وی پی ان",
        "وی‌پی‌ان",
        "وی_پی_ان",
        "شبکه راه دور",
        "remote access",
        "anyconnect",
        "forticlient",
        "openvpn",
    ],
    "email": [
        "email",
        "ایمیل",
        "ایمیل سازمانی",
        "صندوق پستی",
        "outlook",
        "mailbox",
        "پست الکترونیک",
    ],
    "network": [
        "اینترنت",
        "وای فای",
        "وای‌فای",
        "wifi",
        "wi-fi",
        "شبکه",
        "کابل شبکه",
        "lan",
        "ping",
    ],
    "printer": [
        "پرینتر",
        "چاپگر",
        "چاپ",
        "پرینت",
        "صف چاپ",
        "تونر",
        "کارتریج",
        "paper jam",
    ],
    "account": [
        "حساب کاربری",
        "اکانت",
        "رمز",
        "پسورد",
        "password",
        "login",
        "لاگین",
        "ورود",
        "قفل",
    ],
    "hardware": [
        "سخت افزار",
        "سخت‌افزار",
        "لپ تاپ",
        "لپ‌تاپ",
        "کیس",
        "مانیتور",
        "موس",
        "کیبورد",
        "تجهیزات",
        "روشن نمی‌شود",
    ],
    "software": [
        "نرم افزار",
        "نرم‌افزار",
        "نصب",
        "بروزرسانی",
        "آپدیت",
        "update",
        "install",
        "license",
        "کرش",
    ],
    "permission": [
        "دسترسی",
        "مجوز",
        "فایل",
        "پوشه",
        "فولدر",
        "اشتراکی",
        "shared folder",
        "permission",
        "access denied",
    ],
}
