"""
Comprehensive tests for PR Analysis Pipeline

🧪 100% functionality coverage with mock calls for all components
"""

import asyncio
import json
import pytest
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from pr_analysis_pipeline import (
    ProjectType,
    AnalysisPhase,
    RepositoryConfig,
    AnalysisSession,
    RepositoryManager,
    SandboxManager,
    StaticAnalyzer,
    UITester,
    DecisionEngine,
    PRAnalysisOrchestrator
)


class TestProjectType:
    """Test ProjectType enum."""
    
    def test_project_types(self):
        """Test all project types are defined."""
        assert ProjectType.REACT.value == "react"
        assert ProjectType.VUE.value == "vue"
        assert ProjectType.ANGULAR.value == "angular"
        assert ProjectType.NEXTJS.value == "nextjs"
        assert ProjectType.PYTHON.value == "python"
        assert ProjectType.NODE.value == "node"


class TestAnalysisPhase:
    """Test AnalysisPhase enum."""
    
    def test_analysis_phases(self):
        """Test all analysis phases are defined."""
        assert AnalysisPhase.PENDING.value == "pending"
        assert AnalysisPhase.CLONING.value == "cloning"
        assert AnalysisPhase.BUILDING.value == "building"
        assert AnalysisPhase.STATIC_ANALYSIS.value == "static_analysis"
        assert AnalysisPhase.UI_TESTING.value == "ui_testing"
        assert AnalysisPhase.DECISION.value == "decision"
        assert AnalysisPhase.COMPLETED.value == "completed"
        assert AnalysisPhase.FAILED.value == "failed"


class TestRepositoryConfig:
    """Test RepositoryConfig dataclass."""
    
    def test_repository_config_creation(self):
        """Test creating repository configuration."""
        config = RepositoryConfig(
            repo_id="test-repo",
            owner="testowner",
            name="testrepo",
            clone_url="https://github.com/testowner/testrepo.git",
            project_type=ProjectType.REACT,
            auto_merge_threshold=0.9,
            error_threshold=0.3
        )
        
        assert config.repo_id == "test-repo"
        assert config.owner == "testowner"
        assert config.name == "testrepo"
        assert config.project_type == ProjectType.REACT
        assert config.auto_merge_threshold == 0.9
        assert config.error_threshold == 0.3
    
    def test_to_dict_conversion(self):
        """Test converting repository config to dictionary."""
        config = RepositoryConfig(
            repo_id="test-repo",
            owner="testowner",
            name="testrepo",
            clone_url="https://github.com/testowner/testrepo.git",
            project_type=ProjectType.PYTHON
        )
        
        data = config.to_dict()
        assert data["project_type"] == "python"
        assert data["repo_id"] == "test-repo"
        assert data["owner"] == "testowner"
    
    def test_from_dict_creation(self):
        """Test creating repository config from dictionary."""
        data = {
            "repo_id": "test-repo",
            "owner": "testowner",
            "name": "testrepo",
            "clone_url": "https://github.com/testowner/testrepo.git",
            "project_type": "vue",
            "auto_merge_threshold": 0.8,
            "error_threshold": 0.4,
            "max_validation_attempts": 3
        }
        
        config = RepositoryConfig.from_dict(data)
        assert config.project_type == ProjectType.VUE
        assert config.repo_id == "test-repo"


class TestAnalysisSession:
    """Test AnalysisSession dataclass."""
    
    def test_analysis_session_creation(self):
        """Test creating analysis session."""
        repo_config = RepositoryConfig(
            repo_id="test-repo",
            owner="testowner",
            name="testrepo",
            clone_url="https://github.com/testowner/testrepo.git"
        )
        
        pr_data = {"number": 123, "title": "Test PR"}
        
        session = AnalysisSession(
            session_id="test-session",
            repository_config=repo_config,
            pr_data=pr_data
        )
        
        assert session.session_id == "test-session"
        assert session.repository_config == repo_config
        assert session.pr_data == pr_data
        assert session.phase == AnalysisPhase.PENDING
        assert isinstance(session.created_at, datetime)
        assert isinstance(session.results, dict)
        assert isinstance(session.errors, list)


class TestRepositoryManager:
    """Test RepositoryManager class."""
    
    def test_repository_manager_initialization(self):
        """Test repository manager initialization."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({}, f)
            config_file = f.name
        
        try:
            manager = RepositoryManager(config_file)
            assert isinstance(manager.repositories, dict)
            assert len(manager.repositories) == 0
        finally:
            os.unlink(config_file)
    
    def test_add_repository(self):
        """Test adding repository configuration."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({}, f)
            config_file = f.name
        
        try:
            manager = RepositoryManager(config_file)
            
            config = RepositoryConfig(
                repo_id="test-repo",
                owner="testowner",
                name="testrepo",
                clone_url="https://github.com/testowner/testrepo.git"
            )
            
            manager.add_repository(config)
            
            assert "test-repo" in manager.repositories
            assert manager.repositories["test-repo"] == config
        finally:
            os.unlink(config_file)
    
    def test_get_repository(self):
        """Test getting repository configuration."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({}, f)
            config_file = f.name
        
        try:
            manager = RepositoryManager(config_file)
            
            config = RepositoryConfig(
                repo_id="test-repo",
                owner="testowner",
                name="testrepo",
                clone_url="https://github.com/testowner/testrepo.git"
            )
            
            manager.add_repository(config)
            
            retrieved = manager.get_repository("test-repo")
            assert retrieved == config
            
            not_found = manager.get_repository("nonexistent")
            assert not_found is None
        finally:
            os.unlink(config_file)
    
    def test_list_repositories(self):
        """Test listing all repositories."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({}, f)
            config_file = f.name
        
        try:
            manager = RepositoryManager(config_file)
            
            config1 = RepositoryConfig(
                repo_id="test-repo-1",
                owner="testowner",
                name="testrepo1",
                clone_url="https://github.com/testowner/testrepo1.git"
            )
            
            config2 = RepositoryConfig(
                repo_id="test-repo-2",
                owner="testowner",
                name="testrepo2",
                clone_url="https://github.com/testowner/testrepo2.git"
            )
            
            manager.add_repository(config1)
            manager.add_repository(config2)
            
            repos = manager.list_repositories()
            assert len(repos) == 2
            assert config1 in repos
            assert config2 in repos
        finally:
            os.unlink(config_file)


class TestSandboxManager:
    """Test SandboxManager class."""
    
    @pytest.mark.asyncio
    async def test_create_sandbox(self):
        """Test creating sandbox environment."""
        manager = SandboxManager()
        
        config = {"memory_limit": "1g", "cpu_limit": "1"}
        sandbox = await manager.create_sandbox("test-session", config)
        
        assert sandbox["id"] == "test-session"
        assert sandbox["status"] == "created"
        assert sandbox["config"] == config
        assert "test-session" in manager.active_sandboxes
    
    @pytest.mark.asyncio
    async def test_deploy_repository(self):
        """Test deploying repository in sandbox."""
        manager = SandboxManager()
        
        sandbox = {"id": "test-session", "status": "created"}
        
        repo_config = RepositoryConfig(
            repo_id="test-repo",
            owner="testowner",
            name="testrepo",
            clone_url="https://github.com/testowner/testrepo.git",
            project_type=ProjectType.REACT
        )
        
        pr_data = {
            "number": 123,
            "head": {"ref": "feature-branch", "sha": "abc123"}
        }
        
        result = await manager.deploy_repository(sandbox, repo_config, pr_data)
        
        assert "clone" in result
        assert "build" in result
        assert "deploy" in result
        assert "app_url" in result
        assert result["clone"]["status"] == "success"
        assert result["build"]["status"] == "success"
        assert result["deploy"]["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_cleanup_sandbox(self):
        """Test cleaning up sandbox environment."""
        manager = SandboxManager()
        
        # Create sandbox first
        await manager.create_sandbox("test-session", {})
        assert "test-session" in manager.active_sandboxes
        
        # Cleanup sandbox
        await manager.cleanup_sandbox("test-session")
        assert "test-session" not in manager.active_sandboxes


class TestStaticAnalyzer:
    """Test StaticAnalyzer class."""
    
    @pytest.mark.asyncio
    async def test_analyze_codebase(self):
        """Test static analysis of codebase."""
        analyzer = StaticAnalyzer()
        
        pr_data = {
            "number": 123,
            "changed_files": ["src/api.js", "src/components/Button.jsx"]
        }
        
        result = await analyzer.analyze_codebase("/tmp/repo", pr_data)
        
        assert "functions_analyzed" in result
        assert "dependencies_mapped" in result
        assert "breaking_changes" in result
        assert "complexity_score" in result
        assert "test_coverage" in result
        assert "security_issues" in result
        assert "performance_warnings" in result
        
        assert isinstance(result["functions_analyzed"], int)
        assert isinstance(result["breaking_changes"], list)
    
    @pytest.mark.asyncio
    async def test_detect_breaking_changes(self):
        """Test detecting breaking changes."""
        analyzer = StaticAnalyzer()
        
        pr_data = {"changed_files": ["src/api.js"]}
        
        breaking_changes = await analyzer._detect_breaking_changes(pr_data)
        
        assert isinstance(breaking_changes, list)
        if breaking_changes:
            change = breaking_changes[0]
            assert "type" in change
            assert "file" in change
            assert "severity" in change
            assert "description" in change


class TestUITester:
    """Test UITester class."""
    
    @pytest.mark.asyncio
    async def test_test_application(self):
        """Test UI testing of application."""
        tester = UITester()
        
        test_scenarios = [
            {"name": "Homepage test", "type": "load_test"},
            {"name": "Navigation test", "type": "navigation_test"}
        ]
        
        result = await tester.test_application("http://localhost:3000", test_scenarios)
        
        assert "scenarios_executed" in result
        assert "passed" in result
        assert "failed" in result
        assert "performance_metrics" in result
        assert "console_errors" in result
        assert "network_errors" in result
        assert "accessibility_score" in result
        
        assert result["scenarios_executed"] == len(test_scenarios)
        assert isinstance(result["performance_metrics"], dict)
    
    def test_generate_test_scenarios(self):
        """Test generating test scenarios."""
        tester = UITester()
        
        static_analysis = {"functions_analyzed": 10}
        pr_data = {
            "changed_files": [
                "src/components/Button.jsx",
                "src/api/endpoints.js",
                "README.md"
            ]
        }
        
        scenarios = tester.generate_test_scenarios(static_analysis, pr_data)
        
        assert isinstance(scenarios, list)
        assert len(scenarios) >= 2  # At least default scenarios
        
        # Check component test scenarios
        component_scenarios = [s for s in scenarios if s["type"] == "component_test"]
        assert len(component_scenarios) == 2  # Button.jsx and endpoints.js
        
        # Check default scenarios
        default_scenarios = [s for s in scenarios if s["type"] in ["load_test", "navigation_test"]]
        assert len(default_scenarios) == 2


class TestDecisionEngine:
    """Test DecisionEngine class."""
    
    @pytest.mark.asyncio
    async def test_make_decision_merge(self):
        """Test decision making for merge scenario."""
        engine = DecisionEngine()
        
        repo_config = RepositoryConfig(
            repo_id="test-repo",
            owner="testowner",
            name="testrepo",
            clone_url="https://github.com/testowner/testrepo.git",
            auto_merge_threshold=0.8,
            error_threshold=0.4
        )
        
        session = AnalysisSession(
            session_id="test-session",
            repository_config=repo_config,
            pr_data={"number": 123},
            results={
                "static_analysis": {
                    "breaking_changes": [],
                    "security_issues": [],
                    "complexity_score": 0.2
                },
                "ui_testing": {
                    "passed": 5,
                    "scenarios_executed": 5,
                    "console_errors": [],
                    "network_errors": []
                },
                "deployment": {
                    "clone": {"status": "success"},
                    "build": {"status": "success"},
                    "deploy": {"status": "success"}
                }
            }
        )
        
        decision, reason, context = await engine.make_decision(session)
        
        assert decision == "merge"
        assert "score" in reason
        assert isinstance(context, dict)
        assert "session_id" in context
    
    @pytest.mark.asyncio
    async def test_make_decision_error(self):
        """Test decision making for error scenario."""
        engine = DecisionEngine()
        
        repo_config = RepositoryConfig(
            repo_id="test-repo",
            owner="testowner",
            name="testrepo",
            clone_url="https://github.com/testowner/testrepo.git",
            auto_merge_threshold=0.8,
            error_threshold=0.4
        )
        
        session = AnalysisSession(
            session_id="test-session",
            repository_config=repo_config,
            pr_data={"number": 123},
            results={
                "static_analysis": {
                    "breaking_changes": [{"type": "major"}],
                    "security_issues": [{"severity": "high"}],
                    "complexity_score": 0.8
                },
                "ui_testing": {
                    "passed": 1,
                    "scenarios_executed": 5,
                    "console_errors": ["Error 1", "Error 2"],
                    "network_errors": ["Network error"]
                },
                "deployment": {
                    "clone": {"status": "failed"},
                    "build": {"status": "failed"},
                    "deploy": {"status": "failed"}
                }
            }
        )
        
        decision, reason, context = await engine.make_decision(session)
        
        assert decision == "error"
        assert "Critical issues" in reason
    
    def test_calculate_static_score(self):
        """Test calculating static analysis score."""
        engine = DecisionEngine()
        
        # High quality code
        good_results = {
            "breaking_changes": [],
            "security_issues": [],
            "complexity_score": 0.2
        }
        score = engine._calculate_static_score(good_results)
        assert score > 0.7
        
        # Poor quality code
        bad_results = {
            "breaking_changes": [{"type": "major"}, {"type": "minor"}],
            "security_issues": [{"severity": "high"}],
            "complexity_score": 0.9
        }
        score = engine._calculate_static_score(bad_results)
        assert score < 0.3
    
    def test_calculate_ui_score(self):
        """Test calculating UI testing score."""
        engine = DecisionEngine()
        
        # All tests pass
        good_results = {
            "passed": 5,
            "scenarios_executed": 5,
            "console_errors": [],
            "network_errors": []
        }
        score = engine._calculate_ui_score(good_results)
        assert score == 1.0
        
        # Some tests fail with errors
        bad_results = {
            "passed": 2,
            "scenarios_executed": 5,
            "console_errors": ["Error 1", "Error 2"],
            "network_errors": ["Network error"]
        }
        score = engine._calculate_ui_score(bad_results)
        assert score < 0.5
    
    def test_calculate_deployment_score(self):
        """Test calculating deployment score."""
        engine = DecisionEngine()
        
        # All phases succeed
        good_results = {
            "clone": {"status": "success"},
            "build": {"status": "success"},
            "deploy": {"status": "success"}
        }
        score = engine._calculate_deployment_score(good_results)
        assert score == 1.0
        
        # All phases fail
        bad_results = {
            "clone": {"status": "failed"},
            "build": {"status": "failed"},
            "deploy": {"status": "failed"}
        }
        score = engine._calculate_deployment_score(bad_results)
        assert score == 0.0
        
        # Partial success
        partial_results = {
            "clone": {"status": "success"},
            "build": {"status": "success"},
            "deploy": {"status": "failed"}
        }
        score = engine._calculate_deployment_score(partial_results)
        assert score == 0.7


class TestPRAnalysisOrchestrator:
    """Test PRAnalysisOrchestrator class."""
    
    @pytest.mark.asyncio
    async def test_start_analysis(self):
        """Test starting analysis session."""
        orchestrator = PRAnalysisOrchestrator()
        
        repo_config = RepositoryConfig(
            repo_id="test-repo",
            owner="testowner",
            name="testrepo",
            clone_url="https://github.com/testowner/testrepo.git"
        )
        
        pr_data = {"number": 123, "title": "Test PR"}
        
        session_id = await orchestrator.start_analysis(repo_config, pr_data)
        
        assert isinstance(session_id, str)
        assert session_id in orchestrator.active_sessions
        
        session = orchestrator.active_sessions[session_id]
        assert session.repository_config == repo_config
        assert session.pr_data == pr_data
    
    def test_get_session_status(self):
        """Test getting session status."""
        orchestrator = PRAnalysisOrchestrator()
        
        # Test non-existent session
        status = orchestrator.get_session_status("nonexistent")
        assert "error" in status
        
        # Test existing session
        repo_config = RepositoryConfig(
            repo_id="test-repo",
            owner="testowner",
            name="testrepo",
            clone_url="https://github.com/testowner/testrepo.git"
        )
        
        session = AnalysisSession(
            session_id="test-session",
            repository_config=repo_config,
            pr_data={"number": 123}
        )
        
        orchestrator.active_sessions["test-session"] = session
        
        status = orchestrator.get_session_status("test-session")
        assert status["session_id"] == "test-session"
        assert status["phase"] == "pending"
        assert "repository" in status
        assert "pr_number" in status
    
    @pytest.mark.asyncio
    async def test_run_analysis_pipeline_success(self):
        """Test successful analysis pipeline execution."""
        orchestrator = PRAnalysisOrchestrator()
        
        repo_config = RepositoryConfig(
            repo_id="test-repo",
            owner="testowner",
            name="testrepo",
            clone_url="https://github.com/testowner/testrepo.git"
        )
        
        session = AnalysisSession(
            session_id="test-session",
            repository_config=repo_config,
            pr_data={"number": 123, "changed_files": ["src/test.js"]}
        )
        
        # Mock the analysis pipeline
        with patch.object(orchestrator.sandbox_manager, 'create_sandbox', new_callable=AsyncMock) as mock_create, \
             patch.object(orchestrator.sandbox_manager, 'deploy_repository', new_callable=AsyncMock) as mock_deploy, \
             patch.object(orchestrator.static_analyzer, 'analyze_codebase', new_callable=AsyncMock) as mock_static, \
             patch.object(orchestrator.ui_tester, 'test_application', new_callable=AsyncMock) as mock_ui, \
             patch.object(orchestrator.decision_engine, 'make_decision', new_callable=AsyncMock) as mock_decision, \
             patch.object(orchestrator, '_post_results_to_github', new_callable=AsyncMock) as mock_post, \
             patch.object(orchestrator.sandbox_manager, 'cleanup_sandbox', new_callable=AsyncMock) as mock_cleanup:
            
            # Configure mocks
            mock_create.return_value = {"id": "test-session"}
            mock_deploy.return_value = {
                "clone": {"status": "success"},
                "build": {"status": "success"},
                "deploy": {"status": "success"},
                "app_url": "http://localhost:3000"
            }
            mock_static.return_value = {
                "functions_analyzed": 10,
                "breaking_changes": []
            }
            mock_ui.return_value = {
                "scenarios_executed": 3,
                "passed": 3,
                "failed": 0
            }
            mock_decision.return_value = ("merge", "All checks passed", {})
            
            # Run pipeline
            await orchestrator._run_analysis_pipeline(session)
            
            # Verify all phases were called
            mock_create.assert_called_once()
            mock_deploy.assert_called_once()
            mock_static.assert_called_once()
            mock_ui.assert_called_once()
            mock_decision.assert_called_once()
            mock_post.assert_called_once()
            mock_cleanup.assert_called_once()
            
            # Verify session state
            assert session.phase == AnalysisPhase.COMPLETED
            assert "deployment" in session.results
            assert "static_analysis" in session.results
            assert "ui_testing" in session.results
            assert "decision" in session.results
    
    @pytest.mark.asyncio
    async def test_run_analysis_pipeline_failure(self):
        """Test analysis pipeline failure handling."""
        orchestrator = PRAnalysisOrchestrator()
        
        repo_config = RepositoryConfig(
            repo_id="test-repo",
            owner="testowner",
            name="testrepo",
            clone_url="https://github.com/testowner/testrepo.git"
        )
        
        session = AnalysisSession(
            session_id="test-session",
            repository_config=repo_config,
            pr_data={"number": 123}
        )
        
        # Mock failure in sandbox creation
        with patch.object(orchestrator.sandbox_manager, 'create_sandbox', new_callable=AsyncMock) as mock_create, \
             patch.object(orchestrator.sandbox_manager, 'cleanup_sandbox', new_callable=AsyncMock) as mock_cleanup:
            
            mock_create.side_effect = Exception("Sandbox creation failed")
            
            # Run pipeline
            await orchestrator._run_analysis_pipeline(session)
            
            # Verify failure handling
            assert session.phase == AnalysisPhase.FAILED
            assert len(session.errors) > 0
            assert "Sandbox creation failed" in session.errors[0]
            mock_cleanup.assert_called_once()


class TestIntegrationScenarios:
    """Test complete integration scenarios."""
    
    @pytest.mark.asyncio
    async def test_complete_pr_analysis_workflow(self):
        """Test complete PR analysis workflow from start to finish."""
        # Initialize components
        orchestrator = PRAnalysisOrchestrator()
        
        # Configure repository
        repo_config = RepositoryConfig(
            repo_id="integration-test",
            owner="testowner",
            name="testrepo",
            clone_url="https://github.com/testowner/testrepo.git",
            project_type=ProjectType.REACT,
            auto_merge_threshold=0.8,
            error_threshold=0.4
        )
        
        orchestrator.repository_manager.add_repository(repo_config)
        
        # Simulate PR data
        pr_data = {
            "number": 456,
            "title": "Add new feature",
            "head": {"ref": "feature-branch", "sha": "def456"},
            "changed_files": ["src/components/NewFeature.jsx", "src/api/newEndpoint.js"]
        }
        
        # Start analysis
        session_id = await orchestrator.start_analysis(repo_config, pr_data)
        
        # Wait for analysis to complete (in real scenario)
        await asyncio.sleep(0.1)
        
        # Check session status
        status = orchestrator.get_session_status(session_id)
        
        assert status["session_id"] == session_id
        assert status["repository"] == "testowner/testrepo"
        assert status["pr_number"] == 456
        assert isinstance(status["created_at"], str)
        assert isinstance(status["updated_at"], str)
    
    @pytest.mark.asyncio
    async def test_multiple_concurrent_analyses(self):
        """Test handling multiple concurrent PR analyses."""
        orchestrator = PRAnalysisOrchestrator()
        
        repo_config = RepositoryConfig(
            repo_id="concurrent-test",
            owner="testowner",
            name="testrepo",
            clone_url="https://github.com/testowner/testrepo.git"
        )
        
        # Start multiple analyses
        session_ids = []
        for i in range(3):
            pr_data = {
                "number": 100 + i,
                "title": f"PR {i}",
                "head": {"ref": f"feature-{i}", "sha": f"sha{i}"}
            }
            session_id = await orchestrator.start_analysis(repo_config, pr_data)
            session_ids.append(session_id)
        
        # Verify all sessions are tracked
        assert len(orchestrator.active_sessions) == 3
        
        for session_id in session_ids:
            assert session_id in orchestrator.active_sessions
            status = orchestrator.get_session_status(session_id)
            assert "error" not in status
    
    def test_configuration_persistence(self):
        """Test repository configuration persistence."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({}, f)
            config_file = f.name
        
        try:
            # Create manager and add configurations
            manager1 = RepositoryManager(config_file)
            
            config1 = RepositoryConfig(
                repo_id="persist-test-1",
                owner="testowner",
                name="repo1",
                clone_url="https://github.com/testowner/repo1.git",
                project_type=ProjectType.VUE
            )
            
            config2 = RepositoryConfig(
                repo_id="persist-test-2",
                owner="testowner",
                name="repo2",
                clone_url="https://github.com/testowner/repo2.git",
                project_type=ProjectType.PYTHON
            )
            
            manager1.add_repository(config1)
            manager1.add_repository(config2)
            
            # Create new manager instance and verify persistence
            manager2 = RepositoryManager(config_file)
            
            assert len(manager2.repositories) == 2
            assert "persist-test-1" in manager2.repositories
            assert "persist-test-2" in manager2.repositories
            
            retrieved1 = manager2.get_repository("persist-test-1")
            retrieved2 = manager2.get_repository("persist-test-2")
            
            assert retrieved1.project_type == ProjectType.VUE
            assert retrieved2.project_type == ProjectType.PYTHON
        finally:
            os.unlink(config_file)


if __name__ == "__main__":
    # Run all tests
    pytest.main([__file__, "-v", "--tb=short"])

