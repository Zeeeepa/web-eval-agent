"""
Configuration management for Web Eval Agent
"""

from dataclasses import dataclass
from typing import Optional, Tuple
import os


@dataclass
class Config:
    """Configuration class for Web Eval Agent."""
    
    # Required settings
    url: str
    instructions_file: str
    api_key: str
    
    # Output settings
    output_file: str = "web-eval-report.html"
    report_format: str = "html"
    
    # Browser settings
    browser: str = "chromium"
    headless: bool = False
    viewport: str = "1280x720"
    timeout: int = 300
    
    # Logging settings
    verbose: bool = False
    debug: bool = False
    
    # Advanced settings
    max_retries: int = 3
    screenshot_on_failure: bool = True
    capture_network: bool = True
    capture_console: bool = True
    
    def __post_init__(self):
        """Validate and process configuration after initialization."""
        # Ensure URL has protocol
        if not self.url.startswith(("http://", "https://")):
            self.url = "https://" + self.url
        
        # Set API key in environment for compatibility
        if self.api_key:
            os.environ["GEMINI_API_KEY"] = self.api_key
            os.environ["GOOGLE_API_KEY"] = self.api_key
        
        # Disable telemetry
        os.environ["ANONYMIZED_TELEMETRY"] = "false"
    
    @property
    def viewport_size(self) -> Tuple[int, int]:
        """Parse viewport string into width, height tuple."""
        try:
            width, height = self.viewport.split("x")
            return int(width), int(height)
        except (ValueError, AttributeError):
            return 1280, 720
    
    def get_browser_config(self) -> dict:
        """Get browser configuration dictionary."""
        return {
            "browser_type": self.browser,
            "headless": self.headless,
            "viewport": {"width": self.viewport_size[0], "height": self.viewport_size[1]},
            "timeout": self.timeout * 1000,  # Convert to milliseconds
        }
    
    def get_logging_level(self) -> str:
        """Get appropriate logging level based on settings."""
        if self.debug:
            return "DEBUG"
        elif self.verbose:
            return "INFO"
        else:
            return "WARNING"
