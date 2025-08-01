"""
Enhanced Web Eval Agent - Professional-Grade UI Testing Tool

A comprehensive web application testing tool that uses AI-powered browser automation
with advanced monitoring, intelligent reporting, and professional-grade analysis.
"""

__version__ = "2.0.0"
__author__ = "Web Eval Agent Team"
__description__ = "Enhanced AI-powered web application testing and validation tool with comprehensive monitoring"

# Enhanced components
from .core.enhanced_executor import EnhancedTestExecutor
from .reporting.intelligent_reporter import IntelligentReporter
from .config.enhanced_config import EnhancedConfig

# CLI components (avoid circular import)
def main():
    """Main CLI entry point."""
    from .cli.enhanced_cli import EnhancedCLI
    import asyncio
    import sys
    try:
        cli = EnhancedCLI()
        exit_code = asyncio.run(cli.run())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)

# Legacy components for backward compatibility
from .core.test_executor import TestExecutor
from .reporting.reporter import Reporter

__all__ = [
    "main", 
    "EnhancedTestExecutor", 
    "IntelligentReporter",
    "EnhancedConfig",
    # Legacy
    "TestExecutor", 
    "Reporter"
]
