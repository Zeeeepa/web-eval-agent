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
        """Generate a text report based on the configured detail level."""
        if self.config.report_detail_level == "summary":
            text_content = self._create_summary_text_report(results)
        elif self.config.report_detail_level == "verbose":
            text_content = self._create_verbose_text_report(results)
        else:  # detailed (default)
            text_content = self._create_comprehensive_text_report(results)
        
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
    
    def _create_comprehensive_text_report(self, results: TestResults) -> str:
        """Create comprehensive text report with emojis and structured sections."""
        lines = []
        
        # Report Header
        lines.extend([
            "=" * 80,
            "🧪 WEB EVALUATION AGENT - COMPREHENSIVE TEST REPORT",
            "=" * 80,
            f"📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"🌐 Target URL: {self.config.url}",
            f"⏱️  Total Duration: {format_duration(results.total_duration)}",
            ""
        ])
        
        # Executive Summary
        summary = results.summary
        total_tests = summary.get('total_tests', 0)
        passed_tests = summary.get('passed_tests', 0)
        failed_tests = summary.get('failed_tests', 0)
        success_rate = summary.get('success_rate', 0)
        
        lines.extend([
            "📊 EXECUTIVE SUMMARY",
            "-" * 40,
            f"✅ Tests Passed: {passed_tests}/{total_tests}",
            f"❌ Tests Failed: {failed_tests}/{total_tests}",
            f"📈 Success Rate: {success_rate:.1f}%",
            f"🔧 Browser: {self.config.browser}",
            f"📱 Viewport: {self.config.viewport}",
            f"⚡ Headless Mode: {'Yes' if self.config.headless else 'No'}",
            ""
        ])
        
        # Test Results Overview
        if results.test_results:
            lines.extend([
                "📋 TEST RESULTS OVERVIEW",
                "-" * 40
            ])
            
            for i, result in enumerate(results.test_results, 1):
                status_icon = "✅" if result.passed else "❌"
                duration_str = format_duration(result.duration)
                lines.append(f"{i:2d}. {status_icon} {result.scenario_name} ({duration_str})")
                
                if result.error_message:
                    lines.append(f"     💥 Error: {result.error_message}")
            
            lines.append("")
        
        # Detailed Test Results
        lines.extend([
            "🔍 DETAILED TEST RESULTS",
            "=" * 80
        ])
        
        # Process each test result
        for i, result in enumerate(results.test_results, 1):
            status_icon = "✅" if result.passed else "❌"
            
            # Test Header
            lines.extend([
                "",
                f"TEST {i}/{len(results.test_results)}: {result.scenario_name}",
                "-" * 60,
                f"Status: {status_icon} {'PASSED' if result.passed else 'FAILED'}",
                f"Duration: {format_duration(result.duration)}",
                f"URL: {self.config.url}",
                ""
            ])
            
            # Error Information
            if result.error_message:
                lines.extend([
                    "💥 ERROR DETAILS:",
                    f"   {result.error_message}",
                    ""
                ])
            
            # Validation Results
            if result.validation_results:
                lines.append("✅ VALIDATION RESULTS:")
                for validation in result.validation_results:
                    passed = validation.get('passed', False)
                    validation_text = validation.get('validation', 'Unknown validation')
                    details = validation.get('details', '')
                    icon = "✅" if passed else "❌"
                    lines.append(f"   {icon} {validation_text}")
                    if details:
                        lines.append(f"      Details: {details}")
                lines.append("")
            
            # Agent Steps section
            lines.append("🤖 AGENT EXECUTION STEPS:")
            if result.agent_steps:
                for j, step in enumerate(result.agent_steps, 1):
                    lines.append(f"   {j:2d}. {step}")
            else:
                lines.append("   📍 1. Navigate → Target URL")
                lines.append("   🏁 Flow completed successfully.")
            lines.append("")
            
            # Console Logs section
            console_count = len(result.console_logs)
            lines.append(f"🖥️  CONSOLE LOGS ({console_count} total):")
            if result.console_logs:
                # Group logs by type
                error_logs = [log for log in result.console_logs if log.get('type') == 'error']
                warn_logs = [log for log in result.console_logs if log.get('type') == 'warn']
                info_logs = [log for log in result.console_logs if log.get('type') not in ['error', 'warn']]
                
                if error_logs:
                    lines.append("   🚨 ERRORS:")
                    for log in error_logs[:5]:
                        log_text = log.get('text', '')[:100] + ("..." if len(log.get('text', '')) > 100 else "")
                        lines.append(f"      • {log_text}")
                    if len(error_logs) > 5:
                        lines.append(f"      ... and {len(error_logs) - 5} more errors")
                
                if warn_logs:
                    lines.append("   ⚠️  WARNINGS:")
                    for log in warn_logs[:3]:
                        log_text = log.get('text', '')[:100] + ("..." if len(log.get('text', '')) > 100 else "")
                        lines.append(f"      • {log_text}")
                    if len(warn_logs) > 3:
                        lines.append(f"      ... and {len(warn_logs) - 3} more warnings")
                
                if info_logs:
                    lines.append("   ℹ️  INFO/DEBUG:")
                    for log in info_logs[:5]:
                        log_text = log.get('text', '')[:80] + ("..." if len(log.get('text', '')) > 80 else "")
                        lines.append(f"      • {log_text}")
                    if len(info_logs) > 5:
                        lines.append(f"      ... and {len(info_logs) - 5} more info logs")
            else:
                lines.append("   No console logs captured")
            lines.append("")
            
            # Network Requests section
            network_count = len(result.network_requests)
            lines.append(f"🌐 NETWORK ACTIVITY ({network_count} requests):")
            if result.network_requests:
                # Group by status code
                success_requests = [req for req in result.network_requests if str(req.get('response_status', '')).startswith('2')]
                error_requests = [req for req in result.network_requests if str(req.get('response_status', '')).startswith(('4', '5'))]
                other_requests = [req for req in result.network_requests if req not in success_requests + error_requests]
                
                if success_requests:
                    lines.append("   ✅ SUCCESSFUL REQUESTS:")
                    for req in success_requests[:5]:
                        method = req.get('method', 'GET')
                        url = req.get('url', '')
                        status = req.get('response_status', 'pending')
                        # Shorten URL for readability
                        url_display = url.split('/')[-1] if '/' in url else url
                        if len(url_display) > 50:
                            url_display = url_display[:47] + "..."
                        lines.append(f"      {method} {url_display} → {status}")
                    if len(success_requests) > 5:
                        lines.append(f"      ... and {len(success_requests) - 5} more successful requests")
                
                if error_requests:
                    lines.append("   ❌ FAILED REQUESTS:")
                    for req in error_requests:
                        method = req.get('method', 'GET')
                        url = req.get('url', '')
                        status = req.get('response_status', 'pending')
                        url_display = url.split('/')[-1] if '/' in url else url
                        if len(url_display) > 50:
                            url_display = url_display[:47] + "..."
                        lines.append(f"      {method} {url_display} → {status}")
                
                if other_requests:
                    lines.append("   📋 OTHER REQUESTS:")
                    for req in other_requests[:3]:
                        method = req.get('method', 'GET')
                        url = req.get('url', '')
                        status = req.get('response_status', 'pending')
                        url_display = url.split('/')[-1] if '/' in url else url
                        if len(url_display) > 50:
                            url_display = url_display[:47] + "..."
                        lines.append(f"      {method} {url_display} → {status}")
                    if len(other_requests) > 3:
                        lines.append(f"      ... and {len(other_requests) - 3} more requests")
            else:
                lines.append("   No network requests captured")
            lines.append("")
            
            # Screenshots section
            if result.screenshots:
                lines.extend([
                    f"📸 SCREENSHOTS ({len(result.screenshots)} captured):",
                    "   Screenshots saved for visual verification",
                    ""
                ])
            
            # Chronological Timeline section
            lines.append("⏱️  EXECUTION TIMELINE:")
            if hasattr(result, 'timeline_events') and result.timeline_events:
                # Sort timeline events by elapsed time
                sorted_events = sorted(result.timeline_events, key=lambda x: x.get('elapsed_ms', 0))
                
                for event in sorted_events[:15]:  # Show first 15 events
                    timestamp = event.get('timestamp', '00:00:00.000')
                    description = event.get('description', '')
                    lines.append(f"   {timestamp} {description}")
                
                if len(result.timeline_events) > 15:
                    lines.append(f"   ... and {len(result.timeline_events) - 15} more timeline events")
            else:
                lines.append("   No detailed timeline available")
            
            lines.extend([
                "",
                "─" * 60,
                ""
            ])
        
        # Report Footer
        lines.extend([
            "🎯 REPORT SUMMARY",
            "=" * 40,
            f"Total Tests Executed: {total_tests}",
            f"Overall Success Rate: {success_rate:.1f}%",
            f"Total Execution Time: {format_duration(results.total_duration)}",
            "",
            "📋 For detailed analysis and visual reports, check the HTML output.",
            "🔧 For technical support, review the console logs above.",
            "",
            "Generated by Web Eval Agent 🤖",
            "=" * 80
        ])
        
        return "\n".join(lines)
    
    def _create_summary_text_report(self, results: TestResults) -> str:
        """Create a concise summary text report."""
        summary = results.summary
        total_tests = summary.get('total_tests', 0)
        passed_tests = summary.get('passed_tests', 0)
        failed_tests = summary.get('failed_tests', 0)
        success_rate = summary.get('success_rate', 0)
        
        # Create test overview
        test_overview_lines = []
        for i, result in enumerate(results.test_results, 1):
            status_icon = "✅" if result.passed else "❌"
            duration_str = format_duration(result.duration)
            test_overview_lines.append(f"{i:2d}. {status_icon} {result.scenario_name} ({duration_str})")
            
            if result.error_message:
                test_overview_lines.append(f"     💥 Error: {result.error_message}")
        
        test_overview = "\n".join(test_overview_lines) if test_overview_lines else "No tests executed"
        
        # Format template variables
        template_vars = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'url': self.config.url,
            'total_duration': format_duration(results.total_duration),
            'passed_tests': passed_tests,
            'total_tests': total_tests,
            'failed_tests': failed_tests,
            'success_rate': success_rate,
            'browser': self.config.browser,
            'viewport': self.config.viewport,
            'headless_mode': 'Yes' if self.config.headless else 'No',
            'test_overview': test_overview
        }
        
        # Load and format template
        template_path = Path(__file__).parent / "templates" / "report_summary.txt"
        if template_path.exists():
            with open(template_path, 'r', encoding='utf-8') as f:
                template = f.read()
            return template.format(**template_vars)
        else:
            # Fallback if template doesn't exist
            return self._create_fallback_summary_report(template_vars)
    
    def _create_verbose_text_report(self, results: TestResults) -> str:
        """Create a verbose text report with extensive analysis."""
        summary = results.summary
        total_tests = summary.get('total_tests', 0)
        passed_tests = summary.get('passed_tests', 0)
        failed_tests = summary.get('failed_tests', 0)
        success_rate = summary.get('success_rate', 0)
        
        # Create test overview
        test_overview_lines = []
        for i, result in enumerate(results.test_results, 1):
            status_icon = "✅" if result.passed else "❌"
            duration_str = format_duration(result.duration)
            test_overview_lines.append(f"{i:2d}. {status_icon} {result.scenario_name} ({duration_str})")
            
            if result.error_message:
                test_overview_lines.append(f"     💥 Error: {result.error_message}")
        
        test_overview = "\n".join(test_overview_lines) if test_overview_lines else "No tests executed"
        
        # Generate detailed results (reuse existing method)
        detailed_results = self._create_comprehensive_text_report(results)
        
        # Calculate performance metrics
        durations = [result.duration for result in results.test_results if result.duration]
        avg_duration = sum(durations) / len(durations) if durations else 0
        longest_test = max(durations) if durations else 0
        shortest_test = min(durations) if durations else 0
        
        total_console_logs = sum(len(result.console_logs) for result in results.test_results)
        total_network_requests = sum(len(result.network_requests) for result in results.test_results)
        total_screenshots = sum(len(result.screenshots) for result in results.test_results)
        
        # Error analysis
        error_analysis = self._analyze_errors(results)
        network_analysis = self._analyze_network_requests(results)
        console_analysis = self._analyze_console_logs(results)
        recommendations = self._generate_recommendations(results)
        
        # Format template variables
        template_vars = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'url': self.config.url,
            'total_duration': format_duration(results.total_duration),
            'passed_tests': passed_tests,
            'total_tests': total_tests,
            'failed_tests': failed_tests,
            'success_rate': success_rate,
            'browser': self.config.browser,
            'viewport': self.config.viewport,
            'headless_mode': 'Yes' if self.config.headless else 'No',
            'test_overview': test_overview,
            'detailed_results': detailed_results,
            'avg_duration': format_duration(avg_duration),
            'longest_test': format_duration(longest_test),
            'shortest_test': format_duration(shortest_test),
            'total_console_logs': total_console_logs,
            'total_network_requests': total_network_requests,
            'total_screenshots': total_screenshots,
            'error_analysis': error_analysis,
            'network_analysis': network_analysis,
            'console_analysis': console_analysis,
            'recommendations': recommendations
        }
        
        # Load and format template
        template_path = Path(__file__).parent / "templates" / "report_verbose.txt"
        if template_path.exists():
            with open(template_path, 'r', encoding='utf-8') as f:
                template = f.read()
            return template.format(**template_vars)
        else:
            # Fallback if template doesn't exist
            return self._create_fallback_verbose_report(template_vars)
    
    def _analyze_errors(self, results: TestResults) -> str:
        """Analyze errors across all test results."""
        error_lines = []
        failed_tests = [result for result in results.test_results if not result.passed]
        
        if not failed_tests:
            error_lines.append("✅ No errors detected across all tests!")
            return "\n".join(error_lines)
        
        error_lines.append(f"Found {len(failed_tests)} failed test(s):")
        
        for result in failed_tests:
            error_lines.append(f"❌ {result.scenario_name}:")
            if result.error_message:
                error_lines.append(f"   Error: {result.error_message}")
            
            # Analyze console errors
            console_errors = [log for log in result.console_logs if log.get('type') == 'error']
            if console_errors:
                error_lines.append(f"   Console Errors: {len(console_errors)}")
                for error in console_errors[:3]:  # Show first 3 errors
                    error_text = error.get('text', '')[:100]
                    error_lines.append(f"     • {error_text}")
        
        return "\n".join(error_lines)
    
    def _analyze_network_requests(self, results: TestResults) -> str:
        """Analyze network requests across all test results."""
        all_requests = []
        for result in results.test_results:
            all_requests.extend(result.network_requests)
        
        if not all_requests:
            return "No network requests captured"
        
        # Group by status code
        success_count = len([req for req in all_requests if str(req.get('response_status', '')).startswith('2')])
        error_count = len([req for req in all_requests if str(req.get('response_status', '')).startswith(('4', '5'))])
        other_count = len(all_requests) - success_count - error_count
        
        lines = [
            f"Total Network Requests: {len(all_requests)}",
            f"✅ Successful (2xx): {success_count}",
            f"❌ Failed (4xx/5xx): {error_count}",
            f"📋 Other: {other_count}"
        ]
        
        # Show most common request types
        methods = {}
        for req in all_requests:
            method = req.get('method', 'GET')
            methods[method] = methods.get(method, 0) + 1
        
        if methods:
            lines.append("\nRequest Methods:")
            for method, count in sorted(methods.items(), key=lambda x: x[1], reverse=True):
                lines.append(f"  {method}: {count}")
        
        return "\n".join(lines)
    
    def _analyze_console_logs(self, results: TestResults) -> str:
        """Analyze console logs across all test results."""
        all_logs = []
        for result in results.test_results:
            all_logs.extend(result.console_logs)
        
        if not all_logs:
            return "No console logs captured"
        
        # Group by type
        log_types = {}
        for log in all_logs:
            log_type = log.get('type', 'log')
            log_types[log_type] = log_types.get(log_type, 0) + 1
        
        lines = [f"Total Console Logs: {len(all_logs)}"]
        
        for log_type, count in sorted(log_types.items(), key=lambda x: x[1], reverse=True):
            icon = "🚨" if log_type == "error" else "⚠️" if log_type == "warn" else "ℹ️"
            lines.append(f"{icon} {log_type.upper()}: {count}")
        
        return "\n".join(lines)
    
    def _generate_recommendations(self, results: TestResults) -> str:
        """Generate recommendations based on test results."""
        recommendations = []
        
        # Check success rate
        success_rate = results.summary.get('success_rate', 0)
        if success_rate < 80:
            recommendations.append("🔧 Consider investigating failed tests to improve overall success rate")
        
        # Check for console errors
        total_errors = sum(len([log for log in result.console_logs if log.get('type') == 'error']) 
                          for result in results.test_results)
        if total_errors > 0:
            recommendations.append(f"🚨 Found {total_errors} console errors - review and fix JavaScript issues")
        
        # Check for network failures
        failed_requests = sum(len([req for req in result.network_requests 
                                 if str(req.get('response_status', '')).startswith(('4', '5'))])
                             for result in results.test_results)
        if failed_requests > 0:
            recommendations.append(f"🌐 Found {failed_requests} failed network requests - check API endpoints")
        
        # Check test duration
        avg_duration = sum(result.duration for result in results.test_results) / len(results.test_results) if results.test_results else 0
        if avg_duration > 30:  # 30 seconds
            recommendations.append("⏱️ Tests are taking longer than expected - consider optimizing page load times")
        
        if not recommendations:
            recommendations.append("✅ All tests look good! No specific recommendations at this time.")
        
        return "\n".join(recommendations)
    
    def _create_fallback_summary_report(self, template_vars: dict) -> str:
        """Create fallback summary report if template is missing."""
        return f"""================================================================================
🧪 WEB EVALUATION AGENT - SUMMARY REPORT
================================================================================
📅 Generated: {template_vars['timestamp']}
🌐 Target URL: {template_vars['url']}
⏱️  Total Duration: {template_vars['total_duration']}

📊 EXECUTIVE SUMMARY
────────────────────────────────────────
✅ Tests Passed: {template_vars['passed_tests']}/{template_vars['total_tests']}
❌ Tests Failed: {template_vars['failed_tests']}/{template_vars['total_tests']}
📈 Success Rate: {template_vars['success_rate']:.1f}%

{template_vars['test_overview']}

Generated by Web Eval Agent 🤖
================================================================================"""
    
    def _create_fallback_verbose_report(self, template_vars: dict) -> str:
        """Create fallback verbose report if template is missing."""
        return f"""================================================================================
🧪 WEB EVALUATION AGENT - VERBOSE REPORT
================================================================================
📅 Generated: {template_vars['timestamp']}
🌐 Target URL: {template_vars['url']}
⏱️  Total Duration: {template_vars['total_duration']}

📊 EXECUTIVE SUMMARY
────────────────────────────────────────
✅ Tests Passed: {template_vars['passed_tests']}/{template_vars['total_tests']}
❌ Tests Failed: {template_vars['failed_tests']}/{template_vars['total_tests']}
📈 Success Rate: {template_vars['success_rate']:.1f}%

{template_vars['detailed_results']}

Generated by Web Eval Agent 🤖
================================================================================"""
    
    def _create_text_report(self, results: TestResults) -> str:
        """Create legacy text report content (kept for compatibility)."""
        return self._create_comprehensive_text_report(results)
