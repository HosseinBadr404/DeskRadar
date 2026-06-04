# zero_shot_category.py
from transformers import pipeline
from normalizer import normalize_persian_text
from config import CATEGORY_MAP, CATEGORY_LABELS_FA, CATEGORY_THRESHOLD

print("Loading AI Model weights... Please wait...")

classifier = pipeline(
    "zero-shot-classification", 
    model="MoritzLaurer/multilingual-MiniLMv2-L6-mnli-xnli"
)

def classify_category(text: str) -> dict:
    clean_text = normalize_persian_text(text)

    if not clean_text:
        return {
            "category": "unknown", 
            "category_score": 0.0, 
            "top_labels": []
        }

    result = classifier(
        clean_text,
        candidate_labels=CATEGORY_LABELS_FA,
        hypothesis_template="موضوع این تیکت مربوط به {} است.",
    )

    best_label_fa = result["labels"][0]
    best_score = round(result["scores"][0], 2)
    category_en = CATEGORY_MAP.get(best_label_fa, "unknown")

    # Extract top 3 labels for debugging (Taskbook Page 52 requirement)
    top_labels = []
    for label, score in zip(result["labels"][:3], result["scores"][:3]):
        top_labels.append({
            "category_en": CATEGORY_MAP.get(label, "unknown"),
            "score": round(score, 2)
        })

    # Rule Engine Fallback Rule
    if best_score < CATEGORY_THRESHOLD:
        if "vpn" in clean_text:
            category_en = "vpn"

    return {
        "category": category_en,
        "category_score": best_score,
        "top_labels": top_labels
    }

if __name__ == "__main__":
    test_ticket = "سلام، من نیم ساعت دیگه جلسه دارم ولی vpn قطعه و احراز هویت نمیکنه"
    print("\n--- Running AI Analysis Test ---")
    import pprint
    pprint.pprint(classify_category(test_ticket))