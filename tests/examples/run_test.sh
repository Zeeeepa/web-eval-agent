#!/bin/bash
# Comprehensive Web-Eval Test Runner
# This script runs the comprehensive test suite for the web-eval agent

echo "🧪 Web-Eval Agent Comprehensive Test Suite"
echo "=========================================="

# Check if we're in the right directory
if [ ! -f "web_eval/cli.py" ]; then
    echo "❌ Please run this script from the project root directory"
    exit 1
fi

# Check if GEMINI_API_KEY is set
if [ -z "$GEMINI_API_KEY" ]; then
    echo "❌ GEMINI_API_KEY environment variable is not set"
    echo "Please set your Gemini API key:"
    echo "export GEMINI_API_KEY='your_key_here'"
    exit 1
fi

# Install dependencies if needed
echo "📦 Checking dependencies..."
python -c "import flask, requests" 2>/dev/null || {
    echo "📦 Installing missing dependencies..."
    pip install flask requests
}

# Run the comprehensive test
echo "🚀 Starting comprehensive test..."
python tests/run_comprehensive_test.py

echo "✅ Test completed!"

