#!/usr/bin/env python3

"""
Structured logging configuration for web-eval-agent.
Provides comprehensive logging with context, metrics, and GitHub PR integration.
"""

import json
import logging
import sys
import time
import uuid
from datetime import datetime
from typing import Any, Dict, Optional, Union
from pathlib import Path
from contextlib import contextmanager
from dataclasses import dataclass, asdict
import traceback

# Third-party imports
try:
    from loguru import logger as loguru_logger
    LOGURU_AVAILABLE = True
except ImportError:
    LOGURU_AVAILABLE = False


@dataclass
class LogContext:
    """Context information for structured logging."""
    session_id: str
    evaluation_id: Optional[str] = None
    github_repo: Optional[str] = None
    github_pr: Optional[int] = None
    github_branch: Optional[str] = None
    url: Optional[str] = None
    task: Optional[str] = None
    user_id: Optional[str] = None
    timestamp: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()


@dataclass
class PerformanceMetrics:
    """Performance metrics for evaluation sessions."""
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    browser_startup_time: Optional[float] = None
    page_load_time: Optional[float] = None
    ai_response_time: Optional[float] = None
    total_actions: int = 0
    successful_actions: int = 0
    failed_actions: int = 0
    screenshots_taken: int = 0
    network_requests: int = 0
    console_errors: int = 0
    
    def finish(self):
        """Mark the metrics as finished and calculate duration."""
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return asdict(self)


class StructuredLogger:
    """
    Structured logger with context management and GitHub PR integration.
    """
    
    def __init__(self, name: str = "web-eval-agent"):
        self.name = name
        self.context: Optional[LogContext] = None
        self.metrics: Optional[PerformanceMetrics] = None
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging configuration."""
        if LOGURU_AVAILABLE:
            self._setup_loguru()
        else:
            self._setup_standard_logging()
    
    def _setup_loguru(self):
        """Setup loguru-based logging."""
        # Remove default handler
        loguru_logger.remove()
        
        # Add console handler with structured format
        loguru_logger.add(
            sys.stderr,
            format=self._get_loguru_format(),
            level="INFO",
            serialize=False,
            colorize=True,
            backtrace=True,
            diagnose=True
        )
        
        # Add file handler for detailed logs
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        loguru_logger.add(
            log_dir / "web-eval-agent.log",
            format=self._get_loguru_format(),
            level="DEBUG",
            rotation="10 MB",
            retention="7 days",
            serialize=True,
            backtrace=True,
            diagnose=True
        )
        
        # Add JSON file handler for structured logs
        loguru_logger.add(
            log_dir / "web-eval-agent.jsonl",
            format="{message}",
            level="INFO",
            rotation="10 MB",
            retention="7 days",
            serialize=False,
            filter=lambda record: record["extra"].get("structured", False)
        )
    
    def _setup_standard_logging(self):
        """Setup standard Python logging as fallback."""
        # Create logs directory
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Configure root logger
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stderr),
                logging.FileHandler(log_dir / "web-eval-agent.log")
            ]
        )
        
        self.logger = logging.getLogger(self.name)
    
    def _get_loguru_format(self) -> str:
        """Get loguru format string."""
        return (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )
    
    def set_context(self, context: LogContext):
        """Set logging context for the session."""
        self.context = context
        if LOGURU_AVAILABLE:
            loguru_logger.configure(extra={"context": asdict(context)})
    
    def start_metrics(self) -> PerformanceMetrics:
        """Start performance metrics tracking."""
        self.metrics = PerformanceMetrics(start_time=time.time())
        return self.metrics
    
    def _log_structured(self, level: str, message: str, **kwargs):
        """Log structured message with context."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "message": message,
            "logger": self.name,
            **kwargs
        }
        
        # Add context if available
        if self.context:
            log_data["context"] = asdict(self.context)
        
        # Add metrics if available
        if self.metrics:
            log_data["metrics"] = self.metrics.to_dict()
        
        if LOGURU_AVAILABLE:
            loguru_logger.bind(structured=True).info(json.dumps(log_data))
        else:
            self.logger.info(json.dumps(log_data))
    
    def info(self, message: str, **kwargs):
        """Log info message."""
        if LOGURU_AVAILABLE:
            loguru_logger.info(message, **kwargs)
        else:
            self.logger.info(message)
        self._log_structured("INFO", message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        if LOGURU_AVAILABLE:
            loguru_logger.debug(message, **kwargs)
        else:
            self.logger.debug(message)
        self._log_structured("DEBUG", message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message."""
        if LOGURU_AVAILABLE:
            loguru_logger.warning(message, **kwargs)
        else:
            self.logger.warning(message)
        self._log_structured("WARNING", message, **kwargs)
    
    def error(self, message: str, error: Optional[Exception] = None, **kwargs):
        """Log error message with optional exception."""
        if error:
            kwargs["error_type"] = type(error).__name__
            kwargs["error_message"] = str(error)
            kwargs["traceback"] = traceback.format_exc()
        
        if LOGURU_AVAILABLE:
            loguru_logger.error(message, **kwargs)
        else:
            self.logger.error(message, exc_info=error)
        self._log_structured("ERROR", message, **kwargs)
    
    def critical(self, message: str, error: Optional[Exception] = None, **kwargs):
        """Log critical message."""
        if error:
            kwargs["error_type"] = type(error).__name__
            kwargs["error_message"] = str(error)
            kwargs["traceback"] = traceback.format_exc()
        
        if LOGURU_AVAILABLE:
            loguru_logger.critical(message, **kwargs)
        else:
            self.logger.critical(message, exc_info=error)
        self._log_structured("CRITICAL", message, **kwargs)
    
    def log_browser_action(self, action: str, element: Optional[str] = None, 
                          success: bool = True, duration: Optional[float] = None, **kwargs):
        """Log browser action with structured data."""
        if self.metrics:
            self.metrics.total_actions += 1
            if success:
                self.metrics.successful_actions += 1
            else:
                self.metrics.failed_actions += 1
        
        self._log_structured(
            "INFO",
            f"Browser action: {action}",
            action=action,
            element=element,
            success=success,
            duration=duration,
            **kwargs
        )
    
    def log_network_request(self, url: str, method: str, status_code: int, 
                           duration: Optional[float] = None, **kwargs):
        """Log network request."""
        if self.metrics:
            self.metrics.network_requests += 1
        
        self._log_structured(
            "INFO",
            f"Network request: {method} {url} -> {status_code}",
            url=url,
            method=method,
            status_code=status_code,
            duration=duration,
            **kwargs
        )
    
    def log_console_error(self, message: str, source: Optional[str] = None, 
                         line: Optional[int] = None, **kwargs):
        """Log console error from browser."""
        if self.metrics:
            self.metrics.console_errors += 1
        
        self._log_structured(
            "WARNING",
            f"Console error: {message}",
            console_message=message,
            source=source,
            line=line,
            **kwargs
        )
    
    def log_screenshot(self, path: str, step: Optional[str] = None, **kwargs):
        """Log screenshot capture."""
        if self.metrics:
            self.metrics.screenshots_taken += 1
        
        self._log_structured(
            "INFO",
            f"Screenshot captured: {path}",
            screenshot_path=path,
            step=step,
            **kwargs
        )
    
    def log_ai_response(self, prompt: str, response: str, duration: float, 
                       model: Optional[str] = None, **kwargs):
        """Log AI model response."""
        if self.metrics and self.metrics.ai_response_time is None:
            self.metrics.ai_response_time = duration
        
        self._log_structured(
            "INFO",
            "AI response generated",
            prompt_length=len(prompt),
            response_length=len(response),
            duration=duration,
            model=model,
            **kwargs
        )
    
    def log_github_pr_context(self, repo: str, pr_number: int, branch: str, 
                             commit_sha: Optional[str] = None, **kwargs):
        """Log GitHub PR context information."""
        self._log_structured(
            "INFO",
            f"GitHub PR context: {repo}#{pr_number}",
            github_repo=repo,
            github_pr=pr_number,
            github_branch=branch,
            commit_sha=commit_sha,
            **kwargs
        )
    
    def log_evaluation_start(self, url: str, task: str, **kwargs):
        """Log evaluation session start."""
        self._log_structured(
            "INFO",
            f"Evaluation started: {url}",
            url=url,
            task=task,
            **kwargs
        )
    
    def log_evaluation_end(self, success: bool, summary: Optional[str] = None, **kwargs):
        """Log evaluation session end."""
        if self.metrics:
            self.metrics.finish()
        
        self._log_structured(
            "INFO",
            f"Evaluation completed: {'success' if success else 'failed'}",
            success=success,
            summary=summary,
            **kwargs
        )
    
    @contextmanager
    def evaluation_session(self, context: LogContext):
        """Context manager for evaluation sessions."""
        old_context = self.context
        old_metrics = self.metrics
        
        try:
            self.set_context(context)
            self.start_metrics()
            self.log_evaluation_start(
                context.url or "unknown",
                context.task or "unknown"
            )
            yield self
        except Exception as e:
            self.error("Evaluation session failed", error=e)
            raise
        finally:
            if self.metrics:
                self.metrics.finish()
            self.log_evaluation_end(True)  # If we get here, it was successful
            self.context = old_context
            self.metrics = old_metrics


# Global logger instance
_global_logger: Optional[StructuredLogger] = None


def get_logger(name: str = "web-eval-agent") -> StructuredLogger:
    """Get or create global logger instance."""
    global _global_logger
    if _global_logger is None:
        _global_logger = StructuredLogger(name)
    return _global_logger


def create_session_context(
    github_repo: Optional[str] = None,
    github_pr: Optional[int] = None,
    github_branch: Optional[str] = None,
    url: Optional[str] = None,
    task: Optional[str] = None,
    user_id: Optional[str] = None
) -> LogContext:
    """Create a new logging context for an evaluation session."""
    return LogContext(
        session_id=str(uuid.uuid4()),
        github_repo=github_repo,
        github_pr=github_pr,
        github_branch=github_branch,
        url=url,
        task=task,
        user_id=user_id
    )


# Convenience functions
def log_info(message: str, **kwargs):
    """Log info message using global logger."""
    get_logger().info(message, **kwargs)


def log_error(message: str, error: Optional[Exception] = None, **kwargs):
    """Log error message using global logger."""
    get_logger().error(message, error=error, **kwargs)


def log_debug(message: str, **kwargs):
    """Log debug message using global logger."""
    get_logger().debug(message, **kwargs)


def log_warning(message: str, **kwargs):
    """Log warning message using global logger."""
    get_logger().warning(message, **kwargs)

