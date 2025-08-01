#!/usr/bin/env python3
"""
Workflow Orchestrator for Integrated Services
Coordinates between web-eval-agent, Cloudflare, grainchain, Codegen, and graph-sitter
"""

import asyncio
import logging
import json
import time
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

from .config_manager import get_config_manager
from .service_abstractions import get_service_manager, ServiceResponse
from .grainchain_integration import get_grainchain_integration, SandboxConfig
from .graph_sitter_integration import get_graph_sitter_integration
from .tool_handlers import handle_web_evaluation

logger = logging.getLogger(__name__)

class WorkflowStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class WorkflowStepStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class WorkflowStep:
    """Represents a single step in the workflow"""
    id: str
    name: str
    service: str
    status: WorkflowStepStatus = WorkflowStepStatus.PENDING
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    dependencies: List[str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []

@dataclass
class WorkflowContext:
    """Context information for workflow execution"""
    repository: Optional[str] = None
    pull_request_number: Optional[int] = None
    branch: Optional[str] = None
    commit_sha: Optional[str] = None
    changed_files: List[str] = None
    user_requirements: Optional[str] = None
    webhook_event: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.changed_files is None:
            self.changed_files = []

@dataclass
class WorkflowResult:
    """Result from workflow execution"""
    workflow_id: str
    status: WorkflowStatus
    start_time: float
    end_time: Optional[float] = None
    steps: List[WorkflowStep] = None
    context: Optional[WorkflowContext] = None
    summary: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    def __post_init__(self):
        if self.steps is None:
            self.steps = []

class WorkflowOrchestrator:
    """Main workflow orchestrator for all integrated services"""
    
    def __init__(self):
        self.config_manager = get_config_manager()
        self.service_manager = get_service_manager()
        self.grainchain = get_grainchain_integration()
        self.graph_sitter = get_graph_sitter_integration()
        self.logger = logging.getLogger("workflow_orchestrator")
        
        # Active workflows
        self._active_workflows: Dict[str, WorkflowResult] = {}
        
    async def execute_pr_workflow(
        self,
        webhook_event: Dict[str, Any],
        user_requirements: Optional[str] = None
    ) -> WorkflowResult:
        """Execute complete workflow for PR events"""
        
        workflow_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Extract context from webhook event
        context = self._extract_context_from_webhook(webhook_event, user_requirements)
        
        # Create workflow result
        workflow_result = WorkflowResult(
            workflow_id=workflow_id,
            status=WorkflowStatus.RUNNING,
            start_time=start_time,
            context=context
        )
        
        self._active_workflows[workflow_id] = workflow_result
        
        try:
            # Define workflow steps based on event characteristics
            steps = self._plan_workflow_steps(context, webhook_event)
            workflow_result.steps = steps
            
            self.logger.info(f"Starting workflow {workflow_id} with {len(steps)} steps")
            
            # Execute steps
            for step in steps:
                if workflow_result.status == WorkflowStatus.CANCELLED:
                    break
                    
                await self._execute_workflow_step(step, context, workflow_result)
                
                # Check if step failed and should stop workflow
                if step.status == WorkflowStepStatus.FAILED and step.service in ["graph_sitter", "grainchain"]:
                    # Critical services - stop workflow
                    workflow_result.status = WorkflowStatus.FAILED
                    workflow_result.error = f"Critical step {step.name} failed: {step.error}"
                    break
            
            # Generate summary if workflow completed successfully
            if workflow_result.status == WorkflowStatus.RUNNING:
                workflow_result.status = WorkflowStatus.COMPLETED
                workflow_result.summary = self._generate_workflow_summary(workflow_result)
            
            workflow_result.end_time = time.time()
            
            self.logger.info(f"Workflow {workflow_id} completed with status: {workflow_result.status.value}")
            
            return workflow_result
            
        except Exception as e:
            self.logger.error(f"Workflow {workflow_id} failed: {e}")
            workflow_result.status = WorkflowStatus.FAILED
            workflow_result.error = str(e)
            workflow_result.end_time = time.time()
            return workflow_result
    
    def _extract_context_from_webhook(
        self,
        webhook_event: Dict[str, Any],
        user_requirements: Optional[str]
    ) -> WorkflowContext:
        """Extract workflow context from webhook event"""
        
        event_data = webhook_event.get("data", {})
        
        if webhook_event.get("event_type") == "pull_request":
            pr_data = event_data.get("pull_request", {})
            repo_data = event_data.get("repository", {})
            
            return WorkflowContext(
                repository=repo_data.get("full_name"),
                pull_request_number=pr_data.get("number"),
                branch=pr_data.get("head", {}).get("ref"),
                commit_sha=pr_data.get("head", {}).get("sha"),
                changed_files=[],  # Would be populated from PR diff
                user_requirements=user_requirements,
                webhook_event=webhook_event
            )
        
        return WorkflowContext(
            user_requirements=user_requirements,
            webhook_event=webhook_event
        )
    
    def _plan_workflow_steps(
        self,
        context: WorkflowContext,
        webhook_event: Dict[str, Any]
    ) -> List[WorkflowStep]:
        """Plan workflow steps based on context and event"""
        
        steps = []
        
        # Step 1: Code Analysis (always first)
        steps.append(WorkflowStep(
            id="code_analysis",
            name="Code Analysis with Graph-sitter",
            service="graph_sitter"
        ))
        
        # Step 2: Security Validation (depends on code analysis)
        steps.append(WorkflowStep(
            id="security_validation",
            name="Security Validation",
            service="grainchain",
            dependencies=["code_analysis"]
        ))
        
        # Step 3: Sandbox Testing (depends on security validation)
        steps.append(WorkflowStep(
            id="sandbox_testing",
            name="Sandbox Code Testing",
            service="grainchain",
            dependencies=["security_validation"]
        ))
        
        # Step 4: UI Validation (can run in parallel with sandbox testing)
        if self._should_run_ui_validation(context, webhook_event):
            steps.append(WorkflowStep(
                id="ui_validation",
                name="UI Functionality Validation",
                service="web_eval_agent",
                dependencies=["code_analysis"]
            ))
        
        # Step 5: Intelligent Analysis (depends on all previous steps)
        steps.append(WorkflowStep(
            id="intelligent_analysis",
            name="AI-Powered Code Analysis",
            service="codegen",
            dependencies=["code_analysis", "sandbox_testing"]
        ))
        
        # Step 6: Report Generation (final step)
        steps.append(WorkflowStep(
            id="report_generation",
            name="Generate Comprehensive Report",
            service="orchestrator",
            dependencies=["intelligent_analysis"]
        ))
        
        return steps
    
    def _should_run_ui_validation(
        self,
        context: WorkflowContext,
        webhook_event: Dict[str, Any]
    ) -> bool:
        """Determine if UI validation should be run"""
        
        # Run UI validation if:
        # 1. It's a PR with frontend changes
        # 2. User specifically requested it
        # 3. Repository appears to be a web application
        
        if context.user_requirements and "ui" in context.user_requirements.lower():
            return True
        
        # Check if changed files include frontend files
        frontend_extensions = ['.html', '.css', '.js', '.jsx', '.ts', '.tsx', '.vue', '.svelte']
        for file in context.changed_files:
            if any(file.endswith(ext) for ext in frontend_extensions):
                return True
        
        return False
    
    async def _execute_workflow_step(
        self,
        step: WorkflowStep,
        context: WorkflowContext,
        workflow_result: WorkflowResult
    ):
        """Execute a single workflow step"""
        
        # Check dependencies
        if not self._check_step_dependencies(step, workflow_result.steps):
            step.status = WorkflowStepStatus.SKIPPED
            step.error = "Dependencies not met"
            return
        
        step.status = WorkflowStepStatus.RUNNING
        step.start_time = time.time()
        
        self.logger.info(f"Executing step: {step.name}")
        
        try:
            if step.service == "graph_sitter":
                result = await self._execute_graph_sitter_step(step, context)
            elif step.service == "grainchain":
                result = await self._execute_grainchain_step(step, context, workflow_result)
            elif step.service == "web_eval_agent":
                result = await self._execute_web_eval_step(step, context)
            elif step.service == "codegen":
                result = await self._execute_codegen_step(step, context, workflow_result)
            elif step.service == "orchestrator":
                result = await self._execute_orchestrator_step(step, context, workflow_result)
            else:
                raise ValueError(f"Unknown service: {step.service}")
            
            step.result = result
            step.status = WorkflowStepStatus.COMPLETED
            
        except Exception as e:
            self.logger.error(f"Step {step.name} failed: {e}")
            step.status = WorkflowStepStatus.FAILED
            step.error = str(e)
        
        step.end_time = time.time()
    
    def _check_step_dependencies(
        self,
        step: WorkflowStep,
        all_steps: List[WorkflowStep]
    ) -> bool:
        """Check if step dependencies are satisfied"""
        
        for dep_id in step.dependencies:
            dep_step = next((s for s in all_steps if s.id == dep_id), None)
            if not dep_step or dep_step.status != WorkflowStepStatus.COMPLETED:
                return False
        
        return True
    
    async def _execute_graph_sitter_step(
        self,
        step: WorkflowStep,
        context: WorkflowContext
    ) -> Dict[str, Any]:
        """Execute graph-sitter analysis step"""
        
        # For now, use a mock repository path
        # In production, this would clone the repository
        repo_path = "/tmp/mock_repo"
        
        # Perform code analysis
        analysis_result = await self.graph_sitter.analyze_code(repo_path)
        
        # Get runtime errors
        runtime_errors = await self.graph_sitter.get_runtime_errors(repo_path)
        
        # Get SWE-bench metrics
        swe_metrics = await self.graph_sitter.analyze_swe_bench_features(repo_path)
        
        return {
            "analysis_result": asdict(analysis_result),
            "runtime_errors": [asdict(error) for error in runtime_errors],
            "swe_metrics": swe_metrics
        }
    
    async def _execute_grainchain_step(
        self,
        step: WorkflowStep,
        context: WorkflowContext,
        workflow_result: WorkflowResult
    ) -> Dict[str, Any]:
        """Execute grainchain sandbox step"""
        
        if step.id == "security_validation":
            # Security validation step
            test_code = "print('Security validation test')"
            security_result = await self.grainchain.validate_code_security(test_code, "python")
            
            return {
                "security_validation": security_result,
                "safe_to_execute": security_result.get("safe_to_execute", False)
            }
            
        elif step.id == "sandbox_testing":
            # Sandbox testing step
            test_commands = [
                "python -m pytest tests/ -v",
                "python -m flake8 .",
                "python -m mypy ."
            ]
            
            config = SandboxConfig(
                timeout=300,
                network_isolation=True,
                auto_cleanup=True
            )
            
            # Mock repository path
            repo_path = "/tmp/mock_repo"
            test_results = await self.grainchain.test_repository_changes(
                repo_path, test_commands, config
            )
            
            return {
                "test_results": [asdict(result) for result in test_results],
                "all_tests_passed": all(result.success for result in test_results)
            }
        
        return {}
    
    async def _execute_web_eval_step(
        self,
        step: WorkflowStep,
        context: WorkflowContext
    ) -> Dict[str, Any]:
        """Execute web-eval-agent UI validation step"""
        
        # Mock URL - in production this would be determined from the repository
        test_url = "http://localhost:3000"
        
        # Create comprehensive UI test task
        ui_test_task = f"""
        Comprehensive UI validation for repository {context.repository}:
        
        1. Test all interactive elements and forms
        2. Validate responsive design across different screen sizes
        3. Check accessibility compliance
        4. Test navigation and routing
        5. Validate error handling and edge cases
        6. Check performance and loading times
        7. Test user workflows end-to-end
        
        Focus on any changes related to: {', '.join(context.changed_files[:5])}
        
        Additional requirements: {context.user_requirements or 'Standard UI validation'}
        """
        
        # Execute web evaluation
        try:
            eval_result = await handle_web_evaluation(
                url=test_url,
                task=ui_test_task,
                headless_browser=True
            )
            
            return {
                "ui_validation_result": eval_result,
                "ui_tests_passed": "successful" in eval_result.lower() if eval_result else False
            }
            
        except Exception as e:
            return {
                "ui_validation_result": f"UI validation failed: {str(e)}",
                "ui_tests_passed": False,
                "error": str(e)
            }
    
    async def _execute_codegen_step(
        self,
        step: WorkflowStep,
        context: WorkflowContext,
        workflow_result: WorkflowResult
    ) -> Dict[str, Any]:
        """Execute Codegen AI analysis step"""
        
        # Gather context from previous steps
        code_analysis = None
        sandbox_results = None
        ui_results = None
        
        for prev_step in workflow_result.steps:
            if prev_step.id == "code_analysis" and prev_step.result:
                code_analysis = prev_step.result
            elif prev_step.id == "sandbox_testing" and prev_step.result:
                sandbox_results = prev_step.result
            elif prev_step.id == "ui_validation" and prev_step.result:
                ui_results = prev_step.result
        
        # Create comprehensive prompt for Codegen
        prompt = self._create_codegen_prompt(context, code_analysis, sandbox_results, ui_results)
        
        # Get Codegen service
        codegen_service = self.service_manager.get_service("codegen")
        
        if codegen_service:
            # Create agent run
            agent_response = await codegen_service.create_agent_run(
                prompt=prompt,
                repository=context.repository
            )
            
            if agent_response.success:
                run_id = agent_response.data.get("run_id")
                
                # Poll for completion (simplified)
                await asyncio.sleep(5)  # Wait for processing
                
                result_response = await codegen_service.get_agent_run(run_id)
                
                return {
                    "agent_run_id": run_id,
                    "codegen_analysis": result_response.data if result_response.success else None,
                    "analysis_successful": result_response.success
                }
            else:
                return {
                    "error": agent_response.error,
                    "analysis_successful": False
                }
        else:
            return {
                "error": "Codegen service not available",
                "analysis_successful": False
            }
    
    async def _execute_orchestrator_step(
        self,
        step: WorkflowStep,
        context: WorkflowContext,
        workflow_result: WorkflowResult
    ) -> Dict[str, Any]:
        """Execute orchestrator-specific steps like report generation"""
        
        if step.id == "report_generation":
            # Generate comprehensive report
            report = self._generate_comprehensive_report(workflow_result)
            
            return {
                "comprehensive_report": report,
                "report_generated": True
            }
        
        return {}
    
    def _create_codegen_prompt(
        self,
        context: WorkflowContext,
        code_analysis: Optional[Dict[str, Any]],
        sandbox_results: Optional[Dict[str, Any]],
        ui_results: Optional[Dict[str, Any]]
    ) -> str:
        """Create comprehensive prompt for Codegen analysis"""
        
        prompt_parts = [
            f"Analyze the following repository changes and provide intelligent insights:",
            f"Repository: {context.repository}",
            f"PR Number: {context.pull_request_number}",
            f"Branch: {context.branch}",
            f"Commit: {context.commit_sha}",
            ""
        ]
        
        if context.user_requirements:
            prompt_parts.extend([
                "User Requirements:",
                context.user_requirements,
                ""
            ])
        
        if code_analysis:
            analysis_result = code_analysis.get("analysis_result", {})
            prompt_parts.extend([
                "Code Analysis Results:",
                f"- Files analyzed: {analysis_result.get('files_analyzed', 0)}",
                f"- Lines analyzed: {analysis_result.get('lines_analyzed', 0)}",
                f"- Errors found: {len(analysis_result.get('errors', []))}",
                f"- Warnings found: {len(analysis_result.get('warnings', []))}",
                f"- Dependencies: {len(analysis_result.get('dependencies', []))}",
                ""
            ])
        
        if sandbox_results:
            test_results = sandbox_results.get("test_results", [])
            passed_tests = sum(1 for result in test_results if result.get("success", False))
            prompt_parts.extend([
                "Sandbox Testing Results:",
                f"- Tests run: {len(test_results)}",
                f"- Tests passed: {passed_tests}",
                f"- Tests failed: {len(test_results) - passed_tests}",
                ""
            ])
        
        if ui_results:
            ui_passed = ui_results.get("ui_tests_passed", False)
            prompt_parts.extend([
                "UI Validation Results:",
                f"- UI tests passed: {ui_passed}",
                f"- UI validation details: {ui_results.get('ui_validation_result', 'No details')}",
                ""
            ])
        
        prompt_parts.extend([
            "Please provide:",
            "1. Summary of code quality and potential issues",
            "2. Recommendations for improvements",
            "3. Security considerations",
            "4. Performance implications",
            "5. Suggested next steps for the development team"
        ])
        
        return "\n".join(prompt_parts)
    
    def _generate_workflow_summary(self, workflow_result: WorkflowResult) -> Dict[str, Any]:
        """Generate summary of workflow execution"""
        
        completed_steps = [s for s in workflow_result.steps if s.status == WorkflowStepStatus.COMPLETED]
        failed_steps = [s for s in workflow_result.steps if s.status == WorkflowStepStatus.FAILED]
        
        total_time = (workflow_result.end_time or time.time()) - workflow_result.start_time
        
        summary = {
            "workflow_id": workflow_result.workflow_id,
            "total_execution_time": total_time,
            "steps_completed": len(completed_steps),
            "steps_failed": len(failed_steps),
            "steps_total": len(workflow_result.steps),
            "success_rate": len(completed_steps) / len(workflow_result.steps) if workflow_result.steps else 0,
            "repository": workflow_result.context.repository if workflow_result.context else None,
            "pull_request": workflow_result.context.pull_request_number if workflow_result.context else None
        }
        
        # Add step-specific summaries
        for step in completed_steps:
            if step.result:
                summary[f"{step.id}_summary"] = self._summarize_step_result(step)
        
        return summary
    
    def _summarize_step_result(self, step: WorkflowStep) -> Dict[str, Any]:
        """Summarize individual step results"""
        
        if not step.result:
            return {}
        
        if step.service == "graph_sitter":
            analysis = step.result.get("analysis_result", {})
            return {
                "errors_found": len(analysis.get("errors", [])),
                "warnings_found": len(analysis.get("warnings", [])),
                "files_analyzed": analysis.get("files_analyzed", 0),
                "runtime_errors": len(step.result.get("runtime_errors", []))
            }
        
        elif step.service == "grainchain":
            if step.id == "security_validation":
                security = step.result.get("security_validation", {})
                return {
                    "risk_level": security.get("risk_level", "unknown"),
                    "safe_to_execute": security.get("safe_to_execute", False),
                    "security_issues": len(security.get("security_issues", []))
                }
            elif step.id == "sandbox_testing":
                return {
                    "tests_passed": step.result.get("all_tests_passed", False),
                    "test_count": len(step.result.get("test_results", []))
                }
        
        elif step.service == "web_eval_agent":
            return {
                "ui_tests_passed": step.result.get("ui_tests_passed", False),
                "validation_completed": True
            }
        
        elif step.service == "codegen":
            return {
                "analysis_successful": step.result.get("analysis_successful", False),
                "agent_run_id": step.result.get("agent_run_id")
            }
        
        return {"completed": True}
    
    def _generate_comprehensive_report(self, workflow_result: WorkflowResult) -> Dict[str, Any]:
        """Generate comprehensive report from all workflow steps"""
        
        report = {
            "workflow_summary": self._generate_workflow_summary(workflow_result),
            "execution_details": {
                "start_time": workflow_result.start_time,
                "end_time": workflow_result.end_time,
                "total_duration": (workflow_result.end_time or time.time()) - workflow_result.start_time,
                "status": workflow_result.status.value
            },
            "step_results": {}
        }
        
        # Add detailed results from each step
        for step in workflow_result.steps:
            report["step_results"][step.id] = {
                "name": step.name,
                "service": step.service,
                "status": step.status.value,
                "duration": (step.end_time - step.start_time) if step.start_time and step.end_time else 0,
                "result": step.result,
                "error": step.error
            }
        
        # Add recommendations based on results
        report["recommendations"] = self._generate_recommendations(workflow_result)
        
        return report
    
    def _generate_recommendations(self, workflow_result: WorkflowResult) -> List[str]:
        """Generate recommendations based on workflow results"""
        
        recommendations = []
        
        # Check code analysis results
        for step in workflow_result.steps:
            if step.id == "code_analysis" and step.result:
                analysis = step.result.get("analysis_result", {})
                error_count = len(analysis.get("errors", []))
                warning_count = len(analysis.get("warnings", []))
                
                if error_count > 0:
                    recommendations.append(f"Address {error_count} code errors before merging")
                if warning_count > 5:
                    recommendations.append(f"Consider addressing {warning_count} code warnings")
            
            elif step.id == "security_validation" and step.result:
                security = step.result.get("security_validation", {})
                if security.get("risk_level") == "high":
                    recommendations.append("High security risk detected - review code carefully")
            
            elif step.id == "sandbox_testing" and step.result:
                if not step.result.get("all_tests_passed", False):
                    recommendations.append("Some tests failed - fix failing tests before merging")
            
            elif step.id == "ui_validation" and step.result:
                if not step.result.get("ui_tests_passed", False):
                    recommendations.append("UI validation issues detected - review user interface")
        
        if not recommendations:
            recommendations.append("All checks passed - ready for review")
        
        return recommendations
    
    async def get_workflow_status(self, workflow_id: str) -> Optional[WorkflowResult]:
        """Get status of a running or completed workflow"""
        return self._active_workflows.get(workflow_id)
    
    async def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel a running workflow"""
        workflow = self._active_workflows.get(workflow_id)
        if workflow and workflow.status == WorkflowStatus.RUNNING:
            workflow.status = WorkflowStatus.CANCELLED
            workflow.end_time = time.time()
            return True
        return False
    
    async def health_check(self) -> ServiceResponse:
        """Check orchestrator health"""
        try:
            # Check all integrated services
            service_health = await self.service_manager.health_check_all()
            grainchain_health = await self.grainchain.health_check()
            graph_sitter_health = await self.graph_sitter.health_check()
            
            all_healthy = all([
                all(result.success for result in service_health.values()),
                grainchain_health.success,
                graph_sitter_health.success
            ])
            
            return ServiceResponse(
                success=all_healthy,
                data={
                    "orchestrator_status": "healthy",
                    "active_workflows": len(self._active_workflows),
                    "service_health": {name: result.success for name, result in service_health.items()},
                    "grainchain_health": grainchain_health.success,
                    "graph_sitter_health": graph_sitter_health.success
                }
            )
            
        except Exception as e:
            return ServiceResponse(
                success=False,
                error=f"Health check failed: {str(e)}"
            )

# Global instance
_workflow_orchestrator: Optional[WorkflowOrchestrator] = None

def get_workflow_orchestrator() -> WorkflowOrchestrator:
    """Get the global workflow orchestrator instance"""
    global _workflow_orchestrator
    if _workflow_orchestrator is None:
        _workflow_orchestrator = WorkflowOrchestrator()
    return _workflow_orchestrator
