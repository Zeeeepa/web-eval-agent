#!/usr/bin/env python3

import asyncio
import threading
import webbrowser
from flask import Flask, render_template, send_from_directory, request
from flask_socketio import SocketIO
import logging
import os
from datetime import datetime

# --- Async mode selection ---
_async_mode = 'threading'

# Configure logging for Flask and SocketIO (optional, can be noisy)
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR) # Reduce Flask's default logging
logging.getLogger('socketio').setLevel(logging.ERROR)
logging.getLogger('engineio').setLevel(logging.ERROR)

# Get the absolute path to the templates directory
templates_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../templates'))
app = Flask(__name__, template_folder=templates_dir, static_folder=os.path.join(templates_dir, 'static'))
app.config['SECRET_KEY'] = 'secret!' # Replace with a proper secret if needed

# Initialise SocketIO with chosen async_mode
socketio = SocketIO(app, cors_allowed_origins="*", async_mode=_async_mode)

# Store connected SIDs
connected_clients = set()

@app.route('/')
def index():
    """Serve the main HTML dashboard page."""
    return render_template('static/index.html')

@app.route('/static/<path:path>')
def send_static(path):
    """Serve static files (like CSS, JS if added later)."""
    static_folder = os.path.join(os.path.dirname(__file__), '../templates/static')
    return send_from_directory(static_folder, path)

@socketio.on('connect')
def handle_connect():
    # Add client to connected_clients set
    connected_clients.add(request.sid)
    
    # Send status message to dashboard
    send_log(f"Connected to log server at {datetime.now().strftime('%H:%M:%S')}", "✅", log_type='status')

    # Send current evaluation parameters if they exist
    global current_url, current_task
    if current_url or current_task:
        socketio.emit('evaluation_params', {'url': current_url, 'task': current_task}, to=request.sid)

@socketio.on('disconnect')
def handle_disconnect():
    # Remove client from connected_clients set
    if request.sid in connected_clients:
        connected_clients.remove(request.sid)
    
    # Send status message to dashboard
    # Use try-except as send_log might fail if server isn't fully ready/shutting down
    try:
        send_log(f"Disconnected from log server at {datetime.now().strftime('%H:%M:%S')}", "❌", log_type='status')
    except Exception:
        pass

@socketio.on('request_evaluation_params')
def handle_request_evaluation_params():
    """Handle requests for current evaluation parameters."""
    global current_url, current_task
    if current_url or current_task:
        socketio.emit('evaluation_params', {'url': current_url, 'task': current_task}, to=request.sid)

def send_log(message: str, emoji: str = "➡️", log_type: str = 'agent'):
    """Sends a log message with an emoji prefix and type to all connected clients."""
    # Ensure socketio context is available. If called from a non-SocketIO thread,
    # use socketio.emit directly.
    try:
        log_entry = f"{emoji} {message}"
        # Include log_type in the emitted data
        socketio.emit('log_message', {'data': log_entry, 'type': log_type})
    except Exception:
        pass

# --- Evaluation Parameters Function ---
def set_evaluation_params(url: str, task: str):
    """Sets the current URL and task for the evaluation and notifies connected clients."""
    global current_url, current_task
    current_url = url
    current_task = task
    # Emit an event to update connected clients
    socketio.emit('evaluation_params', {'url': url, 'task': task})
    # Log the parameters
    send_log(f"Evaluation parameters set - URL: {url}", "🔍", log_type='status')
    send_log(f"Evaluation parameters set - Task: {task}", "📋", log_type='status')

# --- Browser View Update Function ---
async def send_browser_view(image_data_url: str):
    """Sends the browser view image data URL to all connected clients."""
    # This function is async because it might be called from the asyncio loop
    # in browser_manager. However, socketio.emit needs to be called carefully
    # when interacting between asyncio and other threads (like Flask's).
    # socketio.emit is generally thread-safe, but ensure the event loop is handled.
    
    # Check if the data URL is valid
    if not image_data_url or not image_data_url.startswith("data:image/"):
        return
    
    # Mark the screencast as running when we receive a browser view update
    try:
        from .browser_utils import set_screencast_running
        set_screencast_running(True)
    except ImportError:
        pass
    except Exception:
        pass
        
    try:
        socketio.emit('browser_update', {'data': image_data_url})
    except Exception:
        pass

# --- Agent Control Handler ---
@socketio.on('agent_control')
def handle_agent_control(data):
    """Handles agent control events received from the frontend."""
    action = data.get('action')
    
    # Log to the dashboard
    send_log(f"Agent control: {action}", "🤖", log_type='status')
    
    # Import browser_utils to access the agent_instance
    try:
        from .browser_utils import agent_instance
    except ImportError:
        error_msg = "Could not import agent_instance from browser_utils"
        send_log(f"Agent control error: {error_msg}", "❌", log_type='status')
        return
    
    if not agent_instance:
        error_msg = "No active agent instance"
        send_log(f"Agent control error: {error_msg}", "❌", log_type='status')
        return
    
    try:
        if action == 'pause':
            agent_instance.pause()
            send_log("Agent paused", "⏸️", log_type='status')
            # Send updated state
            socketio.emit('agent_state', {'state': {'paused': True, 'stopped': False}})
            
        elif action == 'resume':
            agent_instance.resume()
            send_log("Agent resumed", "▶️", log_type='status')
            # Send updated state
            socketio.emit('agent_state', {'state': {'paused': False, 'stopped': False}})
            
        elif action == 'stop':
            agent_instance.stop()
            send_log("Agent stopped", "⏹️", log_type='status')
            # Send updated state
            socketio.emit('agent_state', {'state': {'paused': False, 'stopped': True}})
            
        else:
            error_msg = f"Unknown agent control action: {action}"
            send_log(f"Agent control error: {error_msg}", "❓", log_type='status')
            
    except Exception as e:
        error_msg = f"Error controlling agent: {e}"
        send_log(f"Agent control error: {error_msg}", "❌", log_type='status')

# --- Browser Input Handler ---
@socketio.on('browser_input')
def handle_browser_input_event(data):
    """Handles browser interaction events received from the frontend."""
    event_type = data.get('type')
    details = data.get('details')
    
    # Log to the dashboard as well
    send_log(f"Received browser input: {event_type}", "🖱️", log_type='status')
    
    # Import the handle_browser_input function and other utilities from browser_utils
    try:
        from .browser_utils import handle_browser_input, active_cdp_session, active_screencast_running, get_browser_task_loop
    except ImportError:
        error_msg = "Could not import handle_browser_input from browser_utils"
        send_log(f"Input error: {error_msg}", "❌", log_type='status')
        return
    
    # Check if we have an active CDP session
    if not active_cdp_session:
        error_msg = "No active CDP session for input handling"
        send_log(f"Input error: {error_msg}", "❌", log_type='status')
        return
    
    # Since the browser runs in an asyncio loop, and this handler
    # likely runs in a separate thread (Flask/SocketIO default), we need
    # to schedule the async input handler function in the main loop.
    try:
        # Get the browser task loop from browser_utils
        loop = get_browser_task_loop()
        
        if loop is None:
            send_log(f"Input error: Browser task loop not available", "❌", log_type='status')
            return
            
        send_log(f"Scheduling {event_type} input handler in browser task loop", "🔄", log_type='status')
        # Schedule the coroutine call
        task = asyncio.run_coroutine_threadsafe(
            handle_browser_input(event_type, details),
            loop
        )
        send_log(f"Input {event_type} scheduled for processing", "✅", log_type='status')
        
    except RuntimeError as e:
        error_msg = f"No running asyncio event loop found: {e}"
        send_log(f"Input error: {error_msg}", "❌", log_type='status')
    except Exception as e:
        error_msg = f"Error scheduling browser input handler: {e}"
        send_log(f"Input error: {error_msg}", "❌", log_type='status')


def start_log_server(host='127.0.0.1', port=5009):
    """Starts the Flask-SocketIO server in a background thread."""
    def run_server():
        # Use eventlet or gevent for production? For local dev, default Flask dev server is fine.
        # Setting log_output=False to reduce console noise from SocketIO itself
        socketio.run(app, host=host, port=port, log_output=False, use_reloader=False, allow_unsafe_werkzeug=True)

    # Check if templates directory exists
    template_dir = os.path.join(os.path.dirname(__file__), '../templates')
    static_dir = os.path.join(template_dir, 'static')
    
    # Create template directory if it doesn't exist
    if not os.path.exists(template_dir):
        os.makedirs(template_dir)
    
    # Create static directory if it doesn't exist
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
    
    # Create index.html if it's missing
    index_path = os.path.join(template_dir, 'index.html')

    # Start the server in a separate thread.
    # run_server uses host/port from the outer scope, so no args needed here.
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()
    
    # Send initial status message
    send_log("Log server thread started.", "🚀", log_type='status')

def open_log_dashboard(url='http://127.0.0.1:5009'):
    """Opens the specified URL in a new tab in the default web browser."""
    try:
        # Use open_new_tab for better control
        webbrowser.open_new_tab(url)
        try:
            send_log(f"Opened dashboard in browser at {url}.", "🌐", log_type='status')
        except Exception:
            pass
    except Exception as e:
        try:
            send_log(f"Could not open browser automatically: {e}", "⚠️", log_type='status')
        except Exception:
            pass

# Example usage (for testing this module directly)
if __name__ == '__main__':
    pass
    start_log_server()
    import time
    time.sleep(2)
    open_log_dashboard()
    # Use the new log_type argument
    send_log("Server started and dashboard opened.", "✅", log_type='status')
    time.sleep(1)
    send_log("This is a test agent log message.", "🧪", log_type='agent')
    time.sleep(1)
    send_log("This is a test console log.", "🖥️", log_type='console')
    time.sleep(1)
    send_log("This is a test network request.", "➡️", log_type='network')
    time.sleep(1)
    send_log("This is a test network response.", "⬅️", log_type='network')
    # Keep the main thread alive to let the server run
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
