"""
Enhanced CLI Interface

Advanced command-line interface for the enhanced web evaluation agent
with comprehensive options and professional output.
"""

import asyncio
import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
import argparse
import logging

from ..config.enhanced_config import EnhancedConfig
from ..core.enhanced_executor import EnhancedTestExecutor, EnhancedTestConfig
from ..reporting.intelligent_reporter import TestScenarioResult

logger = logging.getLogger(__name__)


class EnhancedCLI:
    """Enhanced command-line interface for web evaluation agent."""
    
    def __init__(self):
        self.config: Optional[EnhancedConfig] = None
        self.executor: Optional[EnhancedTestExecutor] = None
        
    def create_parser(self) -> argparse.ArgumentParser:
        """Create the argument parser with all options."""
        parser = argparse.ArgumentParser(
            prog='web-eval',
            description='🚀 Enhanced Web Evaluation Agent - Professional-grade web testing with AI agents',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Basic usage
  web-eval --url https://example.com --instructions test-scenarios/basic/navigation-test.md
  
  # Advanced usage with custom settings
  web-eval --url https://example.com --instructions test.md --agents 5 --timeout 120 --headless false
  
  # Using configuration profiles
  web-eval --url https://example.com --instructions test.md --profile ci_testing
  
  # Performance testing
  web-eval --url https://example.com --instructions test.md --profile performance_testing --output-format html
  
  # Generate configuration file
  web-eval --generate-config --output config.json
  
  # Use custom configuration
  web-eval --url https://example.com --instructions test.md --config config.json

Environment Variables:
  GEMINI_API_KEY          Google Gemini API key (required)
  WEB_EVAL_ENV           Environment: development, staging, production
  WEB_EVAL_DEBUG         Enable debug mode: true/false
  WEB_EVAL_HEADLESS      Run in headless mode: true/false
  WEB_EVAL_MAX_AGENTS    Maximum number of agents: 1-20
  WEB_EVAL_TIMEOUT       Timeout per agent in seconds: 10-300
            """
        )
        
        # Core arguments
        parser.add_argument(
            '--url',
            type=str,
            help='🌐 Target URL to evaluate (required for testing)'
        )
        
        parser.add_argument(
            '--instructions',
            type=str,
            help='📋 Path to test instructions file (markdown format)'
        )
        
        # Agent configuration
        agent_group = parser.add_argument_group('🤖 Agent Configuration')
        agent_group.add_argument(
            '--agents',
            type=int,
            default=3,
            help='Number of agents to deploy (default: 3, max: 20)'
        )
        
        agent_group.add_argument(
            '--timeout',
            type=int,
            default=60,
            help='Timeout per agent in seconds (default: 60)'
        )
        
        agent_group.add_argument(
            '--retries',
            type=int,
            default=3,
            help='Maximum retries per agent (default: 3)'
        )
        
        agent_group.add_argument(
            '--parallel',
            type=bool,
            default=True,
            help='Enable parallel agent execution (default: true)'
        )
        
        # Browser configuration
        browser_group = parser.add_argument_group('🌐 Browser Configuration')
        browser_group.add_argument(
            '--headless',
            type=str,
            choices=['true', 'false'],
            default='true',
            help='Run browser in headless mode (default: true)'
        )
        
        browser_group.add_argument(
            '--viewport',
            type=str,
            default='1920x1080',
            help='Browser viewport size (default: 1920x1080)'
        )
        
        browser_group.add_argument(
            '--user-agent',
            type=str,
            help='Custom user agent string'
        )
        
        browser_group.add_argument(
            '--slow-mo',
            type=int,
            default=0,
            help='Slow motion delay in milliseconds (default: 0)'
        )
        
        # Monitoring configuration
        monitoring_group = parser.add_argument_group('📊 Monitoring Configuration')
        monitoring_group.add_argument(
            '--console-monitoring',
            type=str,
            choices=['true', 'false'],
            default='true',
            help='Enable console monitoring (default: true)'
        )
        
        monitoring_group.add_argument(
            '--network-monitoring',
            type=str,
            choices=['true', 'false'],
            default='true',
            help='Enable network monitoring (default: true)'
        )
        
        monitoring_group.add_argument(
            '--performance-monitoring',
            type=str,
            choices=['true', 'false'],
            default='true',
            help='Enable performance monitoring (default: true)'
        )
        
        monitoring_group.add_argument(
            '--screenshots',
            type=str,
            choices=['true', 'false'],
            default='true',
            help='Take screenshots on failure (default: true)'
        )
        
        # Reporting configuration
        reporting_group = parser.add_argument_group('📄 Reporting Configuration')
        reporting_group.add_argument(
            '--output-format',
            type=str,
            choices=['json', 'html', 'markdown', 'pdf'],
            default='json',
            help='Report output format (default: json)'
        )
        
        reporting_group.add_argument(
            '--output-dir',
            type=str,
            default='./reports',
            help='Output directory for reports (default: ./reports)'
        )
        
        reporting_group.add_argument(
            '--report-name',
            type=str,
            help='Custom report filename (auto-generated if not specified)'
        )
        
        reporting_group.add_argument(
            '--include-raw-data',
            type=str,
            choices=['true', 'false'],
            default='false',
            help='Include raw monitoring data in report (default: false)'
        )
        
        # Configuration management
        config_group = parser.add_argument_group('⚙️ Configuration Management')
        config_group.add_argument(
            '--config',
            type=str,
            help='Path to configuration file (JSON format)'
        )
        
        config_group.add_argument(
            '--profile',
            type=str,
            choices=['development', 'ci_testing', 'production_monitoring', 'performance_testing', 'accessibility_testing'],
            help='Use predefined configuration profile'
        )
        
        config_group.add_argument(
            '--generate-config',
            action='store_true',
            help='Generate sample configuration file and exit'
        )
        
        config_group.add_argument(
            '--save-config',
            type=str,
            help='Save current configuration to file'
        )
        
        # Environment and debugging
        debug_group = parser.add_argument_group('🐛 Debug and Environment')
        debug_group.add_argument(
            '--debug',
            action='store_true',
            help='Enable debug mode with verbose logging'
        )
        
        debug_group.add_argument(
            '--log-level',
            type=str,
            choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
            default='INFO',
            help='Set logging level (default: INFO)'
        )
        
        debug_group.add_argument(
            '--environment',
            type=str,
            choices=['development', 'staging', 'production'],
            default='development',
            help='Set environment mode (default: development)'
        )
        
        debug_group.add_argument(
            '--dry-run',
            action='store_true',
            help='Validate configuration and exit without running tests'
        )
        
        # Utility options
        parser.add_argument(
            '--version',
            action='version',
            version='Enhanced Web Evaluation Agent v2.0.0'
        )
        
        parser.add_argument(
            '--list-profiles',
            action='store_true',
            help='List available configuration profiles and exit'
        )
        
        return parser
        
    def parse_args(self, args: Optional[List[str]] = None) -> argparse.Namespace:
        """Parse command line arguments."""
        parser = self.create_parser()
        return parser.parse_args(args)
        
    def load_configuration(self, args: argparse.Namespace) -> EnhancedConfig:
        """Load and configure the enhanced configuration."""
        # Start with default configuration
        if args.config:
            # Load from file
            config = EnhancedConfig.load_from_file(args.config)
        else:
            # Create default configuration
            config = EnhancedConfig()
            
        # Apply profile if specified
        if args.profile:
            config.apply_profile(args.profile)
            
        # Override with command line arguments
        self._apply_cli_overrides(config, args)
        
        return config
        
    def _apply_cli_overrides(self, config: EnhancedConfig, args: argparse.Namespace) -> None:
        """Apply command line argument overrides to configuration."""
        # Core settings
        if args.debug:
            config.debug = True
            config.log_level = 'DEBUG'
        if args.log_level:
            config.log_level = args.log_level
        if args.environment:
            config.environment = args.environment
            
        # Browser settings
        if args.headless:
            config.browser.headless = args.headless.lower() == 'true'
        if args.viewport:
            try:
                width, height = map(int, args.viewport.split('x'))
                config.browser.viewport_width = width
                config.browser.viewport_height = height
            except ValueError:
                logger.warning(f"Invalid viewport format: {args.viewport}")
        if args.user_agent:
            config.browser.user_agent = args.user_agent
        if args.slow_mo:
            config.browser.slow_mo = args.slow_mo
            
        # Agent settings
        if args.agents:
            config.agent.default_agents = min(args.agents, config.agent.max_agents)
        if args.timeout:
            config.agent.timeout_per_agent = args.timeout
        if args.retries:
            config.agent.max_retries = args.retries
        if hasattr(args, 'parallel'):
            config.agent.parallel_execution = args.parallel
            
        # Monitoring settings
        if args.console_monitoring:
            config.monitoring.console_monitoring = args.console_monitoring.lower() == 'true'
        if args.network_monitoring:
            config.monitoring.network_monitoring = args.network_monitoring.lower() == 'true'
        if args.performance_monitoring:
            config.monitoring.performance_monitoring = args.performance_monitoring.lower() == 'true'
        if args.screenshots:
            config.monitoring.screenshot_on_failure = args.screenshots.lower() == 'true'
            
        # Reporting settings
        if args.output_format:
            config.reporting.output_format = args.output_format
        if args.output_dir:
            config.reporting.report_directory = args.output_dir
        if args.include_raw_data:
            config.reporting.export_raw_data = args.include_raw_data.lower() == 'true'
            
    def load_test_scenarios(self, instructions_path: str) -> List[Dict[str, Any]]:
        """Load test scenarios from instructions file."""
        instructions_file = Path(instructions_path)
        
        if not instructions_file.exists():
            raise FileNotFoundError(f"Instructions file not found: {instructions_path}")
            
        # Read instructions file
        with open(instructions_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Parse markdown content to extract scenarios
        scenarios = self._parse_markdown_scenarios(content)
        
        if not scenarios:
            # Create single scenario from entire content
            scenarios = [{
                'name': instructions_file.stem.replace('-', ' ').title(),
                'description': content,
                'success_criteria': ['Complete the test successfully']
            }]
            
        logger.info(f"📋 Loaded {len(scenarios)} test scenario(s) from {instructions_path}")
        return scenarios
        
    def _parse_markdown_scenarios(self, content: str) -> List[Dict[str, Any]]:
        """Parse markdown content to extract test scenarios."""
        scenarios = []
        lines = content.split('\n')
        current_scenario = None
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            # Check for scenario headers (## or ###)
            if line.startswith('## ') or line.startswith('### '):
                if current_scenario:
                    scenarios.append(current_scenario)
                    
                current_scenario = {
                    'name': line.lstrip('#').strip(),
                    'description': '',
                    'success_criteria': []
                }
                current_section = 'description'
                continue
                
            # Check for success criteria section
            if line.lower().startswith('success criteria') or line.lower().startswith('expected results'):
                current_section = 'success_criteria'
                continue
                
            # Add content to current section
            if current_scenario and line:
                if current_section == 'description':
                    if current_scenario['description']:
                        current_scenario['description'] += '\n'
                    current_scenario['description'] += line
                elif current_section == 'success_criteria' and line.startswith('- '):
                    current_scenario['success_criteria'].append(line[2:])
                    
        # Add last scenario
        if current_scenario:
            scenarios.append(current_scenario)
            
        return scenarios
        
    def print_banner(self) -> None:
        """Print application banner."""
        banner = """
🚀 Enhanced Web Evaluation Agent v2.0.0
========================================
Professional-grade web testing with AI agents
        """
        print(banner)
        
    def print_configuration_summary(self, config: EnhancedConfig) -> None:
        """Print configuration summary."""
        summary = config.get_summary()
        
        print("\n⚙️  Configuration Summary:")
        print(f"   Environment: {summary['environment']}")
        print(f"   Debug Mode: {summary['debug']}")
        print(f"   API Key: {'✅ Configured' if summary['api_key_configured'] else '❌ Missing'}")
        print(f"   Browser: {'Headless' if summary['browser_headless'] else 'Visible'}")
        print(f"   Max Agents: {summary['max_agents']}")
        print(f"   Output Format: {summary['output_format']}")
        
        monitoring = summary['monitoring_enabled']
        enabled_monitoring = [k for k, v in monitoring.items() if v]
        print(f"   Monitoring: {', '.join(enabled_monitoring) if enabled_monitoring else 'None'}")
        
    def print_test_progress(self, current: int, total: int, scenario_name: str) -> None:
        """Print test progress."""
        progress = (current / total) * 100
        bar_length = 30
        filled_length = int(bar_length * current // total)
        bar = '█' * filled_length + '-' * (bar_length - filled_length)
        
        print(f"\r🧪 Progress: |{bar}| {progress:.1f}% ({current}/{total}) - {scenario_name[:40]}...", end='', flush=True)
        
    def print_results_summary(self, results: Dict[str, Any]) -> None:
        """Print test results summary."""
        print("\n\n📊 Test Results Summary:")
        print("=" * 50)
        
        executive_summary = results.get('report', {}).get('executive_summary', {})
        
        # Overall status
        status = executive_summary.get('overall_status', 'Unknown')
        status_emoji = '✅' if 'passed' in status.lower() else '❌' if 'failed' in status.lower() else '⚠️'
        print(f"   Overall Status: {status_emoji} {status}")
        
        # Test counts
        total = executive_summary.get('total_scenarios', 0)
        passed = executive_summary.get('passed_scenarios', 0)
        failed = executive_summary.get('failed_scenarios', 0)
        
        print(f"   Total Scenarios: {total}")
        print(f"   ✅ Passed: {passed}")
        print(f"   ❌ Failed: {failed}")
        
        # Issues
        critical = executive_summary.get('critical_issues', 0)
        high_priority = executive_summary.get('high_priority_issues', 0)
        
        if critical > 0:
            print(f"   🚨 Critical Issues: {critical}")
        if high_priority > 0:
            print(f"   ⚠️  High Priority Issues: {high_priority}")
            
        # Scores
        perf_score = executive_summary.get('performance_score', 0)
        acc_score = executive_summary.get('accessibility_score', 0)
        sec_score = executive_summary.get('security_score', 0)
        
        print(f"   Performance Score: {perf_score:.1f}/100")
        print(f"   Accessibility Score: {acc_score:.1f}/100")
        print(f"   Security Score: {sec_score:.1f}/100")
        
        # Key findings
        findings = executive_summary.get('key_findings', [])
        if findings:
            print("\n🔍 Key Findings:")
            for finding in findings[:3]:  # Show top 3
                print(f"   • {finding}")
                
        # Recommended actions
        actions = executive_summary.get('recommended_actions', [])
        if actions:
            print("\n💡 Recommended Actions:")
            for action in actions[:3]:  # Show top 3
                print(f"   • {action}")
                
    def save_report(self, results: Dict[str, Any], config: EnhancedConfig, report_name: Optional[str] = None) -> str:
        """Save test report to file."""
        # Create output directory
        output_dir = Path(config.reporting.report_directory)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate report filename
        if not report_name:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            report_name = f"web_eval_report_{timestamp}"
            
        # Save based on format
        if config.reporting.output_format == 'json':
            filepath = output_dir / f"{report_name}.json"
            with open(filepath, 'w') as f:
                json.dump(results, f, indent=2, default=str)
        elif config.reporting.output_format == 'markdown':
            filepath = output_dir / f"{report_name}.md"
            markdown_content = self._generate_markdown_report(results)
            with open(filepath, 'w') as f:
                f.write(markdown_content)
        else:
            # Default to JSON for unsupported formats
            filepath = output_dir / f"{report_name}.json"
            with open(filepath, 'w') as f:
                json.dump(results, f, indent=2, default=str)
                
        return str(filepath)
        
    def _generate_markdown_report(self, results: Dict[str, Any]) -> str:
        """Generate markdown report content."""
        report = results.get('report', {})
        executive_summary = report.get('executive_summary', {})
        
        markdown = f"""# Web Evaluation Report
        
Generated: {report.get('report_metadata', {}).get('generated_at', 'Unknown')}

## Executive Summary

**Overall Status:** {executive_summary.get('overall_status', 'Unknown')}

### Test Results
- Total Scenarios: {executive_summary.get('total_scenarios', 0)}
- Passed: {executive_summary.get('passed_scenarios', 0)}
- Failed: {executive_summary.get('failed_scenarios', 0)}

### Issues Summary
- Critical Issues: {executive_summary.get('critical_issues', 0)}
- High Priority Issues: {executive_summary.get('high_priority_issues', 0)}

### Quality Scores
- Performance: {executive_summary.get('performance_score', 0):.1f}/100
- Accessibility: {executive_summary.get('accessibility_score', 0):.1f}/100
- Security: {executive_summary.get('security_score', 0):.1f}/100

## Key Findings
"""
        
        for finding in executive_summary.get('key_findings', []):
            markdown += f"- {finding}\n"
            
        markdown += "\n## Recommended Actions\n"
        
        for action in executive_summary.get('recommended_actions', []):
            markdown += f"- {action}\n"
            
        return markdown
        
    async def run(self, args: Optional[List[str]] = None) -> int:
        """Main CLI execution method."""
        try:
            # Parse arguments
            parsed_args = self.parse_args(args)
            
            # Handle utility commands
            if parsed_args.generate_config:
                return self._handle_generate_config(parsed_args)
            if parsed_args.list_profiles:
                return self._handle_list_profiles()
                
            # Validate required arguments
            if not parsed_args.url:
                print("❌ Error: --url is required for testing")
                return 1
                
            if not parsed_args.instructions:
                print("❌ Error: --instructions is required for testing")
                return 1
                
            # Print banner
            self.print_banner()
            
            # Load configuration
            config = self.load_configuration(parsed_args)
            
            # Validate API key
            if not config.validate_api_key():
                print("❌ Error: Invalid or missing GEMINI_API_KEY")
                print("   Set the GEMINI_API_KEY environment variable with your Google Gemini API key")
                return 1
                
            # Print configuration summary
            self.print_configuration_summary(config)
            
            # Handle dry run
            if parsed_args.dry_run:
                print("\n✅ Configuration validated successfully (dry run)")
                return 0
                
            # Save configuration if requested
            if parsed_args.save_config:
                config.save_to_file(parsed_args.save_config)
                
            # Load test scenarios
            scenarios = self.load_test_scenarios(parsed_args.instructions)
            
            # Create enhanced test executor
            test_config = EnhancedTestConfig(
                api_key=config.api_key,
                timeout=config.agent.timeout_per_agent,
                headless=config.browser.headless,
                agents=config.agent.default_agents,
                max_retries=config.agent.max_retries,
                screenshot_on_failure=config.monitoring.screenshot_on_failure,
                detailed_logging=config.monitoring.detailed_logging,
                performance_monitoring=config.monitoring.performance_monitoring,
                console_monitoring=config.monitoring.console_monitoring,
                network_monitoring=config.monitoring.network_monitoring,
                interaction_monitoring=config.monitoring.interaction_monitoring
            )
            
            self.executor = EnhancedTestExecutor(test_config)
            
            # Initialize and run tests
            print(f"\n🚀 Starting enhanced web evaluation for {parsed_args.url}")
            print(f"📋 Testing {len(scenarios)} scenario(s) with {config.agent.default_agents} agent(s)")
            
            # Initialize executor
            init_result = await self.executor.initialize(parsed_args.url)
            if not init_result['success']:
                print(f"❌ Failed to initialize: {init_result.get('error', 'Unknown error')}")
                return 1
                
            # Execute test scenarios
            results = await self.executor.execute_test_scenarios(scenarios)
            
            # Print results summary
            self.print_results_summary(results)
            
            # Save report
            report_path = self.save_report(results, config, parsed_args.report_name)
            print(f"\n📄 Report saved: {report_path}")
            
            # Cleanup
            await self.executor.cleanup()
            
            # Return appropriate exit code
            executive_summary = results.get('report', {}).get('executive_summary', {})
            critical_issues = executive_summary.get('critical_issues', 0)
            failed_scenarios = executive_summary.get('failed_scenarios', 0)
            
            if critical_issues > 0:
                return 2  # Critical issues found
            elif failed_scenarios > 0:
                return 1  # Some tests failed
            else:
                return 0  # All tests passed
                
        except KeyboardInterrupt:
            print("\n\n⚠️  Test execution interrupted by user")
            if self.executor:
                await self.executor.cleanup()
            return 130
            
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            if config and config.debug:
                import traceback
                traceback.print_exc()
            if self.executor:
                await self.executor.cleanup()
            return 1
            
    def _handle_generate_config(self, args: argparse.Namespace) -> int:
        """Handle --generate-config command."""
        config = EnhancedConfig()
        output_path = args.output or 'web-eval-config.json'
        config.save_to_file(output_path)
        print(f"✅ Sample configuration generated: {output_path}")
        return 0
        
    def _handle_list_profiles(self) -> int:
        """Handle --list-profiles command."""
        config = EnhancedConfig()
        profiles = config.get_profile_presets()
        
        print("📋 Available Configuration Profiles:")
        print("=" * 40)
        
        for profile_name, settings in profiles.items():
            print(f"\n🔧 {profile_name}:")
            for key, value in settings.items():
                if key != 'custom_settings':
                    print(f"   {key}: {value}")
                    
        return 0


def main():
    """Main entry point for the CLI."""
    cli = EnhancedCLI()
    exit_code = asyncio.run(cli.run())
    sys.exit(exit_code)


if __name__ == '__main__':
    main()

