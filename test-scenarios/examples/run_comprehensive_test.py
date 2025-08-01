#!/usr/bin/env python3
"""
Comprehensive Test Runner for Web-Eval Agent

This script:
1. Starts the example Flask application on port 5000
2. Waits for it to be ready
3. Runs web-eval with comprehensive test instructions
4. Captures and displays the results
5. Cleans up the Flask process
"""

import subprocess
import time
import requests
import sys
import os
import signal
from pathlib import Path

def wait_for_server(url, timeout=30, interval=1):
    """Wait for the server to be ready."""
    print(f"⏳ Waiting for server at {url} to be ready...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ Server is ready at {url}")
                return True
        except requests.exceptions.RequestException:
            pass
        
        time.sleep(interval)
    
    print(f"❌ Server at {url} did not become ready within {timeout} seconds")
    return False

def run_comprehensive_test():
    """Run the comprehensive web-eval test."""
    print("🚀 Starting Comprehensive Web-Eval Test")
    print("=" * 60)
    
    # Get the current directory and set up paths
    current_dir = Path(__file__).parent
    app_dir = current_dir / "example-app"
    instructions_file = current_dir / "comprehensive-web-eval-test.md"
    report_file = current_dir / "comprehensive-test-report.txt"
    
    # Check if files exist
    if not app_dir.exists():
        print(f"❌ Example app directory not found: {app_dir}")
        return False
    
    if not instructions_file.exists():
        print(f"❌ Instructions file not found: {instructions_file}")
        return False
    
    flask_process = None
    
    try:
        # Start the Flask application
        print("🌟 Starting Flask application...")
        flask_process = subprocess.Popen(
            [sys.executable, "app.py"],
            cwd=app_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid  # Create new process group for clean cleanup
        )
        
        # Wait for the server to be ready
        if not wait_for_server("http://localhost:5000", timeout=30):
            print("❌ Flask application failed to start properly")
            return False
        
        print("🧪 Running web-eval with comprehensive test instructions...")
        print(f"📋 Instructions: {instructions_file}")
        print(f"📊 Report will be saved to: {report_file}")
        print()
        
        # Run web-eval
        web_eval_cmd = [
            "python", "-m", "web_eval.cli",
            "--url", "http://localhost:5000",
            "--instructions", str(instructions_file),
            "--output", str(report_file),
            "--format", "text",
            "--headless",
            "--timeout", "600",  # 10 minutes timeout
            "--verbose"
        ]
        
        print("🔧 Running command:")
        print(" ".join(web_eval_cmd))
        print()
        
        # Run the web-eval command
        result = subprocess.run(
            web_eval_cmd,
            cwd=current_dir.parent,  # Run from project root
            capture_output=True,
            text=True,
            timeout=700  # 11+ minutes timeout for the subprocess
        )
        
        print("📊 Web-Eval Results:")
        print("=" * 40)
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        print(f"Return code: {result.returncode}")
        print()
        
        # Check if report was generated
        if report_file.exists():
            print("✅ Report generated successfully!")
            print(f"📄 Report location: {report_file}")
            
            # Display the first part of the report
            print()
            print("📋 Report Preview:")
            print("-" * 40)
            with open(report_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # Show first 2000 characters
                preview = content[:2000]
                print(preview)
                if len(content) > 2000:
                    print("...")
                    print(f"[Report continues for {len(content) - 2000} more characters]")
            
            print()
            print(f"📊 Full report available at: {report_file}")
            return True
        else:
            print("❌ Report was not generated")
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ Web-eval test timed out after 11+ minutes")
        return False
    except KeyboardInterrupt:
        print("\\n⏹️ Test interrupted by user")
        return False
    except Exception as e:
        print(f"❌ Error during test execution: {e}")
        return False
    finally:
        # Clean up Flask process
        if flask_process:
            print("🧹 Cleaning up Flask application...")
            try:
                # Kill the entire process group
                os.killpg(os.getpgid(flask_process.pid), signal.SIGTERM)
                flask_process.wait(timeout=5)
            except (ProcessLookupError, subprocess.TimeoutExpired):
                # Force kill if needed
                try:
                    os.killpg(os.getpgid(flask_process.pid), signal.SIGKILL)
                except ProcessLookupError:
                    pass
            print("✅ Flask application stopped")

def main():
    """Main entry point."""
    print("🧪 Web-Eval Agent Comprehensive Test Runner")
    print("=" * 50)
    
    # Check if we have the required dependencies
    try:
        import requests
        import flask
    except ImportError as e:
        print(f"❌ Missing required dependency: {e}")
        print("Please install requirements: pip install flask requests")
        return False
    
    # Check if GEMINI_API_KEY is set
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ GEMINI_API_KEY environment variable is not set")
        print("Please set your Gemini API key: export GEMINI_API_KEY='your_key_here'")
        return False
    
    success = run_comprehensive_test()
    
    if success:
        print("\\n🎉 Comprehensive test completed successfully!")
        print("📊 Check the generated report for detailed results")
    else:
        print("\\n❌ Comprehensive test failed")
        print("🔍 Check the error messages above for details")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

