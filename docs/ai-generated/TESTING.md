# Quick Start: Running Tests

## Installation

```bash
# Install test dependencies
pip install pytest pytest-asyncio playwright

# For Windows or if using uv:
uv pip install pytest pytest-asyncio playwright

# Install Playwright browsers for UI testing
playwright install
# or with uv:
uv run playwright install
```

## Running Tests

### Quick Commands

```bash
# Run all unit tests (recommended for development)
pytest -m unit

# Run all tests
pytest

# Run specific test file
pytest tests/test_main.py

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=. --cov-report=html
```

### Using Test Runner Scripts

**On Windows:**
```bash
run_tests.bat unit          # Unit tests
run_tests.bat all -vv       # All tests, very verbose
run_tests.bat coverage      # With coverage report
run_tests.bat help          # Show all options
```

**On Linux/Mac:**
```bash
./run_tests.sh unit         # Unit tests
./run_tests.sh all -vv      # All tests, very verbose
./run_tests.sh coverage     # With coverage report
./run_tests.sh help         # Show all options
```

### By Category

```bash
# Only unit tests (fast, no external services needed)
pytest -m unit

# Only integration tests
pytest -m integration

# Only API tests
pytest -m api -v

# Only database tests
pytest -m db -v

# UI tests (requires running server)
pytest -m ui --run-skipped -v
```

## Test Files Overview

| File | Tests | Coverage |
|------|-------|----------|
| `test_main.py` | FastAPI endpoints, CORS, language detection | 40+ tests |
| `test_faq_loader.py` | FAQ loading, embeddings, database ops | 20+ tests |
| `test_load_faq.py` | Alternative FAQ loader | 15+ tests |
| `test_scraper_to_text.py` | Web scraping, text cleaning, URL handling | 25+ tests |
| `test_supabase_db_test.py` | Database connections, queries | 18+ tests |
| `test_vector_loader.py` | Vector database operations, embeddings | 25+ tests |
| `test_ui.py` | Playwright UI tests (browser automation) | 15+ tests |

## Running UI Tests

UI tests require the application to be running:

```bash
# Terminal 1: Start the server
uv run uvicorn main:app --host localhost --port 8000

# Terminal 2: Run UI tests
pytest tests/test_ui.py -m ui --run-skipped -v
```

UI tests include:
- Page load and responsiveness
- Form interactions
- API integration
- Error handling
- Performance metrics

## Common Test Commands

```bash
# Development: Just run unit tests
pytest -m unit

# Before committing: Run all tests
pytest

# Debugging a single test
pytest tests/test_main.py::TestAskEndpoint::test_ask_english_question -vv

# Run tests matching a pattern
pytest -k "test_ask" -v

# Stop on first failure
pytest -x

# Show print statements
pytest -s

# Run previous failures only
pytest --lf

# Run with multiple workers (faster)
pytest -n auto
```

## Fixtures Available

The `conftest.py` file provides reusable fixtures:

```python
def test_with_fixtures(
    fastapi_client,           # FastAPI test client
    mock_supabase_client,     # Mocked Supabase
    mock_embedding_model,     # Mocked embeddings
    mock_llm,                 # Mocked language model
    sample_documents,         # Sample test data
    sample_chunks,            # Sample chunks
    temp_file,               # Temporary file
    env_vars                 # Environment variables
):
    pass
```

## Troubleshooting

### Tests fail with import errors
```bash
# Make sure you're in the right directory
cd path/to/vecinita

# Install the package in development mode
pip install -e .
```

### Playwright tests won't run
```bash
# Install browsers
playwright install

# Check that localhost:8000 is accessible
curl http://localhost:8000/health
```

### Database tests fail
```bash
# Check environment variables
echo $SUPABASE_URL
echo $SUPABASE_KEY

# Tests use mocks by default, so DB shouldn't be needed
```

## Test Results Interpretation

```
PASSED  ✓ Test executed successfully
FAILED  ✗ Test assertion failed
SKIPPED ⊘ Test was skipped (usually marked with @pytest.mark.skip)
ERROR   ✗ Test errored (exception during execution)
```

## Coverage Report

After running `pytest --cov=.`:

```bash
# View in terminal
pytest --cov=. --cov-report=term-missing

# Generate HTML report
pytest --cov=. --cov-report=html
# Open htmlcov/index.html in browser
```

## Tips

1. **Speed**: Unit tests run fastest, use them during development
   ```bash
   pytest -m unit --tb=short
   ```

2. **Debug**: Add `-vv` for very verbose output and `-s` to see print statements
   ```bash
   pytest tests/test_main.py -vv -s
   ```

3. **Focus**: Run only tests for the file you're working on
   ```bash
   pytest tests/test_main.py -v
   ```

4. **Watch mode**: Use pytest-watch to re-run tests on file changes
   ```bash
   pip install pytest-watch
   ptw tests/ -- -m unit
   ```

5. **Parallel execution**: Run tests faster with pytest-xdist
   ```bash
   pip install pytest-xdist
   pytest -n auto
   ```

## Writing New Tests

See `tests/README.md` for detailed information on:
- Test structure and naming
- Using mocks and fixtures
- Writing different test types
- Best practices

Quick template:

```python
import pytest

@pytest.mark.unit
class TestMyFeature:
    """Test my new feature."""
    
    def test_something_works(self, fastapi_client):
        """Test that something works."""
        # Arrange
        expected = "result"
        
        # Act
        response = fastapi_client.get("/endpoint")
        
        # Assert
        assert response.status_code == 200
        assert response.json() == expected
```

## CI/CD Integration

For GitHub Actions, GitLab CI, etc:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    pip install pytest pytest-asyncio
    pytest -v --tb=short
```

## Next Steps

- [ ] Run unit tests to verify setup: `pytest -m unit`
- [ ] Check specific module: `pytest tests/test_main.py -v`
- [ ] Review coverage: `pytest --cov=.`
- [ ] Run all tests: `pytest`
- [ ] Start server and run UI tests: `pytest -m ui --run-skipped`

## Get Help

```bash
# Show pytest help
pytest --help

# Show available markers
pytest --markers

# Run tests matching pattern
pytest -k "ask" -v

# Show test collection without running
pytest --collect-only
```
