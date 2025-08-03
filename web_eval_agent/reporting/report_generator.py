"""
Report generator for web evaluation results
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from ..core.evaluator import EvaluationReport, TestResult


class ReportGenerator:
    """Generate reports in various formats"""
    
    def __init__(self, debug: bool = False):
        self.debug = debug
    
    def generate_report(self, report: EvaluationReport, output_format: str = 'text', 
                       output_file: Optional[str] = None) -> str:
        """
        Generate a report in the specified format
        
        Args:
            report: EvaluationReport to generate from
            output_format: Format ('text', 'json', 'html')
            output_file: Optional output file path
            
        Returns:
            Generated report content
        """
        if output_format.lower() == 'json':
            content = self._generate_json_report(report)
        elif output_format.lower() == 'html':
            content = self._generate_html_report(report)
        else:
            content = self._generate_text_report(report)
        
        # Save to file if specified
        if output_file:
            Path(output_file).write_text(content, encoding='utf-8')
            if self.debug:
                print(f"📄 Report saved to: {output_file}")
        
        return content
    
    def _generate_text_report(self, report: EvaluationReport) -> str:
        """Generate a formatted text report"""
        
        # Header
        content = f"""
┌─────────────────────────────────────────────────────────────────┐
│                     WEB EVALUATION REPORT                      │
├─────────────────────────────────────────────────────────────────┤
│ URL:            {report.url:<47} │
│ Test Duration:  {report.test_duration:.1f} seconds{' ' * (47 - len(f'{report.test_duration:.1f} seconds'))}│
│ Total Tests:    {report.total_scenarios:<47} │
│ Passed:         {report.passed_scenarios:<47} │
│ Failed:         {report.failed_scenarios:<47} │
│ Success Rate:   {(report.passed_scenarios/report.total_scenarios*100):.1f}%{' ' * (47 - len(f'{(report.passed_scenarios/report.total_scenarios*100):.1f}%'))}│
│ Session ID:     {report.session_id[:8]}...{' ' * (47 - len(f'{report.session_id[:8]}...'))}│
│ Generated:      {datetime.fromisoformat(report.timestamp).strftime('%Y-%m-%d %H:%M:%S'):<47} │
└─────────────────────────────────────────────────────────────────┘

"""
        
        # Test Results
        content += "┌─────────────────────────────────────────────────────────────────┐\n"
        content += "│                         TEST RESULTS                           │\n"
        content += "└─────────────────────────────────────────────────────────────────┘\n\n"
        
        for i, result in enumerate(report.results, 1):
            status_emoji = "✅" if result.status == "passed" else "❌" if result.status == "failed" else "⚠️"
            content += f"{status_emoji} Test {i}: {result.scenario_name}\n"
            content += f"   Duration: {result.duration:.1f} seconds\n"
            content += f"   Status: {result.status.upper()}\n"
            
            # Add details (truncated for readability)
            details = result.details[:200] + "..." if len(result.details) > 200 else result.details
            content += f"   Details: {details}\n"
            
            if result.issues:
                content += f"   Issues: {', '.join(result.issues[:2])}\n"
            
            if result.error_message:
                content += f"   Error: {result.error_message[:100]}...\n"
            
            content += "\n"
        
        # Summary
        content += "┌─────────────────────────────────────────────────────────────────┐\n"
        content += "│                           SUMMARY                              │\n"
        content += "└─────────────────────────────────────────────────────────────────┘\n\n"
        content += report.summary + "\n\n"
        
        # Recommendations
        content += "┌─────────────────────────────────────────────────────────────────┐\n"
        content += "│                       RECOMMENDATIONS                          │\n"
        content += "└─────────────────────────────────────────────────────────────────┘\n\n"
        
        if report.failed_scenarios > 0:
            content += "🔧 CRITICAL ACTIONS:\n"
            for result in report.results:
                if result.status == "failed" and result.recommendations:
                    content += f"   • {result.scenario_name}: {result.recommendations[0]}\n"
            content += "\n"
        
        content += "⚡ GENERAL RECOMMENDATIONS:\n"
        content += "   • Review all failed test scenarios\n"
        content += "   • Fix identified issues before deployment\n"
        content += "   • Re-run tests after implementing fixes\n"
        content += "   • Consider implementing automated testing\n\n"
        
        content += f"Report generated by Web Eval Agent v2.0.0\n"
        content += f"For more information, visit: https://github.com/Zeeeepa/web-eval-agent\n"
        
        return content
    
    def _generate_json_report(self, report: EvaluationReport) -> str:
        """Generate a JSON report"""
        
        # Convert dataclasses to dictionaries
        report_dict = {
            'url': report.url,
            'test_duration': report.test_duration,
            'total_scenarios': report.total_scenarios,
            'passed_scenarios': report.passed_scenarios,
            'failed_scenarios': report.failed_scenarios,
            'success_rate': (report.passed_scenarios / report.total_scenarios * 100) if report.total_scenarios > 0 else 0,
            'summary': report.summary,
            'timestamp': report.timestamp,
            'session_id': report.session_id,
            'results': []
        }
        
        for result in report.results:
            result_dict = {
                'scenario_name': result.scenario_name,
                'status': result.status,
                'duration': result.duration,
                'details': result.details,
                'issues': result.issues,
                'recommendations': result.recommendations
            }
            if result.error_message:
                result_dict['error_message'] = result.error_message
            
            report_dict['results'].append(result_dict)
        
        return json.dumps(report_dict, indent=2, ensure_ascii=False)
    
    def _generate_html_report(self, report: EvaluationReport) -> str:
        """Generate an HTML report"""
        
        success_rate = (report.passed_scenarios / report.total_scenarios * 100) if report.total_scenarios > 0 else 0
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Web Evaluation Report - {report.url}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
        }}
        .header p {{
            margin: 10px 0 0 0;
            opacity: 0.9;
        }}
        .metrics {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .metric-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .metric-value {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }}
        .metric-label {{
            color: #666;
            margin-top: 5px;
        }}
        .results {{
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
            margin-bottom: 30px;
        }}
        .results-header {{
            background: #f8f9fa;
            padding: 20px;
            border-bottom: 1px solid #dee2e6;
        }}
        .result-item {{
            padding: 20px;
            border-bottom: 1px solid #dee2e6;
        }}
        .result-item:last-child {{
            border-bottom: none;
        }}
        .result-status {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: bold;
            text-transform: uppercase;
        }}
        .status-passed {{
            background: #d4edda;
            color: #155724;
        }}
        .status-failed {{
            background: #f8d7da;
            color: #721c24;
        }}
        .status-error {{
            background: #fff3cd;
            color: #856404;
        }}
        .summary {{
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }}
        .footer {{
            text-align: center;
            color: #666;
            margin-top: 30px;
        }}
        .success-rate {{
            color: {'#28a745' if success_rate >= 80 else '#ffc107' if success_rate >= 60 else '#dc3545'};
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔍 Web Evaluation Report</h1>
        <p>Comprehensive analysis of {report.url}</p>
    </div>
    
    <div class="metrics">
        <div class="metric-card">
            <div class="metric-value">{report.total_scenarios}</div>
            <div class="metric-label">Total Tests</div>
        </div>
        <div class="metric-card">
            <div class="metric-value" style="color: #28a745;">{report.passed_scenarios}</div>
            <div class="metric-label">Passed</div>
        </div>
        <div class="metric-card">
            <div class="metric-value" style="color: #dc3545;">{report.failed_scenarios}</div>
            <div class="metric-label">Failed</div>
        </div>
        <div class="metric-card">
            <div class="metric-value success-rate">{success_rate:.1f}%</div>
            <div class="metric-label">Success Rate</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{report.test_duration:.1f}s</div>
            <div class="metric-label">Duration</div>
        </div>
    </div>
    
    <div class="results">
        <div class="results-header">
            <h2>📋 Test Results</h2>
        </div>"""
        
        for i, result in enumerate(report.results, 1):
            status_class = f"status-{result.status}"
            html += f"""
        <div class="result-item">
            <h3>Test {i}: {result.scenario_name}</h3>
            <p><span class="result-status {status_class}">{result.status}</span> 
               <small>({result.duration:.1f}s)</small></p>
            <p><strong>Details:</strong> {result.details[:300]}{'...' if len(result.details) > 300 else ''}</p>"""
            
            if result.issues:
                html += f"<p><strong>Issues:</strong> {', '.join(result.issues[:3])}</p>"
            
            if result.recommendations:
                html += f"<p><strong>Recommendations:</strong> {', '.join(result.recommendations[:2])}</p>"
            
            html += "</div>"
        
        html += f"""
    </div>
    
    <div class="summary">
        <h2>📊 Summary</h2>
        <pre style="white-space: pre-wrap; font-family: inherit;">{report.summary}</pre>
    </div>
    
    <div class="footer">
        <p>Generated on {datetime.fromisoformat(report.timestamp).strftime('%Y-%m-%d at %H:%M:%S')}</p>
        <p>Session ID: {report.session_id}</p>
        <p>Report generated by <strong>Web Eval Agent v2.0.0</strong></p>
    </div>
</body>
</html>"""
        
        return html
