"""
Main CLI interface for web-eval command
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

from ..core.evaluator import WebEvaluator
from ..parsers.instruction_parser import InstructionParser
from ..reporting.report_generator import ReportGenerator


def get_api_key() -> Optional[str]:
    """Get GEMINI API key from environment"""
    return os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')


def validate_url(url: str) -> str:
    """Validate and normalize URL"""
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    return url


def create_output_filename(url: str, format: str) -> str:
    """Create output filename based on URL and format"""
    # Extract domain from URL
    domain = url.replace('https://', '').replace('http://', '').split('/')[0]
    domain = domain.replace(':', '_')  # Replace port colon
    
    # Create timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Create filename
    extension = 'json' if format == 'json' else 'html' if format == 'html' else 'txt'
    return f"web_eval_report_{domain}_{timestamp}.{extension}"


async def run_evaluation(args) -> int:
    """Run the web evaluation"""
    
    # Get API key
    api_key = get_api_key()
    if not api_key:
        print("❌ Error: GEMINI_API_KEY or GOOGLE_API_KEY environment variable is required")
        print("   Set it with: export GEMINI_API_KEY=your_api_key_here")
        return 1
    
    # Validate URL
    url = validate_url(args.url)
    
    # Check if instruction file exists
    instruction_path = Path(args.instructions)
    if not instruction_path.exists():
        print(f"❌ Error: Instruction file not found: {args.instructions}")
        return 1
    
    try:
        print(f"🚀 Web Evaluation Agent v2.0.0")
        print(f"🌐 Target URL: {url}")
        print(f"📋 Instructions: {args.instructions}")
        print(f"🔧 Debug Mode: {'On' if args.debug else 'Off'}")
        print("=" * 60)
        
        # Parse instruction file
        parser = InstructionParser(debug=args.debug)
        scenarios = parser.parse_file(str(instruction_path))
        
        if args.debug:
            print(f"📖 Loaded {len(scenarios)} test scenarios")
        
        # Initialize evaluator
        evaluator = WebEvaluator(
            api_key=api_key,
            headless=not args.show_browser,
            debug=args.debug
        )
        
        # Run evaluation
        print("🔍 Starting web evaluation...")
        report = await evaluator.evaluate_website(url, scenarios)
        
        # Generate report
        report_generator = ReportGenerator(debug=args.debug)
        
        # Determine output file
        if args.output:
            output_file = args.output
        else:
            output_file = create_output_filename(url, args.format)
        
        # Generate and save report
        content = report_generator.generate_report(
            report=report,
            output_format=args.format,
            output_file=output_file
        )
        
        # Print summary to console
        print("\n" + "=" * 60)
        print("📊 EVALUATION COMPLETE")
        print("=" * 60)
        print(f"✅ Passed: {report.passed_scenarios}")
        print(f"❌ Failed: {report.failed_scenarios}")
        print(f"⏱️  Duration: {report.test_duration:.1f} seconds")
        print(f"📄 Report saved: {output_file}")
        
        if args.format == 'text':
            print("\n" + "=" * 60)
            print("📋 QUICK SUMMARY")
            print("=" * 60)
            # Print first few lines of summary
            summary_lines = report.summary.split('\n')[:10]
            for line in summary_lines:
                print(line)
            if len(report.summary.split('\n')) > 10:
                print("... (see full report for details)")
        
        return 0 if report.failed_scenarios == 0 else 1
        
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        return 1
    except ValueError as e:
        print(f"❌ Error parsing instruction file: {e}")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        return 1


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Web Evaluation Agent - AI-powered web testing',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  web-eval --url https://example.com --instructions INSTRUCTIONS.md
  web-eval --url localhost:3000 --instructions test_scenarios.json --format json
  web-eval --url https://mysite.com --instructions tests.yaml --output report.html --format html

Environment Variables:
  GEMINI_API_KEY    Your Google Gemini API key (required)
  GOOGLE_API_KEY    Alternative name for the API key
        """
    )
    
    parser.add_argument(
        '--url',
        required=True,
        help='URL of the website to evaluate'
    )
    
    parser.add_argument(
        '--instructions',
        required=True,
        help='Path to instruction file (Markdown, JSON, or YAML)'
    )
    
    parser.add_argument(
        '--format',
        choices=['text', 'json', 'html'],
        default='text',
        help='Output format for the report (default: text)'
    )
    
    parser.add_argument(
        '--output',
        help='Output file path (default: auto-generated based on URL and timestamp)'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug output'
    )
    
    parser.add_argument(
        '--show-browser',
        action='store_true',
        help='Show browser window during evaluation (default: headless)'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='Web Evaluation Agent v2.0.0'
    )
    
    args = parser.parse_args()
    
    # Run the evaluation
    try:
        exit_code = asyncio.run(run_evaluation(args))
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️  Evaluation interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
