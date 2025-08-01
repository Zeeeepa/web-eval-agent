"""
Console Monitor

Advanced console monitoring with intelligent categorization and analysis.
"""

import re
import time
from typing import Dict, List, Optional, Any, Pattern
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ConsoleLevel(Enum):
    """Console message levels with severity mapping."""
    ERROR = "error"
    WARNING = "warning" 
    INFO = "info"
    DEBUG = "debug"
    LOG = "log"
    ASSERT = "assert"
    
    @property
    def severity_score(self) -> int:
        """Get numeric severity score for sorting."""
        scores = {
            self.ERROR: 5,
            self.ASSERT: 5,
            self.WARNING: 3,
            self.INFO: 1,
            self.LOG: 1,
            self.DEBUG: 0
        }
        return scores.get(self, 0)


@dataclass
class ConsolePattern:
    """Pattern for categorizing console messages."""
    name: str
    pattern: Pattern[str]
    category: str
    severity: ConsoleLevel
    description: str
    action_required: bool = False


@dataclass
class ConsoleAnalysis:
    """Analysis results for console messages."""
    total_messages: int
    error_count: int
    warning_count: int
    info_count: int
    categories: Dict[str, int]
    critical_issues: List[str]
    patterns_detected: List[str]
    recommendations: List[str]
    severity_score: float


class ConsoleMonitor:
    """
    Advanced console monitoring with intelligent categorization,
    pattern detection, and actionable analysis.
    """
    
    def __init__(self):
        self.messages: List[Dict[str, Any]] = []
        self.patterns = self._initialize_patterns()
        self.categories: Dict[str, List[Dict[str, Any]]] = {}
        self.start_time = time.time()
        
    def _initialize_patterns(self) -> List[ConsolePattern]:
        """Initialize common console message patterns."""
        return [
            # JavaScript Errors
            ConsolePattern(
                name="uncaught_exception",
                pattern=re.compile(r"Uncaught\s+(TypeError|ReferenceError|SyntaxError|Error)", re.IGNORECASE),
                category="javascript_error",
                severity=ConsoleLevel.ERROR,
                description="Uncaught JavaScript exception",
                action_required=True
            ),
            ConsolePattern(
                name="network_error",
                pattern=re.compile(r"(Failed to load|net::ERR_|NetworkError|fetch.*failed)", re.IGNORECASE),
                category="network_error",
                severity=ConsoleLevel.ERROR,
                description="Network request failure",
                action_required=True
            ),
            ConsolePattern(
                name="cors_error",
                pattern=re.compile(r"(CORS|Cross-Origin|Access-Control-Allow)", re.IGNORECASE),
                category="cors_error",
                severity=ConsoleLevel.ERROR,
                description="CORS policy violation",
                action_required=True
            ),
            ConsolePattern(
                name="csp_violation",
                pattern=re.compile(r"Content Security Policy|CSP", re.IGNORECASE),
                category="security_error",
                severity=ConsoleLevel.ERROR,
                description="Content Security Policy violation",
                action_required=True
            ),
            
            # Performance Warnings
            ConsolePattern(
                name="performance_warning",
                pattern=re.compile(r"(slow|performance|optimization|inefficient)", re.IGNORECASE),
                category="performance_warning",
                severity=ConsoleLevel.WARNING,
                description="Performance-related warning"
            ),
            ConsolePattern(
                name="memory_warning",
                pattern=re.compile(r"(memory|heap|leak|garbage)", re.IGNORECASE),
                category="memory_warning",
                severity=ConsoleLevel.WARNING,
                description="Memory usage warning"
            ),
            
            # Deprecation Warnings
            ConsolePattern(
                name="deprecation",
                pattern=re.compile(r"(deprecated|deprecation|will be removed)", re.IGNORECASE),
                category="deprecation_warning",
                severity=ConsoleLevel.WARNING,
                description="Deprecated API usage"
            ),
            
            # Framework-specific patterns
            ConsolePattern(
                name="react_warning",
                pattern=re.compile(r"React|Warning.*React", re.IGNORECASE),
                category="framework_warning",
                severity=ConsoleLevel.WARNING,
                description="React framework warning"
            ),
            ConsolePattern(
                name="vue_warning",
                pattern=re.compile(r"Vue warn|Vue\.js", re.IGNORECASE),
                category="framework_warning",
                severity=ConsoleLevel.WARNING,
                description="Vue.js framework warning"
            ),
            ConsolePattern(
                name="angular_warning",
                pattern=re.compile(r"Angular|ng-", re.IGNORECASE),
                category="framework_warning",
                severity=ConsoleLevel.WARNING,
                description="Angular framework warning"
            ),
            
            # Security Issues
            ConsolePattern(
                name="mixed_content",
                pattern=re.compile(r"Mixed Content|insecure.*secure", re.IGNORECASE),
                category="security_warning",
                severity=ConsoleLevel.WARNING,
                description="Mixed content warning"
            ),
            
            # Third-party Issues
            ConsolePattern(
                name="third_party_error",
                pattern=re.compile(r"(google|facebook|twitter|analytics|gtag|fbq)", re.IGNORECASE),
                category="third_party_error",
                severity=ConsoleLevel.WARNING,
                description="Third-party service error"
            ),
            
            # Development/Debug Messages
            ConsolePattern(
                name="debug_message",
                pattern=re.compile(r"(debug|dev|development|console\.log)", re.IGNORECASE),
                category="debug_message",
                severity=ConsoleLevel.DEBUG,
                description="Development/debug message"
            )
        ]
        
    def add_message(self, message: Dict[str, Any]) -> None:
        """Add a console message for monitoring and analysis."""
        # Enhance message with timestamp and analysis
        enhanced_message = {
            **message,
            'timestamp': time.time(),
            'relative_time': time.time() - self.start_time,
            'patterns_matched': [],
            'category': 'uncategorized',
            'severity_score': 0,
            'action_required': False
        }
        
        # Analyze message against patterns
        text = message.get('text', '')
        for pattern in self.patterns:
            if pattern.pattern.search(text):
                enhanced_message['patterns_matched'].append(pattern.name)
                enhanced_message['category'] = pattern.category
                enhanced_message['severity_score'] = max(
                    enhanced_message['severity_score'],
                    pattern.severity.severity_score
                )
                if pattern.action_required:
                    enhanced_message['action_required'] = True
                    
        # Categorize message
        category = enhanced_message['category']
        if category not in self.categories:
            self.categories[category] = []
        self.categories[category].append(enhanced_message)
        
        self.messages.append(enhanced_message)
        
        # Log critical issues immediately
        if enhanced_message['severity_score'] >= 5:
            logger.warning(f"Critical console issue detected: {text[:100]}...")
            
    def get_analysis(self) -> ConsoleAnalysis:
        """Get comprehensive analysis of console messages."""
        if not self.messages:
            return ConsoleAnalysis(
                total_messages=0,
                error_count=0,
                warning_count=0,
                info_count=0,
                categories={},
                critical_issues=[],
                patterns_detected=[],
                recommendations=[],
                severity_score=0.0
            )
            
        # Count messages by level
        level_counts = {
            'error': 0,
            'warning': 0,
            'info': 0,
            'debug': 0,
            'log': 0
        }
        
        for msg in self.messages:
            level = msg.get('level', 'info')
            if level in level_counts:
                level_counts[level] += 1
                
        # Category statistics
        category_counts = {cat: len(msgs) for cat, msgs in self.categories.items()}
        
        # Identify critical issues
        critical_issues = []
        for msg in self.messages:
            if msg.get('action_required', False):
                critical_issues.append(msg['text'][:100] + "..." if len(msg['text']) > 100 else msg['text'])
                
        # Detect patterns
        patterns_detected = []
        pattern_counts = {}
        for msg in self.messages:
            for pattern in msg.get('patterns_matched', []):
                pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
                
        patterns_detected = [f"{pattern} ({count}x)" for pattern, count in pattern_counts.items()]
        
        # Generate recommendations
        recommendations = self._generate_recommendations(category_counts, pattern_counts)
        
        # Calculate overall severity score
        total_severity = sum(msg.get('severity_score', 0) for msg in self.messages)
        avg_severity = total_severity / len(self.messages) if self.messages else 0
        
        return ConsoleAnalysis(
            total_messages=len(self.messages),
            error_count=level_counts['error'],
            warning_count=level_counts['warning'],
            info_count=level_counts['info'] + level_counts['log'],
            categories=category_counts,
            critical_issues=critical_issues[:10],  # Limit to top 10
            patterns_detected=patterns_detected,
            recommendations=recommendations,
            severity_score=avg_severity
        )
        
    def _generate_recommendations(self, categories: Dict[str, int], patterns: Dict[str, int]) -> List[str]:
        """Generate actionable recommendations based on console analysis."""
        recommendations = []
        
        # JavaScript error recommendations
        if categories.get('javascript_error', 0) > 0:
            recommendations.append(
                f"🔧 Fix {categories['javascript_error']} JavaScript errors to improve application stability"
            )
            
        # Network error recommendations
        if categories.get('network_error', 0) > 0:
            recommendations.append(
                f"🌐 Investigate {categories['network_error']} network failures - check API endpoints and connectivity"
            )
            
        # CORS error recommendations
        if categories.get('cors_error', 0) > 0:
            recommendations.append(
                "🔒 Configure CORS headers properly to resolve cross-origin request issues"
            )
            
        # Performance recommendations
        if categories.get('performance_warning', 0) > 0:
            recommendations.append(
                "⚡ Address performance warnings to improve user experience"
            )
            
        # Security recommendations
        if categories.get('security_error', 0) > 0 or categories.get('security_warning', 0) > 0:
            recommendations.append(
                "🛡️ Review and fix security-related issues (CSP violations, mixed content)"
            )
            
        # Deprecation recommendations
        if categories.get('deprecation_warning', 0) > 0:
            recommendations.append(
                "📅 Update deprecated API usage to prevent future compatibility issues"
            )
            
        # Framework-specific recommendations
        if categories.get('framework_warning', 0) > 0:
            recommendations.append(
                "⚛️ Address framework-specific warnings to ensure optimal performance"
            )
            
        # Development cleanup recommendations
        if categories.get('debug_message', 0) > 5:
            recommendations.append(
                "🧹 Remove debug/development console messages from production code"
            )
            
        # General recommendations based on volume
        total_errors = categories.get('javascript_error', 0) + categories.get('network_error', 0)
        if total_errors > 10:
            recommendations.append(
                "🚨 High error volume detected - prioritize error resolution for better user experience"
            )
            
        return recommendations
        
    def get_critical_issues(self) -> List[Dict[str, Any]]:
        """Get list of critical issues requiring immediate attention."""
        critical = []
        for msg in self.messages:
            if msg.get('action_required', False) or msg.get('severity_score', 0) >= 5:
                critical.append({
                    'timestamp': msg['timestamp'],
                    'level': msg.get('level', 'unknown'),
                    'text': msg['text'],
                    'category': msg['category'],
                    'patterns': msg['patterns_matched'],
                    'location': msg.get('location')
                })
        return sorted(critical, key=lambda x: x['timestamp'], reverse=True)
        
    def get_category_summary(self, category: str) -> Dict[str, Any]:
        """Get detailed summary for a specific category."""
        if category not in self.categories:
            return {'category': category, 'count': 0, 'messages': []}
            
        messages = self.categories[category]
        return {
            'category': category,
            'count': len(messages),
            'messages': messages[-10:],  # Last 10 messages
            'first_occurrence': min(msg['timestamp'] for msg in messages),
            'last_occurrence': max(msg['timestamp'] for msg in messages),
            'unique_messages': len(set(msg['text'] for msg in messages))
        }
        
    def export_summary(self) -> Dict[str, Any]:
        """Export comprehensive summary for reporting."""
        analysis = self.get_analysis()
        
        return {
            'monitoring_duration': time.time() - self.start_time,
            'analysis': analysis.__dict__,
            'categories': {cat: self.get_category_summary(cat) for cat in self.categories.keys()},
            'critical_issues': self.get_critical_issues(),
            'timeline': [
                {
                    'timestamp': msg['timestamp'],
                    'relative_time': msg['relative_time'],
                    'level': msg.get('level'),
                    'category': msg['category'],
                    'text': msg['text'][:100] + "..." if len(msg['text']) > 100 else msg['text']
                }
                for msg in sorted(self.messages, key=lambda x: x['timestamp'])[-20:]  # Last 20 messages
            ]
        }

