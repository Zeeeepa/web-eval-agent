"""Core functionality for web evaluation agent."""

# Legacy components
from .test_executor import TestExecutor
from .config import Config
from .instruction_parser import InstructionParser

# Enhanced components
from .enhanced_executor import EnhancedTestExecutor

# CLI main function (avoid circular import)
def main():
    """Main CLI entry point."""
    from .cli import main as cli_main
    return cli_main()

__all__ = [
    "main", 
    "TestExecutor", 
    "Config", 
    "InstructionParser",
    "EnhancedTestExecutor"
]
