#!/usr/bin/env python3
"""
ServiceDesk Radar — AI Infrastructure
scripts/seed_embeddings.py  (Step 20)

Builds (or refreshes) the article-embedding cache at
data/.cache/article_embeddings.json so the knowledge base is ready to search
on the next startup without recomputing embeddings.

Idempotent: re-running with unchanged articles/model reuses the cache (the
model_version + text_hash check in KnowledgeBase means zero re-encodes).
Does NOT touch Qdrant — it only writes the local cache.

Usage:
    python scripts/seed_embeddings.py [--config CONFIG] [--articles ARTICLES]
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path

# Make `app` importable when this script is run directly from the ai-core root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.infrastructure.embedding_model import EmbeddingModel  # noqa: E402
from app.infrastructure.knowledge_base import KnowledgeBase  # noqa: E402

logger = logging.getLogger("seed_embeddings")

_DEFAULT_CONFIG = "config/infrastructure_config.json"
_DEFAULT_ARTICLES = "data/knowledge_articles.json"


def _load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        config = json.load(fh)
    if not isinstance(config, dict):
        raise ValueError(f"{path} must be a JSON object")
    return config


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Seed knowledge-base article embeddings.")
    parser.add_argument(
        "--config",
        default=os.environ.get("INFRASTRUCTURE_CONFIG_PATH", _DEFAULT_CONFIG),
        help="Path to infrastructure_config.json",
    )
    parser.add_argument(
        "--articles",
        default=os.environ.get("KNOWLEDGE_ARTICLES_PATH", _DEFAULT_ARTICLES),
        help="Path to knowledge_articles.json",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    config = _load_config(args.config)
    emb = config.get("embedding", {})

    model = EmbeddingModel.instance()
    if not model.is_ready:
        logger.info("Loading embedding model '%s' ...", emb.get("model_name"))
        model.load(
            emb.get("model_name"),
            cache_dir=emb.get("cache_dir"),
            model_version=emb.get("model_version"),
        )

    kb = KnowledgeBase()
    articles = kb.load_articles(args.articles)
    count = kb.build_article_embeddings(articles, model, config)  # qdrant=None -> cache only

    cache_path = config.get("knowledge_base", {}).get(
        "cache_path", "data/.cache/article_embeddings.json"
    )
    print(f"Embedded/cached {count} article(s) -> {cache_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())