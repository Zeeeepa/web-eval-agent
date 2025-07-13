"""
FastAPI Server for PR Analysis Pipeline

🚀 REST API server providing webhook endpoints and management interface
for the automated PR analysis system.
"""

import asyncio
import hashlib
import hmac
import json
import logging
import os
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from pr_analysis_pipeline import (
    PRAnalysisOrchestrator,
    RepositoryManager,
    RepositoryConfig,
    ProjectType
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="PR Analysis Pipeline API",
    description="🚀 Automated PR analysis system with grainchain, graph-sitter, and web-eval-agent",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
orchestrator = PRAnalysisOrchestrator()
repository_manager = RepositoryManager()

# Configuration
GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET", "")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")


# Pydantic models
class RepositoryConfigRequest(BaseModel):
    """Request model for repository configuration."""
    owner: str = Field(..., description="Repository owner")
    name: str = Field(..., description="Repository name")
    clone_url: str = Field(..., description="Repository clone URL")
    project_type: str = Field(default="react", description="Project type")
    auto_merge_threshold: float = Field(default=0.8, ge=0.0, le=1.0)
    error_threshold: float = Field(default=0.4, ge=0.0, le=1.0)
    max_validation_attempts: int = Field(default=3, ge=1, le=10)


class AnalysisStatusResponse(BaseModel):
    """Response model for analysis status."""
    session_id: str
    phase: str
    repository: str
    pr_number: Optional[int]
    created_at: str
    updated_at: str
    results: Dict
    errors: List[str]


class WebhookResponse(BaseModel):
    """Response model for webhook processing."""
    status: str
    session_id: Optional[str] = None
    message: str


# Dependency functions
def verify_github_signature(request: Request) -> bool:
    """Verify GitHub webhook signature."""
    if not GITHUB_WEBHOOK_SECRET:
        logger.warning("GitHub webhook secret not configured")
        return True  # Allow in development
    
    signature = request.headers.get("X-Hub-Signature-256", "")
    if not signature:
        return False
    
    # Get request body
    body = request.body()
    expected_signature = "sha256=" + hmac.new(
        GITHUB_WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)


# API Routes

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "PR Analysis Pipeline API",
        "version": "1.0.0",
        "description": "🚀 Automated PR analysis with grainchain, graph-sitter, and web-eval-agent",
        "endpoints": {
            "repositories": "/repositories",
            "analysis": "/analysis",
            "webhooks": "/webhooks/github",
            "health": "/health"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "active_sessions": len(orchestrator.active_sessions),
        "configured_repositories": len(repository_manager.repositories)
    }


# Repository Management Endpoints

@app.post("/repositories")
async def create_repository_config(config_request: RepositoryConfigRequest):
    """Create a new repository configuration."""
    try:
        # Generate repository ID
        repo_id = f"{config_request.owner}-{config_request.name}"
        
        # Create repository config
        repo_config = RepositoryConfig(
            repo_id=repo_id,
            owner=config_request.owner,
            name=config_request.name,
            clone_url=config_request.clone_url,
            project_type=ProjectType(config_request.project_type),
            auto_merge_threshold=config_request.auto_merge_threshold,
            error_threshold=config_request.error_threshold,
            max_validation_attempts=config_request.max_validation_attempts
        )
        
        # Add to repository manager
        repository_manager.add_repository(repo_config)
        
        logger.info(f"Created repository configuration: {repo_id}")
        return {
            "status": "success",
            "repo_id": repo_id,
            "message": f"Repository {config_request.owner}/{config_request.name} configured successfully"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid project type: {e}")
    except Exception as e:
        logger.error(f"Failed to create repository config: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/repositories")
async def list_repositories():
    """List all configured repositories."""
    repositories = repository_manager.list_repositories()
    return {
        "repositories": [
            {
                "repo_id": repo.repo_id,
                "owner": repo.owner,
                "name": repo.name,
                "project_type": repo.project_type.value,
                "auto_merge_threshold": repo.auto_merge_threshold,
                "error_threshold": repo.error_threshold
            }
            for repo in repositories
        ]
    }


@app.get("/repositories/{repo_id}")
async def get_repository_config(repo_id: str):
    """Get repository configuration by ID."""
    repo_config = repository_manager.get_repository(repo_id)
    if not repo_config:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    return {
        "repo_id": repo_config.repo_id,
        "owner": repo_config.owner,
        "name": repo_config.name,
        "clone_url": repo_config.clone_url,
        "project_type": repo_config.project_type.value,
        "auto_merge_threshold": repo_config.auto_merge_threshold,
        "error_threshold": repo_config.error_threshold,
        "max_validation_attempts": repo_config.max_validation_attempts
    }


@app.delete("/repositories/{repo_id}")
async def delete_repository_config(repo_id: str):
    """Delete repository configuration."""
    if repo_id not in repository_manager.repositories:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    del repository_manager.repositories[repo_id]
    repository_manager.save_repositories()
    
    logger.info(f"Deleted repository configuration: {repo_id}")
    return {"status": "success", "message": f"Repository {repo_id} deleted"}


# Analysis Management Endpoints

@app.get("/analysis")
async def list_active_sessions():
    """List all active analysis sessions."""
    sessions = []
    for session_id, session in orchestrator.active_sessions.items():
        sessions.append({
            "session_id": session_id,
            "phase": session.phase.value,
            "repository": f"{session.repository_config.owner}/{session.repository_config.name}",
            "pr_number": session.pr_data.get("number"),
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat()
        })
    
    return {"active_sessions": sessions}


@app.get("/analysis/{session_id}")
async def get_analysis_status(session_id: str):
    """Get detailed analysis status for a session."""
    status = orchestrator.get_session_status(session_id)
    if "error" in status:
        raise HTTPException(status_code=404, detail=status["error"])
    
    return status


@app.post("/analysis/start")
async def start_manual_analysis(
    repo_id: str,
    pr_number: int,
    background_tasks: BackgroundTasks
):
    """Manually start analysis for a PR."""
    # Get repository configuration
    repo_config = repository_manager.get_repository(repo_id)
    if not repo_config:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    # Mock PR data (in real implementation, fetch from GitHub API)
    pr_data = {
        "number": pr_number,
        "title": f"PR #{pr_number}",
        "head": {
            "ref": "feature-branch",
            "sha": "abc123"
        },
        "changed_files": ["src/example.js"]
    }
    
    # Start analysis
    session_id = await orchestrator.start_analysis(repo_config, pr_data)
    
    logger.info(f"Started manual analysis: session {session_id}")
    return {
        "status": "started",
        "session_id": session_id,
        "message": f"Analysis started for PR #{pr_number}"
    }


# GitHub Webhook Endpoints

@app.post("/webhooks/github")
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    """Handle GitHub webhook events."""
    try:
        # Verify signature
        if not verify_github_signature(request):
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Parse webhook payload
        payload = await request.json()
        event_type = request.headers.get("X-GitHub-Event", "")
        
        logger.info(f"Received GitHub webhook: {event_type}")
        
        # Handle pull request events
        if event_type == "pull_request":
            return await handle_pull_request_webhook(payload, background_tasks)
        
        # Handle other events
        return {"status": "ignored", "message": f"Event type {event_type} not handled"}
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except Exception as e:
        logger.error(f"Webhook processing failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


async def handle_pull_request_webhook(payload: Dict, background_tasks: BackgroundTasks):
    """Handle pull request webhook events."""
    action = payload.get("action", "")
    pr_data = payload.get("pull_request", {})
    repository_data = payload.get("repository", {})
    
    # Only process opened and synchronize events
    if action not in ["opened", "synchronize"]:
        return {
            "status": "ignored",
            "message": f"PR action '{action}' not processed"
        }
    
    # Find repository configuration
    repo_full_name = repository_data.get("full_name", "")
    owner, name = repo_full_name.split("/") if "/" in repo_full_name else ("", "")
    repo_id = f"{owner}-{name}"
    
    repo_config = repository_manager.get_repository(repo_id)
    if not repo_config:
        logger.warning(f"Repository {repo_id} not configured for analysis")
        return {
            "status": "ignored",
            "message": f"Repository {repo_full_name} not configured"
        }
    
    # Extract PR information
    pr_info = {
        "number": pr_data.get("number"),
        "title": pr_data.get("title", ""),
        "head": {
            "ref": pr_data.get("head", {}).get("ref", ""),
            "sha": pr_data.get("head", {}).get("sha", "")
        },
        "base": {
            "ref": pr_data.get("base", {}).get("ref", ""),
            "sha": pr_data.get("base", {}).get("sha", "")
        },
        "changed_files": []  # Would be populated from GitHub API
    }
    
    # Start analysis in background
    session_id = await orchestrator.start_analysis(repo_config, pr_info)
    
    logger.info(f"Started analysis for PR #{pr_info['number']}: session {session_id}")
    
    return {
        "status": "processing",
        "session_id": session_id,
        "message": f"Analysis started for PR #{pr_info['number']}"
    }


# Error handlers

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "status_code": 500
        }
    )


# Startup and shutdown events

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    logger.info("🚀 PR Analysis Pipeline API starting up")
    logger.info(f"Loaded {len(repository_manager.repositories)} repository configurations")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown."""
    logger.info("🛑 PR Analysis Pipeline API shutting down")
    
    # Cleanup active sessions
    for session_id in list(orchestrator.active_sessions.keys()):
        await orchestrator.sandbox_manager.cleanup_sandbox(session_id)


if __name__ == "__main__":
    import uvicorn
    
    # Run the server
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

