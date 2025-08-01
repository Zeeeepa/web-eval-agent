"""Core functionality for web evaluation agent."""

from .cli import main
from .test_executor import TestExecutor
from .config import Config
from .instruction_parser import InstructionParser

__all__ = ["main", "TestExecutor", "Config", "InstructionParser"]

