import re  # کتابخانه‌ای برای جستجو و ویرایش پیشرفته متن‌ها (Regular Expressions)


def normalize_persian_text(text: str) -> str:
    """
    این تابع متن ورودی تیکت را قبل از تحلیل یکدست و تمیز می‌کند.
    """
    if not text:
        return ""

    # تبدیل کاراکترهای عربی به فارسی استاندارد
    text = text.replace("ي", "ی")
    text = text.replace("ك", "ک")

    # کوچک‌سازی حروف انگلیسی (مثلاً VPN تبدیل به vpn می‌شود)
    text = text.lower()

    # تبدیل چند فاصله پشت سر هم به یک فاصله
    text = re.sub(r"\s+", " ", text)

    # حذف فاصله‌های خالی از ابتدا و انتها
    text = text.strip()

    return text


# --- تست دستی سریع ---
if __name__ == "__main__":
    sample = "  کاربر  كمك  می‌خواهد و VPN او قطع است  "
    print("متن تمیز شده:", f"'{normalize_persian_text(sample)}'")
