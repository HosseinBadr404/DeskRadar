import os
import pytest
from app.infrastructure.embedding_model import (
    EmbeddingModel,
    ModelNotReadyError,
    build_ticket_text,
    set_model_for_testing,
    reset_model_for_testing,
)


def test_build_ticket_text():
    # Test formatting with title, description, and category
    text = build_ticket_text("VPN connection issue", "Cannot login with MFA", "vpn")
    assert text == "[vpn] VPN connection issue Cannot login with MFA"

    # Test formatting without category
    text_no_cat = build_ticket_text("Printer offline", "Nothing prints")
    assert text_no_cat == "Printer offline Nothing prints"

    # Test empty or none handling
    text_empty = build_ticket_text(None, "   Some description   ")
    assert text_empty == "Some description"


def test_model_not_ready_error(inject_mock_model):
    # Temporarily reset the model instance to test ModelNotReadyError
    reset_model_for_testing()
    model = EmbeddingModel.instance()
    
    with pytest.raises(ModelNotReadyError):
        model.encode("test text")

    # Re-inject mock model for subsequent tests
    set_model_for_testing(inject_mock_model)


def test_test_environment_guard():
    # If ENVIRONMENT is not "test", set_model_for_testing should raise RuntimeError
    original_env = os.environ.get("ENVIRONMENT")
    try:
        os.environ["ENVIRONMENT"] = "production"
        with pytest.raises(RuntimeError) as excinfo:
            set_model_for_testing(None)
        assert "only allowed when ENVIRONMENT=test" in str(excinfo.value)
    finally:
        if original_env is not None:
            os.environ["ENVIRONMENT"] = original_env
        else:
            del os.environ["ENVIRONMENT"]
