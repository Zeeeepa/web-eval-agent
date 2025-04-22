#!/usr/bin/env python3

import os
import asyncio
from playwright.async_api import async_playwright
from .log_server import send_log

# Directory to store user profile for the browser
USER_DATA_DIR = os.path.expanduser("~/chrome-profiles/google-login")

async def open_login_browser(url: str, timeout: int = 60) -> bool:
    """
    Opens a browser window for the user to manually log in.
    The browser session data will be saved for reuse.
    
    Args:
        url: The URL to navigate to for login
        timeout: Maximum time in seconds to wait for the user to complete login
        
    Returns:
        bool: True if the browser was opened and closed successfully, False otherwise
    """
    # Ensure profile directory exists
    os.makedirs(USER_DATA_DIR, exist_ok=True)
    
    send_log(f"Opening login browser at {url}", "🚀")
    send_log(f"Login session will be saved to {USER_DATA_DIR}", "📝")
    send_log(f"You have {timeout} seconds to complete your login", "⏱️")
    
    try:
        async with async_playwright() as p:
            # Launch a persistent context with the user profile
            browser = await p.chromium.launch_persistent_context(
                user_data_dir=USER_DATA_DIR,
                headless=False,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--start-maximized",
                    "--no-first-run",
                    "--no-default-browser-check",
                ]
            )
            
            page = await browser.new_page()
            await page.goto(url)
            
            send_log("Browser opened, please log in manually", "🖱️")
            
            # Wait for the specified timeout
            try:
                await asyncio.sleep(timeout)
                send_log(f"Session timed out! Hopefully you were able to setup your auth state in that time, if not, feel welcome to try again. Otherwise, we can assume the auth state is setup successfully.", "⏱️")
            except asyncio.CancelledError:
                send_log("Browser closing due to task cancellation", "🛑")
                raise
                
            # Close the browser
            await browser.close()
            send_log("Login browser closed, session data saved", "✅")
            return True
            
    except Exception as e:
        send_log(f"Error opening login browser: {e}", "❌")
        return False

def get_auth_profile_dir() -> str:
    """
    Returns the path to the user profile directory where authentication data is stored.
    
    Returns:
        str: Path to the user profile directory
    """
    return USER_DATA_DIR 