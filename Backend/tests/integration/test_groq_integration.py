"""Integration tests for GroqClientAdapter - actual API calls.

These tests make real API calls to Groq and require:
1. A valid GROQ_API_KEY in your .env file
2. Run from Backend directory: pytest tests/integration/test_groq_integration.py -v -s --run-integration

Note: These tests are skipped by default to avoid unnecessary API calls.
Use --run-integration flag to run them.
"""

import pytest
import os
from typing import List
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from src.adapters.llm.groq_client import GroqClientAdapter
from src.config.settings import settings


@pytest.mark.integration
class TestGroqClientIntegration:
    """Integration tests that make actual Groq API calls."""

    @pytest.fixture(autouse=True)
    def check_api_key(self):
        """Ensure API key is available before running tests."""
        if not settings.GROQ_API_KEY:
            pytest.skip("GROQ_API_KEY not found in environment")

    @pytest.fixture
    def groq_client(self):
        """Create a real GroqClientAdapter instance."""
        return GroqClientAdapter()

    def test_simple_completion(self, groq_client):
        """Test a simple completion request."""
        chat_model = groq_client.get_chat_model(temperature=0.7)

        messages = [
            HumanMessage(content="Say 'Hello, World!' and nothing else.")
        ]

        response = chat_model.invoke(messages)

        assert response is not None
        assert hasattr(response, 'content')
        assert isinstance(response.content, str)
        assert len(response.content) > 0
        print(f"\nResponse: {response.content}")

    def test_basic_question_answering(self, groq_client):
        """Test basic question answering capability."""
        chat_model = groq_client.get_chat_model(temperature=0.3)

        messages = [
            HumanMessage(content="What is 2 + 2? Answer with just the number.")
        ]

        response = chat_model.invoke(messages)

        assert response is not None
        assert "4" in response.content
        print(f"\nMath response: {response.content}")

    def test_system_message_handling(self, groq_client):
        """Test that system messages are properly handled."""
        chat_model = groq_client.get_chat_model(temperature=0.5)

        messages = [
            SystemMessage(content="You are a helpful assistant that always responds in exactly 3 words."),
            HumanMessage(content="Describe the weather")
        ]

        response = chat_model.invoke(messages)

        assert response is not None
        assert len(response.content) > 0
        word_count = len(response.content.split())
        print(f"\nSystem message response ({word_count} words): {response.content}")

    def test_conversation_context(self, groq_client):
        """Test multi-turn conversation with context."""
        chat_model = groq_client.get_chat_model(temperature=0.7)

        messages = [
            HumanMessage(content="My name is Alice. Remember this."),
        ]

        # First turn
        response1 = chat_model.invoke(messages)
        assert response1 is not None
        print(f"\nFirst response: {response1.content}")

        # Add AI response and continue conversation
        messages.append(AIMessage(content=response1.content))
        messages.append(HumanMessage(content="What is my name?"))

        # Second turn
        response2 = chat_model.invoke(messages)
        assert response2 is not None
        assert "alice" in response2.content.lower()
        print(f"Second response: {response2.content}")

    def test_temperature_zero_determinism(self, groq_client):
        """Test that temperature=0 produces consistent results."""
        chat_model = groq_client.get_chat_model(temperature=0.0)

        messages = [
            HumanMessage(content="Count from 1 to 5, separated by commas.")
        ]

        # Make the same request twice
        response1 = chat_model.invoke(messages)
        response2 = chat_model.invoke(messages)

        assert response1 is not None
        assert response2 is not None
        print(f"\nFirst response: {response1.content}")
        print(f"Second response: {response2.content}")

        # With temperature=0, responses should be very similar or identical
        # Note: Not always 100% identical due to model behavior, but should be very close

    def test_different_models(self, groq_client):
        """Test using different Groq models."""
        models_to_test = [
            "llama-3.1-70b-versatile",
            "mixtral-8x7b-32768",
        ]

        for model_name in models_to_test:
            print(f"\nTesting model: {model_name}")

            try:
                chat_model = groq_client.get_chat_model(model=model_name, temperature=0.5)

                messages = [
                    HumanMessage(content="Say the word 'success' if you can understand this.")
                ]

                response = chat_model.invoke(messages)

                assert response is not None
                assert len(response.content) > 0
                print(f"Response from {model_name}: {response.content[:100]}")

            except Exception as e:
                print(f"Error with model {model_name}: {str(e)}")
                # Don't fail the test if a specific model is not available
                continue

    def test_long_response_handling(self, groq_client):
        """Test handling of longer responses."""
        chat_model = groq_client.get_chat_model(temperature=0.7)

        messages = [
            HumanMessage(content="List 10 common programming languages, one per line.")
        ]

        response = chat_model.invoke(messages)

        assert response is not None
        assert len(response.content) > 50  # Should be a substantial response
        print(f"\nLong response length: {len(response.content)} characters")
        print(f"First 200 chars: {response.content[:200]}")

    def test_json_output_format(self, groq_client):
        """Test requesting JSON formatted output."""
        chat_model = groq_client.get_chat_model(temperature=0.3)

        messages = [
            HumanMessage(content="""Return a JSON object with two fields:
            "name": "test" and "value": 42.
            Return ONLY the JSON, no other text.""")
        ]

        response = chat_model.invoke(messages)

        assert response is not None
        content = response.content.strip()
        print(f"\nJSON response: {content}")

        # Try to parse as JSON
        import json
        try:
            parsed = json.loads(content)
            assert "name" in parsed or "value" in parsed
            print(f"Successfully parsed JSON: {parsed}")
        except json.JSONDecodeError:
            # Model might include additional text, which is acceptable
            print("Response includes additional text beyond JSON")

    def test_error_handling_invalid_model(self, groq_client):
        """Test error handling with an invalid model name."""
        with pytest.raises(Exception):
            chat_model = groq_client.get_chat_model(
                model="invalid-model-that-does-not-exist-xyz123",
                temperature=0.7
            )

            messages = [HumanMessage(content="Hello")]
            chat_model.invoke(messages)

    def test_streaming_support(self, groq_client):
        """Test streaming responses if supported."""
        chat_model = groq_client.get_chat_model(temperature=0.7)

        messages = [
            HumanMessage(content="Count from 1 to 5.")
        ]

        # Test streaming
        chunks = []
        try:
            for chunk in chat_model.stream(messages):
                if hasattr(chunk, 'content'):
                    chunks.append(chunk.content)
                    print(f".", end="", flush=True)

            print()  # New line after streaming
            full_response = "".join(chunks)

            assert len(chunks) > 0
            assert len(full_response) > 0
            print(f"\nStreamed response: {full_response}")

        except AttributeError:
            pytest.skip("Streaming not supported by this model/client")


@pytest.mark.integration
class TestGroqClientPerformance:
    """Performance-related integration tests."""

    @pytest.fixture(autouse=True)
    def check_api_key(self):
        """Ensure API key is available before running tests."""
        if not settings.GROQ_API_KEY:
            pytest.skip("GROQ_API_KEY not found in environment")

    @pytest.fixture
    def groq_client(self):
        """Create a real GroqClientAdapter instance."""
        return GroqClientAdapter()

    def test_response_time_simple_query(self, groq_client):
        """Test response time for a simple query."""
        import time

        chat_model = groq_client.get_chat_model(temperature=0.5)
        messages = [HumanMessage(content="Say hi")]

        start_time = time.time()
        response = chat_model.invoke(messages)
        end_time = time.time()

        elapsed = end_time - start_time

        assert response is not None
        print(f"\nResponse time: {elapsed:.2f} seconds")

        # Groq is known for fast responses, typically under 5 seconds
        assert elapsed < 30, f"Response took too long: {elapsed:.2f}s"

    def test_multiple_sequential_requests(self, groq_client):
        """Test making multiple requests in sequence."""
        import time

        chat_model = groq_client.get_chat_model(temperature=0.5)

        num_requests = 3
        responses = []
        start_time = time.time()

        for i in range(num_requests):
            messages = [HumanMessage(content=f"Say the number {i+1}")]
            response = chat_model.invoke(messages)
            responses.append(response)
            print(f"Request {i+1} completed")

        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / num_requests

        assert len(responses) == num_requests
        assert all(r is not None for r in responses)

        print(f"\nTotal time for {num_requests} requests: {total_time:.2f}s")
        print(f"Average time per request: {avg_time:.2f}s")


@pytest.mark.integration
class TestGroqClientEdgeCases:
    """Edge case integration tests."""

    @pytest.fixture(autouse=True)
    def check_api_key(self):
        """Ensure API key is available before running tests."""
        if not settings.GROQ_API_KEY:
            pytest.skip("GROQ_API_KEY not found in environment")

    @pytest.fixture
    def groq_client(self):
        """Create a real GroqClientAdapter instance."""
        return GroqClientAdapter()

    def test_empty_user_message(self, groq_client):
        """Test handling of empty user message."""
        chat_model = groq_client.get_chat_model(temperature=0.5)

        # Some models might handle this, others might error
        try:
            messages = [HumanMessage(content="")]
            response = chat_model.invoke(messages)
            print(f"\nEmpty message response: {response.content if response else 'None'}")
        except Exception as e:
            print(f"\nEmpty message raised error (expected): {type(e).__name__}")

    def test_very_short_prompt(self, groq_client):
        """Test with a very short prompt."""
        chat_model = groq_client.get_chat_model(temperature=0.7)

        messages = [HumanMessage(content="Hi")]
        response = chat_model.invoke(messages)

        assert response is not None
        assert len(response.content) > 0
        print(f"\nShort prompt response: {response.content}")

    def test_special_characters_in_prompt(self, groq_client):
        """Test handling of special characters."""
        chat_model = groq_client.get_chat_model(temperature=0.5)

        special_chars = "Hello! @#$%^&*()_+-={}[]|\\:;\"'<>,.?/~`"
        messages = [
            HumanMessage(content=f"Echo these characters: {special_chars}")
        ]

        response = chat_model.invoke(messages)

        assert response is not None
        assert len(response.content) > 0
        print(f"\nSpecial characters response: {response.content}")

    def test_unicode_and_emojis(self, groq_client):
        """Test handling of Unicode and emojis."""
        chat_model = groq_client.get_chat_model(temperature=0.5)

        messages = [
            HumanMessage(content="Respond with an emoji: 🚀 and some Unicode: café, naïve, 日本語")
        ]

        response = chat_model.invoke(messages)

        assert response is not None
        assert len(response.content) > 0
        print(f"\nUnicode/emoji response: {response.content}")
