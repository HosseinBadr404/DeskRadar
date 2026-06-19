import os
import sys
from pathlib import Path

# Force the test environment variable before any imports
os.environ["ENVIRONMENT"] = "test"

# Make sure `app` is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from app.infrastructure.embedding_model import set_model_for_testing


class MockEmbeddingModel:
    def __init__(self):
        self.model_version = "mock-v1"
        self.dimension = 5
        self.is_ready = True

    def load(self, model_name, cache_dir=None, model_version=None):
        pass

    def encode(self, text: str) -> list[float]:
        return self._vectorize(text)

    def encode_batch(self, texts: list[str]) -> list[list[float]]:
        return [self._vectorize(t) for t in texts]

    def _vectorize(self, text: str) -> list[float]:
        text_lower = text.lower()
        # [vpn, printer, email, network, account]
        vec = [0.0, 0.0, 0.0, 0.0, 0.0]
        if any(kw in text_lower for kw in ["vpn", "mfa", "otp", "احراز هویت"]):
            vec[0] = 1.0
        if any(kw in text_lower for kw in ["printer", "پرینتر", "چاپ", "کاغذ", "spooler"]):
            vec[1] = 1.0
        if any(kw in text_lower for kw in ["email", "ایمیل", "outlook"]):
            vec[2] = 1.0
        if any(kw in text_lower for kw in ["network", "شبکه", "wifi", "dns", "اینترنت"]):
            vec[3] = 1.0
        if any(kw in text_lower for kw in ["account", "حساب", "locked", "قفل"]):
            vec[4] = 1.0

        # if no match, fallback to uniform
        if vec == [0.0, 0.0, 0.0, 0.0, 0.0]:
            vec = [1.0, 1.0, 1.0, 1.0, 1.0]

        # Normalize
        norm = sum(x**2 for x in vec) ** 0.5
        if norm > 0:
            vec = [x / norm for x in vec]
        return vec


@pytest.fixture(autouse=True)
def inject_mock_model():
    mock = MockEmbeddingModel()
    set_model_for_testing(mock)
    yield mock
