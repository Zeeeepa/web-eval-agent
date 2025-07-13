# Web-Eval-Agent Tests

This directory contains comprehensive tests for the web-eval-agent, including tests for local web applications with interactive features.

## Test Files

### Core Tests
- **`simple_test.py`** - Basic functionality and API validation test
- **`test_ssh_demo.py`** - Demonstrates SSH search functionality with AI analysis
- **`test_local_webapp.py`** - Comprehensive local web application testing

### Additional Tests
- **`test_ssh_search.py`** - Direct SSH search on Google (may encounter bot detection)
- **`test_minimal_ssh.py`** - Minimal SSH search test with DuckDuckGo
- **`test_improved_ssh.py`** - Enhanced search with better result extraction
- **`test_direct_mcp.py`** - Direct MCP server testing
- **`test_simple_website.py`** - Simple website evaluation test

### Test Runner
- **`run_tests.py`** - Unified test runner with command-line options

## Quick Start

### 1. Set up your API key
```bash
export GEMINI_API_KEY="your_gemini_api_key_here"
```

### 2. Run basic tests
```bash
# Run basic functionality test
python tests/run_tests.py --test basic

# Run SSH search demonstration
python tests/run_tests.py --test ssh

# Run local webapp test
python tests/run_tests.py --test local

# Run all tests
python tests/run_tests.py --test all
```

## Local Web Application Testing

### Testing Your Local Development Server

The web-eval-agent can test locally hosted applications on any port. Here are common scenarios:

#### React Development Server (port 3000)
```bash
# Start your React app
npm start  # Usually runs on http://localhost:3000

# Test with web-eval-agent
python tests/test_local_webapp.py
```

#### Next.js Application (port 3000)
```bash
# Start your Next.js app
npm run dev  # Usually runs on http://localhost:3000

# Test with web-eval-agent
python tests/test_local_webapp.py
```

#### Express.js Server (port 8000)
```bash
# Start your Express server
node server.js  # Or your server file

# Modify test_local_webapp.py to use http://localhost:8000
python tests/test_local_webapp.py
```

#### Custom Port Applications
```bash
# For applications running on custom ports (e.g., 8080, 5000, 4000)
python tests/run_tests.py --test local --url http://localhost:8080
```

### What the Agent Can Test

The web-eval-agent can interact with and test:

#### 🎯 **Interactive Elements**
- **Forms**: Fill out contact forms, registration forms, search forms
- **Buttons**: Click submit buttons, navigation buttons, action buttons
- **Links**: Navigate through internal and external links
- **Dropdowns**: Select options from dropdown menus
- **Checkboxes & Radio Buttons**: Toggle and select form controls
- **Modals & Popups**: Open and interact with modal dialogs
- **Tabs**: Switch between tab panels and content sections

#### 🔄 **User Workflows**
- **Authentication**: Test login/logout flows (with test credentials)
- **E-commerce**: Browse products, add to cart, checkout process
- **Search**: Use search functionality and evaluate results
- **Navigation**: Test menu navigation and page routing
- **Form Submission**: Complete multi-step forms and wizards
- **File Uploads**: Test file upload functionality (with test files)

#### 📱 **Responsive Design**
- **Mobile Testing**: Resize browser to test mobile layouts
- **Tablet Testing**: Test tablet-sized viewports
- **Desktop Testing**: Verify desktop layout and functionality

#### ⚡ **Performance & UX**
- **Loading Times**: Measure page load performance
- **Error Handling**: Test error scenarios and validation
- **Accessibility**: Basic accessibility evaluation
- **User Experience**: Overall usability assessment

### Example Test Scenarios

#### Testing a Contact Form
```python
task = """
Test the contact form:
1. Fill out all required fields with test data
2. Submit the form and verify success message
3. Test form validation with invalid inputs
4. Check error message clarity and helpfulness
"""
```

#### Testing E-commerce Functionality
```python
task = """
Test the shopping experience:
1. Browse product categories
2. Search for specific products
3. Add items to cart and modify quantities
4. Proceed through checkout process
5. Test payment form validation (don't submit real payment)
"""
```

#### Testing User Authentication
```python
task = """
Test user authentication:
1. Try to access protected pages without login
2. Test login form with valid test credentials
3. Verify successful login redirects correctly
4. Test logout functionality
5. Check password reset flow if available
"""
```

### Customizing Tests for Your Application

#### 1. Modify the URL
Edit `tests/test_local_webapp.py` and change:
```python
"url": "http://localhost:3000",  # Change to your app's URL
```

#### 2. Customize the Test Task
Modify the task description to focus on your app's specific features:
```python
"task": """
Test my specific application features:
1. Test the user dashboard functionality
2. Verify data visualization components
3. Test the settings page and preferences
4. Check the notification system
5. Validate the search and filter features
"""
```

#### 3. Create Feature-Specific Tests
Create new test functions for specific features:
```python
async def test_my_specific_feature():
    test_params = {
        "url": "http://localhost:3000/my-feature",
        "task": "Test this specific feature thoroughly...",
        "headless": False,
        "tool_call_id": "my-feature-test"
    }
    # Run test...
```

### Tips for Effective Testing

#### 🎯 **Be Specific in Your Test Tasks**
- Clearly describe what features to test
- Provide test data to use (names, emails, etc.)
- Specify expected behaviors and outcomes

#### 🔍 **Test Edge Cases**
- Invalid form inputs
- Network error scenarios
- Browser back/forward navigation
- Page refresh during processes

#### 📊 **Request Detailed Reports**
- Ask for specific feedback on usability
- Request performance observations
- Get recommendations for improvements
- Ask for bug reproduction steps

#### 🚀 **Iterative Testing**
- Start with basic functionality tests
- Gradually add more complex scenarios
- Test after each development iteration
- Use feedback to improve your application

### Troubleshooting

#### Common Issues
1. **"Connection refused"** - Make sure your local server is running
2. **"API key not found"** - Set the GEMINI_API_KEY environment variable
3. **"Test hangs"** - Some sites have bot detection; try headless mode
4. **"No results found"** - Check if your app's elements have proper selectors

#### Debug Mode
Run tests with visible browser to see what's happening:
```python
"headless": False,  # Set this in your test parameters
```

#### Verbose Logging
Check the "Operative Control Center" dashboard for detailed logs and screenshots during test execution.

## Contributing

To add new tests:
1. Create a new test file in the `tests/` directory
2. Follow the existing test patterns
3. Add your test to the `run_tests.py` script
4. Update this README with documentation

## Support

For issues or questions about testing:
1. Check the main README.md for setup instructions
2. Verify your GEMINI_API_KEY is correctly set
3. Ensure your local application is running and accessible
4. Review the test logs for specific error messages

