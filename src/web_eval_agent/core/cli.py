#!/usr/bin/env python3
"""
Command Line Interface for Web Eval Agent

Legacy CLI that delegates to the enhanced CLI for backward compatibility.
"""

import sys
import asyncio
from ..cli.enhanced_cli import EnhancedCLI


def main():
    """Main entry point for the CLI - delegates to enhanced CLI."""
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


if __name__ == "__main__":
    main()
