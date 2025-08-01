"""
Web Eval Agent - Standalone UI Testing Tool

A comprehensive web application testing tool that uses AI-powered browser automation
to evaluate user interfaces, test functionality, and generate detailed reports.
"""

__version__ = "2.0.0"
__author__ = "Web Eval Agent Team"
__description__ = "AI-powered web application testing and validation tool"

from .core.cli import main
from .core.test_executor import TestExecutor
from .reporting.reporter import Reporter

__all__ = ["main", "TestExecutor", "Reporter"]
