import json
import tempfile
from pathlib import Path
from app.infrastructure.knowledge_base import KnowledgeBase


def test_knowledge_base_retrieval(inject_mock_model):
    fixture_path = Path(__file__).resolve().parent / "fixtures" / "articles_small.json"
    kb = KnowledgeBase()
    articles = kb.load_articles(str(fixture_path))
    assert len(articles) == 5

    # Prepare temp file for cache path
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        cache_path = tmp.name

    config = {
        "embedding": {"model_version": "mock-v1"},
        "knowledge_base": {
            "article_score_min": 0.70,
            "cache_path": cache_path,
        }
    }

    try:
        # Build embeddings (first run - computes and caches)
        kb.build_article_embeddings(articles, inject_mock_model, config)
        assert kb.articles_indexed == 5

        # Match VPN query
        query_vector = inject_mock_model.encode("MFA/OTP code not working for VPN connection")
        related = kb.find_related_article(query_vector, config)
        assert related is not None
        assert related.article_id == 1  # VPN Article
        assert related.category == "vpn"
        assert related.score >= 0.70

        # Match unrelated query (should return None if score below floor)
        # Using a vector that has no overlapping keywords, e.g. "some random issue"
        unrelated_vector = inject_mock_model.encode("some random issue")
        related_unrelated = kb.find_related_article(unrelated_vector, config)
        # If it matches something with score < 0.70 it returns None
        # With our mock model, "some random issue" has vec[3] = 1.0.
        # The articles in articles_small.json:
        # Article 1 is vpn, 2 is email, 3 is printer, 4 is network, 5 is account.
        # They will all get distinct vectors (not matching 'other'). So cosine similarity with them will be 0.0.
        # 0.0 < 0.70, so it should return None!
        assert related_unrelated is None

    finally:
        # Clean up temporary cache file
        Path(cache_path).unlink(missing_ok=True)


def test_knowledge_base_cache_loading(inject_mock_model):
    fixture_path = Path(__file__).resolve().parent / "fixtures" / "articles_small.json"
    kb1 = KnowledgeBase()
    articles = kb1.load_articles(str(fixture_path))

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        cache_path = tmp.name

    config = {
        "embedding": {"model_version": "mock-v1"},
        "knowledge_base": {
            "article_score_min": 0.70,
            "cache_path": cache_path,
        }
    }

    try:
        # First build writes to cache
        kb1.build_article_embeddings(articles, inject_mock_model, config)

        # Check if cache file was created and is not empty
        assert Path(cache_path).exists()
        assert Path(cache_path).stat().st_size > 0

        # Second build reads from cache
        # We can verify this by checking that it doesn't fail even if the model is not ready
        kb2 = KnowledgeBase()
        # Mock model dimension is 4. Let's load cache into kb2
        kb2.build_article_embeddings(articles, inject_mock_model, config)
        assert kb2.articles_indexed == 5

    finally:
        Path(cache_path).unlink(missing_ok=True)
