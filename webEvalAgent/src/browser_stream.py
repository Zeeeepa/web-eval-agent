# browser_stream/server.py
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# In-memory storage for latest screenshots
latest_screenshots = {}

class ScreenshotUpdate(BaseModel):
    agent_id: str
    screenshot: str # base64 encoded

@app.post("/update_screenshot")
async def update_screenshot(update: ScreenshotUpdate):
    """Receives screenshot updates from agents."""
    latest_screenshots[update.agent_id] = update.screenshot
    logger.debug(f"Received screenshot for {update.agent_id}")
    return {"status": "success"}

@app.get("/get_screenshots")
async def get_screenshots():
    """Provides the latest screenshots to the frontend."""
    return latest_screenshots

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serves the main HTML page to display agent views."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Operative WebEvalAgent Parallel Testing Mode</title>
        <style>
            body { font-family: sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
            h1 { text-align: center; color: #333; margin-bottom: 20px; }
            .agents-container { display: flex; flex-wrap: wrap; justify-content: center; }
            .agent-view {
                border: 1px solid #ddd;
                margin: 10px;
                padding: 15px;
                width: 30%;
                min-width: 300px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                background-color: white;
                border-radius: 8px;
             }
            .agent-view img {
                max-width: 100%;
                height: auto;
                border: 1px solid #eee;
                display: block;
                margin: 0 auto;
            }
            .agent-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 10px;
                padding-bottom: 10px;
                border-bottom: 1px solid #eee;
            }
            h3 { margin: 0; color: #444; }
            .timestamp { color: #888; font-size: 0.8em; }
            .metadata { margin-top: 10px; font-size: 0.9em; color: #555; }
            .status { font-weight: bold; }
        </style>
    </head>
    <body>
        <h1>Operative WebEvalAgent Parallel Testing Mode</h1>
        <div id="agents-container" class="agents-container">
             <!-- Agent views will be dynamically added here -->
        </div>

        <script>
            const agentsContainer = document.getElementById('agents-container');
            const knownAgentIds = new Set(); // Track agents with created divs
            const lastUpdated = {}; // Track when each agent was last updated

            function createOrUpdateAgentElement(agentId, screenshotBase64, metadata) {
                const now = new Date();
                lastUpdated[agentId] = now;
                
                let agentDiv = document.getElementById(`agent-${agentId}`);
                if (!agentDiv) {
                    // Create new div if it doesn't exist
                    knownAgentIds.add(agentId);
                    agentDiv = document.createElement('div');
                    agentDiv.className = 'agent-view';
                    agentDiv.id = `agent-${agentId}`;
                    
                    const headerDiv = document.createElement('div');
                    headerDiv.className = 'agent-header';
                    
                    const title = document.createElement('h3');
                    title.textContent = metadata.description || `Agent: ${agentId}`;
                    
                    const timestamp = document.createElement('span');
                    timestamp.className = 'timestamp';
                    timestamp.id = `timestamp-${agentId}`;
                    timestamp.textContent = 'Just now';
                    
                    headerDiv.appendChild(title);
                    headerDiv.appendChild(timestamp);
                    
                    const img = document.createElement('img');
                    img.alt = `View for ${agentId}`;
                    
                    const metadataDiv = document.createElement('div');
                    metadataDiv.className = 'metadata';
                    metadataDiv.innerHTML = `
                        <div>Status: <span class="status">${metadata.status || 'Unknown'}</span></div>
                        <div>ID: ${agentId}</div>
                        <div>URL: ${metadata.url || 'N/A'}</div>
                    `;
                    
                    agentDiv.appendChild(headerDiv);
                    agentDiv.appendChild(img);
                    agentDiv.appendChild(metadataDiv);
                    
                    agentsContainer.appendChild(agentDiv);
                    console.log(`Created view for ${agentId}`);
                }

                // Update the image source
                const imgElement = agentDiv.querySelector('img');
                if (imgElement) {
                    imgElement.src = `data:image/png;base64,${screenshotBase64}`;
                }
                
                // Update timestamp
                const timestampElement = document.getElementById(`timestamp-${agentId}`);
                if (timestampElement) {
                    timestampElement.textContent = 'Just now';
                }
            }
            
            function updateTimestamps() {
                const now = new Date();
                for (const agentId in lastUpdated) {
                    const timestamp = document.getElementById(`timestamp-${agentId}`);
                    if (timestamp) {
                        const seconds = Math.floor((now - lastUpdated[agentId]) / 1000);
                        if (seconds < 60) {
                            timestamp.textContent = `${seconds}s ago`;
                        } else if (seconds < 3600) {
                            timestamp.textContent = `${Math.floor(seconds / 60)}m ago`;
                        } else {
                            timestamp.textContent = `${Math.floor(seconds / 3600)}h ago`;
                        }
                    }
                }
            }

            async function fetchAndUpdateScreenshots() {
                try {
                    const response = await fetch('/get_screenshots');
                    if (!response.ok) {
                        console.error(`Error fetching screenshots: ${response.status}`);
                        return;
                    }
                    const screenshots = await response.json();

                    // Update existing agent views and create new ones
                    for (const agentId in screenshots) {
                        const metadata = { description: 'Test Description', status: 'Running', url: '/test-url' }; // Placeholder metadata
                        createOrUpdateAgentElement(agentId, screenshots[agentId], metadata);
                    }
                } catch (error) {
                    console.error("Error fetching screenshots:", error);
                }
            }

            // Fetch immediately and then every 1 second
            fetchAndUpdateScreenshots();
            setInterval(fetchAndUpdateScreenshots, 1000);
            setInterval(updateTimestamps, 5000);
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    port = 8080
    logger.info(f"Starting server on http://localhost:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)