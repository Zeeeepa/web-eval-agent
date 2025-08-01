#!/usr/bin/env python3
"""
Test runner for web-eval-agent tests.

This script provides an easy way to run different types of tests for the web-eval-agent.
"""

import asyncio
import os
import sys
import argparse

def check_api_key():
    """Check if GEMINI_API_KEY is set"""
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        print("❌ GEMINI_API_KEY environment variable not set")
        print("   Please set your Gemini API key:")
        print("   export GEMINI_API_KEY='your_key_here'")
        return False
    print(f"✅ API key found: {api_key[:10]}...")
    return True

async def run_basic_test():
    """Run basic functionality test"""
    print("🧪 Running basic functionality test...")
    from unit.simple_test import test_basic_functionality
    await test_basic_functionality()

async def run_ssh_demo():
    """Run SSH search demonstration"""
    print("🔍 Running SSH search demonstration...")
    from integration.test_ssh_demo import test_ssh_demo
    await test_ssh_demo()

async def run_local_webapp_test(url=None):
    """Run local web application test"""
    print("🌐 Running local web application test...")
    
    if url:
        # Override the URL in the test
        import examples.test_local_webapp
        # Modify the test to use the provided URL
        print(f"Testing URL: {url}")
    
    from examples.test_local_webapp import test_local_webapp_interactions
    await test_local_webapp_interactions()

def main():
    parser = argparse.ArgumentParser(description='Run web-eval-agent tests')
    parser.add_argument('--test', choices=['basic', 'ssh', 'local', 'all'], 
                       default='basic', help='Type of test to run')
    parser.add_argument('--url', help='URL for local webapp testing (e.g., http://localhost:3000)')
    parser.add_argument('--list', action='store_true', help='List available tests')
    
    args = parser.parse_args()
    
    if args.list:
        print("Available tests:")
        print("  basic  - Basic functionality and API validation")
        print("  ssh    - SSH search demonstration")
        print("  local  - Local web application testing")
        print("  all    - Run all tests")
        return
    
    print("🚀 Web-Eval-Agent Test Runner")
    print("=" * 40)
    
    if not check_api_key():
        return
    
    if args.test == 'basic':
        asyncio.run(run_basic_test())
    elif args.test == 'ssh':
        asyncio.run(run_ssh_demo())
    elif args.test == 'local':
        asyncio.run(run_local_webapp_test(args.url))
    elif args.test == 'all':
        print("Running all tests...")
        asyncio.run(run_basic_test())
        print("\n" + "="*40 + "\n")
        asyncio.run(run_ssh_demo())
        print("\n" + "="*40 + "\n")
        asyncio.run(run_local_webapp_test(args.url))
    
    print("\n✅ Test run completed!")

if __name__ == "__main__":
    main()
