"""
Intelligent Reporter

Advanced reporting system that correlates browser context data with test outcomes,
provides detailed analysis, and generates actionable insights.
"""

import time
import json
import statistics
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ReportSeverity(Enum):
    """Report severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class IssueCategory(Enum):
    """Issue categorization."""
    FUNCTIONALITY = "functionality"
    PERFORMANCE = "performance"
    ACCESSIBILITY = "accessibility"
    SECURITY = "security"
    USABILITY = "usability"
    COMPATIBILITY = "compatibility"
    CONTENT = "content"


@dataclass
class TestIssue:
    """Represents a test issue with detailed context."""
    id: str
    title: str
    description: str
    category: IssueCategory
    severity: ReportSeverity
    location: Optional[str] = None
    screenshot_path: Optional[str] = None
    browser_context: Optional[Dict[str, Any]] = None
    reproduction_steps: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    related_console_errors: List[str] = field(default_factory=list)
    related_network_issues: List[str] = field(default_factory=list)
    performance_impact: Optional[Dict[str, float]] = None
    timestamp: float = field(default_factory=time.time)


@dataclass
class TestScenarioResult:
    """Detailed test scenario result."""
    scenario_name: str
    status: str  # 'passed', 'failed', 'skipped', 'error'
    duration: float
    agent_id: Optional[int] = None
    issues: List[TestIssue] = field(default_factory=list)
    interactions: List[Dict[str, Any]] = field(default_factory=list)
    console_summary: Optional[Dict[str, Any]] = None
    network_summary: Optional[Dict[str, Any]] = None
    performance_summary: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    success_criteria_met: List[str] = field(default_factory=list)
    success_criteria_failed: List[str] = field(default_factory=list)


@dataclass
class ExecutiveSummary:
    """High-level executive summary."""
    overall_status: str
    total_scenarios: int
    passed_scenarios: int
    failed_scenarios: int
    critical_issues: int
    high_priority_issues: int
    performance_score: float
    accessibility_score: float
    security_score: float
    key_findings: List[str]
    business_impact: str
    recommended_actions: List[str]


class IntelligentReporter:
    """
    Advanced reporting system that provides comprehensive analysis,
    correlates multiple data sources, and generates actionable insights.
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.test_results: List[TestScenarioResult] = []
        self.global_issues: List[TestIssue] = []
        self.start_time = time.time()
        self.end_time: Optional[float] = None
        
        # Analysis components
        self.console_analysis: Optional[Dict[str, Any]] = None
        self.network_analysis: Optional[Dict[str, Any]] = None
        self.performance_analysis: Optional[Dict[str, Any]] = None
        self.interaction_analysis: Optional[Dict[str, Any]] = None
        
    def add_test_result(self, result: TestScenarioResult) -> None:
        """Add a test scenario result."""
        self.test_results.append(result)
        logger.info(f"Added test result: {result.scenario_name} - {result.status}")
        
    def add_global_issue(self, issue: TestIssue) -> None:
        """Add a global issue that affects multiple scenarios."""
        self.global_issues.append(issue)
        logger.warning(f"Added global issue: {issue.title} ({issue.severity.value})")
        
    def set_browser_context_analysis(self, console_analysis: Dict[str, Any], 
                                   network_analysis: Dict[str, Any],
                                   performance_analysis: Dict[str, Any]) -> None:
        """Set browser context analysis data."""
        self.console_analysis = console_analysis
        self.network_analysis = network_analysis
        self.performance_analysis = performance_analysis
        
    def set_interaction_analysis(self, interaction_analysis: Dict[str, Any]) -> None:
        """Set UI interaction analysis data."""
        self.interaction_analysis = interaction_analysis
        
    def finalize_testing(self) -> None:
        """Finalize testing session and prepare for report generation."""
        self.end_time = time.time()
        
        # Perform cross-correlation analysis
        self._correlate_issues_with_context()
        self._identify_patterns()
        self._generate_recommendations()
        
    def _correlate_issues_with_context(self) -> None:
        """Correlate test issues with browser context data."""
        for result in self.test_results:
            for issue in result.issues:
                # Correlate with console errors
                if self.console_analysis:
                    issue.related_console_errors = self._find_related_console_errors(issue)
                    
                # Correlate with network issues
                if self.network_analysis:
                    issue.related_network_issues = self._find_related_network_issues(issue)
                    
                # Add performance impact
                if self.performance_analysis:
                    issue.performance_impact = self._assess_performance_impact(issue)
                    
    def _find_related_console_errors(self, issue: TestIssue) -> List[str]:
        """Find console errors related to a specific issue."""
        if not self.console_analysis or 'critical_issues' not in self.console_analysis:
            return []
            
        related_errors = []
        issue_keywords = issue.title.lower().split() + issue.description.lower().split()
        
        for console_error in self.console_analysis['critical_issues']:
            error_text = console_error.lower()
            if any(keyword in error_text for keyword in issue_keywords if len(keyword) > 3):
                related_errors.append(console_error)
                
        return related_errors[:3]  # Limit to top 3 related errors
        
    def _find_related_network_issues(self, issue: TestIssue) -> List[str]:
        """Find network issues related to a specific issue."""
        if not self.network_analysis or 'issues' not in self.network_analysis:
            return []
            
        related_issues = []
        issue_keywords = issue.title.lower().split() + issue.description.lower().split()
        
        for network_issue in self.network_analysis['issues']:
            issue_text = network_issue.lower()
            if any(keyword in issue_text for keyword in issue_keywords if len(keyword) > 3):
                related_issues.append(network_issue)
                
        return related_issues[:3]  # Limit to top 3 related issues
        
    def _assess_performance_impact(self, issue: TestIssue) -> Optional[Dict[str, float]]:
        """Assess performance impact of an issue."""
        if not self.performance_analysis:
            return None
            
        # Map issue categories to performance metrics
        impact_mapping = {
            IssueCategory.PERFORMANCE: {
                'page_load_impact': 0.8,
                'interaction_impact': 0.9,
                'memory_impact': 0.7
            },
            IssueCategory.FUNCTIONALITY: {
                'page_load_impact': 0.3,
                'interaction_impact': 0.8,
                'memory_impact': 0.2
            },
            IssueCategory.USABILITY: {
                'page_load_impact': 0.2,
                'interaction_impact': 0.6,
                'memory_impact': 0.1
            }
        }
        
        return impact_mapping.get(issue.category, {
            'page_load_impact': 0.1,
            'interaction_impact': 0.1,
            'memory_impact': 0.1
        })
        
    def _identify_patterns(self) -> None:
        """Identify patterns across test results and issues."""
        # Pattern analysis would go here
        # For now, we'll add basic pattern detection
        
        # Check for recurring issue types
        issue_categories = {}
        for result in self.test_results:
            for issue in result.issues:
                category = issue.category.value
                issue_categories[category] = issue_categories.get(category, 0) + 1
                
        # Add pattern-based global issues
        if issue_categories.get('performance', 0) > 2:
            self.add_global_issue(TestIssue(
                id="pattern_performance",
                title="Widespread Performance Issues",
                description=f"Performance issues detected across {issue_categories['performance']} scenarios",
                category=IssueCategory.PERFORMANCE,
                severity=ReportSeverity.HIGH,
                recommendations=[
                    "Conduct comprehensive performance audit",
                    "Implement performance monitoring",
                    "Optimize critical rendering path"
                ]
            ))
            
    def _generate_recommendations(self) -> None:
        """Generate intelligent recommendations based on analysis."""
        # This would use AI/ML to generate contextual recommendations
        # For now, we'll use rule-based recommendations
        
        for result in self.test_results:
            for issue in result.issues:
                if not issue.recommendations:
                    issue.recommendations = self._get_category_recommendations(issue.category, issue.severity)
                    
    def _get_category_recommendations(self, category: IssueCategory, severity: ReportSeverity) -> List[str]:
        """Get recommendations based on issue category and severity."""
        recommendations = {
            IssueCategory.FUNCTIONALITY: [
                "Review and test the affected functionality thoroughly",
                "Check for JavaScript errors in browser console",
                "Verify API endpoints and data flow",
                "Test across different browsers and devices"
            ],
            IssueCategory.PERFORMANCE: [
                "Optimize resource loading and caching",
                "Implement lazy loading for non-critical resources",
                "Minimize and compress assets",
                "Use performance monitoring tools"
            ],
            IssueCategory.ACCESSIBILITY: [
                "Add proper ARIA labels and roles",
                "Ensure keyboard navigation support",
                "Improve color contrast ratios",
                "Test with screen readers"
            ],
            IssueCategory.SECURITY: [
                "Review and fix security vulnerabilities immediately",
                "Implement proper input validation",
                "Use HTTPS for all communications",
                "Regular security audits"
            ],
            IssueCategory.USABILITY: [
                "Improve user interface clarity",
                "Add helpful error messages and guidance",
                "Simplify complex workflows",
                "Conduct user testing"
            ]
        }
        
        base_recommendations = recommendations.get(category, ["Review and address the identified issue"])
        
        if severity in [ReportSeverity.CRITICAL, ReportSeverity.HIGH]:
            base_recommendations.insert(0, "🚨 HIGH PRIORITY: Address this issue immediately")
            
        return base_recommendations
        
    def generate_executive_summary(self) -> ExecutiveSummary:
        """Generate high-level executive summary."""
        total_scenarios = len(self.test_results)
        passed_scenarios = len([r for r in self.test_results if r.status == 'passed'])
        failed_scenarios = len([r for r in self.test_results if r.status == 'failed'])
        
        # Count issues by severity
        all_issues = self.global_issues + [issue for result in self.test_results for issue in result.issues]
        critical_issues = len([i for i in all_issues if i.severity == ReportSeverity.CRITICAL])
        high_priority_issues = len([i for i in all_issues if i.severity == ReportSeverity.HIGH])
        
        # Calculate scores
        performance_score = self._calculate_performance_score()
        accessibility_score = self._calculate_accessibility_score()
        security_score = self._calculate_security_score()
        
        # Determine overall status
        if critical_issues > 0:
            overall_status = "Critical Issues Found"
        elif failed_scenarios > passed_scenarios:
            overall_status = "Multiple Failures"
        elif high_priority_issues > 0:
            overall_status = "Issues Require Attention"
        elif failed_scenarios == 0:
            overall_status = "All Tests Passed"
        else:
            overall_status = "Mixed Results"
            
        # Generate key findings
        key_findings = self._generate_key_findings(all_issues)
        
        # Assess business impact
        business_impact = self._assess_business_impact(critical_issues, high_priority_issues, failed_scenarios, total_scenarios)
        
        # Generate recommended actions
        recommended_actions = self._generate_recommended_actions(all_issues)
        
        return ExecutiveSummary(
            overall_status=overall_status,
            total_scenarios=total_scenarios,
            passed_scenarios=passed_scenarios,
            failed_scenarios=failed_scenarios,
            critical_issues=critical_issues,
            high_priority_issues=high_priority_issues,
            performance_score=performance_score,
            accessibility_score=accessibility_score,
            security_score=security_score,
            key_findings=key_findings,
            business_impact=business_impact,
            recommended_actions=recommended_actions
        )
        
    def _calculate_performance_score(self) -> float:
        """Calculate overall performance score (0-100)."""
        if not self.performance_analysis:
            return 50.0
            
        return self.performance_analysis.get('analysis', {}).get('overall_score', 50.0)
        
    def _calculate_accessibility_score(self) -> float:
        """Calculate accessibility score based on issues found."""
        accessibility_issues = [i for result in self.test_results for i in result.issues 
                              if i.category == IssueCategory.ACCESSIBILITY]
        
        if not accessibility_issues:
            return 85.0  # Good baseline if no issues found
            
        # Deduct points based on severity
        deductions = sum(
            20 if issue.severity == ReportSeverity.CRITICAL else
            15 if issue.severity == ReportSeverity.HIGH else
            10 if issue.severity == ReportSeverity.MEDIUM else 5
            for issue in accessibility_issues
        )
        
        return max(0, 100 - deductions)
        
    def _calculate_security_score(self) -> float:
        """Calculate security score based on issues found."""
        security_issues = [i for result in self.test_results for i in result.issues 
                          if i.category == IssueCategory.SECURITY]
        
        if not security_issues:
            return 90.0  # Good baseline if no issues found
            
        # Security issues are weighted heavily
        deductions = sum(
            40 if issue.severity == ReportSeverity.CRITICAL else
            25 if issue.severity == ReportSeverity.HIGH else
            15 if issue.severity == ReportSeverity.MEDIUM else 5
            for issue in security_issues
        )
        
        return max(0, 100 - deductions)
        
    def _generate_key_findings(self, all_issues: List[TestIssue]) -> List[str]:
        """Generate key findings from analysis."""
        findings = []
        
        # Issue distribution
        if all_issues:
            category_counts = {}
            for issue in all_issues:
                category_counts[issue.category.value] = category_counts.get(issue.category.value, 0) + 1
                
            top_category = max(category_counts.items(), key=lambda x: x[1])
            findings.append(f"Most common issue type: {top_category[0]} ({top_category[1]} issues)")
            
        # Performance findings
        if self.performance_analysis:
            perf_data = self.performance_analysis.get('analysis', {})
            if perf_data.get('overall_score', 0) < 50:
                findings.append("Performance issues detected - page load times exceed acceptable thresholds")
                
        # Console findings
        if self.console_analysis:
            error_count = self.console_analysis.get('error_count', 0)
            if error_count > 0:
                findings.append(f"{error_count} JavaScript errors detected during testing")
                
        # Network findings
        if self.network_analysis:
            failed_requests = self.network_analysis.get('failed_requests', 0)
            if failed_requests > 0:
                findings.append(f"{failed_requests} network requests failed during testing")
                
        return findings[:5]  # Limit to top 5 findings
        
    def _assess_business_impact(self, critical_issues: int, high_priority_issues: int, 
                               failed_scenarios: int, total_scenarios: int) -> str:
        """Assess business impact of test results."""
        if critical_issues > 0:
            return "HIGH IMPACT: Critical issues may prevent users from completing key tasks, potentially affecting revenue and user satisfaction."
        elif high_priority_issues > 2:
            return "MEDIUM-HIGH IMPACT: Multiple high-priority issues may degrade user experience and reduce conversion rates."
        elif failed_scenarios > total_scenarios * 0.5:
            return "MEDIUM IMPACT: Significant test failures indicate potential user experience issues that should be addressed."
        elif high_priority_issues > 0 or failed_scenarios > 0:
            return "LOW-MEDIUM IMPACT: Some issues detected that may affect user experience but are not critical."
        else:
            return "LOW IMPACT: No significant issues detected. Application appears to be functioning well."
            
    def _generate_recommended_actions(self, all_issues: List[TestIssue]) -> List[str]:
        """Generate prioritized recommended actions."""
        actions = []
        
        # Critical issues first
        critical_issues = [i for i in all_issues if i.severity == ReportSeverity.CRITICAL]
        if critical_issues:
            actions.append(f"🚨 IMMEDIATE: Address {len(critical_issues)} critical issues before release")
            
        # High priority issues
        high_issues = [i for i in all_issues if i.severity == ReportSeverity.HIGH]
        if high_issues:
            actions.append(f"⚠️ HIGH PRIORITY: Resolve {len(high_issues)} high-priority issues")
            
        # Category-specific actions
        category_counts = {}
        for issue in all_issues:
            category_counts[issue.category] = category_counts.get(issue.category, 0) + 1
            
        if category_counts.get(IssueCategory.PERFORMANCE, 0) > 1:
            actions.append("⚡ Conduct performance optimization review")
            
        if category_counts.get(IssueCategory.ACCESSIBILITY, 0) > 1:
            actions.append("♿ Perform accessibility audit and remediation")
            
        if category_counts.get(IssueCategory.SECURITY, 0) > 0:
            actions.append("🔒 Security review and vulnerability assessment")
            
        # General recommendations
        if len(all_issues) > 5:
            actions.append("📋 Implement systematic issue tracking and resolution process")
            
        actions.append("🔄 Re-test after fixes to verify resolution")
        
        return actions[:6]  # Limit to top 6 actions
        
    def generate_detailed_report(self) -> Dict[str, Any]:
        """Generate comprehensive detailed report."""
        executive_summary = self.generate_executive_summary()
        
        # Calculate test duration
        duration = (self.end_time or time.time()) - self.start_time
        
        # Compile all issues with context
        all_issues_with_context = []
        for issue in self.global_issues + [i for result in self.test_results for i in result.issues]:
            issue_dict = {
                'id': issue.id,
                'title': issue.title,
                'description': issue.description,
                'category': issue.category.value,
                'severity': issue.severity.value,
                'location': issue.location,
                'timestamp': issue.timestamp,
                'recommendations': issue.recommendations,
                'related_console_errors': issue.related_console_errors,
                'related_network_issues': issue.related_network_issues,
                'performance_impact': issue.performance_impact,
                'reproduction_steps': issue.reproduction_steps
            }
            all_issues_with_context.append(issue_dict)
            
        return {
            'report_metadata': {
                'generated_at': datetime.now().isoformat(),
                'test_duration': duration,
                'total_scenarios': len(self.test_results),
                'report_version': '2.0'
            },
            'executive_summary': {
                'overall_status': executive_summary.overall_status,
                'total_scenarios': executive_summary.total_scenarios,
                'passed_scenarios': executive_summary.passed_scenarios,
                'failed_scenarios': executive_summary.failed_scenarios,
                'critical_issues': executive_summary.critical_issues,
                'high_priority_issues': executive_summary.high_priority_issues,
                'performance_score': executive_summary.performance_score,
                'accessibility_score': executive_summary.accessibility_score,
                'security_score': executive_summary.security_score,
                'key_findings': executive_summary.key_findings,
                'business_impact': executive_summary.business_impact,
                'recommended_actions': executive_summary.recommended_actions
            },
            'test_results': [
                {
                    'scenario_name': result.scenario_name,
                    'status': result.status,
                    'duration': result.duration,
                    'agent_id': result.agent_id,
                    'error_message': result.error_message,
                    'issues_count': len(result.issues),
                    'success_criteria_met': result.success_criteria_met,
                    'success_criteria_failed': result.success_criteria_failed,
                    'console_summary': result.console_summary,
                    'network_summary': result.network_summary,
                    'performance_summary': result.performance_summary
                }
                for result in self.test_results
            ],
            'issues': all_issues_with_context,
            'browser_context_analysis': {
                'console_analysis': self.console_analysis,
                'network_analysis': self.network_analysis,
                'performance_analysis': self.performance_analysis,
                'interaction_analysis': self.interaction_analysis
            },
            'recommendations': {
                'immediate_actions': [action for action in executive_summary.recommended_actions if '🚨' in action or 'IMMEDIATE' in action],
                'high_priority_actions': [action for action in executive_summary.recommended_actions if '⚠️' in action or 'HIGH PRIORITY' in action],
                'general_improvements': [action for action in executive_summary.recommended_actions if action not in [a for a in executive_summary.recommended_actions if '🚨' in action or '⚠️' in action or 'IMMEDIATE' in action or 'HIGH PRIORITY' in action]]
            }
        }

