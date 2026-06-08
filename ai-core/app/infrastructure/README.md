# AI Infrastructure – `ai-core/app/infrastructure`

Three components make up the AI layer. Each wraps a Qdrant collection and degrades gracefully to an in-memory fallback when Qdrant is unavailable.

| File | Responsibility |
|---|---|
| `embedding_model.py` | Singleton model loader + text normalization + encoding |
| `similarity_search.py` | Store and query ticket embeddings (`tickets_embedding` collection) |
| `knowledge_base.py` | Store and query article embeddings (`knowledge_articles` collection) |

**Embedding model:** `paraphrase-multilingual-MiniLM-L12-v2` → 384-dim cosine vectors.  
**Vector DB:** Qdrant — `docker run -p 6333:6333 qdrant/qdrant`

---

### 🧠 AI Core Architecture & Data Flow

```mermaid
graph TD
    %% بخش اول: جستجوی معنایی تیکت‌ها
    subgraph Semantic Search Pipeline
        T1[Ticket] --> TB[Text Builder]
        TB --> EM[Embedding Model]
        EM --> V[Vector]
        V --> SS[Similarity Search]
        SS --> RT[Related Tickets]
    end

    %% بخش دوم: بازیابی دانش
    subgraph Knowledge Base Retrieval
        T2[Ticket] --> KR[Knowledge Retrieval]
        KR --> SA[Suggested Article]
    end

    %% بخش سوم: تشخیص رخداد
    subgraph Incident Detection
        TS[Ticket Stream] --> ID[Incident Detector]
        ID --> IA[Incident Alert]
    end

    %% استایل‌دهی رنگی به باکس‌ها
    style T1 fill:#e1f5fe,stroke:#0288d1,stroke-width:2px
    style T2 fill:#e1f5fe,stroke:#0288d1,stroke-width:2px
    style TS fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    style RT fill:#e8f5e9,stroke:#388e3c,stroke-width:2px
    style SA fill:#e8f5e9,stroke:#388e3c,stroke-width:2px
    style IA fill:#ffebee,stroke:#d32f2f,stroke-width:2px
```
