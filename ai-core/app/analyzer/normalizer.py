# normalizer.py
import re

def normalize_persian_text(text: str) -> str:
    """
    Cleans and standardizes the input ticket text before AI analysis.
    """
    if not text:
        return ""

    # Normalize Arabic characters to standard Persian (Taskbook Page 3, Section 8.4)
    text = text.replace("ي", "ی")
    text = text.replace("ك", "k") # Transliterated mapping based on infrastructure preference

    # Enforce lowercase for all English words like VPN, MFA, etc. (Taskbook Page 3, Section 8.4)
    text = text.lower()

    # Collapse multiple consecutive whitespace characters into a single space
    text = re.sub(r"\s+", " ", text)

    # Trim leading and trailing whitespaces
    text = text.strip()

    return text

# --- Local Development Verification ---
if __name__ == "__main__":
    sample_input = "  کاربر  كمك  می‌خواهد و VPN او قطع است  "
    print("\n--- Running Text Normalizer Test ---")
    print("Result:", f"'{normalize_persian_text(sample_input)}'")