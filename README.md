# 🚀 Web Eval Agent - Multi-Agent AI Web Testing

> *Revolutionary multi-agent AI testing framework - Deploy multiple intelligent agents to comprehensively test your web applications.*

![Demo](demo.gif)

## 🔥 What is Web Eval Agent?

Web Eval Agent is a cutting-edge multi-agent AI testing framework that deploys multiple intelligent agents to simultaneously test different aspects of your web applications. Using advanced browser automation with AI-powered analysis, it provides comprehensive testing reports with severity classification and detailed issue analysis.

## ⚡ Key Features

- 🤖 **Multi-Agent Testing** - Deploy 3+ agents simultaneously for comprehensive coverage
- 🔍 **Scout Mode** - Intelligent element discovery and targeted test generation
- ⚡ **Parallel Execution** - Agents work in parallel for faster testing
- 🧠 **AI-Powered Analysis** - Severity classification and detailed issue analysis
- 🌐 **Full Browser Automation** - Real browser testing with browser-use framework
- 📊 **Comprehensive Reports** - Detailed text reports with severity breakdown
- 🚨 **Smart Error Detection** - AI-powered issue classification and analysis
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

### 3. Run Multi-Agent Tests

```bash
# Run with default 3 agents
web-eval --url http://localhost:3000 --instructions test-scenarios/basic/test_instructions.md

# Deploy 5 agents for comprehensive testing
web-eval --url http://localhost:3000 --instructions test-scenarios/advanced/multi-agent-comprehensive.md --agents 5

# Run with GUI mode to see agents in action
web-eval --url http://localhost:3000 --instructions test-scenarios/basic/test_instructions.md --no-headless
```

This command will:
1. **Deploy multiple AI agents** simultaneously (default: 3 agents)
2. **Scout the page** for interactive elements (if scout mode enabled)
3. **Execute parallel testing** with agents focusing on different aspects
4. **Analyze findings** using AI for severity classification
5. **Generate comprehensive reports** with detailed issue breakdown

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

### Basic Multi-Agent Testing

```bash
# Test with default 3 agents
web-eval --url http://localhost:3000 --instructions test-scenarios/basic/test_instructions.md

# Test with custom viewport and browser
web-eval --url http://localhost:8080 --instructions test-scenarios/basic/test_instructions.md --viewport 1280x720 --browser firefox

# Generate detailed text report
web-eval --url https://example.com --instructions test-scenarios/basic/test_instructions.md --format text
```

### Advanced Multi-Agent Scenarios

```bash
# Deploy 5 agents for comprehensive testing
web-eval \
  --url http://localhost:3000 \
  --instructions test-scenarios/advanced/multi-agent-comprehensive.md \
  --agents 5

# E-commerce flow testing with multiple agents
web-eval \
  --url http://localhost:3000 \
  --instructions test-scenarios/advanced/e-commerce-flow.md \
  --agents 4 \
  --no-headless

# Disable scout mode and use instruction-based testing only
web-eval \
  --url http://localhost:3000 \
  --instructions test-scenarios/basic/test_instructions.md \
  --no-scout \
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
