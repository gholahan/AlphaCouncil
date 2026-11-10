# Groq Client Testing Guide

This document explains how to run the tests for the Groq client adapter.

## Setup

Make sure you have installed all dependencies including the test requirements:

```bash
# Activate your virtual environment
.\.venv\Scripts\activate  # Windows PowerShell
# or
source .venv/bin/activate  # Linux/Mac

# Install pydantic-settings if not already installed
pip install pydantic-settings python-dotenv
```

## Test Structure

### Unit Tests
**Location:** `tests/unit/test_groq_client.py`
- **20 test cases** covering initialization, model creation, and edge cases
- Uses mocking to avoid actual API calls
- Fast and safe to run anytime
- No API key required

### Integration Tests
**Location:** `tests/integration/test_groq_integration.py`
- **16 test cases** that make real API calls to Groq
- Tests actual LLM behavior, streaming, error handling, and performance
- Requires a valid `GROQ_API_KEY` in your `.env` file
- **Skipped by default** to avoid unnecessary API usage and costs

## Running Tests

**Important:** Always run pytest from the `Backend` directory:

```bash
cd C:\Users\DELL\AlphaCouncil\Backend
```

### Run Unit Tests (Mocked - No API calls)

```bash
# Run all unit tests for Groq client
.\.venv\Scripts\python.exe -m pytest tests/unit/test_groq_client.py -v

# Run with more details
.\.venv\Scripts\python.exe -m pytest tests/unit/test_groq_client.py -v -s

# Run a specific test
.\.venv\Scripts\python.exe -m pytest tests/unit/test_groq_client.py::TestGroqClientAdapter::test_init_with_default_settings -v
```

### Run Integration Tests (Real API calls)

```bash
# First, make sure you have GROQ_API_KEY in your .env file
# Then run with the --run-integration flag:

.\.venv\Scripts\python.exe -m pytest tests/integration/test_groq_integration.py -v -s --run-integration

# Run a specific integration test
.\.venv\Scripts\python.exe -m pytest tests/integration/test_groq_integration.py::TestGroqClientIntegration::test_simple_completion -v -s --run-integration
```

### Run All Tests

```bash
# Run only unit tests (skip integration)
.\.venv\Scripts\python.exe -m pytest tests/ -v -m "not integration"

# Run all tests including integration (requires API key and --run-integration flag)
.\.venv\Scripts\python.exe -m pytest tests/ -v -s --run-integration

# Just collect tests without running them
.\.venv\Scripts\python.exe -m pytest tests/unit/test_groq_client.py -v --collect-only
.\.venv\Scripts\python.exe -m pytest tests/integration/test_groq_integration.py -v --collect-only
```

## Test Coverage

### Unit Tests Cover:
- ✅ Default initialization from settings
- ✅ Custom API key and model initialization
- ✅ Chat model creation with different parameters
- ✅ Temperature settings (0.0 to 1.0)
- ✅ Multiple model instances
- ✅ Edge cases (None API key, empty strings)
- ✅ Interface implementation verification
- ✅ Realistic usage scenarios

### Integration Tests Cover:
- ✅ Simple completions
- ✅ Question answering
- ✅ System message handling
- ✅ Multi-turn conversations with context
- ✅ Temperature=0 determinism
- ✅ Different Groq models (llama-3.1-70b, mixtral-8x7b)
- ✅ Long response handling
- ✅ JSON output formatting
- ✅ Streaming support
- ✅ Error handling (invalid models)
- ✅ Response time measurements
- ✅ Special characters and Unicode/emoji handling

## Environment Setup

Create a `.env` file in the `Backend` directory with:

```env
GROQ_API_KEY=your_groq_api_key_here
DEFAULT_GROQ_MODEL=llama-3.1-70b-versatile
```

Get your Groq API key from: https://console.groq.com

## Pytest Configuration

The project includes:
- `pytest.ini` - Main pytest configuration
- `tests/conftest.py` - Shared fixtures and pytest hooks

### Custom Markers

- `@pytest.mark.integration` - Integration tests (require `--run-integration`)
- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.slow` - Slow running tests

## Troubleshooting

### "ModuleNotFoundError: No module named 'src'"
**Solution:** Make sure you're running pytest from the `Backend` directory, not from the root `AlphaCouncil` directory.

### "ModuleNotFoundError: No module named 'langchain_groq'"
**Solution:** Install dependencies:
```bash
pip install langchain-groq langchain-core
```

### "ModuleNotFoundError: No module named 'pydantic_settings'"
**Solution:** Install pydantic-settings:
```bash
pip install pydantic-settings python-dotenv
```

### Integration tests are being skipped
**Solution:** Add the `--run-integration` flag to run them:
```bash
.\.venv\Scripts\python.exe -m pytest tests/integration/test_groq_integration.py -v -s --run-integration
```

### "ValidationError: DATABASE_URL"
**Solution:** This has been fixed. `DATABASE_URL` is now optional in settings.py.

## Quick Reference

```bash
# Quick commands (run from Backend directory)

# Unit tests only (fast, no API calls)
.\.venv\Scripts\python.exe -m pytest tests/unit/test_groq_client.py -v

# Integration tests (requires API key and --run-integration flag)
.\.venv\Scripts\python.exe -m pytest tests/integration/test_groq_integration.py -v -s --run-integration

# All tests except integration
.\.venv\Scripts\python.exe -m pytest tests/ -v -m "not integration"

# See what tests would run
.\.venv\Scripts\python.exe -m pytest tests/ -v --collect-only
```

## Expected Results

### Unit Tests
All 20 unit tests should pass quickly (< 1 second) since they use mocking.

### Integration Tests
16 integration tests will make real API calls:
- Each test may take 1-5 seconds
- Total runtime: ~30-60 seconds
- You'll see actual API responses printed with the `-s` flag
- Some tests may skip if certain features aren't available

## Notes

- **Cost:** Integration tests make real API calls and will consume Groq API credits
- **Rate Limits:** Running integration tests repeatedly may hit rate limits
- **API Key:** Integration tests check for API key and skip if not found
- **Default Behavior:** Integration tests are skipped by default to prevent accidental API usage
