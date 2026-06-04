# normalizer.py
import re


def normalize_persian_text(text: str) -> str:
    if not text:
        return ""

    # Convert Arabic characters to standard Persian
    text = text.replace("ي", "ی")
    text = text.replace("ك", "ک")

    # Enforce lowercase for English words
    text = text.lower()

    # Collapse whitespaces
    text = re.sub(r"\s+", " ", text)
    text = text.strip()

    return text


if __name__ == "__main__":
    sample_input = "  کاربر  كمك  می‌خواهد و VPN او قطع است  "
    print("Result:", f"'{normalize_persian_text(sample_input)}'")
