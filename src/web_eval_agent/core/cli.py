#!/usr/bin/env python3
"""
Command Line Interface for Web Eval Agent

Provides a simple CLI for running web application tests with instruction files.
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path
from typing import Optional

from .instruction_parser import InstructionParser
from .test_executor import TestExecutor
from .config import Config
from ..utils.utils import setup_logging, validate_url, check_dependencies
from ..reporting.reporter import Reporter


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        prog="web-eval",
        description="AI-powered web application testing and validation tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  web-eval --url http://localhost:3000 --instructions INSTRUCTIONS.md
  web-eval --url https://example.com --instructions tests/form-test.md --output report.html
  web-eval --url http://localhost:3000 --instructions tests/e2e.md --timeout 300
  web-eval --url http://localhost:3000 --instructions tests/ui.md --no-headless
        """
    )
    
    # Required arguments
    parser.add_argument(
        "--url",
        required=True,
        help="URL of the web application to test (e.g., http://localhost:3000)"
    )
    
    parser.add_argument(
        "--instructions",
        required=True,
        help="Path to the instruction file containing test scenarios"
    )
    
    # Optional arguments
    parser.add_argument(
        "--output",
        default="web-eval-report.txt",
        help="Output file for the test report (default: web-eval-report.txt)"
    )
    
    parser.add_argument(
        "--format",
        choices=["html", "json", "text"],
        default="text",
        help="Report format (default: text - comprehensive format with emojis)"
    )
    
    parser.add_argument(
        "--headless",
        action="store_true",
        default=True,
        help="Run browser in headless mode (default: True, use --no-headless to disable)"
    )
    
    parser.add_argument(
        "--no-headless",
        action="store_false",
        dest="headless",
        help="Run browser with GUI (disable headless mode)"
    )
    
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Test timeout in seconds (default: 300)"
    )
    
    parser.add_argument(
        "--browser",
        choices=["chromium", "firefox", "webkit"],
        default="chromium",
        help="Browser to use for testing (default: chromium)"
    )
    
    parser.add_argument(
        "--viewport",
        default="1280x720",
        help="Browser viewport size (default: 1280x720)"
    )
    
    parser.add_argument(
        "--api-key",
        help="Gemini API key (can also be set via GEMINI_API_KEY environment variable)"
    )
    
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode with detailed logging"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 2.0.0"
    )
    
    return parser


def validate_arguments(args) -> bool:
    """Validate command line arguments."""
    # Check if instruction file exists
    if not Path(args.instructions).exists():
        print(f"❌ Error: Instruction file '{args.instructions}' not found")
        return False
    
    # Validate URL format
    if not validate_url(args.url):
        print(f"❌ Error: Invalid URL format '{args.url}'")
        return False
    
    # Check API key
    api_key = args.api_key or os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ Error: Gemini API key required. Set GEMINI_API_KEY environment variable or use --api-key")
        return False
    
    # Validate viewport format
    if args.viewport and "x" not in args.viewport:
        print(f"❌ Error: Invalid viewport format '{args.viewport}'. Use format like '1280x720'")
        return False
    
    return True


async def run_tests(args) -> int:
    """Run the web evaluation tests."""
    try:
        # Setup configuration
        config = Config(
            url=args.url,
            instructions_file=args.instructions,
            output_file=args.output,
            report_format=args.format,
            headless=args.headless,
            timeout=args.timeout,
            browser=args.browser,
            viewport=args.viewport,
            api_key=args.api_key or os.getenv("GEMINI_API_KEY"),
            verbose=args.verbose,
            debug=args.debug
        )
        
        print(f"🚀 Starting web evaluation for {args.url}")
        print(f"📋 Using instructions from {args.instructions}")
        
        # Parse instructions
        parser = InstructionParser()
        test_scenarios = await parser.parse_file(args.instructions)
        
        if not test_scenarios:
            print("❌ No test scenarios found in instruction file")
            return 1
        
        print(f"📝 Found {len(test_scenarios)} test scenario(s)")
        
        # Execute tests
        executor = TestExecutor(config)
        results = await executor.run_tests(test_scenarios)
        
        # Generate report
        reporter = Reporter(config)
        report_path = await reporter.generate_report(results)
        
        # Print summary
        total_tests = len(results.test_results)
        passed_tests = sum(1 for r in results.test_results if r.passed)
        failed_tests = total_tests - passed_tests
        
        print(f"\n📊 Test Results Summary:")
        print(f"   ✅ Passed: {passed_tests}")
        print(f"   ❌ Failed: {failed_tests}")
        print(f"   📄 Report: {report_path}")
        
        if results.errors:
            print(f"   ⚠️  Errors: {len(results.errors)}")
        
        return 0 if failed_tests == 0 else 1
        
    except KeyboardInterrupt:
        print("\n⏹️  Test execution interrupted by user")
        return 130
    except Exception as e:
        print(f"❌ Error during test execution: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        return 1


def main():
    """Main entry point for the CLI."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(verbose=args.verbose, debug=args.debug)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Validate arguments
    if not validate_arguments(args):
        sys.exit(1)
    
    # Run tests
    try:
        exit_code = asyncio.run(run_tests(args))
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⏹️  Interrupted by user")
        sys.exit(130)


if __name__ == "__main__":
    main()
