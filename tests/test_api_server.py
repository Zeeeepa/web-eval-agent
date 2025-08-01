"""
Comprehensive tests for FastAPI Server

🧪 100% API endpoint coverage with mock calls
"""

import asyncio
import json
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import tempfile
import os

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from api_server import app, orchestrator, repository_manager
from pr_analysis_pipeline import RepositoryConfig, ProjectType, AnalysisSession, AnalysisPhase


class TestAPIEndpoints:
    """Test all API endpoints."""
    
    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)
    
    def test_root_endpoint(self):
        """Test root endpoint."""
        response = self.client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "PR Analysis Pipeline API"
        assert data["version"] == "1.0.0"
        assert "endpoints" in data
        assert "repositories" in data["endpoints"]
        assert "analysis" in data["endpoints"]
        assert "webhooks" in data["endpoints"]
        assert "health" in data["endpoints"]
    
    def test_health_check_endpoint(self):
        """Test health check endpoint."""
        response = self.client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "active_sessions" in data
        assert "configured_repositories" in data
        assert isinstance(data["active_sessions"], int)
        assert isinstance(data["configured_repositories"], int)


class TestRepositoryEndpoints:
    """Test repository management endpoints."""
    
    def setup_method(self):
        """Set up test client and clean repository manager."""
        self.client = TestClient(app)
        # Clear repositories for clean test state
        repository_manager.repositories.clear()
    
    def test_create_repository_config(self):
        """Test creating repository configuration."""
        config_data = {
            "owner": "testowner",
            "name": "testrepo",
            "clone_url": "https://github.com/testowner/testrepo.git",
            "project_type": "react",
            "auto_merge_threshold": 0.9,
            "error_threshold": 0.3,
            "max_validation_attempts": 5
        }
        
        response = self.client.post("/repositories", json=config_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert data["repo_id"] == "testowner-testrepo"
        assert "configured successfully" in data["message"]
    
    def test_create_repository_config_invalid_project_type(self):
        """Test creating repository with invalid project type."""
        config_data = {
            "owner": "testowner",
            "name": "testrepo",
            "clone_url": "https://github.com/testowner/testrepo.git",
            "project_type": "invalid_type"
        }
        
        response = self.client.post("/repositories", json=config_data)
        assert response.status_code == 400
        
        data = response.json()
        assert "Invalid project type" in data["error"]
    
    def test_list_repositories_empty(self):
        """Test listing repositories when none exist."""
        response = self.client.get("/repositories")
        assert response.status_code == 200
        
        data = response.json()
        assert "repositories" in data
        assert len(data["repositories"]) == 0
    
    def test_list_repositories_with_data(self):
        """Test listing repositories with existing data."""
        # Add test repository
        config = RepositoryConfig(
            repo_id="test-repo",
            owner="testowner",
            name="testrepo",
            clone_url="https://github.com/testowner/testrepo.git",
            project_type=ProjectType.VUE
        )
        repository_manager.add_repository(config)
        
        response = self.client.get("/repositories")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["repositories"]) == 1
        
        repo = data["repositories"][0]
        assert repo["repo_id"] == "test-repo"
        assert repo["owner"] == "testowner"
        assert repo["name"] == "testrepo"
        assert repo["project_type"] == "vue"
    
    def test_get_repository_config(self):
        """Test getting specific repository configuration."""
        # Add test repository
        config = RepositoryConfig(
            repo_id="get-test-repo",
            owner="testowner",
            name="testrepo",
            clone_url="https://github.com/testowner/testrepo.git",
            project_type=ProjectType.PYTHON,
            auto_merge_threshold=0.85,
            error_threshold=0.35
        )
        repository_manager.add_repository(config)
        
        response = self.client.get("/repositories/get-test-repo")
        assert response.status_code == 200
        
        data = response.json()
        assert data["repo_id"] == "get-test-repo"
        assert data["owner"] == "testowner"
        assert data["name"] == "testrepo"
        assert data["project_type"] == "python"
        assert data["auto_merge_threshold"] == 0.85
        assert data["error_threshold"] == 0.35
    
    def test_get_repository_config_not_found(self):
        """Test getting non-existent repository configuration."""
        response = self.client.get("/repositories/nonexistent")
        assert response.status_code == 404
        
        data = response.json()
        assert data["error"] == "Repository not found"
    
    def test_delete_repository_config(self):
        """Test deleting repository configuration."""
        # Add test repository
        config = RepositoryConfig(
            repo_id="delete-test-repo",
            owner="testowner",
            name="testrepo",
            clone_url="https://github.com/testowner/testrepo.git"
        )
        repository_manager.add_repository(config)
        
        # Verify it exists
        assert "delete-test-repo" in repository_manager.repositories
        
        # Delete it
        response = self.client.delete("/repositories/delete-test-repo")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert "deleted" in data["message"]
        
        # Verify it's gone
        assert "delete-test-repo" not in repository_manager.repositories
    
    def test_delete_repository_config_not_found(self):
        """Test deleting non-existent repository configuration."""
        response = self.client.delete("/repositories/nonexistent")
        assert response.status_code == 404
        
        data = response.json()
        assert data["error"] == "Repository not found"


class TestAnalysisEndpoints:
    """Test analysis management endpoints."""
    
    def setup_method(self):
        """Set up test client and clean state."""
        self.client = TestClient(app)
        orchestrator.active_sessions.clear()
        repository_manager.repositories.clear()
    
    def test_list_active_sessions_empty(self):
        """Test listing active sessions when none exist."""
        response = self.client.get("/analysis")
        assert response.status_code == 200
        
        data = response.json()
        assert "active_sessions" in data
        assert len(data["active_sessions"]) == 0
    
    def test_list_active_sessions_with_data(self):
        """Test listing active sessions with existing data."""
        # Add test session
        repo_config = RepositoryConfig(
            repo_id="test-repo",
            owner="testowner",
            name="testrepo",
            clone_url="https://github.com/testowner/testrepo.git"
        )
        
        session = AnalysisSession(
            session_id="test-session",
            repository_config=repo_config,
            pr_data={"number": 123, "title": "Test PR"},
            phase=AnalysisPhase.STATIC_ANALYSIS
        )
        
        orchestrator.active_sessions["test-session"] = session
        
        response = self.client.get("/analysis")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["active_sessions"]) == 1
        
        session_data = data["active_sessions"][0]
        assert session_data["session_id"] == "test-session"
        assert session_data["phase"] == "static_analysis"
        assert session_data["repository"] == "testowner/testrepo"
        assert session_data["pr_number"] == 123
    
    def test_get_analysis_status(self):
        """Test getting analysis status for specific session."""
        # Add test session
        repo_config = RepositoryConfig(
            repo_id="status-test-repo",
            owner="testowner",
            name="testrepo",
            clone_url="https://github.com/testowner/testrepo.git"
        )
        
        session = AnalysisSession(
            session_id="status-test-session",
            repository_config=repo_config,
            pr_data={"number": 456, "title": "Status Test PR"},
            phase=AnalysisPhase.UI_TESTING
        )
        session.results = {"static_analysis": {"functions_analyzed": 10}}
        session.errors = ["Test error"]
        
        orchestrator.active_sessions["status-test-session"] = session
        
        response = self.client.get("/analysis/status-test-session")
        assert response.status_code == 200
        
        data = response.json()
        assert data["session_id"] == "status-test-session"
        assert data["phase"] == "ui_testing"
        assert data["repository"] == "testowner/testrepo"
        assert data["pr_number"] == 456
        assert "results" in data
        assert "errors" in data
        assert len(data["errors"]) == 1
    
    def test_get_analysis_status_not_found(self):
        """Test getting analysis status for non-existent session."""
        response = self.client.get("/analysis/nonexistent-session")
        assert response.status_code == 404
        
        data = response.json()
        assert "Session not found" in data["error"]
    
    @pytest.mark.asyncio
    async def test_start_manual_analysis(self):
        """Test starting manual analysis."""
        # Add repository configuration
        config = RepositoryConfig(
            repo_id="manual-test-repo",
            owner="testowner",
            name="testrepo",
            clone_url="https://github.com/testowner/testrepo.git"
        )
        repository_manager.add_repository(config)
        
        # Mock the orchestrator start_analysis method
        with patch.object(orchestrator, 'start_analysis', new_callable=AsyncMock) as mock_start:
            mock_start.return_value = "mock-session-id"
            
            response = self.client.post(
                "/analysis/start",
                params={"repo_id": "manual-test-repo", "pr_number": 789}
            )
            
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "started"
            assert data["session_id"] == "mock-session-id"
            assert "Analysis started for PR #789" in data["message"]
            
            # Verify the mock was called
            mock_start.assert_called_once()
    
    def test_start_manual_analysis_repo_not_found(self):
        """Test starting manual analysis with non-existent repository."""
        response = self.client.post(
            "/analysis/start",
            params={"repo_id": "nonexistent-repo", "pr_number": 789}
        )
        
        assert response.status_code == 404
        
        data = response.json()
        assert data["error"] == "Repository not found"


class TestWebhookEndpoints:
    """Test GitHub webhook endpoints."""
    
    def setup_method(self):
        """Set up test client and clean state."""
        self.client = TestClient(app)
        repository_manager.repositories.clear()
    
    def test_github_webhook_invalid_event_type(self):
        """Test GitHub webhook with invalid event type."""
        payload = {"action": "opened", "repository": {"full_name": "test/repo"}}
        
        response = self.client.post(
            "/webhooks/github",
            json=payload,
            headers={"X-GitHub-Event": "issues"}
        )
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "ignored"
        assert "Event type issues not handled" in data["message"]
    
    def test_github_webhook_pull_request_ignored_action(self):
        """Test GitHub webhook with ignored PR action."""
        payload = {
            "action": "closed",
            "pull_request": {"number": 123, "title": "Test PR"},
            "repository": {"full_name": "testowner/testrepo"}
        }
        
        response = self.client.post(
            "/webhooks/github",
            json=payload,
            headers={"X-GitHub-Event": "pull_request"}
        )
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "ignored"
        assert "PR action 'closed' not processed" in data["message"]
    
    def test_github_webhook_pull_request_repo_not_configured(self):
        """Test GitHub webhook with unconfigured repository."""
        payload = {
            "action": "opened",
            "pull_request": {
                "number": 123,
                "title": "Test PR",
                "head": {"ref": "feature", "sha": "abc123"},
                "base": {"ref": "main", "sha": "def456"}
            },
            "repository": {"full_name": "unconfigured/repo"}
        }
        
        response = self.client.post(
            "/webhooks/github",
            json=payload,
            headers={"X-GitHub-Event": "pull_request"}
        )
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "ignored"
        assert "Repository unconfigured/repo not configured" in data["message"]
    
    @pytest.mark.asyncio
    async def test_github_webhook_pull_request_success(self):
        """Test successful GitHub webhook processing."""
        # Add repository configuration
        config = RepositoryConfig(
            repo_id="testowner-testrepo",
            owner="testowner",
            name="testrepo",
            clone_url="https://github.com/testowner/testrepo.git"
        )
        repository_manager.add_repository(config)
        
        payload = {
            "action": "opened",
            "pull_request": {
                "number": 123,
                "title": "Test PR",
                "head": {"ref": "feature", "sha": "abc123"},
                "base": {"ref": "main", "sha": "def456"}
            },
            "repository": {"full_name": "testowner/testrepo"}
        }
        
        # Mock the orchestrator start_analysis method
        with patch.object(orchestrator, 'start_analysis', new_callable=AsyncMock) as mock_start:
            mock_start.return_value = "webhook-session-id"
            
            response = self.client.post(
                "/webhooks/github",
                json=payload,
                headers={"X-GitHub-Event": "pull_request"}
            )
            
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "processing"
            assert data["session_id"] == "webhook-session-id"
            assert "Analysis started for PR #123" in data["message"]
            
            # Verify the mock was called
            mock_start.assert_called_once()
    
    def test_github_webhook_invalid_json(self):
        """Test GitHub webhook with invalid JSON."""
        response = self.client.post(
            "/webhooks/github",
            data="invalid json",
            headers={
                "X-GitHub-Event": "pull_request",
                "Content-Type": "application/json"
            }
        )
        
        assert response.status_code == 400
        
        data = response.json()
        assert data["error"] == "Invalid JSON payload"


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)
    
    def test_404_endpoint(self):
        """Test accessing non-existent endpoint."""
        response = self.client.get("/nonexistent")
        assert response.status_code == 404
    
    def test_method_not_allowed(self):
        """Test using wrong HTTP method."""
        response = self.client.put("/health")
        assert response.status_code == 405
    
    def test_validation_error(self):
        """Test request validation error."""
        # Send invalid data to repository creation endpoint
        invalid_data = {
            "owner": "",  # Empty owner should fail validation
            "name": "testrepo",
            "clone_url": "invalid-url"
        }
        
        response = self.client.post("/repositories", json=invalid_data)
        assert response.status_code == 422  # Validation error
    
    @patch('api_server.repository_manager.add_repository')
    def test_internal_server_error(self, mock_add):
        """Test internal server error handling."""
        # Mock an internal error
        mock_add.side_effect = Exception("Internal error")
        
        config_data = {
            "owner": "testowner",
            "name": "testrepo",
            "clone_url": "https://github.com/testowner/testrepo.git",
            "project_type": "react"
        }
        
        response = self.client.post("/repositories", json=config_data)
        assert response.status_code == 500
        
        data = response.json()
        assert data["error"] == "Internal server error"


class TestCORSAndMiddleware:
    """Test CORS and middleware functionality."""
    
    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)
    
    def test_cors_headers(self):
        """Test CORS headers are present."""
        response = self.client.options("/")
        
        # Check for CORS headers
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers
        assert "access-control-allow-headers" in response.headers
    
    def test_preflight_request(self):
        """Test preflight CORS request."""
        response = self.client.options(
            "/repositories",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type"
            }
        )
        
        assert response.status_code == 200


class TestSignatureVerification:
    """Test GitHub webhook signature verification."""
    
    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)
    
    @patch.dict(os.environ, {"GITHUB_WEBHOOK_SECRET": ""})
    def test_signature_verification_disabled(self):
        """Test signature verification when secret is not configured."""
        from api_server import verify_github_signature
        
        # Mock request
        mock_request = Mock()
        mock_request.headers = {}
        
        # Should return True when secret is not configured (development mode)
        result = verify_github_signature(mock_request)
        assert result is True
    
    @patch.dict(os.environ, {"GITHUB_WEBHOOK_SECRET": "test-secret"})
    def test_signature_verification_missing_header(self):
        """Test signature verification with missing signature header."""
        from api_server import verify_github_signature
        
        # Mock request without signature header
        mock_request = Mock()
        mock_request.headers = {}
        
        result = verify_github_signature(mock_request)
        assert result is False
    
    @patch.dict(os.environ, {"GITHUB_WEBHOOK_SECRET": "test-secret"})
    def test_signature_verification_valid(self):
        """Test signature verification with valid signature."""
        import hmac
        import hashlib
        from api_server import verify_github_signature
        
        # Mock request body and signature
        body = b'{"test": "payload"}'
        secret = "test-secret"
        expected_signature = "sha256=" + hmac.new(
            secret.encode(),
            body,
            hashlib.sha256
        ).hexdigest()
        
        mock_request = Mock()
        mock_request.headers = {"X-Hub-Signature-256": expected_signature}
        mock_request.body.return_value = body
        
        result = verify_github_signature(mock_request)
        assert result is True


class TestStartupShutdown:
    """Test application startup and shutdown events."""
    
    def test_startup_event(self):
        """Test application startup event."""
        # This is tested implicitly when the TestClient is created
        # The startup event should run without errors
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_shutdown_event(self):
        """Test application shutdown event."""
        # Add a test session to verify cleanup
        repo_config = RepositoryConfig(
            repo_id="shutdown-test",
            owner="testowner",
            name="testrepo",
            clone_url="https://github.com/testowner/testrepo.git"
        )
        
        session = AnalysisSession(
            session_id="shutdown-session",
            repository_config=repo_config,
            pr_data={"number": 999}
        )
        
        orchestrator.active_sessions["shutdown-session"] = session
        
        # Mock the cleanup method
        with patch.object(orchestrator.sandbox_manager, 'cleanup_sandbox', new_callable=AsyncMock) as mock_cleanup:
            # Import and call shutdown event directly
            from api_server import shutdown_event
            await shutdown_event()
            
            # Verify cleanup was called
            mock_cleanup.assert_called_once_with("shutdown-session")


if __name__ == "__main__":
    # Run all tests
    pytest.main([__file__, "-v", "--tb=short"])

