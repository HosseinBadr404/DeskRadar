import config
from normalizer import normalize_persian_text

CATEGORY_FALLBACK_THRESHOLD = getattr(config, "CATEGORY_FALLBACK_THRESHOLD", 0.55)
CATEGORY_MAP = config.CATEGORY_MAP
CATEGORY_LABELS_FA = config.CATEGORY_LABELS_FA
CATEGORY_THRESHOLD = getattr(config, "CATEGORY_THRESHOLD", 0.70)
CATEGORY_KEYWORDS = getattr(config, "CATEGORY_KEYWORDS", {})
CATEGORY_LABEL_BY_CODE = getattr(config, "CATEGORY_LABEL_BY_CODE", {})
CATEGORY_TOP_K = getattr(config, "CATEGORY_TOP_K", 3)
UNKNOWN_CATEGORY = getattr(config, "UNKNOWN_CATEGORY", "unknown")
MODEL_NAME = getattr(
    config,
    "ZERO_SHOT_MODEL_NAME",
    "MoritzLaurer/multilingual-MiniLMv2-L6-mnli-xnli",
)
HYPOTHESIS_TEMPLATE = getattr(
    config,
    "ZERO_SHOT_HYPOTHESIS_TEMPLATE",
    "موضوع این تیکت مربوط به {} است.",
)

MODEL_STRONG_CONFIDENCE = 0.90
RULE_OVERRIDE_MODEL_LIMIT = 0.85

_classifier = None


def get_classifier():
    global _classifier

    if _classifier is None:
        try:
            from transformers import pipeline
        except ImportError as exc:
            raise RuntimeError(
                "کتابخانه transformers نصب نیست. برای اجرای zero-shot category باید transformers و torch نصب باشند."
            ) from exc

        _classifier = pipeline(
            "zero-shot-classification",
            model=MODEL_NAME,
        )

    return _classifier


def get_category_label_fa(category_code: str) -> str:
    return CATEGORY_LABEL_BY_CODE.get(category_code, category_code)


def normalize_score(score) -> float:
    try:
        return round(float(score), 2)
    except (TypeError, ValueError):
        return 0.0


def build_empty_result(reason: str = "متن تیکت خالی است.") -> dict:
    return {
        "category": UNKNOWN_CATEGORY,
        "category_label_fa": get_category_label_fa(UNKNOWN_CATEGORY),
        "category_score": 0.0,
        "category_source": "empty",
        "top_labels": [],
        "matched_keywords": [],
        "reason": reason,
        "model_name": MODEL_NAME,
    }


def build_top_labels(labels: list, scores: list) -> list:
    top_labels = []

    for label, score in zip(labels[:CATEGORY_TOP_K], scores[:CATEGORY_TOP_K]):
        category_code = CATEGORY_MAP.get(label, UNKNOWN_CATEGORY)

        top_labels.append(
            {
                "category_en": category_code,
                "category_label_fa": get_category_label_fa(category_code),
                "score": normalize_score(score),
            }
        )

    return top_labels


def find_keyword_category(clean_text: str) -> dict:
    best_category = UNKNOWN_CATEGORY
    best_matches = []
    best_score = 0.0

    for category_code, keywords in CATEGORY_KEYWORDS.items():
        matches = []
        seen = set()

        for keyword in keywords:
            clean_keyword = normalize_persian_text(keyword)

            if (
                clean_keyword
                and clean_keyword in clean_text
                and clean_keyword not in seen
            ):
                matches.append(clean_keyword)
                seen.add(clean_keyword)

        if not matches:
            continue

        score = min(1.0, 0.55 + (len(matches) * 0.10))

        if score > best_score:
            best_category = category_code
            best_matches = matches
            best_score = score

    return {
        "category": best_category,
        "score": round(best_score, 2),
        "matched_keywords": best_matches,
    }


def classify_with_model(clean_text: str) -> dict:
    classifier = get_classifier()

    result = classifier(
        clean_text,
        candidate_labels=CATEGORY_LABELS_FA,
        hypothesis_template=HYPOTHESIS_TEMPLATE,
        multi_label=False,
    )

    labels = result.get("labels", [])
    scores = result.get("scores", [])

    if not labels or not scores:
        return build_empty_result("مدل zero-shot خروجی معتبری تولید نکرد.")

    best_label = labels[0]
    best_score = normalize_score(scores[0])
    category_code = CATEGORY_MAP.get(best_label, UNKNOWN_CATEGORY)

    return {
        "category": category_code,
        "category_label_fa": get_category_label_fa(category_code),
        "category_score": best_score,
        "category_source": "zero_shot_model",
        "top_labels": build_top_labels(labels, scores),
        "matched_keywords": [],
        "reason": "دسته‌بندی با مدل zero-shot انجام شد.",
        "model_name": MODEL_NAME,
    }


def build_rule_result(
    keyword_result: dict,
    category_source: str,
    reason: str,
    top_labels: list = None,
) -> dict:
    category_code = keyword_result.get("category", UNKNOWN_CATEGORY)
    keyword_score = keyword_result.get("score", 0.0)

    return {
        "category": category_code,
        "category_label_fa": get_category_label_fa(category_code),
        "category_score": keyword_score,
        "category_source": category_source,
        "top_labels": top_labels or [],
        "matched_keywords": keyword_result.get("matched_keywords", []),
        "reason": reason,
        "model_name": MODEL_NAME,
    }


def apply_rule_fallback(clean_text: str, model_result: dict) -> dict:
    keyword_result = find_keyword_category(clean_text)

    model_category = model_result.get("category", UNKNOWN_CATEGORY)
    model_score = normalize_score(model_result.get("category_score", 0.0))
    keyword_category = keyword_result.get("category", UNKNOWN_CATEGORY)
    keyword_score = normalize_score(keyword_result.get("score", 0.0))
    top_labels = model_result.get("top_labels", [])

    if keyword_category == UNKNOWN_CATEGORY:
        if model_category != UNKNOWN_CATEGORY and model_score >= CATEGORY_THRESHOLD:
            return model_result

        model_result["category"] = UNKNOWN_CATEGORY
        model_result["category_label_fa"] = get_category_label_fa(UNKNOWN_CATEGORY)
        model_result["category_source"] = "unknown"
        model_result["matched_keywords"] = []
        model_result["reason"] = (
            "امتیاز مدل پایین بود و قانون fallback هم دسته‌بندی معتبری پیدا نکرد."
        )

        return model_result

    if model_category == UNKNOWN_CATEGORY:
        if keyword_score >= CATEGORY_FALLBACK_THRESHOLD:
            return build_rule_result(
                keyword_result=keyword_result,
                category_source="rule_fallback",
                reason="به دلیل نامشخص بودن خروجی مدل، دسته‌بندی با rule fallback انجام شد.",
                top_labels=top_labels,
            )

        return build_empty_result("مدل و rule fallback دسته‌بندی معتبری پیدا نکردند.")

    if keyword_category == model_category:
        model_result["matched_keywords"] = keyword_result.get("matched_keywords", [])

        if (
            model_score < CATEGORY_THRESHOLD
            and keyword_score >= CATEGORY_FALLBACK_THRESHOLD
        ):
            model_result["category_score"] = max(model_score, keyword_score)
            model_result["category_source"] = "model_rule_agreement"
            model_result["reason"] = (
                "مدل و rule fallback روی یک دسته‌بندی توافق داشتند."
            )

        return model_result

    if (
        keyword_score >= CATEGORY_FALLBACK_THRESHOLD
        and model_score < RULE_OVERRIDE_MODEL_LIMIT
    ):
        return build_rule_result(
            keyword_result=keyword_result,
            category_source="rule_override",
            reason="مدل zero-shot دسته‌بندی متفاوتی پیشنهاد داد، اما keyword rule قوی‌تر بود و category اصلاح شد.",
            top_labels=top_labels,
        )

    if model_score >= MODEL_STRONG_CONFIDENCE:
        return model_result

    if keyword_score >= CATEGORY_FALLBACK_THRESHOLD:
        return build_rule_result(
            keyword_result=keyword_result,
            category_source="rule_override",
            reason="به دلیل تعارض مدل و keyword rule، دسته‌بندی براساس rule قابل اعتمادتر اصلاح شد.",
            top_labels=top_labels,
        )

    return model_result


def classify_category(text: str) -> dict:
    clean_text = normalize_persian_text(text)

    if not clean_text:
        return build_empty_result()

    keyword_result = find_keyword_category(clean_text)

    try:
        model_result = classify_with_model(clean_text)
    except Exception as error:
        if (
            keyword_result.get("category") != UNKNOWN_CATEGORY
            and keyword_result.get("score", 0.0) >= CATEGORY_FALLBACK_THRESHOLD
        ):
            return build_rule_result(
                keyword_result=keyword_result,
                category_source="rule_only_fallback",
                reason=f"مدل zero-shot اجرا نشد و دسته‌بندی با rule fallback انجام شد. خطا: {error}",
                top_labels=[],
            )

        return {
            "category": UNKNOWN_CATEGORY,
            "category_label_fa": get_category_label_fa(UNKNOWN_CATEGORY),
            "category_score": 0.0,
            "category_source": "model_failed",
            "top_labels": [],
            "matched_keywords": [],
            "reason": f"مدل zero-shot اجرا نشد و rule fallback هم نتیجه معتبری نداشت. خطا: {error}",
            "model_name": MODEL_NAME,
        }

    return apply_rule_fallback(clean_text, model_result)


if __name__ == "__main__":
    samples = [
        "سلام، وی پی ان من وصل نمیشه و احراز هویت خطا میده",
        "حجم ایمیل من پر شده و پیام جدید دریافت نمیکنم",
        "کل شرکت اینترنت ندارد و همه کاربران مشکل دارند",
        "پرینتر اتاق مالی چاپ نمیکنه",
        "رمز سامانه را فراموش کردم و وارد حساب کاربری نمیشم",
    ]

    for sample in samples:
        print(classify_category(sample))
