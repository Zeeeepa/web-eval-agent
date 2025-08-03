"""
Core web evaluation engine using GEMINI API and browser-use
"""

import asyncio
import os
import time
import uuid
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from browser_use import Agent, Browser, BrowserConfig
from langchain_google_genai import ChatGoogleGenerativeAI


@dataclass
class TestResult:
    """Individual test result"""
    scenario_name: str
    status: str  # 'passed', 'failed', 'error'
    duration: float
    details: str
    issues: List[str] = None
    recommendations: List[str] = None
    error_message: Optional[str] = None

    def __post_init__(self):
        if self.issues is None:
            self.issues = []
        if self.recommendations is None:
            self.recommendations = []


@dataclass
class EvaluationReport:
    """Complete evaluation report"""
    url: str
    test_duration: float
    total_scenarios: int
    passed_scenarios: int
    failed_scenarios: int
    results: List[TestResult]
    summary: str
    timestamp: str
    session_id: str


class WebEvaluator:
    """Main web evaluation engine"""
    
    def __init__(self, api_key: str, headless: bool = True, debug: bool = False):
        self.api_key = api_key
        self.headless = headless
        self.debug = debug
        self.session_id = str(uuid.uuid4())
        
        # Initialize LLM
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            temperature=0.1,
            google_api_key=api_key
        )
        
        # Browser config
        self.browser_config = BrowserConfig(
            headless=headless,
            disable_security=True,
            chrome_instance_path=None,
            extra_chromium_args=['--disable-gpu', '--no-sandbox', '--disable-dev-shm-usage']
        )
        
        if debug:
            print(f"🔧 WebEvaluator initialized (Session: {self.session_id[:8]})")
    
    async def evaluate_website(self, url: str, test_scenarios: List[Dict[str, Any]]) -> EvaluationReport:
        """
        Evaluate a website against provided test scenarios
        
        Args:
            url: Website URL to evaluate
            test_scenarios: List of test scenarios with instructions
            
        Returns:
            EvaluationReport with complete results
        """
        start_time = time.time()
        results = []
        
        if self.debug:
            print(f"🚀 Starting evaluation of {url}")
            print(f"📋 Running {len(test_scenarios)} test scenarios")
        
        # Create browser instance
        browser = Browser(config=self.browser_config)
        
        try:
            for i, scenario in enumerate(test_scenarios):
                if self.debug:
                    print(f"🔍 Running scenario {i+1}/{len(test_scenarios)}: {scenario.get('name', 'Unnamed')}")
                
                result = await self._run_single_scenario(browser, url, scenario)
                results.append(result)
                
                if self.debug:
                    status_emoji = "✅" if result.status == "passed" else "❌"
                    print(f"{status_emoji} Scenario completed: {result.status}")
        
        finally:
            await browser.close()
        
        # Calculate metrics
        end_time = time.time()
        test_duration = end_time - start_time
        passed_scenarios = len([r for r in results if r.status == "passed"])
        failed_scenarios = len([r for r in results if r.status == "failed"])
        
        # Generate summary
        summary = self._generate_summary(results, passed_scenarios, failed_scenarios)
        
        report = EvaluationReport(
            url=url,
            test_duration=test_duration,
            total_scenarios=len(test_scenarios),
            passed_scenarios=passed_scenarios,
            failed_scenarios=failed_scenarios,
            results=results,
            summary=summary,
            timestamp=datetime.now().isoformat(),
            session_id=self.session_id
        )
        
        if self.debug:
            print(f"📊 Evaluation completed in {test_duration:.1f}s")
            print(f"✅ Passed: {passed_scenarios}, ❌ Failed: {failed_scenarios}")
        
        return report
    
    async def _run_single_scenario(self, browser: Browser, url: str, scenario: Dict[str, Any]) -> TestResult:
        """Run a single test scenario"""
        start_time = time.time()
        scenario_name = scenario.get('name', 'Unnamed Scenario')
        
        try:
            # Create task description for the agent
            task_description = self._create_task_description(url, scenario)
            
            # Create and run agent
            agent = Agent(
                task=task_description,
                llm=self.llm,
                browser=browser,
                use_vision=True
            )
            
            # Execute the task
            history = await agent.run()
            
            # Get result
            result_text = str(history.final_result()) if hasattr(history, 'final_result') else str(history)
            
            # Analyze result
            status, details, issues, recommendations = self._analyze_result(result_text, scenario)
            
            duration = time.time() - start_time
            
            return TestResult(
                scenario_name=scenario_name,
                status=status,
                duration=duration,
                details=details,
                issues=issues,
                recommendations=recommendations
            )
            
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                scenario_name=scenario_name,
                status="error",
                duration=duration,
                details=f"Error during execution: {str(e)}",
                error_message=str(e)
            )
    
    def _create_task_description(self, url: str, scenario: Dict[str, Any]) -> str:
        """Create a detailed task description for the agent"""
        name = scenario.get('name', 'Web Evaluation Task')
        description = scenario.get('description', '')
        steps = scenario.get('steps', [])
        success_criteria = scenario.get('success_criteria', [])
        
        task = f"""Visit {url} and perform the following evaluation:

SCENARIO: {name}
{description}

STEPS TO PERFORM:"""
        
        for i, step in enumerate(steps, 1):
            task += f"\n{i}. {step}"
        
        if success_criteria:
            task += "\n\nSUCCESS CRITERIA:"
            for criterion in success_criteria:
                task += f"\n- {criterion}"
        
        task += """

IMPORTANT INSTRUCTIONS:
- Navigate to the website and perform each step carefully
- Look for any errors, broken functionality, or usability issues
- Test interactive elements like buttons, forms, and links
- Check for accessibility and performance issues
- Provide specific details about what you find
- If you encounter errors, describe them precisely
- Report both positive findings and issues

Provide a detailed summary of your findings, including:
1. What worked correctly
2. Any issues or problems found
3. Specific recommendations for improvement
4. Overall assessment of the scenario"""
        
        return task
    
    def _analyze_result(self, result_text: str, scenario: Dict[str, Any]) -> tuple:
        """Analyze the agent's result and determine pass/fail status"""
        result_lower = result_text.lower()
        
        # Simple heuristic analysis
        error_indicators = ['error', 'failed', 'broken', 'not working', 'issue', 'problem']
        success_indicators = ['success', 'working', 'functional', 'correct', 'good', 'passed']
        
        has_errors = any(indicator in result_lower for indicator in error_indicators)
        has_success = any(indicator in result_lower for indicator in success_indicators)
        
        # Determine status
        if has_errors and not has_success:
            status = "failed"
        elif has_success and not has_errors:
            status = "passed"
        elif len(result_text) < 50:  # Very short response might indicate failure
            status = "failed"
        else:
            # Mixed results - lean towards passed if more positive indicators
            status = "passed" if has_success else "failed"
        
        # Extract issues and recommendations
        issues = []
        recommendations = []
        
        if has_errors:
            issues.append("Issues detected during testing - see details for specifics")
        
        if status == "failed":
            recommendations.append("Review and fix identified issues")
            recommendations.append("Re-test after implementing fixes")
        
        return status, result_text, issues, recommendations
    
    def _generate_summary(self, results: List[TestResult], passed: int, failed: int) -> str:
        """Generate a summary of the evaluation"""
        total = len(results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        summary = f"""EVALUATION SUMMARY:
- Total Scenarios: {total}
- Passed: {passed}
- Failed: {failed}
- Success Rate: {success_rate:.1f}%

"""
        
        if failed > 0:
            summary += "ISSUES FOUND:\n"
            for result in results:
                if result.status == "failed":
                    summary += f"- {result.scenario_name}: {result.details[:100]}...\n"
        
        if passed == total:
            summary += "🎉 All tests passed! Website appears to be functioning well."
        elif failed > passed:
            summary += "⚠️ Multiple issues detected. Immediate attention recommended."
        else:
            summary += "✅ Most tests passed with some minor issues to address."
        
        return summary
