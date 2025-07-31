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
    
    # Install playwright browsers
    python -m playwright install chromium
    
    # Install system dependencies for playwright (Linux only)
    if [[ $(detect_os) == "linux" ]]; then
        print_status "Installing system dependencies for Playwright..."
        python -m playwright install-deps chromium || {
            print_warning "Could not install system dependencies automatically."
            print_warning "You may need to install them manually if you encounter issues."
        }
    fi
    
    print_success "Playwright browsers installed successfully"
}

# Function to check API key
check_api_key() {
    print_status "Checking for Gemini API key..."
    
    if [[ -z "${GEMINI_API_KEY}" ]]; then
        print_warning "GEMINI_API_KEY environment variable is not set."
        echo ""
        echo "To use web-eval, you need a Google Gemini API key."
        echo "1. Get your API key from: https://aistudio.google.com/app/apikey"
        echo "2. Set it as an environment variable:"
        echo "   export GEMINI_API_KEY='your_api_key_here'"
        echo "3. Or pass it directly when running: web-eval --api-key your_key ..."
        echo ""
        print_warning "You can continue installation, but you'll need the API key to run tests."
    else
        print_success "GEMINI_API_KEY found in environment"
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
    
    # Install Python dependencies
    install_python_deps
    
    # Install Playwright
    install_playwright
    
    # Check API key
    check_api_key
    
    # Create example instructions
    create_example_instructions
    
    # Verify installation
    verify_installation
    
    echo ""
    print_success "🎉 Installation completed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Set your Gemini API key: export GEMINI_API_KEY='your_key'"
    echo "2. Test the installation: web-eval --version"
    echo "3. Run a test: web-eval --url http://localhost:3000 --instructions INSTRUCTIONS.md"
    echo ""
    echo "For more information, see the README.md file."
    echo ""
}

# Run main function
main "$@"
