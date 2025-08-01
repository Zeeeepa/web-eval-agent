#!/usr/bin/env python3
"""
Enhanced Tool Handlers for Integrated Services
Extends existing web-eval-agent with comprehensive integration capabilities
"""

import asyncio
import logging
import json
from typing import Dict, Any, Optional, List
from mcp.types import TextContent

from .config_manager import get_config_manager
from .service_abstractions import get_service_manager
from .workflow_orchestrator import get_workflow_orchestrator
from .grainchain_integration import get_grainchain_integration
from .graph_sitter_integration import get_graph_sitter_integration
from .tool_handlers import handle_web_evaluation, handle_setup_browser_state

logger = logging.getLogger(__name__)

async def handle_comprehensive_analysis(
    repository_path: str,
    analysis_type: str = "full",
    include_ui_validation: bool = True,
    user_requirements: Optional[str] = None
) -> str:
    """
    Comprehensive analysis combining all integrated services
    
    Args:
        repository_path: Path to repository or URL to analyze
        analysis_type: Type of analysis ("full", "code_only", "ui_only", "security_only")
        include_ui_validation: Whether to include UI validation
        user_requirements: Additional user requirements
    
    Returns:
        Comprehensive analysis report
    """
    
    try:
        logger.info(f"Starting comprehensive analysis for {repository_path}")
        
        # Initialize services
        config_manager = get_config_manager()
        orchestrator = get_workflow_orchestrator()
        
        # Create mock webhook event for analysis
        webhook_event = {
            "event_type": "analysis_request",
            "data": {
                "repository": {"full_name": repository_path},
                "analysis_type": analysis_type,
                "include_ui_validation": include_ui_validation
            }
        }
        
        # Execute workflow
        workflow_result = await orchestrator.execute_pr_workflow(
            webhook_event=webhook_event,
            user_requirements=user_requirements
        )
        
        # Generate formatted report
        report = _format_comprehensive_report(workflow_result)
        
        logger.info(f"Comprehensive analysis completed with status: {workflow_result.status.value}")
        
        return report
        
    except Exception as e:
        logger.error(f"Comprehensive analysis failed: {e}")
        return f"❌ Comprehensive analysis failed: {str(e)}"

async def handle_code_analysis_with_runtime_errors(
    code_path: str,
    languages: Optional[List[str]] = None,
    include_serena: bool = True
) -> str:
    """
    Advanced code analysis with runtime error detection using graph-sitter and Serena
    
    Args:
        code_path: Path to code to analyze
        languages: List of languages to analyze
        include_serena: Whether to include Serena LSP analysis
    
    Returns:
        Detailed code analysis report
    """
    
    try:
        logger.info(f"Starting code analysis for {code_path}")
        
        graph_sitter = get_graph_sitter_integration()
        
        # Perform comprehensive code analysis
        analysis_result = await graph_sitter.analyze_code(
            code_path=code_path,
            languages=languages,
            include_serena=include_serena
        )
        
        # Get runtime errors specifically
        runtime_errors = await graph_sitter.get_runtime_errors(code_path)
        
        # Get SWE-bench metrics
        swe_metrics = await graph_sitter.analyze_swe_bench_features(code_path)
        
        # Format report
        report_parts = [
            "🔍 **Advanced Code Analysis Report**",
            f"📁 **Path**: {code_path}",
            f"⏱️ **Analysis Time**: {analysis_result.analysis_time:.2f}s",
            f"📊 **Files Analyzed**: {analysis_result.files_analyzed}",
            f"📏 **Lines Analyzed**: {analysis_result.lines_analyzed}",
            ""
        ]
        
        # Language statistics
        if analysis_result.language_stats:
            report_parts.extend([
                "📈 **Language Distribution**:",
                *[f"  - {lang}: {count} files" for lang, count in analysis_result.language_stats.items()],
                ""
            ])
        
        # Errors and warnings
        if analysis_result.errors:
            report_parts.extend([
                f"❌ **Errors Found ({len(analysis_result.errors)})**:",
                *[f"  - {error.file_path}:{error.line_number} - {error.message}" 
                  for error in analysis_result.errors[:10]],  # Limit to first 10
                ""
            ])
        
        if analysis_result.warnings:
            report_parts.extend([
                f"⚠️ **Warnings Found ({len(analysis_result.warnings)})**:",
                *[f"  - {warning.file_path}:{warning.line_number} - {warning.message}" 
                  for warning in analysis_result.warnings[:10]],  # Limit to first 10
                ""
            ])
        
        # Runtime errors from Serena
        if runtime_errors:
            report_parts.extend([
                f"🚨 **Runtime Errors Detected ({len(runtime_errors)})**:",
                *[f"  - {error.file_path}:{error.line_number} - {error.message}" 
                  for error in runtime_errors[:5]],  # Limit to first 5
                ""
            ])
        
        # SWE-bench metrics
        if swe_metrics:
            report_parts.extend([
                "📊 **SWE-bench Metrics**:",
                f"  - Complexity Score: {swe_metrics.get('complexity_score', 0):.1f}/100",
                f"  - Maintainability Score: {swe_metrics.get('maintainability_score', 0):.1f}/100",
                f"  - Error Density: {swe_metrics.get('error_density', 0):.3f}",
                f"  - Dependencies: {swe_metrics.get('dependency_count', 0)}",
                ""
            ])
        
        # Dependencies
        if analysis_result.dependencies:
            report_parts.extend([
                f"📦 **Dependencies ({len(analysis_result.dependencies)})**:",
                *[f"  - {dep}" for dep in analysis_result.dependencies[:10]],
                ""
            ])
        
        # Recommendations
        recommendations = _generate_code_recommendations(analysis_result, runtime_errors, swe_metrics)
        if recommendations:
            report_parts.extend([
                "💡 **Recommendations**:",
                *[f"  - {rec}" for rec in recommendations],
                ""
            ])
        
        report_parts.append("✅ **Code analysis completed successfully**")
        
        return "\n".join(report_parts)
        
    except Exception as e:
        logger.error(f"Code analysis failed: {e}")
        return f"❌ Code analysis failed: {str(e)}"

async def handle_secure_code_execution(
    code: str,
    language: str = "python",
    files: Optional[Dict[str, str]] = None,
    security_level: str = "high"
) -> str:
    """
    Secure code execution using grainchain with security validation
    
    Args:
        code: Code to execute
        language: Programming language
        files: Additional files to include
        security_level: Security level ("low", "medium", "high")
    
    Returns:
        Execution results with security analysis
    """
    
    try:
        logger.info(f"Starting secure code execution for {language} code")
        
        grainchain = get_grainchain_integration()
        
        # First, validate code security
        security_result = await grainchain.validate_code_security(code, language)
        
        report_parts = [
            "🛡️ **Secure Code Execution Report**",
            f"🔒 **Security Level**: {security_level}",
            f"⚠️ **Risk Level**: {security_result.get('risk_level', 'unknown')}",
            f"✅ **Safe to Execute**: {security_result.get('safe_to_execute', False)}",
            ""
        ]
        
        # Security issues
        security_issues = security_result.get('security_issues', [])
        if security_issues:
            report_parts.extend([
                f"🚨 **Security Issues Found ({len(security_issues)})**:",
                *[f"  - {issue.get('description', 'Unknown issue')}" for issue in security_issues[:5]],
                ""
            ])
        
        # Execute code if safe or if security level allows
        should_execute = (
            security_result.get('safe_to_execute', False) or
            (security_level == "low" and security_result.get('risk_level') != "high") or
            (security_level == "medium" and security_result.get('risk_level') == "low")
        )
        
        if should_execute:
            # Execute in sandbox
            execution_result = await grainchain.execute_code(
                code=code,
                language=language,
                files=files
            )
            
            report_parts.extend([
                "🚀 **Execution Results**:",
                f"✅ **Success**: {execution_result.success}",
                f"⏱️ **Execution Time**: {execution_result.execution_time:.3f}s",
                f"🔢 **Return Code**: {execution_result.return_code}",
                ""
            ])
            
            if execution_result.stdout:
                report_parts.extend([
                    "📤 **Standard Output**:",
                    f"```",
                    execution_result.stdout,
                    f"```",
                    ""
                ])
            
            if execution_result.stderr:
                report_parts.extend([
                    "📥 **Standard Error**:",
                    f"```",
                    execution_result.stderr,
                    f"```",
                    ""
                ])
            
            if execution_result.files_created:
                report_parts.extend([
                    f"📁 **Files Created ({len(execution_result.files_created)})**:",
                    *[f"  - {file}" for file in execution_result.files_created],
                    ""
                ])
            
            if execution_result.error:
                report_parts.extend([
                    "❌ **Execution Error**:",
                    execution_result.error,
                    ""
                ])
        
        else:
            report_parts.extend([
                "🚫 **Execution Blocked**:",
                f"Code execution was blocked due to security concerns.",
                f"Risk level: {security_result.get('risk_level', 'unknown')}",
                f"Security level: {security_level}",
                ""
            ])
        
        return "\n".join(report_parts)
        
    except Exception as e:
        logger.error(f"Secure code execution failed: {e}")
        return f"❌ Secure code execution failed: {str(e)}"

async def handle_webhook_processing(
    webhook_payload: Dict[str, Any],
    process_immediately: bool = True
) -> str:
    """
    Process GitHub webhook events through the integrated workflow
    
    Args:
        webhook_payload: GitHub webhook payload
        process_immediately: Whether to process immediately or queue
    
    Returns:
        Processing status and workflow ID
    """
    
    try:
        logger.info("Processing webhook event")
        
        orchestrator = get_workflow_orchestrator()
        
        if process_immediately:
            # Execute workflow immediately
            workflow_result = await orchestrator.execute_pr_workflow(webhook_payload)
            
            report_parts = [
                "🔄 **Webhook Processing Complete**",
                f"🆔 **Workflow ID**: {workflow_result.workflow_id}",
                f"📊 **Status**: {workflow_result.status.value}",
                f"⏱️ **Duration**: {(workflow_result.end_time or 0) - workflow_result.start_time:.2f}s",
                f"📋 **Steps**: {len(workflow_result.steps)}",
                ""
            ]
            
            # Step summary
            completed_steps = [s for s in workflow_result.steps if s.status.value == "completed"]
            failed_steps = [s for s in workflow_result.steps if s.status.value == "failed"]
            
            report_parts.extend([
                f"✅ **Completed Steps**: {len(completed_steps)}",
                f"❌ **Failed Steps**: {len(failed_steps)}",
                ""
            ])
            
            # Summary
            if workflow_result.summary:
                summary = workflow_result.summary
                report_parts.extend([
                    "📈 **Summary**:",
                    f"  - Success Rate: {summary.get('success_rate', 0):.1%}",
                    f"  - Repository: {summary.get('repository', 'N/A')}",
                    f"  - PR Number: {summary.get('pull_request', 'N/A')}",
                    ""
                ])
            
            # Recommendations
            if workflow_result.steps and workflow_result.steps[-1].result:
                report_data = workflow_result.steps[-1].result.get("comprehensive_report", {})
                recommendations = report_data.get("recommendations", [])
                if recommendations:
                    report_parts.extend([
                        "💡 **Recommendations**:",
                        *[f"  - {rec}" for rec in recommendations[:5]],
                        ""
                    ])
            
            if workflow_result.error:
                report_parts.extend([
                    "❌ **Error**:",
                    workflow_result.error,
                    ""
                ])
            
            return "\n".join(report_parts)
        
        else:
            # Queue for later processing (simplified implementation)
            return f"📥 Webhook queued for processing. Event type: {webhook_payload.get('event_type', 'unknown')}"
        
    except Exception as e:
        logger.error(f"Webhook processing failed: {e}")
        return f"❌ Webhook processing failed: {str(e)}"

async def handle_service_health_check() -> str:
    """
    Check health of all integrated services
    
    Returns:
        Health status report for all services
    """
    
    try:
        logger.info("Checking service health")
        
        # Get all service managers
        config_manager = get_config_manager()
        service_manager = get_service_manager()
        orchestrator = get_workflow_orchestrator()
        grainchain = get_grainchain_integration()
        graph_sitter = get_graph_sitter_integration()
        
        # Check configuration validity
        config_validation = config_manager.validate_configurations()
        
        # Check service health
        service_health = await service_manager.health_check_all()
        orchestrator_health = await orchestrator.health_check()
        grainchain_health = await grainchain.health_check()
        graph_sitter_health = await graph_sitter.health_check()
        
        report_parts = [
            "🏥 **Service Health Check Report**",
            f"🕐 **Timestamp**: {asyncio.get_event_loop().time()}",
            ""
        ]
        
        # Configuration status
        report_parts.extend([
            "⚙️ **Configuration Status**:",
            *[f"  - {service}: {'✅' if valid else '❌'}" 
              for service, valid in config_validation.items()],
            ""
        ])
        
        # Service health
        report_parts.extend([
            "🔗 **External Services**:",
            *[f"  - {service}: {'✅' if result.success else '❌'}" 
              for service, result in service_health.items()],
            ""
        ])
        
        # Integration health
        integrations = {
            "Workflow Orchestrator": orchestrator_health.success,
            "Grainchain Integration": grainchain_health.success,
            "Graph-sitter Integration": graph_sitter_health.success
        }
        
        report_parts.extend([
            "🔧 **Integration Services**:",
            *[f"  - {service}: {'✅' if healthy else '❌'}" 
              for service, healthy in integrations.items()],
            ""
        ])
        
        # Overall status
        all_healthy = (
            all(config_validation.values()) and
            all(result.success for result in service_health.values()) and
            all(integrations.values())
        )
        
        report_parts.extend([
            f"🎯 **Overall Status**: {'✅ All systems healthy' if all_healthy else '⚠️ Some issues detected'}",
            ""
        ])
        
        # Detailed information
        if not all_healthy:
            report_parts.extend([
                "🔍 **Issue Details**:",
                ""
            ])
            
            # Configuration issues
            for service, valid in config_validation.items():
                if not valid:
                    report_parts.append(f"  - {service}: Configuration invalid")
            
            # Service issues
            for service, result in service_health.items():
                if not result.success:
                    report_parts.append(f"  - {service}: {result.error}")
            
            # Integration issues
            for service, healthy in integrations.items():
                if not healthy:
                    report_parts.append(f"  - {service}: Health check failed")
        
        return "\n".join(report_parts)
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return f"❌ Service health check failed: {str(e)}"

def _format_comprehensive_report(workflow_result) -> str:
    """Format comprehensive workflow report"""
    
    report_parts = [
        "📊 **Comprehensive Analysis Report**",
        f"🆔 **Workflow ID**: {workflow_result.workflow_id}",
        f"📊 **Status**: {workflow_result.status.value}",
        f"⏱️ **Duration**: {(workflow_result.end_time or 0) - workflow_result.start_time:.2f}s",
        ""
    ]
    
    if workflow_result.context:
        context = workflow_result.context
        report_parts.extend([
            "📋 **Context**:",
            f"  - Repository: {context.repository or 'N/A'}",
            f"  - PR Number: {context.pull_request_number or 'N/A'}",
            f"  - Branch: {context.branch or 'N/A'}",
            f"  - Commit: {context.commit_sha or 'N/A'}",
            ""
        ])
    
    # Step results
    if workflow_result.steps:
        completed_steps = [s for s in workflow_result.steps if s.status.value == "completed"]
        failed_steps = [s for s in workflow_result.steps if s.status.value == "failed"]
        
        report_parts.extend([
            "🔄 **Workflow Steps**:",
            f"  - Total: {len(workflow_result.steps)}",
            f"  - Completed: {len(completed_steps)}",
            f"  - Failed: {len(failed_steps)}",
            ""
        ])
        
        # Individual step details
        for step in workflow_result.steps:
            status_emoji = {
                "completed": "✅",
                "failed": "❌",
                "running": "🔄",
                "pending": "⏳",
                "skipped": "⏭️"
            }.get(step.status.value, "❓")
            
            duration = ""
            if step.start_time and step.end_time:
                duration = f" ({step.end_time - step.start_time:.2f}s)"
            
            report_parts.append(f"  {status_emoji} {step.name}{duration}")
            
            if step.error:
                report_parts.append(f"    Error: {step.error}")
        
        report_parts.append("")
    
    # Summary
    if workflow_result.summary:
        summary = workflow_result.summary
        report_parts.extend([
            "📈 **Summary**:",
            f"  - Success Rate: {summary.get('success_rate', 0):.1%}",
            ""
        ])
        
        # Step-specific summaries
        for key, value in summary.items():
            if key.endswith("_summary") and isinstance(value, dict):
                step_name = key.replace("_summary", "").replace("_", " ").title()
                report_parts.append(f"  **{step_name}**:")
                for sub_key, sub_value in value.items():
                    report_parts.append(f"    - {sub_key.replace('_', ' ').title()}: {sub_value}")
                report_parts.append("")
    
    # Final report from last step
    if workflow_result.steps and workflow_result.steps[-1].result:
        final_report = workflow_result.steps[-1].result.get("comprehensive_report", {})
        recommendations = final_report.get("recommendations", [])
        
        if recommendations:
            report_parts.extend([
                "💡 **Recommendations**:",
                *[f"  - {rec}" for rec in recommendations],
                ""
            ])
    
    if workflow_result.error:
        report_parts.extend([
            "❌ **Workflow Error**:",
            workflow_result.error,
            ""
        ])
    
    return "\n".join(report_parts)

def _generate_code_recommendations(analysis_result, runtime_errors, swe_metrics) -> List[str]:
    """Generate code improvement recommendations"""
    
    recommendations = []
    
    # Error-based recommendations
    if analysis_result.errors:
        error_count = len(analysis_result.errors)
        if error_count > 10:
            recommendations.append(f"High error count ({error_count}) - prioritize fixing critical errors")
        elif error_count > 0:
            recommendations.append(f"Address {error_count} code errors before deployment")
    
    # Warning-based recommendations
    if analysis_result.warnings:
        warning_count = len(analysis_result.warnings)
        if warning_count > 20:
            recommendations.append(f"Consider addressing {warning_count} warnings to improve code quality")
    
    # Runtime error recommendations
    if runtime_errors:
        recommendations.append(f"Fix {len(runtime_errors)} runtime errors detected by LSP analysis")
    
    # Complexity recommendations
    if swe_metrics:
        complexity = swe_metrics.get('complexity_score', 0)
        maintainability = swe_metrics.get('maintainability_score', 100)
        
        if complexity > 70:
            recommendations.append("High complexity detected - consider refactoring complex functions")
        
        if maintainability < 60:
            recommendations.append("Low maintainability score - improve code structure and documentation")
        
        error_density = swe_metrics.get('error_density', 0)
        if error_density > 0.1:
            recommendations.append("High error density - focus on code quality improvements")
    
    # Dependency recommendations
    if analysis_result.dependencies and len(analysis_result.dependencies) > 50:
        recommendations.append("Large number of dependencies - consider dependency cleanup")
    
    if not recommendations:
        recommendations.append("Code quality looks good - no major issues detected")
    
    return recommendations
