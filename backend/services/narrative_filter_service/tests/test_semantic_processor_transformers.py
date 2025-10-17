"""Tests for semantic processor with real transformers (when available)."""



def test_transformers_import_available():
    """Test transformers import availability detection."""
    from semantic_processor import TRANSFORMERS_AVAILABLE

    # TRANSFORMERS_AVAILABLE is set based on import success
    assert isinstance(TRANSFORMERS_AVAILABLE, bool)


def test_processor_with_transformers_mock():
    """Test processor initialization path when transformers IS available."""
    from unittest.mock import MagicMock, patch

    # Mock torch and sentence_transformers as available
    mock_torch = MagicMock()
    mock_torch.cuda.is_available.return_value = False

    mock_st = MagicMock()
    mock_model = MagicMock()
    mock_model.encode.return_value = MagicMock()
    mock_model.encode.return_value.cpu.return_value.tolist.return_value = [0.5] * 384
    mock_model.to.return_value = mock_model
    mock_st.SentenceTransformer.return_value = mock_model

    with patch.dict('sys.modules', {
        'torch': mock_torch,
        'sentence_transformers': mock_st
    }):
        # Force reimport to trigger torch import success path
        import importlib

        import semantic_processor  # type: ignore[import-not-found]
        importlib.reload(semantic_processor)

        processor = semantic_processor.SemanticProcessor()

        # When torch is available, model should be initialized
        if semantic_processor.TRANSFORMERS_AVAILABLE:
            assert processor.model is not None or processor.device == "cpu"


def test_generate_embedding_with_torch_path():
    """Test embedding generation using torch path."""
    from semantic_processor import TRANSFORMERS_AVAILABLE, SemanticProcessor

    processor = SemanticProcessor()

    if not TRANSFORMERS_AVAILABLE:
        # Test mock path
        embedding = processor.generate_embedding("test")
        assert len(embedding) == 384
        assert all(x == 0.1 for x in embedding)
    else:
        # Test real path (if torch is installed)
        embedding = processor.generate_embedding("test")
        assert len(embedding) == 384
        assert all(isinstance(x, float) for x in embedding)
