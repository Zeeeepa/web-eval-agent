#!/usr/bin/env python3
"""
Web Eval Agent Test Runner

This script runs comprehensive tests by:
1. Starting a local test server on localhost:3000
2. Running web-eval-agent with test instructions
3. Generating and displaying test reports

Usage:
    python tests
    python -m tests
"""

import os
import sys
import time
import signal
import subprocess
import threading
from pathlib import Path
from typing import Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from web_eval_agent.core.cli import main as web_eval_main
    from web_eval_agent.core.config import Config
except ImportError as e:
    print(f"❌ Error importing web_eval_agent: {e}")
    print("💡 Make sure you've run 'bash install.sh' first")
    sys.exit(1)


class TestServer:
    """Simple HTTP server for testing purposes."""
    
    def __init__(self, port: int = 3000):
        self.port = port
        self.process: Optional[subprocess.Popen] = None
        
    def start(self):
        """Start the test server."""
        print(f"🚀 Starting test server on http://localhost:{self.port}")
        
        # Create a simple test HTML page
        test_app_dir = Path(__file__).parent / "examples" / "example-app"
        test_app_dir.mkdir(parents=True, exist_ok=True)
        
        # Create index.html
        index_html = test_app_dir / "index.html"
        if not index_html.exists():
            index_html.write_text("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Web Eval Test App</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .container { max-width: 800px; margin: 0 auto; }
        .nav { margin-bottom: 30px; }
        .nav a { margin-right: 20px; text-decoration: none; color: #007bff; }
        .nav a:hover { text-decoration: underline; }
        .form-group { margin-bottom: 15px; }
        .form-group label { display: block; margin-bottom: 5px; }
        .form-group input, .form-group textarea { width: 100%; padding: 8px; }
        .btn { background: #007bff; color: white; padding: 10px 20px; border: none; cursor: pointer; }
        .btn:hover { background: #0056b3; }
        .counter { margin: 20px 0; }
        .counter button { margin: 5px; padding: 10px 15px; }
        #counter-value { font-size: 24px; font-weight: bold; margin: 0 15px; }
    </style>
</head>
<body>
    <div class="container">
        <nav class="nav">
            <a href="#home">Home</a>
            <a href="#about">About</a>
            <a href="#contact">Contact</a>
            <a href="#services">Services</a>
            <a href="#blog">Blog</a>
        </nav>
        
        <h1>Web Eval Test Application</h1>
        <p>This is a test application for demonstrating Web Eval Agent capabilities.</p>
        
        <div class="counter">
            <h2>Interactive Counter</h2>
            <button onclick="decrementCounter()">-</button>
            <span id="counter-value">0</span>
            <button onclick="incrementCounter()">+</button>
            <button onclick="resetCounter()">Reset</button>
        </div>
        
        <form id="contact-form" onsubmit="handleSubmit(event)">
            <h2>Contact Form</h2>
            <div class="form-group">
                <label for="name">Name:</label>
                <input type="text" id="name" name="name" required>
            </div>
            <div class="form-group">
                <label for="email">Email:</label>
                <input type="email" id="email" name="email" required>
            </div>
            <div class="form-group">
                <label for="message">Message:</label>
                <textarea id="message" name="message" rows="4" required></textarea>
            </div>
            <button type="submit" class="btn">Send Message</button>
        </form>
        
        <div id="form-result" style="margin-top: 20px; display: none;"></div>
    </div>
    
    <script>
        let counter = 0;
        
        function updateCounter() {
            document.getElementById('counter-value').textContent = counter;
        }
        
        function incrementCounter() {
            counter++;
            updateCounter();
            console.log('Counter incremented to:', counter);
        }
        
        function decrementCounter() {
            counter--;
            updateCounter();
            console.log('Counter decremented to:', counter);
        }
        
        function resetCounter() {
            counter = 0;
            updateCounter();
            console.log('Counter reset to:', counter);
        }
        
        function handleSubmit(event) {
            event.preventDefault();
            const formData = new FormData(event.target);
            const data = Object.fromEntries(formData);
            
            console.log('Form submitted with data:', data);
            
            // Simulate form processing
            const resultDiv = document.getElementById('form-result');
            resultDiv.innerHTML = '<p style="color: green;">✅ Message sent successfully!</p>';
            resultDiv.style.display = 'block';
            
            // Reset form
            event.target.reset();
            
            // Hide result after 3 seconds
            setTimeout(() => {
                resultDiv.style.display = 'none';
            }, 3000);
        }
        
        // Log page load
        console.log('Test application loaded successfully');
    </script>
</body>
</html>""")
        
        # Start Python HTTP server
        try:
            self.process = subprocess.Popen([
                sys.executable, "-m", "http.server", str(self.port)
            ], cwd=test_app_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait a moment for server to start
            time.sleep(2)
            
            # Check if server is running
            if self.process.poll() is None:
                print(f"✅ Test server started successfully on http://localhost:{self.port}")
                return True
            else:
                print("❌ Failed to start test server")
                return False
                
        except Exception as e:
            print(f"❌ Error starting test server: {e}")
            return False
    
    def stop(self):
        """Stop the test server."""
        if self.process:
            print("🛑 Stopping test server...")
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None
            print("✅ Test server stopped")


def run_web_eval_test():
    """Run the web eval agent test."""
    print("🤖 Starting Web Eval Agent test...")
    
    # Check for API key
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ GEMINI_API_KEY environment variable not set")
        print("💡 Please run 'nano .env' and add your Gemini API key")
        return False
    
    # Prepare test arguments
    test_url = "http://localhost:3000"
    instructions_file = Path(__file__).parent.parent / "examples" / "test_instructions" / "INSTRUCTIONS.md"
    
    if not instructions_file.exists():
        # Create basic instructions if they don't exist
        instructions_file.parent.mkdir(parents=True, exist_ok=True)
        instructions_file.write_text("""# Web Application Test Instructions

## Comprehensive Test Scenario

**Description:**
Test all major functionality of the web application including navigation, forms, and interactive elements.

**Steps:**
1. Navigate to the homepage and verify it loads correctly
2. Test all navigation links in the header
3. Test the interactive counter functionality:
   - Click increment button multiple times
   - Click decrement button multiple times  
   - Click reset button and verify counter resets to 0
4. Test the contact form:
   - Fill out all fields with test data
   - Submit the form and verify success message
   - Test form validation with invalid data
5. Check for any console errors or warnings
6. Evaluate overall user experience and responsiveness

**Validations:**
- Page should load within 5 seconds
- No JavaScript console errors should be present
- All navigation links should be functional
- Counter should increment/decrement correctly
- Form should accept valid input and show success message
- Form validation should work for invalid input
- User interface should be responsive and intuitive

**Expected Outcomes:**
- Homepage displays correctly with all elements
- Navigation works smoothly
- Counter functionality works as expected
- Contact form processes submissions correctly
- No critical errors or usability issues
- Overall positive user experience

**Priority:** high
**Tags:** #comprehensive #navigation #forms #interactive #smoke-test
""")
    
    try:
        # Run web eval agent
        print(f"🎯 Testing URL: {test_url}")
        print(f"📋 Using instructions: {instructions_file}")
        
        # Prepare arguments for web eval agent
        test_args = [
            "--url", test_url,
            "--instructions", str(instructions_file),
            "--report-format", "text",
            "--report-detail", "structured",
            "--headless", "false",  # Show browser for demo
            "--output-file", "reports/test-report.txt"
        ]
        
        # Create reports directory
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)
        
        # Run the web eval agent
        print("🚀 Launching Web Eval Agent...")
        print("   (Browser window will open - this is normal)")
        
        # Save original sys.argv
        original_argv = sys.argv.copy()
        
        try:
            # Set sys.argv for the web eval agent
            sys.argv = ["web-eval-agent"] + test_args
            
            # Run the web eval agent
            web_eval_main()
            
            print("✅ Web Eval Agent test completed successfully!")
            
            # Show report location
            report_file = reports_dir / "test-report.txt"
            if report_file.exists():
                print(f"📊 Test report generated: {report_file}")
                print("📋 Report preview:")
                print("-" * 50)
                # Show first 20 lines of report
                with open(report_file, 'r') as f:
                    lines = f.readlines()
                    for i, line in enumerate(lines[:20]):
                        print(line.rstrip())
                    if len(lines) > 20:
                        print(f"... ({len(lines) - 20} more lines)")
                print("-" * 50)
            
            return True
            
        finally:
            # Restore original sys.argv
            sys.argv = original_argv
            
    except Exception as e:
        print(f"❌ Error running Web Eval Agent: {e}")
        return False


def main():
    """Main test runner function."""
    print("🧪 Web Eval Agent Test Suite")
    print("=" * 40)
    print()
    
    # Check if we're in the right directory
    if not Path("pyproject.toml").exists():
        print("❌ Please run this from the web-eval-agent project root directory")
        sys.exit(1)
    
    # Start test server
    server = TestServer(port=3000)
    
    def signal_handler(signum, frame):
        """Handle Ctrl+C gracefully."""
        print("\n🛑 Received interrupt signal, cleaning up...")
        server.stop()
        sys.exit(0)
    
    # Register signal handler
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Start the test server
        if not server.start():
            print("❌ Failed to start test server")
            sys.exit(1)
        
        # Wait a moment for server to be fully ready
        print("⏳ Waiting for server to be ready...")
        time.sleep(3)
        
        # Run the web eval test
        success = run_web_eval_test()
        
        if success:
            print("\n🎉 All tests completed successfully!")
            print("\n📊 Test Summary:")
            print("   ✅ Local test server: Started and running")
            print("   ✅ Web Eval Agent: Executed test scenarios")
            print("   ✅ Test report: Generated successfully")
            print("\n💡 Next steps:")
            print("   • Review the generated test report")
            print("   • Check the reports/ directory for detailed results")
            print("   • Run 'python -m web_eval_agent --help' for more options")
        else:
            print("\n❌ Some tests failed")
            print("💡 Check the error messages above for details")
            sys.exit(1)
            
    finally:
        # Always stop the server
        server.stop()


if __name__ == "__main__":
    main()

