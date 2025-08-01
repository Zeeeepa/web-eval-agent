"""
Enhanced Test Executor

Advanced test executor that integrates with the existing system
and provides enhanced reporting and analysis.
"""

import asyncio
import time
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging

from browser_use import Agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

from .test_executor import TestExecutor
from .config import Config
from ..reporting.intelligent_reporter import (
    IntelligentReporter, TestScenarioResult, TestIssue, 
    IssueCategory, ReportSeverity
)

logger = logging.getLogger(__name__)


@dataclass
class EnhancedTestConfig:
    """Enhanced test configuration."""
    api_key: str
    timeout: int = 60
    headless: bool = True
    agents: int = 3
    max_retries: int = 3
    screenshot_on_failure: bool = True
    detailed_logging: bool = True
    performance_monitoring: bool = True
    console_monitoring: bool = True
    network_monitoring: bool = True
    interaction_monitoring: bool = True


class EnhancedTestExecutor:
    """
    Enhanced test executor that wraps the existing TestExecutor
    with advanced reporting and analysis capabilities.
    """
    
    def __init__(self, config: EnhancedTestConfig):
        self.config = config
        self.reporter: Optional[IntelligentReporter] = None
        
        # Create underlying test executor
        self.base_executor = TestExecutor(Config(
            url="",  # Will be set when executing
            instructions_file="",  # Will be set when executing
            api_key=config.api_key,
            timeout=config.timeout,
            headless=config.headless,
            num_agents=config.agents
        ))
        
        # LLM for AI analysis
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=0.1,
            api_key=config.api_key
        )
        
        # Test state
        self.test_session_id: Optional[str] = None
        self.current_url: Optional[str] = None
        self.test_scenarios: List[Dict[str, Any]] = []
        
    async def initialize(self, url: str) -> Dict[str, Any]:
        """Initialize the enhanced test executor."""
        logger.info("🚀 Initializing Enhanced Test Executor...")
        
        try:
            # Generate test session ID
            self.test_session_id = str(uuid.uuid4())
            self.current_url = url
            
            # Initialize intelligent reporter
            self.reporter = IntelligentReporter(self.config.api_key)
            
            logger.info("✅ Enhanced Test Executor initialized successfully")
            
            return {
                'success': True,
                'session_id': self.test_session_id,
                'url': url
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Enhanced Test Executor: {e}")
            await self.cleanup()
            raise
            
    async def execute_test_scenarios(self, scenarios: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute multiple test scenarios with enhanced analysis."""
        if not self.reporter:
            raise Exception("Test executor not initialized")
            
        logger.info(f"🧪 Executing {len(scenarios)} test scenarios...")
        self.test_scenarios = scenarios
        
        # Convert scenarios to the format expected by base executor
        from .instruction_parser import TestScenario
        test_scenarios = []
        for scenario in scenarios:
            test_scenarios.append(TestScenario(
                name=scenario.get('name', 'Test Scenario'),
                description=scenario.get('description', ''),
                steps=scenario.get('steps', ['Navigate and test the website']),
                validations=scenario.get('success_criteria', ['Complete successfully']),
                expected_outcomes=scenario.get('expected_outcomes', ['Test completes without errors'])
            ))
        
        # Update base executor config with current URL
        self.base_executor.config.url = self.current_url
        
        # Execute tests using base executor
        base_results = await self.base_executor.run_tests(test_scenarios)
        
        # Convert results to enhanced format with AI analysis
        enhanced_results = []
        
        for i, base_result in enumerate(base_results.test_results):
            # Analyze result with AI
            analysis = await self._analyze_test_result(base_result, scenarios[i] if i < len(scenarios) else {})
            
            # Create enhanced result
            enhanced_result = TestScenarioResult(
                scenario_name=base_result.scenario_name,
                status='passed' if base_result.passed else 'failed',
                duration=base_result.duration,
                agent_id=i,
                error_message=base_result.error_message,
                issues=analysis.get('issues', []),
                success_criteria_met=analysis.get('success_criteria_met', []),
                success_criteria_failed=analysis.get('success_criteria_failed', [])
            )
            
            enhanced_results.append(enhanced_result)
            self.reporter.add_test_result(enhanced_result)
                
        # Finalize testing and generate report
        await self._finalize_testing()
        
        return {
            'success': True,
            'session_id': self.test_session_id,
            'total_scenarios': len(scenarios),
            'results': enhanced_results,
            'report': self.reporter.generate_detailed_report()
        }
        
    async def _analyze_test_result(self, base_result, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze test result with AI to extract insights and issues."""
        try:
            # Create analysis prompt
            analysis_prompt = f"""
Analyze this test result and provide insights:

SCENARIO: {scenario.get('name', 'Test Scenario')}
DESCRIPTION: {scenario.get('description', 'No description')}
SUCCESS CRITERIA: {', '.join(scenario.get('success_criteria', ['Complete successfully']))}

TEST RESULT:
- Status: {'Passed' if base_result.passed else 'Failed'}
- Duration: {base_result.duration:.1f}s
- Error: {base_result.error_message or 'None'}

Please provide a JSON response with:
{{
    "success_criteria_met": ["criteria that were met"],
    "success_criteria_failed": ["criteria that failed"],
    "issues": [
        {{
            "title": "Issue title",
            "description": "Description",
            "category": "functionality",
            "severity": "medium"
        }}
    ]
}}
"""
            
            response = await self.llm.ainvoke([HumanMessage(content=analysis_prompt)])
            
            # Parse JSON response
            import json
            import re
            
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if json_match:
                analysis_data = json.loads(json_match.group())
            else:
                # Fallback analysis
                analysis_data = {
                    "success_criteria_met": scenario.get('success_criteria', []) if base_result.passed else [],
                    "success_criteria_failed": [] if base_result.passed else scenario.get('success_criteria', []),
                    "issues": []
                }
                
            # Convert issues to TestIssue objects
            issues = []
            for issue_data in analysis_data.get('issues', []):
                try:
                    issue = TestIssue(
                        id=f"issue_{len(issues)}",
                        title=issue_data.get('title', 'Unknown Issue'),
                        description=issue_data.get('description', 'No description'),
                        category=IssueCategory(issue_data.get('category', 'functionality')),
                        severity=ReportSeverity(issue_data.get('severity', 'medium'))
                    )
                    issues.append(issue)
                except Exception as e:
                    logger.warning(f"Failed to create issue: {e}")
                    
            return {
                'success_criteria_met': analysis_data.get('success_criteria_met', []),
                'success_criteria_failed': analysis_data.get('success_criteria_failed', []),
                'issues': issues
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze test result: {e}")
            return {
                'success_criteria_met': scenario.get('success_criteria', []) if base_result.passed else [],
                'success_criteria_failed': [] if base_result.passed else scenario.get('success_criteria', []),
                'issues': []
            }
        
    async def _finalize_testing(self):
        """Finalize testing session and prepare final reports."""
        logger.info("🏁 Finalizing test session...")
        
        try:
            logger.info("✅ Test session finalized")
            
        except Exception as e:
            logger.error(f"Error during test finalization: {e}")
            
    async def cleanup(self):
        """Clean up resources."""
        logger.info("🧹 Cleaning up Enhanced Test Executor...")
        
        try:
            # Clean up base executor if needed
            if hasattr(self.base_executor, 'cleanup'):
                await self.base_executor.cleanup()
                
            logger.info("✅ Enhanced Test Executor cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            
    def get_session_summary(self) -> Dict[str, Any]:
        """Get comprehensive session summary."""
        return {
            'session_id': self.test_session_id,
            'url': self.current_url,
            'total_scenarios': len(self.test_scenarios),
            'config': {
                'timeout': self.config.timeout,
                'headless': self.config.headless,
                'agents': self.config.agents,
                'monitoring_enabled': {
                    'console': self.config.console_monitoring,
                    'network': self.config.network_monitoring,
                    'performance': self.config.performance_monitoring,
                    'interaction': self.config.interaction_monitoring
                }
            }
        }
