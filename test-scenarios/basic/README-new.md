# 🚀 Web Eval Agent - Standalone UI Testing Tool

> *AI-powered web application testing that actually works.*

![Web Eval Agent](./demo.gif)

## 🔥 What is Web Eval Agent?

Web Eval Agent is a **standalone CLI tool** that uses AI-powered browser automation to test web applications comprehensively. It evaluates user interfaces, validates functionality, and generates detailed reports - perfect for **GitHub PR validation** and **codebase testing**.

## ⚡ Key Features

- 🤖 **AI-Powered Testing** - Uses Google Gemini to intelligently interact with your web app
- 📋 **Instruction-Based** - Define test scenarios in simple Markdown files
- 🌐 **Real Browser Testing** - Uses Playwright for authentic browser automation
- 📊 **Comprehensive Reports** - Generates detailed HTML, JSON, or text reports
- 🚨 **Error Detection** - Captures console errors, network failures, and UI issues
- 📸 **Visual Documentation** - Takes screenshots at key interaction points
- 🔄 **CI/CD Ready** - Perfect for automated testing in GitHub Actions

## 🏁 Quick Start

### Installation

```bash
git clone https://github.com/Zeeeepa/web-eval-agent
cd web-eval-agent
bash install.sh
```

### Set Your API Key

Get your Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey):

```bash
export GEMINI_API_KEY="your_api_key_here"
```

### Run Your First Test

```bash
web-eval --url http://localhost:3000 --instructions INSTRUCTIONS.md
```

That's it! 🎉

## 📋 How It Works

### 1. Create Instruction Files

Define your test scenarios in Markdown format:

```markdown
# Contact Form Test

## Form Validation Test

**Description:**
Test the contact form validation and submission process.

**Steps:**
1. Navigate to the contact page
2. Fill out the contact form with test data
3. Submit the form and verify success message
4. Test form validation with invalid data

**Validations:**
- Form accepts valid input
- Validation errors appear for invalid input
- Success message displays after submission
- No console errors occur

**Expected Outcomes:**
- Form submission works correctly
- Validation prevents invalid submissions
- User receives appropriate feedback
```

### 2. Run Tests

```bash
web-eval --url http://localhost:3000 --instructions contact-test.md --output report.html
```

### 3. Review Results

Web Eval Agent generates comprehensive reports showing:
- ✅ **Test Results** - Pass/fail status for each scenario
- 🐛 **Console Errors** - JavaScript errors and warnings
- 🌐 **Network Activity** - API calls and response status
- 📸 **Screenshots** - Visual documentation of interactions
- ⏱️ **Performance Metrics** - Load times and interaction delays

## 🛠️ CLI Options

```bash
web-eval [OPTIONS]

Required:
  --url TEXT              URL to test (e.g., http://localhost:3000)
  --instructions TEXT     Path to instruction file

Optional:
  --output TEXT          Output file path (default: web-eval-report.html)
  --format [html|json|text]  Report format (default: html)
  --headless             Run browser in headless mode
  --timeout INTEGER      Test timeout in seconds (default: 300)
  --browser [chromium|firefox|webkit]  Browser to use (default: chromium)
  --viewport TEXT        Browser viewport size (default: 1280x720)
  --api-key TEXT         Gemini API key (or set GEMINI_API_KEY env var)
  --verbose              Enable verbose logging
  --debug                Enable debug mode
  --version              Show version
```

## 📝 Instruction File Formats

Web Eval Agent supports multiple instruction formats:

### Markdown (.md)
```markdown
# Test Scenarios

## User Registration Test
**Description:** Test user registration flow
**Steps:**
1. Navigate to signup page
2. Fill registration form
3. Submit and verify account creation
```

### YAML (.yaml/.yml)
```yaml
scenarios:
  - name: "User Registration Test"
    description: "Test user registration flow"
    steps:
      - "Navigate to signup page"
      - "Fill registration form"
      - "Submit and verify account creation"
    validations:
      - "Registration succeeds with valid data"
      - "Validation errors appear for invalid data"
```

### JSON (.json)
```json
{
  "scenarios": [
    {
      "name": "User Registration Test",
      "description": "Test user registration flow",
      "steps": [
        "Navigate to signup page",
        "Fill registration form",
        "Submit and verify account creation"
      ],
      "validations": [
        "Registration succeeds with valid data"
      ]
    }
  ]
}
```

## 🎯 Perfect For

### GitHub PR Testing
```yaml
# .github/workflows/ui-tests.yml
name: UI Tests
on: [pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Start application
        run: npm start &
      - name: Run UI tests
        run: |
          git clone https://github.com/Zeeeepa/web-eval-agent
          cd web-eval-agent
          bash install.sh
          web-eval --url http://localhost:3000 --instructions ../tests/ui-tests.md
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
```

### Local Development Testing
```bash
# Test your React app
npm start &
web-eval --url http://localhost:3000 --instructions tests/smoke-test.md

# Test your Django app
python manage.py runserver &
web-eval --url http://localhost:8000 --instructions tests/admin-test.md

# Test with custom viewport
web-eval --url http://localhost:3000 --instructions mobile-test.md --viewport 375x667
```

### Comprehensive E2E Testing
```bash
# Run full test suite
web-eval --url https://staging.myapp.com --instructions tests/full-e2e.md --format json --output results.json
```

## 📊 Example Report Output

```
📊 Test Results Summary:
   ✅ Passed: 8
   ❌ Failed: 1
   📄 Report: web-eval-report.html
   ⚠️  Errors: 2

🧪 Running test 1/3: Homepage Navigation
   ✅ PASSED (2.3s)

🧪 Running test 2/3: Contact Form Validation
   ❌ FAILED (5.1s)
   Error: Form validation not working for email field

🧪 Running test 3/3: User Registration Flow
   ✅ PASSED (8.7s)
```

## 🔧 Advanced Usage

### Custom Test Scenarios

Create sophisticated test scenarios with priorities and tags:

```markdown
## E-commerce Checkout Test

**Description:** Test the complete checkout process
**Priority:** critical
**Tags:** #checkout #payment #e2e

**Steps:**
1. Add items to cart
2. Proceed to checkout
3. Fill shipping information
4. Select payment method
5. Complete purchase

**Validations:**
- Cart updates correctly
- Shipping form accepts valid addresses
- Payment processing works
- Order confirmation appears
- No console errors during checkout

**Expected Outcomes:**
- Checkout completes successfully
- User receives order confirmation
- Payment is processed correctly
```

### Environment-Specific Testing

```bash
# Test different environments
web-eval --url http://localhost:3000 --instructions dev-tests.md
web-eval --url https://staging.myapp.com --instructions staging-tests.md
web-eval --url https://myapp.com --instructions prod-smoke-tests.md
```

### Headless vs Visual Testing

```bash
# Visual testing (see browser interactions)
web-eval --url http://localhost:3000 --instructions debug-test.md

# Headless testing (for CI/CD)
web-eval --url http://localhost:3000 --instructions ci-tests.md --headless
```

## 🚨 Troubleshooting

### Common Issues

**"web-eval command not found"**
```bash
# Add to your PATH
export PATH="$HOME/.local/bin:$PATH"
# Or reinstall
pip install -e .
```

**"Playwright browsers not installed"**
```bash
python -m playwright install chromium
```

**"API key not found"**
```bash
export GEMINI_API_KEY="your_api_key_here"
# Or pass directly
web-eval --api-key your_key --url http://localhost:3000 --instructions test.md
```

**Tests timing out**
```bash
# Increase timeout
web-eval --url http://localhost:3000 --instructions test.md --timeout 600
```

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Run tests: `python -m pytest`
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🌟 Why Web Eval Agent?

- **No Complex Setup** - Single installation script, ready to use
- **Real Browser Testing** - Tests exactly what users experience
- **AI-Powered** - Intelligently interacts with dynamic content
- **Comprehensive Reports** - Detailed insights into what works and what doesn't
- **CI/CD Ready** - Perfect for automated testing pipelines
- **Framework Agnostic** - Works with React, Vue, Angular, Django, Rails, etc.

## 🚀 Get Started Now

```bash
git clone https://github.com/Zeeeepa/web-eval-agent
cd web-eval-agent
bash install.sh
export GEMINI_API_KEY="your_api_key"
web-eval --url http://localhost:3000 --instructions INSTRUCTIONS.md
```

**Transform your web testing today!** 🎉
