"""
Report generator for Web Eval Agent

Generates comprehensive test reports in various formats (HTML, JSON, text).
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from .config import Config
from .test_executor import TestResults, TestResult
from .utils import format_duration, ensure_directory, get_file_size_mb


class Reporter:
    """Generates test reports in various formats."""
    
    def __init__(self, config: Config):
        self.config = config
    
    async def generate_report(self, results: TestResults) -> str:
        """Generate a test report and return the file path."""
        ensure_directory(self.config.output_file)
        
        if self.config.report_format == "html":
            return await self._generate_html_report(results)
        elif self.config.report_format == "json":
            return await self._generate_json_report(results)
        elif self.config.report_format == "text":
            return await self._generate_text_report(results)
        else:
            raise ValueError(f"Unsupported report format: {self.config.report_format}")
    
    async def _generate_html_report(self, results: TestResults) -> str:
        """Generate an HTML report."""
        html_content = self._create_html_report(results)
        
        output_path = self.config.output_file
        if not output_path.endswith('.html'):
            output_path += '.html'
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return output_path
    
    async def _generate_json_report(self, results: TestResults) -> str:
        """Generate a JSON report."""
        report_data = self._create_json_report_data(results)
        
        output_path = self.config.output_file
        if not output_path.endswith('.json'):
            output_path += '.json'
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        return output_path
    
    async def _generate_text_report(self, results: TestResults) -> str:
        """Generate a text report."""
        text_content = self._create_text_report(results)
        
        output_path = self.config.output_file
        if not output_path.endswith('.txt'):
            output_path += '.txt'
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text_content)
        
        return output_path
    
    def _create_html_report(self, results: TestResults) -> str:
        """Create HTML report content."""
        # Generate test result rows
        test_rows = []
        for result in results.test_results:
            status_icon = "✅" if result.passed else "❌"
            status_class = "passed" if result.passed else "failed"
            duration_str = format_duration(result.duration)
            
            # Create validation summary
            validation_summary = ""
            if result.validation_results:
                passed_validations = sum(1 for v in result.validation_results if v.get("passed", False))
                total_validations = len(result.validation_results)
                validation_summary = f"{passed_validations}/{total_validations} validations passed"
            
            error_info = ""
            if result.error_message:
                error_info = f'<div class="error-message">{result.error_message}</div>'
            
            test_rows.append(f"""
                <tr class="{status_class}">
                    <td>{status_icon} {result.scenario_name}</td>
                    <td>{duration_str}</td>
                    <td>{validation_summary}</td>
                    <td>{len(result.console_logs)} logs</td>
                    <td>{len(result.network_requests)} requests</td>
                    <td>{len(result.screenshots)} screenshots</td>
                </tr>
                {error_info}
            """)
        
        # Generate detailed sections for each test
        detailed_sections = []
        for result in results.test_results:
            detailed_sections.append(self._create_test_detail_section(result))
        
        # Calculate summary stats
        summary = results.summary
        success_rate = summary.get("success_rate", 0)
        
        html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Web Eval Agent - Test Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
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
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
        }}
        .summary-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .summary-card h3 {{
            margin: 0 0 10px 0;
            color: #333;
        }}
        .summary-card .value {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }}
        .success-rate {{
            color: {('#28a745' if success_rate >= 80 else '#ffc107' if success_rate >= 60 else '#dc3545')};
        }}
        .content {{
            padding: 30px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 30px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #f8f9fa;
            font-weight: 600;
        }}
        .passed {{
            background-color: #f8fff8;
        }}
        .failed {{
            background-color: #fff8f8;
        }}
        .error-message {{
            color: #dc3545;
            font-size: 0.9em;
            margin-top: 5px;
            padding: 10px;
            background-color: #f8d7da;
            border-radius: 4px;
        }}
        .test-detail {{
            margin-bottom: 40px;
            border: 1px solid #ddd;
            border-radius: 8px;
            overflow: hidden;
        }}
        .test-detail-header {{
            background: #f8f9fa;
            padding: 15px 20px;
            border-bottom: 1px solid #ddd;
        }}
        .test-detail-content {{
            padding: 20px;
        }}
        .validation-item {{
            padding: 8px 12px;
            margin: 5px 0;
            border-radius: 4px;
            border-left: 4px solid;
        }}
        .validation-passed {{
            background-color: #f8fff8;
            border-left-color: #28a745;
        }}
        .validation-failed {{
            background-color: #fff8f8;
            border-left-color: #dc3545;
        }}
        .console-log {{
            background: #f8f9fa;
            padding: 10px;
            margin: 5px 0;
            border-radius: 4px;
            font-family: monospace;
            font-size: 0.9em;
        }}
        .console-error {{
            background: #fff8f8;
            border-left: 4px solid #dc3545;
        }}
        .console-warn {{
            background: #fff9f0;
            border-left: 4px solid #ffc107;
        }}
        .network-request {{
            background: #f8f9fa;
            padding: 10px;
            margin: 5px 0;
            border-radius: 4px;
            font-family: monospace;
            font-size: 0.9em;
        }}
        .collapsible {{
            cursor: pointer;
            padding: 10px;
            background: #f1f1f1;
            border: none;
            text-align: left;
            outline: none;
            font-size: 15px;
            width: 100%;
        }}
        .collapsible:hover {{
            background-color: #ddd;
        }}
        .collapsible-content {{
            padding: 0 18px;
            display: none;
            overflow: hidden;
            background-color: #f9f9f9;
        }}
        .collapsible-content.active {{
            display: block;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧪 Web Eval Agent Report</h1>
            <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>Testing: {self.config.url}</p>
        </div>
        
        <div class="summary">
            <div class="summary-card">
                <h3>Total Tests</h3>
                <div class="value">{summary.get('total_tests', 0)}</div>
            </div>
            <div class="summary-card">
                <h3>Passed</h3>
                <div class="value" style="color: #28a745;">{summary.get('passed', 0)}</div>
            </div>
            <div class="summary-card">
                <h3>Failed</h3>
                <div class="value" style="color: #dc3545;">{summary.get('failed', 0)}</div>
            </div>
            <div class="summary-card">
                <h3>Success Rate</h3>
                <div class="value success-rate">{success_rate:.1f}%</div>
            </div>
            <div class="summary-card">
                <h3>Duration</h3>
                <div class="value">{format_duration(results.total_duration)}</div>
            </div>
        </div>
        
        <div class="content">
            <h2>Test Results Overview</h2>
            <table>
                <thead>
                    <tr>
                        <th>Test Name</th>
                        <th>Duration</th>
                        <th>Validations</th>
                        <th>Console Logs</th>
                        <th>Network Requests</th>
                        <th>Screenshots</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(test_rows)}
                </tbody>
            </table>
            
            <h2>Detailed Test Results</h2>
            {''.join(detailed_sections)}
        </div>
    </div>
    
    <script>
        // Make collapsible sections work
        document.querySelectorAll('.collapsible').forEach(button => {{
            button.addEventListener('click', function() {{
                this.classList.toggle('active');
                const content = this.nextElementSibling;
                content.classList.toggle('active');
            }});
        }});
    </script>
</body>
</html>
        """
        
        return html_template
    
    def _create_test_detail_section(self, result: TestResult) -> str:
        """Create detailed section for a single test result."""
        status_icon = "✅" if result.passed else "❌"
        
        # Validation results
        validation_html = ""
        if result.validation_results:
            validation_items = []
            for validation in result.validation_results:
                passed = validation.get("passed", False)
                css_class = "validation-passed" if passed else "validation-failed"
                icon = "✅" if passed else "❌"
                validation_items.append(f"""
                    <div class="{css_class} validation-item">
                        {icon} {validation.get('validation', 'Unknown validation')}
                        <br><small>{validation.get('details', '')}</small>
                    </div>
                """)
            validation_html = ''.join(validation_items)
        
        # Console logs
        console_html = ""
        if result.console_logs:
            console_items = []
            for log in result.console_logs[:20]:  # Limit to first 20 logs
                log_type = log.get("type", "log")
                css_class = f"console-{log_type}" if log_type in ["error", "warn"] else "console-log"
                console_items.append(f"""
                    <div class="{css_class} console-log">
                        [{log_type.upper()}] {log.get('text', '')}
                    </div>
                """)
            console_html = ''.join(console_items)
            if len(result.console_logs) > 20:
                console_html += f"<p><em>... and {len(result.console_logs) - 20} more logs</em></p>"
        
        # Network requests
        network_html = ""
        if result.network_requests:
            network_items = []
            for req in result.network_requests[:10]:  # Limit to first 10 requests
                status = req.get("response_status", "pending")
                network_items.append(f"""
                    <div class="network-request">
                        [{req.get('method', 'GET')}] {req.get('url', '')} - {status}
                    </div>
                """)
            network_html = ''.join(network_items)
            if len(result.network_requests) > 10:
                network_html += f"<p><em>... and {len(result.network_requests) - 10} more requests</em></p>"
        
        # Agent steps
        steps_html = ""
        if result.agent_steps:
            steps_items = []
            for i, step in enumerate(result.agent_steps, 1):
                steps_items.append(f"<li>{step}</li>")
            steps_html = f"<ol>{''.join(steps_items)}</ol>"
        
        return f"""
        <div class="test-detail">
            <div class="test-detail-header">
                <h3>{status_icon} {result.scenario_name}</h3>
                <p>Duration: {format_duration(result.duration)}</p>
                {f'<p style="color: #dc3545;">Error: {result.error_message}</p>' if result.error_message else ''}
            </div>
            <div class="test-detail-content">
                {f'<h4>Validations</h4>{validation_html}' if validation_html else ''}
                
                {f'<button class="collapsible">Agent Steps ({len(result.agent_steps)})</button><div class="collapsible-content">{steps_html}</div>' if steps_html else ''}
                
                {f'<button class="collapsible">Console Logs ({len(result.console_logs)})</button><div class="collapsible-content">{console_html}</div>' if console_html else ''}
                
                {f'<button class="collapsible">Network Requests ({len(result.network_requests)})</button><div class="collapsible-content">{network_html}</div>' if network_html else ''}
                
                {f'<h4>Screenshots</h4><p>{len(result.screenshots)} screenshot(s) captured</p>' if result.screenshots else ''}
            </div>
        </div>
        """
    
    def _create_json_report_data(self, results: TestResults) -> Dict[str, Any]:
        """Create JSON report data."""
        return {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "url": self.config.url,
                "total_duration": results.total_duration,
                "config": {
                    "browser": self.config.browser,
                    "headless": self.config.headless,
                    "viewport": self.config.viewport,
                    "timeout": self.config.timeout
                }
            },
            "summary": results.summary,
            "test_results": [
                {
                    "scenario_name": result.scenario_name,
                    "passed": result.passed,
                    "duration": result.duration,
                    "error_message": result.error_message,
                    "validation_results": result.validation_results,
                    "console_logs": result.console_logs,
                    "network_requests": result.network_requests,
                    "agent_steps": result.agent_steps,
                    "screenshots": result.screenshots
                }
                for result in results.test_results
            ],
            "errors": results.errors
        }
    
    def _create_text_report(self, results: TestResults) -> str:
        """Create text report content."""
        lines = [
            "=" * 80,
            "WEB EVAL AGENT - TEST REPORT",
            "=" * 80,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"URL: {self.config.url}",
            f"Total Duration: {format_duration(results.total_duration)}",
            "",
            "SUMMARY",
            "-" * 40,
            f"Total Tests: {results.summary.get('total_tests', 0)}",
            f"Passed: {results.summary.get('passed', 0)}",
            f"Failed: {results.summary.get('failed', 0)}",
            f"Success Rate: {results.summary.get('success_rate', 0):.1f}%",
            "",
            "TEST RESULTS",
            "-" * 40
        ]
        
        for result in results.test_results:
            status = "PASSED" if result.passed else "FAILED"
            lines.extend([
                f"[{status}] {result.scenario_name}",
                f"  Duration: {format_duration(result.duration)}",
                f"  Console Logs: {len(result.console_logs)}",
                f"  Network Requests: {len(result.network_requests)}",
                f"  Screenshots: {len(result.screenshots)}"
            ])
            
            if result.error_message:
                lines.append(f"  Error: {result.error_message}")
            
            if result.validation_results:
                lines.append("  Validations:")
                for validation in result.validation_results:
                    status_icon = "✓" if validation.get("passed", False) else "✗"
                    lines.append(f"    {status_icon} {validation.get('validation', 'Unknown')}")
            
            lines.append("")
        
        if results.errors:
            lines.extend([
                "ERRORS",
                "-" * 40
            ])
            for error in results.errors:
                lines.append(f"• {error}")
        
        lines.append("=" * 80)
        
        return "\n".join(lines)
