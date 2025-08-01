#!/bin/bash

# Web Eval Agent Installation Script
# This script installs all dependencies and sets up the web-eval CLI tool

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to detect OS
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
        echo "windows"
    else
        echo "unknown"
    fi
}

# Function to install system dependencies
install_system_deps() {
    print_status "Installing system dependencies..."
    
    if [[ $(detect_os) == "linux" ]]; then
        # Update package list
        print_status "Updating package list..."
        sudo apt-get update -qq
        
        # Install essential packages
        print_status "Installing essential packages (curl, jq, build tools)..."
        sudo apt-get install -y curl jq build-essential python3-dev python3-pip python3-venv
        
        print_success "System dependencies installed successfully"
        
    elif [[ $(detect_os) == "macos" ]]; then
        # macOS
        if command_exists brew; then
            print_status "Installing dependencies via Homebrew..."
            brew install curl jq python3
            print_success "System dependencies installed successfully"
        else
            print_warning "Homebrew not found. Please install manually: curl, jq, python3"
        fi
    else
        print_warning "Unsupported OS. Please install manually: curl, jq, python3, build tools"
    fi
}

# Function to install UV (Python package manager)
install_uv() {
    print_status "Installing UV (Python package manager)..."
    
    if ! command_exists uv; then
        curl -LsSf https://astral.sh/uv/install.sh | sh
        
        # Source the shell configuration to make uv available
        if [[ -f "$HOME/.bashrc" ]]; then
            source "$HOME/.bashrc" 2>/dev/null || true
        fi
        if [[ -f "$HOME/.zshrc" ]]; then
            source "$HOME/.zshrc" 2>/dev/null || true
        fi
        
        # Add to PATH for current session
        export PATH="$HOME/.cargo/bin:$PATH"
        
        print_success "UV installed successfully"
    else
        print_status "UV already installed"
    fi
}

# Function to install Node.js and npm
install_nodejs() {
    print_status "Checking Node.js and npm..."
    
    if ! command_exists node || ! command_exists npm; then
        if [[ $(detect_os) == "linux" ]]; then
            print_status "Installing Node.js and npm..."
            curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
            sudo apt-get install -y nodejs
            print_success "Node.js and npm installed successfully"
        elif [[ $(detect_os) == "macos" ]]; then
            if command_exists brew; then
                print_status "Installing Node.js and npm via Homebrew..."
                brew install node npm
                print_success "Node.js and npm installed successfully"
            else
                print_warning "Please install Node.js and npm manually"
            fi
        else
            print_warning "Please install Node.js and npm manually"
        fi
    else
        print_status "Node.js and npm already installed"
    fi
}

# Function to install Python dependencies
install_python_deps() {
    print_status "Installing Python dependencies..."
    
    # Check if we have pip
    if ! command_exists pip && ! command_exists pip3; then
        print_error "pip is not installed. Please install Python and pip first."
        exit 1
    fi
    
    # Use pip3 if available, otherwise pip
    PIP_CMD="pip"
    if command_exists pip3; then
        PIP_CMD="pip3"
    fi
    
    # Install the package in development mode
    $PIP_CMD install -e .
    
    print_success "Python dependencies installed successfully"
}

# Function to install Playwright browsers
install_playwright() {
    print_status "Installing Playwright browsers..."
    
    # Install Playwright globally via npm if available
    if command_exists npm; then
        print_status "Installing Playwright via npm..."
        npm install -g playwright chromium 2>/dev/null || {
            print_warning "Could not install Playwright globally via npm, trying alternative method..."
        }
    fi
    
    # Install playwright browsers using Python
    if command_exists python3; then
        python3 -m playwright install chromium
    elif command_exists python; then
        python -m playwright install chromium
    fi
    
    # Install system dependencies for playwright with enhanced method
    if [[ $(detect_os) == "linux" ]]; then
        print_status "Installing system dependencies for Playwright..."
        
        # Try the enhanced uvx method first
        if command_exists uv; then
            print_status "Using UV to install Playwright with dependencies..."
            uvx --with playwright playwright install --with-deps 2>/dev/null || {
                print_warning "UV method failed, trying standard method..."
                python3 -m playwright install-deps chromium || {
                    print_warning "Could not install system dependencies automatically."
                    print_warning "You may need to install them manually if you encounter issues."
                }
            }
        else
            # Fallback to standard method
            python3 -m playwright install-deps chromium || {
                print_warning "Could not install system dependencies automatically."
                print_warning "You may need to install them manually if you encounter issues."
            }
        fi
    fi
    
    print_success "Playwright browsers installed successfully"
}

# Function to create .env file and show configuration instructions
setup_environment() {
    print_status "Setting up environment configuration..."
    
    # Create .env file if it doesn't exist
    if [[ ! -f ".env" ]]; then
        print_status "Creating .env file..."
        cat > .env << 'EOF'
# Web Eval Agent Environment Configuration
# ========================================

# Required: Google Gemini API Key
# Get your API key from: https://aistudio.google.com/app/apikey
GEMINI_API_KEY=your_gemini_api_key_here

# Optional: Browser Configuration
BROWSER_TYPE=chromium
HEADLESS=true
VIEWPORT_WIDTH=1920
VIEWPORT_HEIGHT=1080

# Optional: Report Configuration
REPORT_FORMAT=html
REPORT_DETAIL_LEVEL=detailed
OUTPUT_DIRECTORY=reports

# Optional: Performance Configuration
PAGE_TIMEOUT=30000
NAVIGATION_TIMEOUT=30000
EOF
        print_success "Created .env file with default configuration"
    else
        print_status ".env file already exists"
    fi
    
    # Check if API key is set
    if [[ -z "${GEMINI_API_KEY}" ]]; then
        echo ""
        echo "🔧 CONFIGURATION REQUIRED"
        echo "========================="
        echo ""
        print_warning "You need to configure your environment variables before using Web Eval Agent."
        echo ""
        echo "📝 To configure your environment:"
        echo ""
        echo "   nano .env"
        echo ""
        echo "📋 Required configuration:"
        echo "   1. Get your Gemini API key from: https://aistudio.google.com/app/apikey"
        echo "   2. Replace 'your_gemini_api_key_here' with your actual API key"
        echo "   3. Save and exit (Ctrl+X, then Y, then Enter in nano)"
        echo ""
        echo "🚀 After configuration, you can run tests with:"
        echo "   python tests"
        echo ""
        print_warning "Installation complete, but configuration is required before running tests."
        return 1
    else
        print_success "GEMINI_API_KEY found in environment"
        return 0
    fi
}

# Function to verify installation
verify_installation() {
    print_status "Verifying installation..."
    
    # Check if web-eval command is available
    if command_exists web-eval; then
        print_success "web-eval command is available"
        
        # Test the command
        if web-eval --version >/dev/null 2>&1; then
            print_success "web-eval is working correctly"
        else
            print_warning "web-eval command exists but may not be working properly"
        fi
    else
        print_error "web-eval command not found in PATH"
        print_status "Trying to add to PATH..."
        
        # Try to find where pip installed it
        PYTHON_SCRIPTS_DIR=$(python -c "import site; print(site.USER_BASE + '/bin')" 2>/dev/null || echo "")
        if [[ -n "$PYTHON_SCRIPTS_DIR" ]] && [[ -f "$PYTHON_SCRIPTS_DIR/web-eval" ]]; then
            print_status "Found web-eval in $PYTHON_SCRIPTS_DIR"
            print_status "Add this to your PATH: export PATH=\"$PYTHON_SCRIPTS_DIR:\$PATH\""
        fi
    fi
}

# Function to create example instruction file
create_example_instructions() {
    print_status "Creating example instruction file..."
    
    cat > INSTRUCTIONS.md << 'EOF'
# Web Application Test Instructions

## Basic Navigation Test

**Description:**
Test the basic navigation and functionality of the web application.

**Steps:**
1. Navigate to the homepage
2. Check that the page loads without errors
3. Look for main navigation elements
4. Test any visible buttons or links
5. Verify that forms are accessible and functional

**Validations:**
- Page should load within 5 seconds
- No console errors should be present
- All navigation links should be clickable
- Forms should accept input properly

**Expected Outcomes:**
- Homepage displays correctly
- Navigation works smoothly
- No JavaScript errors occur
- User interface is responsive and functional

**Priority:** high
**Tags:** #navigation #basic #smoke-test
EOF
    
    print_success "Created example INSTRUCTIONS.md file"
}

# Main installation function
main() {
    echo ""
    echo "🚀 Web Eval Agent Installation Script"
    echo "======================================"
    echo ""
    
    # Detect OS
    OS=$(detect_os)
    print_status "Detected OS: $OS"
    
    # Check Python
    if ! command_exists python && ! command_exists python3; then
        print_error "Python is not installed. Please install Python 3.11+ first."
        exit 1
    fi
    
    # Check Python version
    PYTHON_CMD="python"
    if command_exists python3; then
        PYTHON_CMD="python3"
    fi
    
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2)
    print_status "Using Python $PYTHON_VERSION"
    
    # Check if we're in the right directory
    if [[ ! -f "pyproject.toml" ]] && [[ ! -f "pyproject-new.toml" ]]; then
        print_error "This script must be run from the web-eval-agent project directory"
        exit 1
    fi
    
    # Use new pyproject.toml if it exists
    if [[ -f "pyproject-new.toml" ]]; then
        print_status "Using new project configuration..."
        mv pyproject-new.toml pyproject.toml
    fi
    
    # Use new requirements.txt if it exists
    if [[ -f "requirements-new.txt" ]]; then
        print_status "Using new requirements..."
        mv requirements-new.txt requirements.txt
    fi
    
    # Install system dependencies first
    install_system_deps
    
    # Install UV (Python package manager)
    install_uv
    
    # Install Node.js and npm
    install_nodejs
    
    # Install Python dependencies
    install_python_deps
    
    # Install Playwright
    install_playwright
    
    # Setup environment configuration (but don't exit on missing API key during install)
    setup_environment || true
    
    # Create example instructions
    create_example_instructions
    
    # Verify installation
    verify_installation
    
    echo ""
    print_success "🎉 Installation completed successfully!"
    echo ""
    echo "✅ Installed components:"
    echo "   • System dependencies (curl, jq, build tools)"
    echo "   • UV (Python package manager)"
    echo "   • Node.js and npm"
    echo "   • Python dependencies"
    echo "   • Playwright browsers with system dependencies"
    echo "   • Environment configuration (.env file)"
    echo "   • Example test instructions (INSTRUCTIONS.md)"
    echo ""
    
    # Check if API key is configured
    if [[ -n "${GEMINI_API_KEY}" ]] && [[ "${GEMINI_API_KEY}" != "your_gemini_api_key_here" ]]; then
        echo "🚀 Ready to run tests!"
        echo ""
        echo "Quick start:"
        echo "   python tests"
        echo ""
        echo "This will:"
        echo "   • Start a localhost:3000 test server"
        echo "   • Run web-eval-agent with test instructions"
        echo "   • Generate comprehensive test reports"
        echo ""
    else
        echo "⚠️  Configuration required before running tests."
        echo ""
        echo "Next steps:"
        echo "1. Configure environment: nano .env"
        echo "2. Add your Gemini API key"
        echo "3. Run tests: python tests"
        echo ""
    fi
    
    echo "💡 Pro tip: The installation includes UV for faster Python package management"
    echo "   and enhanced Playwright setup for reliable browser automation."
    echo ""
    echo "For more information, see the README.md file."
    echo ""
}

# Run main function
main "$@"
