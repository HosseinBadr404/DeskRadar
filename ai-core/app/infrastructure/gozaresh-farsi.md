<div dir="rtl" align="right">

# گزارش پروژه — هوش مصنوعی زیرساخت (AI Infrastructure)

**پروژه:** ServiceDesk Radar — داشبورد هوشمند مدیریت تیکت‌های پشتیبانی IT با هسته‌ی AI فارسی‌محور
**شاخه (Branch):** `ai-infrastructure`
**دامنه‌ی کاری این گزارش:** فقط `ai-core/app/infrastructure/`
**وضعیت:** هر ۲۱ گام نقشه‌ی راه پیاده‌سازی و تست شد؛ اصلاحات بازبینی (Review) هم اعمال شد. ۲۵ تست واحد/یکپارچه با موفقیت پاس شدند.

---

## ۱) این بخش چه کاری انجام می‌دهد؟

این کامپوننت، «روابط پنهان» بین تیکت‌ها و مقاله‌ها را پیدا می‌کند؛ چیزی که تحلیل تک‌تیکتی نمی‌تواند ببیند. با دریافت یک تیکت جدید به‌همراه مجموعه‌ی تیکت‌های قبلی، خروجی زیر (بلوک `intelligence`) را تولید می‌کند:

- **پنج تیکت مشابه برتر** همراه با امتیاز شباهت و سطح تطبیق (`similar` یا `very_similar`).
- **مرتبط‌ترین مقاله‌ی راهنما** (یا `null` اگر امتیاز پایین‌تر از حد آستانه باشد).
- **تشخیص رخداد احتمالی (Incident)**: اینکه آیا چند تیکت مشابه در یک دسته، نشانه‌ی یک مشکل گسترده هستند؛ به‌همراه شدت (`medium`/`high`)، عنوان و دلیل فارسی، شناسه‌ی تیکت‌های مرتبط، میانگین شباهت و پرچم `is_duplicate`.
- **اطلاعات همراه**: نسخه‌ی مدل embedding، زمان پردازش (ms)، و فیلد `error` که در موفقیت `null` است.

این بخش **دسته‌بندی/فوریت/پاسخ تولید نمی‌کند**؛ آن وظیفه‌ی Analyzer AI است. این دو کاملاً مستقل‌اند و ترکیب خروجی‌ها در Backend انجام می‌شود.

---

## ۲) جایگاه در سیستم

پروژه چهار بخش مستقل دارد:

| بخش | مسئولیت |
|---|---|
| Frontend (Next.js) | داشبورد: تیکت‌ها، رخدادها، مقاله‌ها، هشدارها |
| Backend (FastAPI) | داده، دیتابیس، Import CSV، WebSocket، هماهنگ‌سازی |
| Analyzer AI | تحلیل متن فارسی: category، intent، urgency، sentiment، summary، reply |
| **AI Infrastructure** (این بخش) | **embedding، شباهت، بازیابی دانش، تشخیص رخداد** |

Backend از طریق HTTP این سرویس را صدا می‌زند، تیکت جدید و مجموعه‌ی تیکت‌های قبلی را می‌فرستد و خروجی را ذخیره می‌کند.

---

## ۳) معماری

```
infrastructure_config.json  (تنها منبع حقیقت برای آستانه‌ها)
        │
        ▼
EmbeddingModel  (singleton، فقط یک‌بار در startup لود می‌شود)
        │                              │
        ▼                              ▼
similarity_search.py            knowledge_base.py
 (+ qdrant_adapter اختیاری)      (+ qdrant_adapter اختیاری)
        │                              │
        └──────────────┬───────────────┘
                       ▼
              incident_detector.py   (لیست SimilarTicket را پارامتری می‌گیرد؛ هرگز similarity_search را صدا نمی‌زند)
                       │
                       ▼
              __init__.py  →  run_infrastructure() کل خط لوله را هماهنگ می‌کند
                       │
                       ▼
              InfrastructureResult  →  app/main.py (FastAPI)

evaluation.py — فقط آفلاین؛ از بقیه import می‌کند ولی هیچ ماژولی آن را import نمی‌کند.
```

- **مدل embedding:** `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (پشتیبانی بومی از فارسی و متن ترکیبی فارسی/انگلیسی).
- **ذخیره‌سازی بردار:** پیش‌فرض و همیشه‌دردسترس، شباهت کسینوسی خالص با Python است. **Qdrant اختیاری** و کاملاً ایزوله است.

---

## ۴) اجزای پیاده‌سازی‌شده (گام به گام)

| گام | فایل | کار انجام‌شده |
|---|---|---|
| ۱ | `config/infrastructure_config.json` | تنها منبع آستانه‌ها (top_k، آستانه‌های شباهت، حداقل امتیاز مقاله، قوانین رخداد، تنظیمات Qdrant). |
| ۲ | `.env.example` | متغیرهای محیطی اجرا (بدون هیچ آستانه و بدون secret واقعی). |
| ۳ | `app/infrastructure/schemas.py` | همه‌ی مدل‌های Pydantic (ورودی، داخلی، خروجی، گزارش ارزیابی). |
| ۴ | `data/knowledge_articles.json` | ۱۱ مقاله‌ی فارسی پوشش‌دهنده‌ی vpn، email، printer، network، account. |
| ۵ | `data/old_tickets.json` | ۵۵ تیکت نمونه با خوشه‌ی VPN برای سناریوی رخداد و ترکیب وضعیت‌ها. |
| ۶ | `data/evaluation_set.json` | ۶۰ تیکت برچسب‌خورده (۱۲ تیکت در هر دسته). |
| ۷ | `data/similarity_pairs.json` | ۲۳ جفت مشابه + ۲۲ جفت غیرمشابه به‌عنوان ground truth. |
| ۸ تا ۱۱ | `tests/fixtures/*.json` | داده‌های کوچک و قطعی برای تست‌ها (۵ VPN + ۵ printer، ۵ مقاله، جفت‌ها، سناریوی رخداد VPN). |
| ۱۲ | `embedding_model.py` | کلاس singleton مدل، `encode()`، `build_ticket_text()`، خطای `ModelNotReadyError`. |
| ۱۳ | `qdrant_adapter.py` | اتصال اختیاری Qdrant: health_check، ensure_collections، upsert، search + پرچم availability. |
| ۱۴ | `similarity_search.py` | تابع `find_similar_tickets` با حذف self-match، فیلتر بسته/حذف‌شده، آستانه‌های config. |
| ۱۵ | `knowledge_base.py` | بارگذاری مقاله، ساخت embedding با cache (بر اساس model_version و text_hash)، و `find_related_article`. |
| ۱۶ | `incident_detector.py` | تابع `detect_incident_candidate` با شدت medium/high، عنوان و دلیل فارسی، `is_duplicate`. |
| ۱۷ | `__init__.py` | هماهنگ‌کننده (Orchestrator) و API عمومی (سه تابع). |
| ۱۸ | `evaluation.py` | ارزیابی آفلاین: کیفیت شباهت، جاروی آستانه، دقت دسته‌بندی. |
| ۱۹ | `app/main.py` | اپ FastAPI: `/health` و `/analyze-ticket`. |
| ۲۰ | `scripts/seed_embeddings.py` | ساخت cache مقاله‌ها. |
| ۲۱ | `scripts/evaluate_infrastructure.py` | اجرای ارزیابی و تولید `docs/evaluation.md`. |

علاوه بر این‌ها: `requirements.txt`، `README.md`، `.gitignore`، `app/__init__.py` و مجموعه‌ی تست (`tests/`).

---

## ۵) خط لوله‌ی پردازش هر تیکت (per request)

تابع `run_infrastructure()` این مراحل ثابت را اجرا می‌کند:

1. ساخت **متن استاندارد** از عنوان + توضیح (+ دسته‌ی اختیاری).
2. تبدیل به **بردار** با مدل (مدل یک‌بار لود شده و بازاستفاده می‌شود).
3. **یافتن تیکت‌های مشابه**: شباهت کسینوسی، حذف خودتطبیقی، فیلتر تیکت‌های `closed`/`deleted`، نگه‌داشتن موارد بالای آستانه‌ی شباهت، مرتب‌سازی و محدودسازی به `top_k`.
4. **یافتن مقاله‌ی مرتبط** (نزدیک‌ترین مقاله ≥ حداقل امتیاز، در غیر این‌صورت `null`).
5. **تشخیص رخداد**: در میان تیکت‌های مشابهِ هم‌دسته و بالای کف شباهت، اگر تعداد ≥ آستانه‌ی high باشد `high`، اگر در بازه‌ی medium باشد `medium`، وگرنه بدون رخداد.
6. **مونتاژ نتیجه**.

هر مرحله ایزوله است؛ خطای یک مرحله نتایج مراحل قبل را از بین نمی‌برد و در فیلد `error` گزارش می‌شود.

---

## ۶) ارزیابی (Evaluation)

اسکریپت `scripts/evaluate_infrastructure.py` سه سنجش آفلاین را روی داده‌های کامل اجرا و فایل `docs/evaluation.md` را تولید می‌کند:

- **کیفیت شباهت**: میانگین شباهت جفت‌های مشابه در برابر غیرمشابه، فاصله‌ی جداسازی (هدف **بزرگ‌تر از ۰.۱۵**)، نرخ قبولی، و آستانه‌ی پیشنهادی.
- **جاروی آستانه (Threshold Sweep)**: نرخ قبولی برای چند آستانه‌ی کاندید و انتخاب بهترین.
- **دقت دسته‌بندی**: برای هر تیکت ارزیابی، نزدیک‌ترین تیکت‌ها به دسته رأی می‌دهند؛ دقت کلی و به‌تفکیک دسته گزارش می‌شود.

پیش از اجرا، بررسی می‌شود که همه‌ی شناسه‌های جفت‌ها در مجموعه‌ی ارزیابی موجود باشند؛ و اگر فاصله‌ی جداسازی کمتر از هدف بود، هشدار داده می‌شود (بدون دستکاری آستانه‌ها).

---

## ۷) قوانین طراحی (که همیشه رعایت شده‌اند)

1. `run_infrastructure()` هرگز exception پرتاب نمی‌کند؛ خطاها در فیلد `error` می‌آیند.
2. `incident_detector.py` هرگز `similarity_search.py` را import نمی‌کند.
3. مدل هرگز هنگام import لود نمی‌شود؛ فقط در فراخوانی صریح `load()`.
4. همه‌ی آستانه‌های عددی از `infrastructure_config.json` می‌آیند.
5. زیرساخت هرگز از `analyzer/` import نمی‌کند.
6. `evaluation.py` فقط آفلاین است و در مسیر زنده استفاده نمی‌شود.
7. هر فایل داده با Pydantic اعتبارسنجی می‌شود؛ رکورد نامعتبر با WARNING رد می‌شود، نه crash.
8. سرویس بدون Qdrant هم کار می‌کند؛ پیش‌فرض، کسینوسی Python است.

---

## ۸) تست‌ها

مجموعه‌ی تست در `tests/` شامل fixtureهای قطعی و ۲۵ تست است که **همگی پاس شدند**:

- `test_embedding_model.py` — فرمت `build_ticket_text`، خطای `ModelNotReadyError`، نگهبان `ENVIRONMENT=test`.
- `test_similarity_search.py` — «فقط VPN در پنج نتیجه‌ی برتر»، حذف self-match، فیلتر بسته/حذف‌شده، آستانه.
- `test_knowledge_base.py` — مقاله‌ی VPN با امتیاز ≥ ۰.۷۰، نامرتبط → None، بارگذاری از cache در startup دوم (بدون محاسبه‌ی مجدد).
- `test_incident_detector.py` — ۵ تیکت → high، ۲–۳ → medium، ۱ → بدون رخداد، رشته‌های فارسی، `is_duplicate`.
- `test_pipeline.py` — یکپارچه: initialize → ok، سناریوی رخداد VPN → شدت high و مقاله‌ی VPN و `error=None`.

تست‌ها از یک «مدل ساختگی» استفاده می‌کنند، پس برای اجرا نیازی به دانلود مدل واقعی نیست.

---

## ۹) نحوه‌ی اجرا

```bash
cd ai-core
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# ۱) ساخت cache مقاله‌ها
python scripts/seed_embeddings.py

# ۲) اجرای سرویس (Swagger در http://localhost:8001/docs)
uvicorn app.main:app --host 0.0.0.0 --port 8001

# ۳) اجرای ارزیابی (تولید docs/evaluation.md)
python scripts/evaluate_infrastructure.py

# اجرای تست‌ها
pytest
```

---

## ۱۰) وضعیت و کارهای باقی‌مانده

### کامل‌شده (در دامنه‌ی این بخش)
هر ۲۱ گام + تست‌ها + مستندات. همه‌ی وظایف Taskbook بخش ۹ (Infrastructure) پوشش داده شده‌اند.

### باقی‌مانده — در دامنه (کوچک)
- اجرای ارزیابی با **مدل واقعی** یک‌بار و commit کردن `docs/evaluation.md`؛ تأیید اینکه فاصله‌ی جداسازی > ۰.۱۵ است (در غیر این‌صورت جفت‌های غیرمشابه‌ی نامناسب اصلاح شوند، نه آستانه‌ها).
- افزودن یک قانون CI که مطمئن شود `evaluation.py` در مسیر زنده import نمی‌شود (قانون ۶).
- قراردادن فایل‌ها در مسیر درست repo و افزودن `app/__init__.py` خالی.

### باقی‌مانده — خارج از دامنه (مسئول دیگر)
Frontend (بخش ۵)، Backend (بخش ۶)، Database (بخش ۷)، Analyzer AI (بخش ۸)، endpoint ترکیبی Core-AI (بخش ۱۰)، فایل `tickets_sample.csv` (بخش ۱۱)، DevOps/Docker/Compose (بخش ۱۲)، و QA کل لایه‌ها (بخش ۱۳).

---

## ۱۱) قدم بعدی پیشنهادی

1. فایل‌ها را در مسیرهای درست `ai-core/` قرار بده و `app/__init__.py` خالی را اضافه کن.
2. در یک محیط واقعی: `pip install -r requirements.txt`، سپس `seed_embeddings.py` و بعد `evaluate_infrastructure.py` را اجرا کن و `docs/evaluation.md` را بررسی و commit کن.
3. سرویس را با `uvicorn` بالا بیاور و `/health` و `/analyze-ticket` را در Swagger تست کن.
4. قانون CI برای قانون ۶ را اضافه کن.
5. شاخه را commit و push کن و برای ادغام با Backend هماهنگ شو (Backend تیکت‌ها را در `old_tickets` می‌فرستد و خروجی را ذخیره می‌کند).

</div>