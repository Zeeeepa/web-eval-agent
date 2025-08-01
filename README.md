# 🚀 Web Eval Agent - AI-Powered Web Application Testing

> *Autonomous web application testing powered by AI - Let the agent test your apps while you focus on building.*

![Demo](demo.gif)

## 🔥 What is Web Eval Agent?

Web Eval Agent is an AI-powered testing framework that autonomously navigates, tests, and evaluates web applications. It uses advanced browser automation with AI to provide comprehensive testing reports, including UX evaluation, performance analysis, and bug detection.

## ⚡ Key Features

- 🤖 **AI-Powered Testing** - Intelligent test execution using Google Gemini
- 🌐 **Full Browser Automation** - Real browser testing with Playwright
- 📊 **Comprehensive Reports** - Detailed HTML and structured text reports
- 🚨 **Error Detection** - Captures console errors, network failures, and UX issues
- 📱 **Responsive Testing** - Multi-viewport and device testing
- 🔄 **CI/CD Integration** - Easy integration with development workflows
- 📈 **Performance Monitoring** - Page load times and interaction metrics

## 🏁 Quick Start

### 1. Clone and Install

```bash
# Clone the repository
git clone https://github.com/Zeeeepa/web-eval-agent.git
cd web-eval-agent

# Run the installation script
bash install.sh
```

The `install.sh` script will:
- Install Python dependencies using `uv`
- Install Playwright browsers
- Set up the project structure
- Display instructions to configure environment variables

### 2. Configure Environment Variables

After running `install.sh`, you'll see instructions to configure your environment:

```bash
# Edit the .env file to add your API keys
nano .env
```

Add the following variables to your `.env` file:
```env
# Required: Google Gemini API Key (get from https://aistudio.google.com/app/apikey)
GEMINI_API_KEY=your_gemini_api_key_here

# Optional: Additional configuration
BROWSER_TYPE=chromium
HEADLESS=true
VIEWPORT_WIDTH=1920
VIEWPORT_HEIGHT=1080
```

### 3. Run Tests

```bash
# Run the comprehensive test suite
python tests
```

This command will:
1. **Start a local test server** on `http://localhost:3000`
2. **Launch Web Eval Agent** with `--url http://localhost:3000 --instructions examples/test_instructions/INSTRUCTIONS.md`
3. **Execute comprehensive tests** including navigation, forms, and interactive elements
4. **Generate detailed reports** in both HTML and structured text formats
5. **Display results** with links to generated reports

## 📊 What Gets Tested

### 🎯 Interactive Elements
- **Forms**: Contact forms, registration, search, multi-step wizards
- **Navigation**: Menus, breadcrumbs, pagination, routing
- **Controls**: Buttons, dropdowns, checkboxes, sliders, file uploads
- **Dynamic Content**: Modals, popups, tabs, accordions, tooltips

### 🔄 Complete User Workflows
- **Authentication**: Login/logout, password reset, registration
- **E-commerce**: Product browsing, cart management, checkout
- **Search & Filtering**: Search functionality, filters, sorting
- **Data Management**: CRUD operations, form validation
- **User Profiles**: Profile editing, settings, preferences

### 📱 Cross-Platform Testing
- **Responsive Design**: Multiple viewport sizes and devices
- **Performance**: Page load times, interaction responsiveness
- **Accessibility**: Basic accessibility evaluation
- **Error Handling**: Form validation, network errors, edge cases

## 🛠️ Usage Examples

### Basic Web Application Testing

```bash
# Test a local development server
python -m web_eval_agent --url http://localhost:3000 --instructions examples/test_instructions/simple-test.md

# Test with custom viewport
python -m web_eval_agent --url http://localhost:8080 --viewport 1280x720 --browser firefox

# Generate structured report
python -m web_eval_agent --url https://example.com --report-format text --report-detail structured
```

### Advanced Testing Scenarios

```bash
# Test specific user workflows
python -m web_eval_agent \
  --url http://localhost:3000 \
  --instructions examples/test_instructions/comprehensive-test.md \
  --headless false \
  --output-file reports/comprehensive-test.html

# Performance testing
python -m web_eval_agent \
  --url http://localhost:3000 \
  --instructions examples/test_instructions/performance-test.md \
  --report-detail verbose
```

### Supported Frameworks

| Framework | Default Port | Test Command |
|-----------|-------------|--------------|
| **React** | 3000 | `python -m web_eval_agent --url http://localhost:3000` |
| **Next.js** | 3000 | `python -m web_eval_agent --url http://localhost:3000` |
| **Vue.js** | 8080 | `python -m web_eval_agent --url http://localhost:8080` |
| **Angular** | 4200 | `python -m web_eval_agent --url http://localhost:4200` |
| **Express.js** | 8000 | `python -m web_eval_agent --url http://localhost:8000` |
| **Django** | 8000 | `python -m web_eval_agent --url http://localhost:8000` |
| **Flask** | 5000 | `python -m web_eval_agent --url http://localhost:5000` |

## 📁 Project Structure

```
web-eval-agent/
├── src/web_eval_agent/          # Main package
│   ├── core/                    # Core functionality
│   │   ├── cli.py              # Command-line interface
│   │   ├── config.py           # Configuration management
│   │   ├── instruction_parser.py # Test instruction parsing
│   │   └── test_executor.py    # Test execution engine
│   ├── browser/                 # Browser management
│   │   ├── browser_manager.py  # Browser lifecycle management
│   │   ├── browser_pool.py     # Browser instance pooling
│   │   └── browser_utils.py    # Browser utilities
│   ├── reporting/               # Report generation
│   │   ├── reporter.py         # Report generation engine
│   │   └── templates/          # Report templates
│   ├── mcp/                     # MCP server integration
│   │   ├── mcp_server.py       # MCP server implementation
│   │   └── tool_handlers.py    # MCP tool handlers
│   └── utils/                   # Utilities
│       ├── logging_config.py   # Logging configuration
│       ├── prompts.py          # AI prompts
│       └── utils.py            # General utilities
├── tests/                       # Test suite
│   ├── unit/                   # Unit tests
│   ├── integration/            # Integration tests
│   └── examples/               # Example tests
├── examples/
│   ├── reports/                # Sample reports
│   ├── test_instructions/      # Test instruction files
│   └── demo_apps/             # Demo applications
└── docs/                       # Documentation
```

## 📊 Report Formats

### HTML Reports (Default)
- **Visual Screenshots**: Step-by-step visual documentation
- **Interactive Timeline**: Chronological test execution
- **Network Analysis**: Request/response details
- **Console Logs**: JavaScript errors and warnings
- **Performance Metrics**: Load times and interaction delays

### Structured Text Reports
- **ASCII Tables**: Professional formatted tables
- **Summary Statistics**: Key metrics at a glance
- **Test Execution Results**: Detailed pass/fail analysis
- **Performance Data**: Timing and resource usage
- **Configuration Details**: Test environment information

### Report Detail Levels
- **`summary`**: High-level overview with key metrics
- **`structured`**: Professional ASCII tables with comprehensive data
- **`detailed`**: Full test analysis with screenshots and logs
- **`verbose`**: Complete debugging information with all captured data

## 🔧 Configuration Options

### Command Line Arguments

```bash
python -m web_eval_agent [OPTIONS]

Options:
  --url TEXT                    Target URL to test [required]
  --instructions TEXT           Path to test instructions file
  --browser [chromium|firefox|webkit]  Browser to use (default: chromium)
  --viewport TEXT               Viewport size (e.g., 1920x1080)
  --headless / --no-headless    Run browser in headless mode
  --report-format [html|text]   Report output format
  --report-detail [summary|structured|detailed|verbose]  Report detail level
  --output-file TEXT            Output file path
  --timeout INTEGER             Test timeout in seconds
  --help                        Show this message and exit
```

### Environment Variables

```env
# API Configuration
GEMINI_API_KEY=your_api_key_here

# Browser Configuration
BROWSER_TYPE=chromium
HEADLESS=true
VIEWPORT_WIDTH=1920
VIEWPORT_HEIGHT=1080

# Report Configuration
REPORT_FORMAT=html
REPORT_DETAIL_LEVEL=detailed
OUTPUT_DIRECTORY=reports

# Performance Configuration
PAGE_TIMEOUT=30000
NAVIGATION_TIMEOUT=30000
```

## 🧪 Testing Your Application

### 1. Start Your Application
```bash
# Start your development server
npm start  # or your preferred start command
# Application should be running on http://localhost:3000
```

### 2. Create Test Instructions
Create a markdown file with your test scenarios:

```markdown
# My App Test Instructions

## Test Scenarios

### 1. Homepage Navigation
- Navigate to the homepage
- Verify all navigation links work
- Check responsive design on mobile viewport

### 2. User Registration
- Fill out the registration form
- Test form validation with invalid data
- Verify successful registration flow

### 3. Search Functionality
- Use the search feature with various queries
- Test search filters and sorting
- Verify search results accuracy
```

### 3. Run the Test
```bash
python -m web_eval_agent \
  --url http://localhost:3000 \
  --instructions my-test-instructions.md \
  --report-format html \
  --output-file reports/my-app-test.html
```

## 🚀 CI/CD Integration

### GitHub Actions Example

```yaml
name: Web Eval Agent Tests

on: [push, pull_request]

jobs:
  web-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          
      - name: Install Web Eval Agent
        run: |
          pip install uv
          bash install.sh
          
      - name: Start Application
        run: |
          npm install
          npm start &
          sleep 10  # Wait for app to start
          
      - name: Run Web Eval Tests
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
        run: |
          python -m web_eval_agent \
            --url http://localhost:3000 \
            --instructions tests/ci-test-instructions.md \
            --headless \
            --report-format html \
            --output-file reports/ci-test-report.html
            
      - name: Upload Test Reports
        uses: actions/upload-artifact@v3
        with:
          name: test-reports
          path: reports/
```

## 🛠️ Development

### Setting Up Development Environment

```bash
# Clone the repository
git clone https://github.com/Zeeeepa/web-eval-agent.git
cd web-eval-agent

# Install development dependencies
uv sync --dev

# Install pre-commit hooks
pre-commit install

# Run tests
python -m pytest tests/
```

### Running Tests

```bash
# Run all tests
python tests

# Run specific test categories
python -m pytest tests/unit/          # Unit tests
python -m pytest tests/integration/   # Integration tests
python -m pytest tests/examples/      # Example tests

# Run with coverage
python -m pytest --cov=src/web_eval_agent tests/
```

## 📚 Documentation

- **[Testing Guide](tests/TESTING_GUIDE.md)** - Comprehensive testing documentation
- **[API Reference](docs/API.md)** - Detailed API documentation
- **[Configuration Guide](docs/CONFIGURATION.md)** - Configuration options
- **[Examples](examples/)** - Example test scenarios and reports

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/Zeeeepa/web-eval-agent/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Zeeeepa/web-eval-agent/discussions)
- **Documentation**: [Wiki](https://github.com/Zeeeepa/web-eval-agent/wiki)

## 🌟 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=Zeeeepa/web-eval-agent&type=Date)](https://star-history.com/#Zeeeepa/web-eval-agent&Date)

---

**Built with ❤️ for developers who want reliable, automated web testing.**

