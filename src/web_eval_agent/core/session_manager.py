"""
Session Manager for Web Eval Agent

Manages multiple browser sessions with intelligent positioning and resource management.
"""

import asyncio
import platform
import subprocess
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from browser_use.browser import Browser, BrowserConfig

from .config import Config


@dataclass
class BrowserSession:
    """Represents a browser session with its configuration."""
    session_id: int
    browser: Browser
    config: BrowserConfig
    window_position: Optional[Tuple[int, int]] = None
    window_size: Optional[Tuple[int, int]] = None
    is_active: bool = True


class SessionManager:
    """Manages multiple browser sessions for parallel testing."""
    
    def __init__(self, config: Config):
        self.config = config
        self.sessions: Dict[int, BrowserSession] = {}
        self.active_sessions: List[int] = []
        self.semaphore = asyncio.Semaphore(min(config.num_agents, 10))
    
    def get_screen_dimensions(self) -> Tuple[int, int]:
        """Get screen dimensions with fallback for headless environments."""
        try:
            import screeninfo
            screen = screeninfo.get_monitors()[0]
            return screen.width, screen.height
        except Exception:
            return 1920, 1080
    
    def calculate_window_position(self, session_id: int, total_sessions: int) -> Dict[str, Any]:
        """Calculate optimal window positioning for non-headless mode."""
        if self.config.headless:
            return {}
        
        screen_width, screen_height = self.get_screen_dimensions()
        
        # Window configuration
        window_width = 300
        window_height = 400
        viewport_width = 280
        viewport_height = 350
        
        margin = 10
        spacing = 15
        
        # Calculate grid layout
        usable_width = screen_width - (2 * margin)
        windows_per_row = max(1, usable_width // (window_width + spacing))
        
        row = session_id // windows_per_row
        col = session_id % windows_per_row
        
        x_offset = margin + col * (window_width + spacing)
        y_offset = margin + row * (window_height + spacing)
        
        # Ensure windows stay on screen
        if x_offset + window_width > screen_width:
            x_offset = screen_width - window_width - margin
        if y_offset + window_height > screen_height:
            y_offset = screen_height - window_height - margin
        
        return {
            "window_size": {"width": window_width, "height": window_height},
            "window_position": {"width": x_offset, "height": y_offset},
            "viewport": {"width": viewport_width, "height": viewport_height}
        }
    
    async def create_session(self, session_id: int) -> BrowserSession:
        """Create a new browser session with optimal configuration."""
        # Base browser arguments
        browser_args = ['--disable-gpu', '--no-sandbox', '--disable-dev-shm-usage']
        
        if self.config.headless:
            browser_args.append('--headless=new')
        
        # Calculate window positioning
        window_config = self.calculate_window_position(session_id, self.config.num_agents)
        
        # Create browser configuration
        browser_config = BrowserConfig(
            headless=self.config.headless,
            disable_security=True,
            chrome_instance_path=None,
            chrome_user_data_dir=None,
            additional_args=browser_args,
            ignore_default_args=['--enable-automation'],
            wait_for_network_idle_page_load_time=2.0,
            maximum_wait_page_load_time=8.0,
            wait_between_actions=0.5,
            **window_config
        )
        
        # Create browser instance
        browser = Browser(config=browser_config)
        
        # Create session object
        session = BrowserSession(
            session_id=session_id,
            browser=browser,
            config=browser_config,
            window_position=window_config.get("window_position"),
            window_size=window_config.get("window_size")
        )
        
        # Store session
        self.sessions[session_id] = session
        self.active_sessions.append(session_id)
        
        # Apply zoom for non-headless mode
        if not self.config.headless:
            await self._apply_zoom_settings(session)
        
        return session
    
    async def _apply_zoom_settings(self, session: BrowserSession):
        """Apply zoom settings for better visibility in small windows."""
        try:
            # Wait a bit for browser to initialize
            await asyncio.sleep(0.5)
            
            # Get the page from browser_use Browser
            if hasattr(session.browser, 'page') and session.browser.page:
                page = session.browser.page
                
                # Apply zoom
                await page.evaluate("""
                    document.body.style.zoom = '0.25';
                    document.documentElement.style.zoom = '0.25';
                """)
                
                # Set up event listeners for dynamic zoom
                await page.evaluate("""
                    const applyZoom = () => {
                        document.body.style.zoom = '0.25';
                        document.documentElement.style.zoom = '0.25';
                    };
                    
                    // Apply zoom on page load events
                    if (document.readyState === 'loading') {
                        document.addEventListener('DOMContentLoaded', applyZoom);
                    } else {
                        applyZoom();
                    }
                    
                    window.addEventListener('load', applyZoom);
                """)
                
        except Exception as e:
            print(f"⚠️ Failed to apply zoom settings for session {session.session_id}: {e}")
    
    async def close_session(self, session_id: int):
        """Close a specific browser session."""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            try:
                await session.browser.close()
                session.is_active = False
            except Exception as e:
                print(f"⚠️ Error closing session {session_id}: {e}")
            
            # Remove from tracking
            if session_id in self.active_sessions:
                self.active_sessions.remove(session_id)
            del self.sessions[session_id]
    
    async def close_all_sessions(self):
        """Close all active browser sessions."""
        close_tasks = []
        for session_id in list(self.active_sessions):
            close_tasks.append(self.close_session(session_id))
        
        if close_tasks:
            await asyncio.gather(*close_tasks, return_exceptions=True)
        
        # Cleanup lingering browser processes
        await self._cleanup_browser_processes()
    
    async def _cleanup_browser_processes(self):
        """Clean up any lingering browser processes."""
        try:
            await asyncio.sleep(1)  # Give processes time to close gracefully
            
            if platform.system() == 'Darwin':  # macOS
                subprocess.run(['pkill', '-f', 'chromium'], capture_output=True, check=False)
                subprocess.run(['pkill', '-f', 'chrome'], capture_output=True, check=False)
            elif platform.system() == 'Linux':
                subprocess.run(['pkill', '-f', 'chromium'], capture_output=True, check=False)
                subprocess.run(['pkill', '-f', 'chrome'], capture_output=True, check=False)
            elif platform.system() == 'Windows':
                subprocess.run(['taskkill', '/f', '/im', 'chrome.exe'], capture_output=True, check=False)
                subprocess.run(['taskkill', '/f', '/im', 'chromium.exe'], capture_output=True, check=False)
                
        except Exception as e:
            print(f"⚠️ Browser cleanup warning: {e}")
    
    async def get_session(self, session_id: int) -> Optional[BrowserSession]:
        """Get a specific browser session."""
        return self.sessions.get(session_id)
    
    def get_active_session_count(self) -> int:
        """Get the number of active sessions."""
        return len(self.active_sessions)
    
    async def run_with_semaphore(self, coro):
        """Run a coroutine with semaphore limiting."""
        async with self.semaphore:
            return await coro
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get statistics about current sessions."""
        return {
            "total_sessions": len(self.sessions),
            "active_sessions": len(self.active_sessions),
            "headless_mode": self.config.headless,
            "max_concurrent": self.semaphore._value,
            "session_ids": list(self.active_sessions)
        }
