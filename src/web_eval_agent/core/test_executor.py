"""
Test executor for Web Eval Agent

Executes test scenarios using multi-agent browser automation and AI-powered interaction.
"""

import asyncio
import json
import logging
import time
import traceback
import warnings
import uuid
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from collections import deque
from datetime import datetime

# Browser automation imports
from browser_use import Agent, Browser, BrowserConfig
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage

from .config import Config
from .instruction_parser import TestScenario
from .scout_agent import ScoutAgent
from .session_manager import SessionManager
from ..utils.utils import format_duration, truncate_text


@dataclass
class TestResult:
    """Result of a single test scenario."""
    scenario_name: str
    passed: bool
    duration: float
    error_message: Optional[str] = None
    screenshots: List[str] = field(default_factory=list)
    console_logs: List[Dict] = field(default_factory=list)
    network_requests: List[Dict] = field(default_factory=list)
    agent_steps: List[str] = field(default_factory=list)
    validation_results: List[Dict] = field(default_factory=list)
    timeline_events: List[Dict] = field(default_factory=list)  # New: chronological timeline


@dataclass
class TestResults:
    """Collection of test results."""
    test_results: List[TestResult]
    total_duration: float
    errors: List[str] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)


class TestExecutor:
    """Executes web application tests using multi-agent browser automation."""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Multi-agent components
        self.session_manager = SessionManager(config)
        self.scout_agent = ScoutAgent(config) if config.scout_mode else None
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=0.9,
            google_api_key=config.api_key
        )
        
        # Storage for test results
        self._test_results = {}
        self.test_start_time = None
    
    async def run_tests(self, scenarios: List[TestScenario]) -> TestResults:
        """Run all test scenarios using multi-agent parallel execution."""
        start_time = time.time()
        self.test_start_time = start_time
        
        print(f"🚀 Starting multi-agent web evaluation for {self.config.url}")
        print(f"🤖 Using {self.config.num_agents} agents in {'headless' if self.config.headless else 'GUI'} mode")
        
        try:
            # Step 1: Scout the page if enabled
            if self.scout_agent:
                print("🔍 Scouting page for interactive elements...")
                qa_tasks = await self.scout_agent.scout_page(self.config.url)
                print(f"📝 Found {len(qa_tasks)} targeted test tasks")
            else:
                # Use scenarios directly
                qa_tasks = [scenario.description for scenario in scenarios]
                print(f"📝 Using {len(qa_tasks)} instruction-based tasks")
            
            # Step 2: Run multi-agent pool
            test_id = await self._run_agent_pool(qa_tasks)
            
            # Step 3: Generate comprehensive results
            results = await self._generate_test_results(test_id, scenarios)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Multi-agent test execution failed: {e}", exc_info=True)
            return TestResults(
                test_results=[],
                total_duration=time.time() - start_time,
                errors=[f"Multi-agent execution failed: {str(e)}"]
            )
        finally:
            # Cleanup all sessions
            await self.session_manager.close_all_sessions()
    
    async def _run_agent_pool(self, qa_tasks: List[str]) -> str:
        """Run multiple agents in parallel to test different aspects of the site."""
        test_id = str(uuid.uuid4())
        start_time = time.time()
        
        print(f"🏊 Running agent pool with {self.config.num_agents} agents...")
        
        # Run agents in parallel with semaphore limiting
        async def run_single_agent(agent_id: int):
            task_description = qa_tasks[agent_id % len(qa_tasks)]
            session = None
            
            try:
                # Create browser session with timeout
                session = await asyncio.wait_for(
                    self.session_manager.create_session(agent_id),
                    timeout=30.0
                )
                
                # Enhanced task description with better error handling instructions
                enhanced_task = f"""
                Navigate to {self.config.url} and {task_description}
                
                IMPORTANT INSTRUCTIONS:
                - If the page fails to load, report the specific error
                - If elements are not found, describe what you can see instead
                - If any action fails, explain what happened and what you observed
                - Focus on functional testing, not subjective opinions
                - Report specific technical issues like broken links, form errors, or JavaScript errors
                """
                
                # Create and run agent with timeout
                agent = Agent(
                    task=enhanced_task,
                    llm=self.llm,
                    browser=session.browser,
                    use_vision=True
                )
                
                print(f"🤖 Agent {agent_id}: {task_description[:60]}...")
                
                # Run agent with timeout
                history = await asyncio.wait_for(
                    agent.run(),
                    timeout=self.config.timeout
                )
                
                # Extract result with better error handling
                if hasattr(history, 'final_result') and callable(history.final_result):
                    result_text = str(history.final_result())
                elif hasattr(history, 'result'):
                    result_text = str(history.result)
                else:
                    result_text = str(history)
                
                # Ensure we have meaningful content
                if not result_text or result_text.strip() in ['None', '', 'null']:
                    result_text = f"Agent {agent_id} completed task but returned no specific findings. Task: {task_description}"
                
                return {
                    "agent_id": agent_id,
                    "task": task_description,
                    "result": result_text,
                    "timestamp": time.time(),
                    "status": "success",
                    "duration": time.time() - start_time
                }
                
            except asyncio.TimeoutError:
                error_msg = f"Agent {agent_id} timed out after {self.config.timeout}s"
                print(f"⏰ {error_msg}")
                return {
                    "agent_id": agent_id,
                    "task": task_description,
                    "error": error_msg,
                    "timestamp": time.time(),
                    "status": "timeout"
                }
                
            except Exception as e:
                error_msg = f"Agent {agent_id} failed: {str(e)}"
                print(f"❌ {error_msg}")
                return {
                    "agent_id": agent_id,
                    "task": task_description,
                    "error": error_msg,
                    "timestamp": time.time(),
                    "status": "error"
                }
                
            finally:
                # Ensure session cleanup
                if session:
                    try:
                        await self.session_manager.close_session(agent_id)
                    except Exception as cleanup_error:
                        print(f"⚠️ Failed to cleanup session {agent_id}: {cleanup_error}")
        
        # Execute agents with semaphore control
        results = await asyncio.gather(
            *[self.session_manager.run_with_semaphore(run_single_agent(i)) 
              for i in range(self.config.num_agents)], 
            return_exceptions=True
        )
        
        end_time = time.time()
        
        # Store results
        test_data = {
            "test_id": test_id,
            "url": self.config.url,
            "agents": self.config.num_agents,
            "start_time": start_time,
            "end_time": end_time,
            "duration": end_time - start_time,
            "results": [r for r in results if not isinstance(r, Exception)],
            "status": "completed"
        }
        
        self._test_results[test_id] = test_data
        
        print(f"✅ Agent pool completed in {format_duration(end_time - start_time)}")
        
        return test_id
    
    async def _generate_test_results(self, test_id: str, original_scenarios: List[TestScenario]) -> TestResults:
        """Generate comprehensive test results with AI analysis."""
        if test_id not in self._test_results:
            return TestResults(
                test_results=[],
                total_duration=0.0,
                errors=[f"Test ID {test_id} not found"]
            )
        
        test_data = self._test_results[test_id]
        
        # Separate successful results and errors
        agent_results = []
        bug_reports = []
        errors = []
        
        for result in test_data["results"]:
            if isinstance(result, Exception):
                errors.append(f"Agent execution exception: {str(result)}")
                continue
                
            if result.get("status") == "success":
                agent_results.append(result)
                if "result" in result and result["result"]:
                    bug_reports.append({
                        "agent_id": result["agent_id"],
                        "task": result["task"],
                        "findings": result["result"],
                        "timestamp": result["timestamp"]
                    })
            elif result.get("status") in ["error", "timeout"]:
                error_msg = result.get('error', 'Unknown error')
                errors.append(f"Agent {result['agent_id']}: {error_msg}")
            else:
                # Handle unexpected result format
                errors.append(f"Agent {result.get('agent_id', 'unknown')}: Unexpected result format")
        
        # Generate AI-powered analysis
        analysis_result = await self._analyze_findings(bug_reports, test_data["url"])
        
        # Create test results
        test_results = []
        
        # Create a result for each original scenario
        for i, scenario in enumerate(original_scenarios):
            # Find corresponding agent results
            scenario_findings = []
            for report in bug_reports:
                if i < len(bug_reports):  # Map scenarios to findings
                    scenario_findings.append(report["findings"])
            
            # Determine if test passed based on analysis
            passed = self._determine_test_status(analysis_result, scenario_findings)
            
            test_result = TestResult(
                scenario_name=scenario.name,
                passed=passed,
                duration=test_data["duration"] / len(original_scenarios),  # Distribute duration
                error_message=None if passed else "Issues found during testing",
                agent_steps=scenario_findings,
                validation_results=[analysis_result] if analysis_result else []
            )
            
            test_results.append(test_result)
        
        # Generate summary
        passed_count = sum(1 for r in test_results if r.passed)
        failed_count = len(test_results) - passed_count
        
        summary = {
            "total_tests": len(test_results),
            "passed": passed_count,
            "failed": failed_count,
            "success_rate": (passed_count / len(test_results) * 100) if test_results else 0,
            "total_duration": test_data["duration"],
            "agents_used": test_data["agents"],
            "analysis": analysis_result
        }
        
        return TestResults(
            test_results=test_results,
            total_duration=test_data["duration"],
            errors=errors,
            summary=summary
        )
    
    async def _analyze_findings(self, bug_reports: List[Dict], url: str) -> Dict[str, Any]:
        """Use AI to analyze findings and classify severity."""
        if not bug_reports:
            return {
                "overall_status": "passing",
                "status_emoji": "✅",
                "status_description": "No issues detected during testing",
                "total_issues": 0,
                "severity_breakdown": {
                    "high_severity": [],
                    "medium_severity": [],
                    "low_severity": []
                }
            }
        
        # Prepare findings text
        bug_reports_text = "\n\n".join([
            f"Agent {report['agent_id']} Report:\nTask: {report['task']}\nFindings: {report['findings']}"
            for report in bug_reports
        ])
        
        try:
            prompt = f"""
You are an objective QA analyst. Review the following test reports from agents that explored the website {url}.

Identify only actual functional issues, broken features, or technical problems. Do NOT classify subjective opinions, missing features that may be intentional, or design preferences as issues.

Only report issues if they represent:
- Broken functionality (buttons that don't work, forms that fail)
- Technical errors (404s, JavaScript errors, broken links)
- Accessibility violations (missing alt text, poor contrast)
- Performance problems (very slow loading, timeouts)

For each issue you identify, provide SPECIFIC and DETAILED descriptions including:
- The exact element that was tested (button name, link text, form field, etc.)
- The specific action taken (clicked, typed, submitted, etc.)
- The exact result or error observed (404 error, no response, broken redirect, etc.)
- Any relevant context from the agent's testing

Here are the test reports: {bug_reports_text}

Format the output as JSON with the following structure:
{{
  "high_severity": [
    {{"category": "category_name", "description": "specific detailed description with exact steps and results"}},
    ...
  ],
  "medium_severity": [
    {{"category": "category_name", "description": "specific detailed description with exact steps and results"}},
    ...
  ],
  "low_severity": [
    {{"category": "category_name", "description": "specific detailed description with exact steps and results"}},
    ...
  ]
}}

Only include real issues found during testing. Provide clear, concise descriptions. Deduplicate similar issues.
"""

            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            
            # Parse JSON response
            import re
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if json_match:
                severity_analysis = json.loads(json_match.group())
            else:
                severity_analysis = {
                    "high_severity": [],
                    "medium_severity": [],
                    "low_severity": []
                }
            
            total_issues = (
                len(severity_analysis.get("high_severity", [])) +
                len(severity_analysis.get("medium_severity", [])) +
                len(severity_analysis.get("low_severity", []))
            )
            
            # Determine overall status
            if len(severity_analysis.get("high_severity", [])) > 0:
                overall_status = "high-severity"
                status_emoji = "🔴"
                status_description = "Critical issues found that need immediate attention"
            elif len(severity_analysis.get("medium_severity", [])) > 0:
                overall_status = "medium-severity"
                status_emoji = "🟠"
                status_description = "Moderate issues found that should be addressed"
            elif len(severity_analysis.get("low_severity", [])) > 0:
                overall_status = "low-severity"
                status_emoji = "🟡"
                status_description = "Minor issues found that could be improved"
            else:
                overall_status = "passing"
                status_emoji = "✅"
                status_description = "No technical issues detected during testing"
            
            return {
                "overall_status": overall_status,
                "status_emoji": status_emoji,
                "status_description": status_description,
                "total_issues": total_issues,
                "severity_breakdown": severity_analysis,
                "llm_analysis": {
                    "raw_response": response.content,
                    "model_used": "gemini-2.0-flash"
                }
            }
            
        except Exception as e:
            print(f"⚠️ AI analysis failed: {e}")
            # Fallback analysis with better error handling
            if "API key not valid" in str(e) or "API_KEY_INVALID" in str(e):
                status_description = "AI analysis unavailable (API key required). Manual review recommended."
                analysis_error = "Invalid API key - please set a valid GEMINI_API_KEY"
            elif "quota" in str(e).lower() or "limit" in str(e).lower():
                status_description = "AI analysis unavailable (API quota exceeded). Manual review recommended."
                analysis_error = "API quota exceeded"
            else:
                status_description = f"AI analysis failed. Manual review recommended. Error: {str(e)[:100]}"
                analysis_error = str(e)
            
            return {
                "overall_status": "low-severity" if bug_reports else "passing",
                "status_emoji": "🟡" if bug_reports else "✅",
                "status_description": status_description,
                "total_issues": len(bug_reports),
                "severity_breakdown": {
                    "high_severity": [],
                    "medium_severity": [],
                    "low_severity": [{"category": "general", "description": f"Found {len(bug_reports)} potential issues requiring manual review"}] if bug_reports else []
                },
                "llm_analysis_error": analysis_error,
                "fallback_analysis": True
            }
    
    def _determine_test_status(self, analysis_result: Dict[str, Any], findings: List[str]) -> bool:
        """Determine if a test passed based on analysis results."""
        if not analysis_result:
            return len(findings) == 0
        
        # Test fails if there are high severity issues
        high_severity_count = len(analysis_result.get("severity_breakdown", {}).get("high_severity", []))
        if high_severity_count > 0:
            return False
        
        # Test passes if no issues or only low severity issues
        overall_status = analysis_result.get("overall_status", "passing")
        return overall_status in ["passing", "low-severity"]
    
    def get_test_results(self, test_id: str) -> Optional[Dict[str, Any]]:
        """Get stored test results by ID."""
        return self._test_results.get(test_id)
