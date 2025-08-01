# 🧪 Web-Eval Agent Test Suite

This directory contains comprehensive tests for the web-eval agent, including an example Flask application and automated test runners.

## 📁 Contents

### Example Application
- **`example-app/`** - Complete Flask web application for testing
  - **`app.py`** - Main Flask application with multiple features
  - **`templates/`** - HTML templates for all pages
  - **`static/`** - CSS and JavaScript assets
  - **`requirements.txt`** - Python dependencies

### Test Instructions
- **`comprehensive-web-eval-test.md`** - Comprehensive test scenarios covering:
  - Homepage navigation and overview
  - Interactive counter functionality
  - Contact form validation and submission
  - Todo list AJAX operations
  - User registration and authentication flow
  - Interactive elements and API integration
  - Cross-page navigation and state persistence
  - Performance and error monitoring

### Test Runners
- **`run_comprehensive_test.py`** - Python script that:
  - Starts the Flask application on port 5000
  - Waits for server readiness
  - Runs web-eval with comprehensive instructions
  - Captures and displays results
  - Cleans up processes
- **`run_test.sh`** - Shell script wrapper for easy execution

## 🚀 Quick Start

### Prerequisites
1. Set your Gemini API key:
   ```bash
   export GEMINI_API_KEY="your_api_key_here"
   ```

2. Install dependencies:
   ```bash
   pip install flask requests
   ```

### Run Comprehensive Test

From the project root directory:

```bash
# Using the shell script
./tests/run_test.sh

# Or directly with Python
python tests/run_comprehensive_test.py
```

## 🎯 What the Test Does

1. **Starts Flask App** - Launches the example web application on `http://localhost:5000`
2. **Runs 8 Test Scenarios** - Executes comprehensive test instructions covering:
   - Basic navigation and page loading
   - Interactive form elements and validation
   - AJAX operations and API calls
   - User authentication and session management
   - Cross-page state persistence
   - Performance and error monitoring
3. **Generates Report** - Creates a comprehensive text report with:
   - 📊 Test results summary
   - 🔍 Agent steps with emojis
   - 🖥️ Console logs
   - 🌐 Network requests
   - ⏱️ Chronological timeline
4. **Cleanup** - Properly stops the Flask application

## 📊 Example Output

```
🧪 Web-Eval Agent Comprehensive Test Runner
==================================================
🚀 Starting Comprehensive Web-Eval Test
============================================================
🌟 Starting Flask application...
⏳ Waiting for server at http://localhost:5000 to be ready...
✅ Server is ready at http://localhost:5000
🧪 Running web-eval with comprehensive test instructions...

📊 Web-Eval Results:
========================================
🧪 Running test 1/8: Homepage Navigation and Overview Test
   ✅ PASSED (3.8s)
🧪 Running test 2/8: Interactive Counter Functionality Test
   ✅ PASSED (3.5s)
...

📊 Test Results Summary:
   ✅ Passed: 8
   ❌ Failed: 0
   📄 Report: comprehensive-test-report.txt
```

## 📋 Generated Report Format

The test generates a comprehensive text report with the exact format specified:

```
📊 Web Evaluation Report for http://localhost:5000 complete!
📝 Task: Homepage Navigation and Overview Test

🔍 Agent Steps
  📍 1. Navigate → http://localhost:5000
  📍 2. Click "Counter" (navigation link)
  🏁 Flow completed successfully.

🖥️ Console Logs (5)
  1. [log] Web Eval Test App loaded successfully!
  2. [log] Current page: /
  ...

🌐 Network Requests (3)
  1. GET /static/style.css                   200
  2. POST /api/todos                         201
  ...

⏱️ Chronological Timeline
  02:23:09.189 🖥️ Console [log] Web Eval Test App loaded successfully!
  02:23:09.312 ➡️ GET /static/style.css
  02:23:09.318 ⬅️ 200 /static/style.css
  ...
👁️  See the "Operative Control Center" dashboard for live logs.
```

## 🎯 Flask Application Features

The example Flask application includes:

- **Homepage** - Navigation overview with feature cards
- **Counter** - Interactive increment/decrement/reset functionality
- **Forms** - Contact form with validation and error handling
- **Todo List** - AJAX-powered todo management with API endpoints
- **Authentication** - User registration, login, logout, and dashboard
- **Interactive Elements** - Random quotes, slow/error API endpoints
- **Modal Dialogs** - Testing modal interactions
- **API Endpoints** - RESTful APIs for todos, quotes, and testing

## 🔧 Customization

### Adding New Test Scenarios

Edit `comprehensive-web-eval-test.md` to add new test scenarios:

```markdown
## Your New Test

**Description:**
Describe what this test does.

**Steps:**
1. Navigate to the target page
2. Perform specific actions
3. Verify expected outcomes

**Validations:**
- List validation criteria
- Expected behaviors
- Error conditions to check

**Expected Outcomes:**
- What should happen
- Success criteria

**Priority:** high/medium/low
**Tags:** #your-tags
```

### Modifying the Flask App

The Flask application in `example-app/` can be extended with:
- New routes and pages
- Additional API endpoints
- More interactive features
- Database integration
- Authentication enhancements

### Customizing Test Runner

Modify `run_comprehensive_test.py` to:
- Change port numbers
- Adjust timeouts
- Add pre/post test hooks
- Customize report formatting
- Add additional validation

## 🎉 Success Criteria

A successful test run should show:
- ✅ All 8 test scenarios passing
- 📊 Comprehensive text report generated
- 🖥️ Console logs captured
- 🌐 Network requests tracked
- ⏱️ Chronological timeline with precise timestamps
- 🧹 Clean process cleanup

This test suite validates that the web-eval agent can successfully analyze and interact with a real web application while generating the comprehensive text reports with emojis exactly as specified!

