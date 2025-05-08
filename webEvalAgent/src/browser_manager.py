#!/usr/bin/env python3

import asyncio
import base64
import socket
from typing import Dict, List, Optional

# Import log server functions
# We will add send_browser_view later
from .log_server import start_log_server, open_log_dashboard, send_log, send_browser_view

class PlaywrightBrowserManager:
    # Class variable to hold the singleton instance
    _instance: Optional['PlaywrightBrowserManager'] = None
    _log_server_started = False # Flag to ensure server starts only once
    
    @classmethod
    def get_instance(cls) -> 'PlaywrightBrowserManager':
        """Get or create the singleton instance of PlaywrightBrowserManager."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        # Check if an instance already exists
        if PlaywrightBrowserManager._instance is not None:
            send_log("PlaywrightBrowserManager is a singleton. Use get_instance() instead.", "⚠️", log_type='status')
            return
            
        # Set this instance as the singleton
        PlaywrightBrowserManager._instance = self
        
        self.playwright = None
        self.browser = None
        self.page = None
        self.cdp_session = None # Added for CDP
        self.screencast_task_running = False # Added for screencast state
        self.console_logs = []
        self.network_requests = []
        self.is_initialized = False

    async def initialize(self) -> None:
        """Initialize the Playwright browser if not already initialized."""
        if self.is_initialized:
            return
            
        if not PlaywrightBrowserManager._log_server_started:
            try:
                send_log("Initializing Operative Agent (Browser Manager)...", "🚀", log_type='status')
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                try:
                    s.connect(('localhost', 5009))
                    s.close()
                    PlaywrightBrowserManager._log_server_started = True
                    send_log("Connected to existing log server (Browser Manager).", "✅", log_type='status')
                except (socket.error, Exception):
                    s.close()
                    start_log_server()
                    await asyncio.sleep(1)
                    # Use the enhanced open_log_dashboard which will refresh existing tabs
                    # instead of opening new ones
                    open_log_dashboard()
                    PlaywrightBrowserManager._log_server_started = True
            except Exception as e:
                send_log(f"Error with log server/dashboard (Browser Manager): {e}", "❌", log_type='status')

        # Import here to avoid module import issues
        from playwright.async_api import async_playwright

        self.playwright = await async_playwright().start()
        # Launch headless
        self.browser = await self.playwright.chromium.launch(headless=True)
        self.is_initialized = True
        send_log("Playwright initialized (Browser Manager - Headless).", "🎭", log_type='status')

    async def close(self) -> None:
        """Close the browser and Playwright instance."""
        # Stop screencast if running
        if self.cdp_session and self.screencast_task_running:
            try:
                await self.cdp_session.send("Page.stopScreencast")
            except Exception:
                pass
            self.screencast_task_running = False

        # Detach CDP session if exists
        if self.cdp_session:
            try:
                await self.cdp_session.detach()
            except Exception:
                pass
            self.cdp_session = None

        if self.page:
            try:
                await self.page.close()
            except Exception:
                pass
            self.page = None

        if self.browser:
            try:
                await self.browser.close()
            except Exception:
                pass
            self.browser = None
            
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None

        self.is_initialized = False
        self.console_logs = []
        self.network_requests = []
        send_log("Browser manager closed.", "🛑", log_type='status')

    # Non-async wrapper functions for event listeners
    def _on_console(self, message):
        asyncio.create_task(self._handle_console_message(message))
    
    def _on_request(self, request):
        asyncio.create_task(self._handle_request(request))
    
    def _on_response(self, response):
        asyncio.create_task(self._handle_response(response))
    
    def _on_request_failed(self, message):
        asyncio.create_task(self._handle_console_message(message))
    
    def _on_web_error(self, message):
        asyncio.create_task(self._handle_console_message(message))
    
    def _on_page_error(self, message):
        asyncio.create_task(self._handle_console_message(message))
    
    async def open_url(self, url: str) -> str:
        """Open a URL in the browser and start monitoring console and network.
        The browser will stay open for user interaction."""
        if not self.is_initialized:
            await self.initialize()

        # Stop screencast and close previous page/session if they exist
        if self.cdp_session and self.screencast_task_running:
            try:
                await self.cdp_session.send("Page.stopScreencast")
            except Exception:
                pass
            self.screencast_task_running = False
        if self.cdp_session:
             try:
                 await self.cdp_session.detach()
             except Exception:
                 pass
             self.cdp_session = None
        if self.page:
            try:
                await self.page.close()
            except Exception:
                pass
            self.page = None

        # Clear previous logs and requests
        self.console_logs = []
        self.network_requests = []
        
        # Create a new page
        self.page = await self.browser.new_page()
        
        # Set up console log listener using non-async wrapper functions
        self.page.on("console", self._on_console)
        
        # Set up network request listener using non-async wrapper functions
        self.page.on("request", self._on_request)
        self.page.on("response", self._on_response)
        self.page.on("requestfailed", self._on_request_failed)
        self.page.on("weberror", self._on_web_error)
        self.page.on("pageerror", self._on_page_error)
        # Navigate to the URL
        await self.page.goto(url, wait_until="networkidle")
        send_log(f"Navigated to: {url} (Headless Mode)", "🌍", log_type='agent')

        # --- Start CDP Screencast ---
        try:
            self.cdp_session = await self.page.context.new_cdp_session(self.page)
            # Listen for screencast frames using a non-async wrapper function
            self.cdp_session.on("Page.screencastFrame", self._handle_screencast_frame)
            # Start the screencast
            await self.cdp_session.send("Page.startScreencast", {
                "format": "png",  # jpeg is generally smaller than png
                "quality": 100,     # Adjust quality vs size (0-100)
                "maxWidth": 1920,  # Optional: limit width
                "maxHeight": 1080   # Optional: limit height
            })
            self.screencast_task_running = True
            send_log("CDP screencast started.", "📹", log_type='status')
        except Exception as e:
            send_log(f"Failed to start CDP screencast: {e}", "❌", log_type='status')
            self.screencast_task_running = False
            if self.cdp_session:
                 try: await self.cdp_session.detach()
                 except: pass
                 self.cdp_session = None
            return f"Opened {url}, but failed to start screen streaming."

        return f"Opened {url} successfully in headless mode. Streaming view to dashboard."

    async def _handle_console_message(self, message) -> None:
        """Handle console messages from the page."""
        log_entry = {
            "type": message.type,
            "text": message.text,
            "location": message.location,
            "timestamp": asyncio.get_event_loop().time()
        }
        self.console_logs.append(log_entry)
        try:
            send_log(f"CONSOLE [{log_entry['type']}]: {log_entry['text']}", "🖥️", log_type='console')
        except Exception:
            pass

    async def _handle_request(self, request) -> None:
        """Handle network requests."""
        request_entry = {
            "url": request.url,
            "method": request.method,
            "headers": request.headers,
            "timestamp": asyncio.get_event_loop().time(),
            "resourceType": request.resource_type,
            "id": id(request)
        }
        self.network_requests.append(request_entry)
        try:
            send_log(f"NET REQ [{request_entry['method']}]: {request_entry['url']}", "➡️", log_type='network')
        except Exception:
            pass

    async def _handle_response(self, response) -> None:
        """Handle network responses."""
        response_timestamp = asyncio.get_event_loop().time()
        response_data = {
            "status": response.status,
            "statusText": response.status_text,
            "headers": response.headers,
            "timestamp": response_timestamp
        }
        # Find the matching request and update it with response data
        found = False
        for req in self.network_requests:
            # Use id for more reliable matching if available
            if req.get("id") == id(response.request) and "response" not in req:
                req["response"] = response_data
                try:
                    send_log(f"NET RESP [{response_data['status']}]: {req['url']}", "⬅️", log_type='network')
                except Exception:
                    pass
                found = True
                break
        if not found:
             try:
                 send_log(f"NET RESP* [{response_data['status']}]: {response.url} (request not matched)", "⬅️", log_type='network')
             except Exception:
                 pass

    # --- CDP Screencast Handling ---
    async def _handle_screencast_frame(self, params: Dict) -> None:
        """Handle incoming screencast frames from CDP."""
        if not self.cdp_session:
            return # Session closed or not initialized

        image_data = params.get('data')
        session_id = params.get('sessionId')

        if image_data and session_id:
            # Format as data URL
            image_data_url = f"data:image/jpeg;base64,{image_data}"

            # Send to frontend via SocketIO
            try:
                # Use asyncio.create_task to avoid blocking the CDP event handler
                asyncio.create_task(send_browser_view(image_data_url))
            except Exception:
                pass

            # IMPORTANT: Acknowledge the frame back to the browser
            try:
                await self.cdp_session.send("Page.screencastFrameAck", {"sessionId": session_id})
            except Exception as e:
                # If acknowledging fails, the stream might stop
                # For now, just handle the error. If the session is closed, this will likely fail.
                if "Target closed" in str(e) or "Session closed" in str(e) or "Connection closed" in str(e):
                    self.screencast_task_running = False # Mark as stopped
                    if self.cdp_session:
                        try: await self.cdp_session.detach()
                        except: pass
                        self.cdp_session = None


    # --- Input Handling ---
    async def handle_browser_input(self, event_type: str, details: Dict) -> None:
        """Handles input events received from the frontend via log_server."""
        # Check if we have an active CDP session
        if not self.cdp_session:
            send_log(f"Input error: No active CDP session", "❌", log_type='status')
            return
            
        # Check if screencast is running
        if not self.screencast_task_running:
            send_log(f"Input error: Screencast not running", "❌", log_type='status')
            return

        if event_type != 'scroll':
            send_log(f"Processing input: {event_type}", "🔄", log_type='status')

        try:
            if event_type == 'click':
                # CDP expects separate press and release events for a click
                button = details.get('button', 'left')
                x = details.get('x', 0)
                y = details.get('y', 0)
                click_count = details.get('clickCount', 1)
                # Modifiers might be needed for complex interactions, but start simple
                modifiers = 0 # TODO: Map ctrlKey, shiftKey etc. if needed
                
                # Mouse Pressed
                mouse_pressed_params = {
                    "type": "mousePressed",
                    "button": button,
                    "x": x,
                    "y": y,
                    "modifiers": modifiers,
                    "clickCount": click_count
                }
                
                try:
                    await self.cdp_session.send("Input.dispatchMouseEvent", mouse_pressed_params)
                except Exception as press_error:
                    send_log(f"Input error: Failed to send mousePressed: {press_error}", "❌", log_type='status')
                    return
                
                # Short delay often helps reliability
                await asyncio.sleep(0.05)
                
                # Mouse Released
                mouse_released_params = {
                    "type": "mouseReleased",
                    "button": button,
                    "x": x,
                    "y": y,
                    "modifiers": modifiers,
                    "clickCount": click_count
                }
                
                try:
                    await self.cdp_session.send("Input.dispatchMouseEvent", mouse_released_params)
                except Exception as release_error:
                    send_log(f"Input error: Failed to send mouseReleased: {release_error}", "❌", log_type='status')
                    return
                
                send_log(f"Click sent at ({x},{y})", "👆", log_type='status')

            elif event_type == 'keydown':
                # Map frontend details to CDP key event parameters
                key = details.get('key', '')
                code = details.get('code', '')
                modifiers = self._map_modifiers(details)
                
                key_params = {
                    "type": "keyDown",
                    "modifiers": modifiers,
                    "key": key,
                    "code": code,
                }
                
                try:
                    await self.cdp_session.send("Input.dispatchKeyEvent", key_params)
                except Exception as key_error:
                    send_log(f"Input error: Failed to send keyDown: {key_error}", "❌", log_type='status')
                    return
                
                send_log(f"Key down sent: {key}", "⌨️", log_type='status')

            elif event_type == 'keyup':
                key = details.get('key', '')
                code = details.get('code', '')
                modifiers = self._map_modifiers(details)
                
                key_params = {
                    "type": "keyUp",
                    "modifiers": modifiers,
                    "key": key,
                    "code": code,
                }
                
                try:
                    await self.cdp_session.send("Input.dispatchKeyEvent", key_params)
                except Exception as key_error:
                    send_log(f"Input error: Failed to send keyUp: {key_error}", "❌", log_type='status')
                    return
                
                send_log(f"Key up sent: {key}", "⌨️", log_type='status')

            elif event_type == 'scroll':
                # Use dispatchMouseEvent with type 'mouseWheel'
                x = details.get('x', 0)
                y = details.get('y', 0)
                delta_x = details.get('deltaX', 0)
                delta_y = details.get('deltaY', 0)
                
                wheel_params = {
                    "type": "mouseWheel",
                    "x": x,
                    "y": y,
                    "deltaX": delta_x,
                    "deltaY": delta_y,
                    "modifiers": 0 # Modifiers usually not needed for scroll
                }
                
                try:
                    await self.cdp_session.send("Input.dispatchMouseEvent", wheel_params)
                except Exception as wheel_error:
                    send_log(f"Input error: Failed to send mouseWheel: {wheel_error}", "❌", log_type='status')
                    return
                
                # send_log(f"Scroll sent: dY={delta_y}", "📜", log_type='status')

            else:
                send_log(f"Unknown input type: {event_type}", "❓", log_type='status')

        except Exception as e:
            send_log(f"Input error: {e}", "❌", log_type='status')
            
            # Check if the session is closed
            if "Target closed" in str(e) or "Session closed" in str(e) or "Connection closed" in str(e):
                send_log("CDP session closed, stopping input handling", "⚠️", log_type='status')
                self.screencast_task_running = False # Mark as stopped
                if self.cdp_session:
                    try: 
                        await self.cdp_session.detach()
                    except: 
                        pass
                    self.cdp_session = None

    def _map_modifiers(self, details: Dict) -> int:
        """Maps modifier keys from frontend details to CDP modifier bitmask."""
        modifiers = 0
        if details.get('altKey'): modifiers |= 1
        if details.get('ctrlKey'): modifiers |= 2
        if details.get('metaKey'): modifiers |= 4 # Command key on Mac
        if details.get('shiftKey'): modifiers |= 8
        return modifiers
