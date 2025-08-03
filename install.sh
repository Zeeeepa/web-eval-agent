#!/bin/bash

# Web Eval Agent Installation Script
# This script installs the web-eval-agent CLI tool

set -e  # Exit on any error

echo "🚀 Installing Web Evaluation Agent v2.0.0"
echo "=========================================="

# Check if Python 3.8+ is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is required but not installed"
    echo "   Please install Python 3.8 or higher"
    exit 1
fi

# Check Python version
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
required_version="3.8"

if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
    echo "❌ Error: Python 3.8+ is required (found Python $python_version)"
    exit 1
fi

echo "✅ Python $python_version detected"

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    echo "❌ Error: pip3 is required but not installed"
    echo "   Please install pip3"
    exit 1
fi

echo "✅ pip3 detected"

# Install the package in development mode
echo "📦 Installing web-eval-agent..."
pip3 install -e .

# Install playwright browsers
echo "🌐 Installing Playwright browsers..."
python3 -m playwright install chromium

# Verify installation
echo "🔍 Verifying installation..."
if command -v web-eval &> /dev/null; then
    echo "✅ web-eval command is available"
    web-eval --version
else
    echo "❌ Error: web-eval command not found in PATH"
    echo "   You may need to add ~/.local/bin to your PATH"
    echo "   Run: export PATH=\"\$HOME/.local/bin:\$PATH\""
    exit 1
fi

echo ""
echo "🎉 Installation completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Set your GEMINI API key:"
echo "   export GEMINI_API_KEY=your_api_key_here"
echo ""
echo "2. Create an INSTRUCTIONS.md file with your test scenarios"
echo ""
echo "3. Run web evaluation:"
echo "   web-eval --url https://example.com --instructions INSTRUCTIONS.md"
echo ""
echo "📚 For more information, see: https://github.com/Zeeeepa/web-eval-agent"
