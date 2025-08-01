#!/usr/bin/env python3
"""
Demo script to showcase the enhanced report generation capabilities.
"""

import sys
import asyncio
from datetime import datetime
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, '.')

from web_eval.config import Config
from web_eval.test_executor import TestResults, TestResult
from web_eval.reporter import Reporter

def create_mock_test_results():
    """Create comprehensive mock test results for demonstration."""
    
    # Test 1: Successful homepage test
    test1 = TestResult(
        scenario_name='Homepage Navigation and Overview Test',
        passed=True,
        duration=2.3,
        error_message=None,
        validation_results=[
            {'validation': 'Homepage loads within 3 seconds', 'passed': True, 'details': 'Page loaded in 1.2s'},
            {'validation': 'No JavaScript console errors on page load', 'passed': True, 'details': '0 errors detected'},
            {'validation': 'All navigation links are functional', 'passed': True, 'details': 'Found 5 working navigation links'},
            {'validation': 'Counter value is displayed correctly', 'passed': True, 'details': 'Counter shows initial value: 0'},
            {'validation': 'Page title and meta information are present', 'passed': True, 'details': 'Title: "Home - Web Eval Test App"'}
        ],
        console_logs=[
            {'type': 'log', 'text': 'Page loaded successfully'},
            {'type': 'info', 'text': 'Navigation initialized with 5 menu items'},
            {'type': 'log', 'text': 'Counter component ready with initial value 0'},
            {'type': 'info', 'text': 'Bootstrap CSS loaded successfully'}
        ],
        network_requests=[
            {'method': 'GET', 'url': 'http://localhost:5000/', 'response_status': '200'},
            {'method': 'GET', 'url': 'http://localhost:5000/static/bootstrap.min.css', 'response_status': '200'},
            {'method': 'GET', 'url': 'http://localhost:5000/static/fontawesome.css', 'response_status': '200'},
            {'method': 'GET', 'url': 'http://localhost:5000/static/app.js', 'response_status': '200'}
        ],
        agent_steps=[
            'Navigate to homepage at http://localhost:5000',
            'Verify page loads completely without errors',
            'Check navigation links are present and clickable',
            'Examine page structure and main content areas',
            'Test counter display functionality',
            'Validate page title and meta information'
        ],
        screenshots=['homepage_loaded.png', 'navigation_verified.png']
    )
    
    # Test 2: Failed contact form test
    test2 = TestResult(
        scenario_name='Contact Form Validation Test',
        passed=False,
        duration=5.7,
        error_message='Form validation failed: Email field does not show error for invalid input',
        validation_results=[
            {'validation': 'Form accepts valid input', 'passed': True, 'details': 'Valid form data accepted'},
            {'validation': 'Validation errors appear for invalid input', 'passed': False, 'details': 'Email validation not working properly'},
            {'validation': 'Success message displays after submission', 'passed': True, 'details': 'Success message shown correctly'},
            {'validation': 'No console errors occur', 'passed': False, 'details': '2 JavaScript errors detected'}
        ],
        console_logs=[
            {'type': 'log', 'text': 'Contact form initialized'},
            {'type': 'error', 'text': 'Uncaught TypeError: Cannot read property "validate" of undefined at contact.js:45'},
            {'type': 'warn', 'text': 'Email validation function not found'},
            {'type': 'error', 'text': 'Form validation library failed to load'},
            {'type': 'info', 'text': 'Form submitted with potentially invalid data'}
        ],
        network_requests=[
            {'method': 'GET', 'url': 'http://localhost:5000/contact', 'response_status': '200'},
            {'method': 'GET', 'url': 'http://localhost:5000/static/contact.js', 'response_status': '404'},
            {'method': 'POST', 'url': 'http://localhost:5000/contact/submit', 'response_status': '200'},
            {'method': 'GET', 'url': 'http://localhost:5000/static/validator.js', 'response_status': '404'}
        ],
        agent_steps=[
            'Navigate to contact form page',
            'Fill out form with test data',
            'Test form validation with invalid email',
            'Submit form and check response',
            'Verify error handling'
        ],
        screenshots=['contact_form.png', 'validation_error.png', 'form_submitted.png']
    )
    
    # Test 3: Successful counter functionality test
    test3 = TestResult(
        scenario_name='Interactive Counter Functionality Test',
        passed=True,
        duration=3.1,
        error_message=None,
        validation_results=[
            {'validation': 'Counter increments correctly', 'passed': True, 'details': 'Counter increased from 0 to 5'},
            {'validation': 'Counter decrements correctly', 'passed': True, 'details': 'Counter decreased from 5 to 2'},
            {'validation': 'Reset button works', 'passed': True, 'details': 'Counter reset to 0'},
            {'validation': 'State consistency maintained', 'passed': True, 'details': 'No race conditions detected'}
        ],
        console_logs=[
            {'type': 'log', 'text': 'Counter page loaded'},
            {'type': 'info', 'text': 'Counter initialized with value: 0'},
            {'type': 'log', 'text': 'Increment button clicked 5 times'},
            {'type': 'log', 'text': 'Decrement button clicked 3 times'},
            {'type': 'log', 'text': 'Reset button clicked, counter reset to 0'}
        ],
        network_requests=[
            {'method': 'GET', 'url': 'http://localhost:5000/counter', 'response_status': '200'},
            {'method': 'POST', 'url': 'http://localhost:5000/counter/increment', 'response_status': '200'},
            {'method': 'POST', 'url': 'http://localhost:5000/counter/decrement', 'response_status': '200'},
            {'method': 'POST', 'url': 'http://localhost:5000/counter/reset', 'response_status': '200'}
        ],
        agent_steps=[
            'Navigate to counter page (/counter)',
            'Verify current counter value is displayed',
            'Click increment button 5 times',
            'Click decrement button 3 times',
            'Click reset button and verify counter resets to 0'
        ],
        screenshots=['counter_initial.png', 'counter_incremented.png', 'counter_reset.png']
    )
    
    # Create test results container
    results = TestResults(
        test_results=[test1, test2, test3],
        total_duration=11.1,
        summary={
            'total_tests': 3,
            'passed_tests': 2,
            'failed_tests': 1,
            'success_rate': 66.7
        },
        errors=[
            'Contact form validation not working properly',
            'Missing JavaScript files: contact.js, validator.js'
        ]
    )
    
    return results

async def generate_demo_reports():
    """Generate all three types of reports for demonstration."""
    
    print("🧪 Web Eval Agent - Report Generation Demo")
    print("=" * 50)
    
    # Create mock test results
    results = create_mock_test_results()
    
    # Create base config
    config = Config(
        url='http://localhost:5000',
        instructions_file='simple-test.md',
        api_key='demo-key',
        output_file='demo-report',
        report_format='text',
        browser='chromium',
        headless=True,
        viewport='1280x720'
    )
    
    print(f"📊 Generated mock test results:")
    print(f"   • Total Tests: {results.summary['total_tests']}")
    print(f"   • Passed: {results.summary['passed_tests']}")
    print(f"   • Failed: {results.summary['failed_tests']}")
    print(f"   • Success Rate: {results.summary['success_rate']:.1f}%")
    print()
    
    reporter = Reporter(config)
    
    # Generate summary report
    print("📋 Generating Summary Report...")
    config.report_detail_level = 'summary'
    config.output_file = 'demo-summary-report.txt'
    summary_path = await reporter._generate_text_report(results)
    print(f"   ✅ Generated: {summary_path}")
    
    # Generate detailed report
    print("📋 Generating Detailed Report...")
    config.report_detail_level = 'detailed'
    config.output_file = 'demo-detailed-report.txt'
    detailed_path = await reporter._generate_text_report(results)
    print(f"   ✅ Generated: {detailed_path}")
    
    # Generate verbose report
    print("📋 Generating Verbose Report...")
    config.report_detail_level = 'verbose'
    config.output_file = 'demo-verbose-report.txt'
    verbose_path = await reporter._generate_text_report(results)
    print(f"   ✅ Generated: {verbose_path}")
    
    print()
    print("🎉 All reports generated successfully!")
    print()
    print("📁 Generated Files:")
    print(f"   • {summary_path} - Concise overview")
    print(f"   • {detailed_path} - Comprehensive details")
    print(f"   • {verbose_path} - Full analysis with recommendations")
    
    return [summary_path, detailed_path, verbose_path]

if __name__ == "__main__":
    asyncio.run(generate_demo_reports())

