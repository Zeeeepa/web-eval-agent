# 🧪 Web Eval Agent Testing Guide

This guide explains how to run tests in the newly structured test suite.

## 📁 Test Structure Overview

The tests are now organized into logical categories:

```
tests/
├── unit/                    # Unit tests for individual components
├── integration/             # Integration tests for system components  
├── api/                     # Tests for external API interactions
├── examples/                # Example applications and demo tests
├── fixtures/                # Test fixtures and shared data
├── conftest.py             # Pytest configuration and fixtures
├── run_tests.py            # Legacy test runner (still works)
└── README.md               # Main documentation
```

## 🚀 Running Tests

### Using Pytest (Recommended)

#### Run All Tests
```bash
pytest tests/
```

#### Run Tests by Category
```bash
# Unit tests only
pytest tests/unit/

# Integration tests only  
pytest tests/integration/

# API tests only
pytest tests/api/

# Example/demo tests only
pytest tests/examples/
```

#### Run Tests by Markers
```bash
# Run only fast tests (exclude slow tests)
pytest -m "not slow" tests/

# Run only tests that don't require API keys
pytest -m "not requires_api_key" tests/

# Run only tests that don't require network
pytest -m "not requires_network" tests/

# Run specific test types
pytest -m unit tests/
pytest -m integration tests/
pytest -m api tests/
```

#### Verbose Output
```bash
# Show detailed test output
pytest -v tests/

# Show test output with print statements
pytest -s tests/

# Show coverage report (if pytest-cov is installed)
pytest --cov=webEvalAgent tests/
```

### Using Legacy Test Runner

The original `run_tests.py` script still works with the new structure:

```bash
# Run basic tests
python tests/run_tests.py --test basic

# Run SSH integration tests
python tests/run_tests.py --test ssh

# Run local webapp tests
python tests/run_tests.py --test local --url http://localhost:3000

# Run all tests
python tests/run_tests.py --test all

# List available tests
python tests/run_tests.py --list
```

## 📊 Report Generation

The Web Eval Agent now supports multiple report formats and detail levels:

### Report Formats
- **HTML** (default): Rich, interactive reports with collapsible sections
- **JSON**: Machine-readable format for integration with other tools
- **TXT**: Human-readable text reports with emojis and structure

### Report Detail Levels
- **Summary**: Concise overview with key metrics and test results
- **Detailed** (default): Comprehensive report with all test information
- **Verbose**: Extensive analysis with recommendations and insights

### Examples

```bash
# Generate summary text report
web-eval --url http://localhost:3000 --instructions test.md --format text --report-detail-level summary

# Generate detailed HTML report (default)
web-eval --url http://localhost:3000 --instructions test.md --format html

# Generate verbose text report with full analysis
web-eval --url http://localhost:3000 --instructions test.md --format text --report-detail-level verbose --output verbose-report.txt
```

## 🔧 Test Configuration

### Environment Variables

Set these environment variables before running tests:

```bash
# Required for most tests
export GEMINI_API_KEY="your_gemini_api_key"

# Optional for GitHub integration tests
export GITHUB_TOKEN="your_github_token"

# Optional for specific tests
export GOOGLE_API_KEY="your_google_api_key"  # Alternative to GEMINI_API_KEY
```

### Pytest Configuration

The `pytest.ini` file configures test discovery and execution:

- **Test Discovery**: Automatically finds test files matching `test_*.py` or `*_test.py`
- **Markers**: Tests are automatically marked based on their location and content
- **Timeout**: Tests timeout after 300 seconds by default
- **Output**: Colored output with short traceback format

### Test Markers

Tests are automatically marked based on their location:

- `unit`: Tests in `tests/unit/`
- `integration`: Tests in `tests/integration/`
- `api`: Tests in `tests/api/`
- `examples`: Tests in `tests/examples/`
- `slow`: Tests with "slow" or "comprehensive" in the name
- `requires_api_key`: Tests with "api_key" in the name
- `requires_network`: Tests in `tests/api/` or with "github" in the name

## 📋 Test Categories Explained

### Unit Tests (`tests/unit/`)
- Test individual functions and components in isolation
- Fast execution, no external dependencies
- Mock external services and APIs
- Examples: API key validation, utility functions

### Integration Tests (`tests/integration/`)
- Test interaction between multiple components
- May require external services (SSH, GitHub)
- Test complete workflows and scenarios
- Examples: GitHub PR integration, SSH connections

### API Tests (`tests/api/`)
- Test external API interactions
- Require network access and API keys
- May be slower due to network latency
- Examples: Google API integration, external service calls

### Example Tests (`tests/examples/`)
- Demonstrate real-world usage scenarios
- Include complete example applications
- Comprehensive end-to-end testing
- Examples: Flask web app testing, full evaluation scenarios

## 🎯 Best Practices

### Writing Tests
1. **Use descriptive test names** that explain what is being tested
2. **Add appropriate markers** for test categorization
3. **Use fixtures** from `conftest.py` for common setup
4. **Mock external dependencies** in unit tests
5. **Test both success and failure scenarios**

### Running Tests
1. **Start with unit tests** for quick feedback
2. **Use markers** to skip tests requiring external resources
3. **Run integration tests** in a controlled environment
4. **Use verbose output** when debugging test failures
5. **Generate reports** to analyze test results

### Debugging
1. **Use `-s` flag** to see print statements
2. **Use `-v` flag** for detailed test output
3. **Run specific test files** to isolate issues
4. **Check environment variables** if tests fail
5. **Review generated reports** for detailed error information

## 🔍 Troubleshooting

### Common Issues

**"No module named 'webEvalAgent'"**
```bash
# Make sure you're running from the project root
cd /path/to/web-eval-agent
pytest tests/
```

**"API key not found"**
```bash
# Set the required environment variable
export GEMINI_API_KEY="your_api_key_here"
```

**"Network connection failed"**
```bash
# Skip network-dependent tests
pytest -m "not requires_network" tests/
```

**"Tests taking too long"**
```bash
# Skip slow tests
pytest -m "not slow" tests/
```

### Getting Help

1. **Check test output** for specific error messages
2. **Review the main README.md** for general setup instructions
3. **Look at example test files** for usage patterns
4. **Use pytest's built-in help**: `pytest --help`
5. **Check the generated reports** for detailed analysis

## 📈 Continuous Integration

For CI/CD pipelines, use these commands:

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests with coverage
pytest --cov=webEvalAgent --cov-report=xml tests/

# Run only fast, non-network tests
pytest -m "not slow and not requires_network" tests/

# Generate machine-readable reports
web-eval --format json --output results.json [other options]
```

This structured approach ensures reliable, maintainable testing for the Web Eval Agent! 🚀

