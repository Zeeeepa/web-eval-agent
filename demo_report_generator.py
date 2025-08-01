#!/usr/bin/env python3
"""
Demo report generator to show the structured text report format
"""

import os
from datetime import datetime
from pathlib import Path

def create_demo_report():
    """Create a demo report showing the structured text format"""
    
    # Create reports directory if it doesn't exist
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    
    # Demo data
    test_url = "https://example.com"
    test_duration = 45.7
    tests_executed = 5
    tests_passed = 4
    tests_failed = 1
    success_rate = (tests_passed / tests_executed) * 100
    
    # Generate report content
    report_content = f"""
┌─────────────────────────────────────────────────────────────────┐
│                        TEST EXECUTION SUMMARY                   │
├─────────────────────────────────────────────────────────────────┤
│ Test URL:           {test_url:<40} │
│ Test Duration:      {test_duration:.1f} seconds{' ' * 25} │
│ Tests Executed:     {tests_executed:<40} │
│ Tests Passed:       {tests_passed:<40} │
│ Tests Failed:       {tests_failed:<40} │
│ Success Rate:       {success_rate:.0f}%{' ' * 36} │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                           TEST RESULTS                          │
└─────────────────────────────────────────────────────────────────┘

✅ Test 1: Page Load Test
   Duration: 8.2 seconds
   Status: PASSED
   Details: Page loaded successfully within timeout
   
✅ Test 2: Navigation Test  
   Duration: 12.5 seconds
   Status: PASSED
   Details: All navigation elements are functional
   
✅ Test 3: Content Verification
   Duration: 6.8 seconds
   Status: PASSED
   Details: Main content is properly displayed
   
❌ Test 4: Basic Interaction Test
   Duration: 15.3 seconds
   Status: FAILED
   Details: Contact form submission failed - validation error
   Error: Required field 'email' is missing validation
   
✅ Test 5: Responsive Design Check
   Duration: 2.9 seconds
   Status: PASSED
   Details: Layout adapts correctly to different screen sizes

┌─────────────────────────────────────────────────────────────────┐
│                        PERFORMANCE METRICS                      │
├─────────────────────────────────────────────────────────────────┤
│ Page Load Time:     2.3 seconds                                │
│ First Paint:        1.1 seconds                                │
│ DOM Ready:          1.8 seconds                                │
│ Total Resources:    24 files                                   │
│ Page Size:          1.2 MB                                     │
│ JavaScript Errors:  1 error found                             │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                           RECOMMENDATIONS                       │
└─────────────────────────────────────────────────────────────────┘

🔧 CRITICAL ISSUES:
   • Fix email validation in contact form
   • Address JavaScript error in navigation menu

⚡ PERFORMANCE IMPROVEMENTS:
   • Optimize image sizes to reduce page load time
   • Consider lazy loading for below-fold content

♿ ACCESSIBILITY:
   • Add alt text to decorative images
   • Improve color contrast for better readability

🎯 USER EXPERIENCE:
   • Add loading indicators for form submissions
   • Implement better error messaging

┌─────────────────────────────────────────────────────────────────┐
│                        CONFIGURATION DETAILS                    │
├─────────────────────────────────────────────────────────────────┤
│ Browser:            Chromium                                    │
│ Viewport:           1280x720                                   │
│ User Agent:         Chrome/120.0.0.0                          │
│ Test Environment:   Headless Mode                             │
│ Timeout:            300 seconds                               │
│ Generated:          {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                        │
└─────────────────────────────────────────────────────────────────┘

📊 SUMMARY:
This evaluation identified 1 critical issue that should be addressed immediately.
The website performs well overall with good responsive design and navigation.
Focus on fixing the form validation to improve user experience.

Report generated by Web Eval Agent v2.0.0
For more information, visit: https://github.com/Zeeeepa/web-eval-agent
"""

    # Write report to file
    report_file = reports_dir / "demo-structured-report.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report_content.strip())
    
    print(f"✅ Demo report generated: {report_file}")
    print(f"📄 Report size: {len(report_content)} characters")
    return report_file

if __name__ == "__main__":
    create_demo_report()
