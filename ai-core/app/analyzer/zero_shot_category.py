# zero_shot_category.py
from transformers import pipeline
from normalizer import normalize_persian_text
from config import CATEGORY_MAP, CATEGORY_LABELS_FA, CATEGORY_THRESHOLD

print("Loading AI Model weights... Please wait...")

# Initialize the pipeline once at system startup (Taskbook Page 4, Section 8.5)
classifier = pipeline(
    "zero-shot-classification", model="MoritzLaurer/multilingual-MiniLMv2-L6-mnli-xnli"
)


def classify_category(text: str) -> dict:
    """
    Analyzes ticket text and extracts the corresponding English category key.
    """
    clean_text = normalize_persian_text(text)

    if not clean_text:
        return {"category": "unknown", "score": 0.0}

    # Execute zero-shot classification using Persian hypothesis template
    result = classifier(
        clean_text,
        candidate_labels=CATEGORY_LABELS_FA,
        hypothesis_template="موضوع این تیکت مربوط به {} است.",
    )

    best_label_fa = result["labels"][0]
    best_score = round(result["scores"][0], 2)

    # Map the predicted Persian label to an English database constant
    category_en = CATEGORY_MAP.get(best_label_fa, "unknown")

    # Apply Rule Engine Fallback if AI confidence is below threshold
    if best_score < CATEGORY_THRESHOLD:
        if "vpn" in clean_text:
            category_en = "vpn"

    return {"category": category_en, "score": best_score}


if __name__ == "__main__":
    test_ticket = "سلام، من نیم ساعت دیگه جلسه دارم ولی vpn قطعه و احراز هویت نمیکنه"
    print("\n--- Running AI Analysis Test ---")
    print("Result:", classify_category(test_ticket))
