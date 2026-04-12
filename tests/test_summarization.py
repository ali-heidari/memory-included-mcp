"""Unit tests for text summarization functionality"""

import pytest
from unittest.mock import patch, MagicMock
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from mcp_server.summarization import summarize_text, get_summarization_model


class TestSummarization:
    """Test text summarization operations"""

    def test_summarize_short_text(self):
        """Test summarization of short text (should return as-is)"""
        short_text = "Hello world"

        # Mock the model to ensure it's not called for short text
        with patch('mcp_server.summarization.pipeline', MagicMock()) as mock_pipeline:
            result = summarize_text(short_text)

            # Should return original text for short content
            assert result == short_text
            # Pipeline should not be called
            mock_pipeline.assert_not_called()

    def test_summarize_medium_text(self):
        """Test summarization of medium-length text"""
        medium_text = "This is a medium length text that should be summarized. " * 10
        expected_summary = "Medium text summary"

        with patch('mcp_server.summarization.pipeline') as mock_pipeline:
            # Mock the summarization pipeline
            mock_summarizer = MagicMock()
            mock_summarizer.return_value = [{"summary_text": expected_summary}]
            mock_pipeline.return_value = mock_summarizer

            result = summarize_text(medium_text)

            # Should use summarization
            assert result == expected_summary
            mock_pipeline.assert_called_once_with(
                "summarization",
                model="facebook/bart-large-cnn",
                truncation=True
            )
            mock_summarizer.assert_called_once()

    def test_summarize_long_text(self):
        """Test summarization of long text"""
        long_text = "This is a very long text that definitely needs summarization. " * 50
        expected_summary = "Long text comprehensive summary"

        with patch('mcp_server.summarization.pipeline') as mock_pipeline:
            mock_summarizer = MagicMock()
            mock_summarizer.return_value = [{"summary_text": expected_summary}]
            mock_pipeline.return_value = mock_summarizer

            result = summarize_text(long_text)

            assert result == expected_summary
            mock_summarizer.assert_called_once()

    def test_summarize_fallback_on_failure(self):
        """Test fallback behavior when summarization fails"""
        medium_text = "This is medium text that should be summarized but summarization fails. " * 5

        with patch('mcp_server.summarization.pipeline') as mock_pipeline:
            # Mock pipeline to raise exception
            mock_pipeline.side_effect = Exception("Model loading failed")

            result = summarize_text(medium_text)

            # Should fall back to extractive summarization or truncation
            assert isinstance(result, str)
            assert len(result) < len(medium_text)

    def test_summarize_extract_short_sentences(self):
        """Test extractive summarization for short texts"""
        text = "First sentence. Second sentence. Third sentence."

        with patch('mcp_server.summarization.pipeline') as mock_pipeline:
            mock_pipeline.side_effect = Exception("Model failed")

            result = summarize_text(text)

            # Should extract meaningful content
            assert isinstance(result, str)
            assert len(result) > 0

    def test_get_summarization_model(self):
        """Test getting the summarization model"""
        with patch('mcp_server.summarization.pipeline') as mock_pipeline:
            model = get_summarization_model()

            mock_pipeline.assert_called_once_with(
                "summarization",
                model="facebook/bart-large-cnn",
                truncation=True
            )

    @pytest.mark.parametrize("text_length,expected_max_length", [
        (50, 30),    # Short text
        (200, 50),   # Medium text
        (1000, 150), # Long text
    ])
    def test_summary_length_rules(self, text_length, expected_max_length):
        """Test that summary length rules are applied correctly"""
        text = "Word " * text_length

        with patch('mcp_server.summarization.pipeline') as mock_pipeline:
            mock_summarizer = MagicMock()
            mock_summarizer.return_value = [{"summary_text": "Summary text"}]
            mock_pipeline.return_value = mock_summarizer

            result = summarize_text(text)

            # Verify the call was made with appropriate parameters
            call_args = mock_summarizer.call_args
            assert call_args[1]['max_length'] == expected_max_length
            assert call_args[1]['min_length'] == 10  # Default min_length