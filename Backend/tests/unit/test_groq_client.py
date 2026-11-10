"""Unit tests for GroqClientAdapter."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Optional

from src.adapters.llm.groq_client import GroqClientAdapter
from src.config.settings import Settings


class TestGroqClientAdapter:
    """Test suite for GroqClientAdapter."""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing."""
        mock = Mock(spec=Settings)
        mock.GROQ_API_KEY = "test-api-key-123"
        mock.DEFAULT_GROQ_MODEL = "llama-3.1-70b-versatile"
        return mock

    @pytest.fixture
    def groq_client(self, mock_settings):
        """Create a GroqClientAdapter instance with mocked settings."""
        with patch('src.adapters.llm.groq_client.settings', mock_settings):
            return GroqClientAdapter()

    def test_init_with_default_settings(self, mock_settings):
        """Test initialization with default settings from environment."""
        with patch('src.adapters.llm.groq_client.settings', mock_settings):
            client = GroqClientAdapter()

            assert client.api_key == "test-api-key-123"
            assert client.default_model == "llama-3.1-70b-versatile"

    def test_init_with_custom_api_key(self, mock_settings):
        """Test initialization with custom API key."""
        with patch('src.adapters.llm.groq_client.settings', mock_settings):
            custom_key = "custom-api-key-456"
            client = GroqClientAdapter(api_key=custom_key)

            assert client.api_key == custom_key
            assert client.default_model == "llama-3.1-70b-versatile"

    def test_init_with_custom_model(self, mock_settings):
        """Test initialization with custom default model."""
        with patch('src.adapters.llm.groq_client.settings', mock_settings):
            custom_model = "llama-3.2-90b-text-preview"
            client = GroqClientAdapter(default_model=custom_model)

            assert client.api_key == "test-api-key-123"
            assert client.default_model == custom_model

    def test_init_with_custom_api_key_and_model(self, mock_settings):
        """Test initialization with both custom API key and model."""
        with patch('src.adapters.llm.groq_client.settings', mock_settings):
            custom_key = "custom-api-key-789"
            custom_model = "mixtral-8x7b-32768"
            client = GroqClientAdapter(api_key=custom_key, default_model=custom_model)

            assert client.api_key == custom_key
            assert client.default_model == custom_model

    @patch('src.adapters.llm.groq_client.ChatGroq')
    def test_get_chat_model_with_defaults(self, mock_chat_groq, groq_client):
        """Test getting chat model with default parameters."""
        mock_model = MagicMock()
        mock_chat_groq.return_value = mock_model

        result = groq_client.get_chat_model()

        mock_chat_groq.assert_called_once_with(
            model_name="llama-3.1-70b-versatile",
            temperature=0.7,
            api_key="test-api-key-123"
        )
        assert result == mock_model

    @patch('src.adapters.llm.groq_client.ChatGroq')
    def test_get_chat_model_with_custom_model(self, mock_chat_groq, groq_client):
        """Test getting chat model with custom model name."""
        mock_model = MagicMock()
        mock_chat_groq.return_value = mock_model
        custom_model = "llama-3.2-90b-text-preview"

        result = groq_client.get_chat_model(model=custom_model)

        mock_chat_groq.assert_called_once_with(
            model_name=custom_model,
            temperature=0.7,
            api_key="test-api-key-123"
        )
        assert result == mock_model

    @patch('src.adapters.llm.groq_client.ChatGroq')
    def test_get_chat_model_with_custom_temperature(self, mock_chat_groq, groq_client):
        """Test getting chat model with custom temperature."""
        mock_model = MagicMock()
        mock_chat_groq.return_value = mock_model
        custom_temp = 0.2

        result = groq_client.get_chat_model(temperature=custom_temp)

        mock_chat_groq.assert_called_once_with(
            model_name="llama-3.1-70b-versatile",
            temperature=custom_temp,
            api_key="test-api-key-123"
        )
        assert result == mock_model

    @patch('src.adapters.llm.groq_client.ChatGroq')
    def test_get_chat_model_with_all_custom_params(self, mock_chat_groq, groq_client):
        """Test getting chat model with all custom parameters."""
        mock_model = MagicMock()
        mock_chat_groq.return_value = mock_model
        custom_model = "mixtral-8x7b-32768"
        custom_temp = 0.9

        result = groq_client.get_chat_model(model=custom_model, temperature=custom_temp)

        mock_chat_groq.assert_called_once_with(
            model_name=custom_model,
            temperature=custom_temp,
            api_key="test-api-key-123"
        )
        assert result == mock_model

    @patch('src.adapters.llm.groq_client.ChatGroq')
    def test_get_chat_model_with_zero_temperature(self, mock_chat_groq, groq_client):
        """Test getting chat model with temperature set to 0 (deterministic)."""
        mock_model = MagicMock()
        mock_chat_groq.return_value = mock_model

        result = groq_client.get_chat_model(temperature=0.0)

        mock_chat_groq.assert_called_once_with(
            model_name="llama-3.1-70b-versatile",
            temperature=0.0,
            api_key="test-api-key-123"
        )
        assert result == mock_model

    @patch('src.adapters.llm.groq_client.ChatGroq')
    def test_get_chat_model_with_max_temperature(self, mock_chat_groq, groq_client):
        """Test getting chat model with maximum temperature (creative)."""
        mock_model = MagicMock()
        mock_chat_groq.return_value = mock_model

        result = groq_client.get_chat_model(temperature=1.0)

        mock_chat_groq.assert_called_once_with(
            model_name="llama-3.1-70b-versatile",
            temperature=1.0,
            api_key="test-api-key-123"
        )
        assert result == mock_model

    @patch('src.adapters.llm.groq_client.ChatGroq')
    def test_multiple_model_calls_create_separate_instances(self, mock_chat_groq, groq_client):
        """Test that multiple calls create separate model instances."""
        mock_model_1 = MagicMock()
        mock_model_2 = MagicMock()
        mock_chat_groq.side_effect = [mock_model_1, mock_model_2]

        result_1 = groq_client.get_chat_model(temperature=0.5)
        result_2 = groq_client.get_chat_model(temperature=0.8)

        assert mock_chat_groq.call_count == 2
        assert result_1 == mock_model_1
        assert result_2 == mock_model_2

    def test_groq_client_implements_llm_client_interface(self, groq_client):
        """Test that GroqClientAdapter implements the LLMClient interface."""
        from src.application.ports.outbound.llm_client import LLMClient

        assert isinstance(groq_client, LLMClient)
        assert hasattr(groq_client, 'get_chat_model')
        assert callable(groq_client.get_chat_model)

    @patch('src.adapters.llm.groq_client.ChatGroq')
    def test_chat_model_returns_correct_type(self, mock_chat_groq, groq_client):
        """Test that get_chat_model returns the expected type."""
        mock_model = MagicMock()
        mock_chat_groq.return_value = mock_model

        result = groq_client.get_chat_model()

        assert result is not None
        assert result == mock_model


class TestGroqClientAdapterEdgeCases:
    """Test edge cases and error scenarios."""

    @pytest.fixture
    def mock_settings_no_api_key(self):
        """Mock settings without API key."""
        mock = Mock(spec=Settings)
        mock.GROQ_API_KEY = None
        mock.DEFAULT_GROQ_MODEL = "llama-3.1-70b-versatile"
        return mock

    def test_init_with_none_api_key_from_settings(self, mock_settings_no_api_key):
        """Test initialization when settings have no API key."""
        with patch('src.adapters.llm.groq_client.settings', mock_settings_no_api_key):
            client = GroqClientAdapter()

            assert client.api_key is None
            assert client.default_model == "llama-3.1-70b-versatile"

    def test_init_overrides_none_api_key_with_custom(self, mock_settings_no_api_key):
        """Test that custom API key overrides None from settings."""
        with patch('src.adapters.llm.groq_client.settings', mock_settings_no_api_key):
            client = GroqClientAdapter(api_key="valid-key")

            assert client.api_key == "valid-key"

    @patch('src.adapters.llm.groq_client.ChatGroq')
    def test_get_chat_model_with_empty_string_model(self, mock_chat_groq):
        """Test get_chat_model with empty string as model (should use default)."""
        mock_settings = Mock(spec=Settings)
        mock_settings.GROQ_API_KEY = "test-key"
        mock_settings.DEFAULT_GROQ_MODEL = "llama-3.1-70b-versatile"

        with patch('src.adapters.llm.groq_client.settings', mock_settings):
            client = GroqClientAdapter()
            mock_model = MagicMock()
            mock_chat_groq.return_value = mock_model

            # Empty string is falsy, so should use default
            result = client.get_chat_model(model="")

            mock_chat_groq.assert_called_once_with(
                model_name="llama-3.1-70b-versatile",
                temperature=0.7,
                api_key="test-key"
            )

    def test_client_can_be_instantiated_multiple_times(self):
        """Test that multiple client instances can coexist."""
        mock_settings = Mock(spec=Settings)
        mock_settings.GROQ_API_KEY = "test-key"
        mock_settings.DEFAULT_GROQ_MODEL = "llama-3.1-70b-versatile"

        with patch('src.adapters.llm.groq_client.settings', mock_settings):
            client1 = GroqClientAdapter(api_key="key1")
            client2 = GroqClientAdapter(api_key="key2")

            assert client1.api_key == "key1"
            assert client2.api_key == "key2"
            assert client1.api_key != client2.api_key


class TestGroqClientAdapterIntegration:
    """Integration-style tests (still mocked but testing realistic scenarios)."""

    @pytest.fixture
    def realistic_settings(self):
        """Create realistic settings."""
        mock = Mock(spec=Settings)
        mock.GROQ_API_KEY = "gsk_1234567890abcdefghijklmnopqrstuvwxyz"
        mock.DEFAULT_GROQ_MODEL = "llama-3.1-70b-versatile"
        return mock

    @patch('src.adapters.llm.groq_client.ChatGroq')
    def test_realistic_usage_scenario(self, mock_chat_groq, realistic_settings):
        """Test a realistic usage scenario."""
        with patch('src.adapters.llm.groq_client.settings', realistic_settings):
            # Initialize client
            client = GroqClientAdapter()

            # Create a chat model for general conversation
            mock_chat_model = MagicMock()
            mock_chat_groq.return_value = mock_chat_model

            chat_model = client.get_chat_model(temperature=0.7)

            assert chat_model is not None
            mock_chat_groq.assert_called_with(
                model_name="llama-3.1-70b-versatile",
                temperature=0.7,
                api_key="gsk_1234567890abcdefghijklmnopqrstuvwxyz"
            )

    @patch('src.adapters.llm.groq_client.ChatGroq')
    def test_code_generation_scenario(self, mock_chat_groq, realistic_settings):
        """Test scenario for code generation (low temperature)."""
        with patch('src.adapters.llm.groq_client.settings', realistic_settings):
            client = GroqClientAdapter()
            mock_model = MagicMock()
            mock_chat_groq.return_value = mock_model

            # Code generation typically uses lower temperature
            model = client.get_chat_model(
                model="llama-3.1-70b-versatile",
                temperature=0.2
            )

            mock_chat_groq.assert_called_with(
                model_name="llama-3.1-70b-versatile",
                temperature=0.2,
                api_key="gsk_1234567890abcdefghijklmnopqrstuvwxyz"
            )

    @patch('src.adapters.llm.groq_client.ChatGroq')
    def test_creative_writing_scenario(self, mock_chat_groq, realistic_settings):
        """Test scenario for creative writing (high temperature)."""
        with patch('src.adapters.llm.groq_client.settings', realistic_settings):
            client = GroqClientAdapter()
            mock_model = MagicMock()
            mock_chat_groq.return_value = mock_model

            # Creative writing uses higher temperature
            model = client.get_chat_model(temperature=0.9)

            mock_chat_groq.assert_called_with(
                model_name="llama-3.1-70b-versatile",
                temperature=0.9,
                api_key="gsk_1234567890abcdefghijklmnopqrstuvwxyz"
            )
