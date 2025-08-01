"""
Pytest configuration and shared fixtures for Web Eval Agent tests.
"""

import os
import pytest
import asyncio
from pathlib import Path
from typing import Generator, Optional

# Add the parent directory to the path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def api_key() -> Optional[str]:
    """Get API key from environment variables."""
    return os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')


@pytest.fixture(scope="session")
def github_token() -> Optional[str]:
    """Get GitHub token from environment variables."""
    return os.getenv('GITHUB_TOKEN')


@pytest.fixture
def skip_if_no_api_key(api_key):
    """Skip test if no API key is available."""
    if not api_key:
        pytest.skip("API key not available (set GEMINI_API_KEY or GOOGLE_API_KEY)")


@pytest.fixture
def skip_if_no_github_token(github_token):
    """Skip test if no GitHub token is available."""
    if not github_token:
        pytest.skip("GitHub token not available (set GITHUB_TOKEN)")


@pytest.fixture
def skip_if_no_network():
    """Skip test if network access is not available."""
    import socket
    try:
        # Try to connect to Google DNS
        socket.create_connection(("8.8.8.8", 53), timeout=3)
    except OSError:
        pytest.skip("Network access not available")


@pytest.fixture
def test_url() -> str:
    """Default test URL for web evaluation tests."""
    return "http://localhost:5000"


@pytest.fixture
def sample_instructions_file(tmp_path) -> Path:
    """Create a sample instructions file for testing."""
    instructions_content = """
# Sample Test Instructions

## Basic Navigation Test

**Description:**
Test basic navigation functionality.

**Steps:**
1. Navigate to the homepage
2. Check that the page loads without errors
3. Verify main navigation elements are present

**Validations:**
- Page loads within 5 seconds
- No console errors present
- Navigation links are clickable

**Expected Outcomes:**
- Homepage displays correctly
- Navigation works smoothly
- No JavaScript errors occur

**Priority:** high
**Tags:** #navigation #basic
"""
    
    instructions_file = tmp_path / "test_instructions.md"
    instructions_file.write_text(instructions_content)
    return instructions_file


@pytest.fixture
def mock_test_results():
    """Create mock test results for testing report generation."""
    from web_eval.test_executor import TestResults, TestResult
    
    # Create a mock test result
    test_result = TestResult(
        scenario_name="Sample Test",
        passed=True,
        duration=2.5,
        error_message=None,
        validation_results=[
            {"validation": "Page loads successfully", "passed": True, "details": "Page loaded in 1.2s"},
            {"validation": "No console errors", "passed": True, "details": "0 errors found"}
        ],
        console_logs=[
            {"type": "log", "text": "Page loaded successfully"},
            {"type": "info", "text": "Navigation initialized"}
        ],
        network_requests=[
            {"method": "GET", "url": "http://example.com/", "response_status": "200"},
            {"method": "GET", "url": "http://example.com/style.css", "response_status": "200"}
        ],
        agent_steps=[
            "Navigate to homepage",
            "Verify page elements",
            "Check for errors"
        ],
        screenshots=["screenshot1.png"]
    )
    
    # Create test results container
    results = TestResults(
        test_results=[test_result],
        total_duration=2.5,
        summary={
            "total_tests": 1,
            "passed_tests": 1,
            "failed_tests": 0,
            "success_rate": 100.0
        },
        errors=[]
    )
    
    return results


def pytest_configure(config):
    """Configure pytest with custom settings."""
    # Add custom markers
    config.addinivalue_line("markers", "unit: Unit tests for individual components")
    config.addinivalue_line("markers", "integration: Integration tests for system components")
    config.addinivalue_line("markers", "api: Tests that interact with external APIs")
    config.addinivalue_line("markers", "examples: Example and demo tests")
    config.addinivalue_line("markers", "slow: Tests that take a long time to run")
    config.addinivalue_line("markers", "requires_api_key: Tests that require API keys to run")
    config.addinivalue_line("markers", "requires_network: Tests that require network access")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test location."""
    for item in items:
        # Add markers based on test file location
        test_path = str(item.fspath)
        
        if "/unit/" in test_path:
            item.add_marker(pytest.mark.unit)
        elif "/integration/" in test_path:
            item.add_marker(pytest.mark.integration)
        elif "/api/" in test_path:
            item.add_marker(pytest.mark.api)
            item.add_marker(pytest.mark.requires_network)
        elif "/examples/" in test_path:
            item.add_marker(pytest.mark.examples)
        
        # Add markers based on test name patterns
        if "api_key" in item.name.lower():
            item.add_marker(pytest.mark.requires_api_key)
        
        if "github" in item.name.lower():
            item.add_marker(pytest.mark.requires_network)
        
        if "slow" in item.name.lower() or "comprehensive" in item.name.lower():
            item.add_marker(pytest.mark.slow)

