#!/usr/bin/env python3
"""
Demo script showing the new structured text report format.
"""

import sys
import os
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from web_eval_agent.core.config import Config
from web_eval_agent.core.test_executor import TestResults, TestResult
from web_eval_agent.reporting.reporter import Reporter


def create_sample_test_results():
    """Create sample test results for demonstration."""
    
    # Create sample test results
    test_results = [
        TestResult(
            scenario_name="Login Form Validation",
            passed=True,
            duration=2.5,
            validation_results=[
                {"name": "Username field exists", "passed": True},
                {"name": "Password field exists", "passed": True},
                {"name": "Submit button works", "passed": True}
            ],
            console_logs=["Info: Page loaded", "Info: Form validated"],
            network_requests=[
                {"url": "/api/login", "method": "POST", "status": 200}
            ],
            screenshots=["login_form.png"],
            error_message=None
        ),
        TestResult(
            scenario_name="Navigation Menu Test",
            passed=False,
            duration=1.8,
            validation_results=[
                {"name": "Menu items visible", "passed": True},
                {"name": "Dropdown functionality", "passed": False}
            ],
            console_logs=["Error: Dropdown not responding"],
            network_requests=[],
            screenshots=["nav_menu.png", "nav_error.png"],
            error_message="Dropdown menu failed to open after 5 seconds"
        ),
        TestResult(
            scenario_name="Search Functionality",
            passed=True,
            duration=3.2,
            validation_results=[
                {"name": "Search box present", "passed": True},
                {"name": "Search results display", "passed": True},
                {"name": "Pagination works", "passed": True}
            ],
            console_logs=["Info: Search initiated", "Info: Results loaded"],
            network_requests=[
                {"url": "/api/search", "method": "GET", "status": 200},
                {"url": "/api/search?page=2", "method": "GET", "status": 200}
            ],
            screenshots=["search_results.png"],
            error_message=None
        )
    ]
    
    # Calculate summary
    total_tests = len(test_results)
    passed_tests = sum(1 for r in test_results if r.passed)
    failed_tests = total_tests - passed_tests
    success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
    
    summary = {
        "total_tests": total_tests,
        "passed_tests": passed_tests,
        "failed_tests": failed_tests,
        "success_rate": success_rate
    }
    
    return TestResults(
        test_results=test_results,
        total_duration=sum(r.duration for r in test_results),
        summary=summary
    )


def main():
    """Generate demo reports in different formats."""
    
    # Create sample configuration
    config = Config(
        url="https://example.com/demo-app",
        browser="chromium",
        viewport="1920x1080",
        headless=True,
        report_format="text",
        report_detail_level="structured",
        output_file="examples/reports/demo_structured_report.txt"
    )
    
    # Create sample test results
    results = create_sample_test_results()
    
    # Create reporter
    reporter = Reporter(config)
    
    print("🚀 Generating structured text report demo...")
    
    # Generate structured report
    structured_content = reporter._create_structured_text_report(results)
    
    # Ensure output directory exists
    os.makedirs("examples/reports", exist_ok=True)
    
    # Write structured report
    structured_path = "examples/reports/demo_structured_report.txt"
    with open(structured_path, 'w', encoding='utf-8') as f:
        f.write(structured_content)
    
    print(f"✅ Structured report generated: {structured_path}")
    
    # Also generate comprehensive report for comparison
    config.report_detail_level = "detailed"
    comprehensive_content = reporter._create_comprehensive_text_report(results)
    
    comprehensive_path = "examples/reports/demo_comprehensive_report.txt"
    with open(comprehensive_path, 'w', encoding='utf-8') as f:
        f.write(comprehensive_content)
    
    print(f"✅ Comprehensive report generated: {comprehensive_path}")
    
    # Show preview of structured report
    print("\n" + "="*80)
    print("PREVIEW OF STRUCTURED REPORT:")
    print("="*80)
    print(structured_content[:1000] + "..." if len(structured_content) > 1000 else structured_content)
    print("="*80)
    
    print(f"\n📊 Report Statistics:")
    print(f"   • Total Tests: {results.summary['total_tests']}")
    print(f"   • Success Rate: {results.summary['success_rate']:.1f}%")
    print(f"   • Total Duration: {results.total_duration:.1f}s")
    print(f"   • Report Length: {len(structured_content)} characters")


if __name__ == "__main__":
    main()

