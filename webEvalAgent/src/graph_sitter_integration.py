#!/usr/bin/env python3
"""
Graph-sitter Integration with Serena Extension
Provides comprehensive code analysis and runtime error detection
"""

import asyncio
import logging
import json
import os
import tempfile
from typing import Dict, Any, Optional, List, Union, Set
from dataclasses import dataclass, asdict
from pathlib import Path
import subprocess
import time
import re

from .config_manager import get_config_manager
from .service_abstractions import ServiceResponse

logger = logging.getLogger(__name__)

@dataclass
class CodeError:
    """Represents a code error detected by analysis"""
    error_type: str
    severity: str  # "error", "warning", "info"
    message: str
    file_path: str
    line_number: int
    column_number: int = 0
    end_line: Optional[int] = None
    end_column: Optional[int] = None
    source: str = "graph_sitter"  # "graph_sitter", "serena", "lsp"
    code: Optional[str] = None
    suggestions: List[str] = None
    
    def __post_init__(self):
        if self.suggestions is None:
            self.suggestions = []

@dataclass
class CodeAnalysisResult:
    """Result from code analysis"""
    success: bool
    errors: List[CodeError] = None
    warnings: List[CodeError] = None
    info: List[CodeError] = None
    analysis_time: float = 0.0
    files_analyzed: int = 0
    lines_analyzed: int = 0
    language_stats: Dict[str, int] = None
    dependencies: List[str] = None
    complexity_metrics: Dict[str, Any] = None
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
        if self.info is None:
            self.info = []
        if self.language_stats is None:
            self.language_stats = {}
        if self.dependencies is None:
            self.dependencies = []
        if self.complexity_metrics is None:
            self.complexity_metrics = {}

@dataclass
class SerenaAnalysisResult:
    """Result from Serena LSP analysis"""
    runtime_errors: List[CodeError] = None
    type_errors: List[CodeError] = None
    lsp_diagnostics: List[Dict[str, Any]] = None
    symbol_information: List[Dict[str, Any]] = None
    completion_suggestions: List[str] = None
    
    def __post_init__(self):
        if self.runtime_errors is None:
            self.runtime_errors = []
        if self.type_errors is None:
            self.type_errors = []
        if self.lsp_diagnostics is None:
            self.lsp_diagnostics = []
        if self.symbol_information is None:
            self.symbol_information = []
        if self.completion_suggestions is None:
            self.completion_suggestions = []

class GraphSitterIntegration:
    """Integration with graph-sitter for code analysis"""
    
    def __init__(self):
        self.config_manager = get_config_manager()
        self.graph_sitter_config = self.config_manager.get_graph_sitter_config()
        self.logger = logging.getLogger("graph_sitter_integration")
        self._graph_sitter_available = None
        self._serena_available = None
        
    async def _check_graph_sitter_availability(self) -> bool:
        """Check if graph-sitter is available"""
        if self._graph_sitter_available is not None:
            return self._graph_sitter_available
            
        try:
            # Try to import graph_sitter
            import graph_sitter
            from graph_sitter import Codebase
            
            # Test basic functionality
            test_code = "def test(): pass"
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(test_code)
                temp_path = f.name
            
            try:
                # Test codebase creation
                codebase = Codebase(os.path.dirname(temp_path))
                functions = list(codebase.functions)
                
                self._graph_sitter_available = True
                self.logger.info("Graph-sitter is available and working")
                return True
                
            finally:
                os.unlink(temp_path)
                
        except ImportError:
            self.logger.warning("Graph-sitter not installed. Install with: pip install graph-sitter")
        except Exception as e:
            self.logger.error(f"Graph-sitter availability check failed: {e}")
            
        self._graph_sitter_available = False
        return False
    
    async def _check_serena_availability(self) -> bool:
        """Check if Serena extension is available"""
        if self._serena_available is not None:
            return self._serena_available
            
        try:
            # Try to import serena extension
            from graph_sitter.extensions.serena import SerenaAnalyzer
            
            self._serena_available = True
            self.logger.info("Serena extension is available")
            return True
            
        except ImportError:
            self.logger.warning("Serena extension not available. Install with: pip install graph-sitter[serena]")
        except Exception as e:
            self.logger.error(f"Serena availability check failed: {e}")
            
        self._serena_available = False
        return False
    
    async def analyze_code(
        self,
        code_path: str,
        languages: Optional[List[str]] = None,
        include_serena: bool = True
    ) -> CodeAnalysisResult:
        """Analyze code using graph-sitter and optionally Serena"""
        start_time = time.time()
        
        try:
            # Check availability
            graph_sitter_available = await self._check_graph_sitter_availability()
            serena_available = include_serena and await self._check_serena_availability()
            
            if not graph_sitter_available:
                return await self._fallback_analysis(code_path, languages)
            
            # Use graph-sitter for analysis
            result = await self._analyze_with_graph_sitter(code_path, languages)
            
            # Add Serena analysis if available
            if serena_available:
                serena_result = await self._analyze_with_serena(code_path, languages)
                result = self._merge_analysis_results(result, serena_result)
            
            result.analysis_time = time.time() - start_time
            return result
            
        except Exception as e:
            self.logger.error(f"Code analysis failed: {e}")
            return CodeAnalysisResult(
                success=False,
                error_message=f"Analysis failed: {str(e)}",
                analysis_time=time.time() - start_time
            )
    
    async def _analyze_with_graph_sitter(
        self,
        code_path: str,
        languages: Optional[List[str]]
    ) -> CodeAnalysisResult:
        """Analyze code using graph-sitter"""
        try:
            from graph_sitter import Codebase
            
            # Create codebase
            codebase = Codebase(code_path)
            
            errors = []
            warnings = []
            info = []
            files_analyzed = 0
            lines_analyzed = 0
            language_stats = {}
            dependencies = []
            
            # Analyze functions
            for function in codebase.functions:
                files_analyzed += 1
                
                # Get function details
                try:
                    # Check for potential issues
                    if not function.usages:
                        warnings.append(CodeError(
                            error_type="unused_function",
                            severity="warning",
                            message=f"Function '{function.name}' appears to be unused",
                            file_path=function.file_path,
                            line_number=function.line_number,
                            source="graph_sitter"
                        ))
                    
                    # Check dependencies
                    for dep in function.dependencies:
                        if dep.name not in dependencies:
                            dependencies.append(dep.name)
                    
                    # Count lines
                    if hasattr(function, 'end_line') and hasattr(function, 'line_number'):
                        lines_analyzed += function.end_line - function.line_number + 1
                    
                except Exception as e:
                    errors.append(CodeError(
                        error_type="analysis_error",
                        severity="error",
                        message=f"Failed to analyze function '{function.name}': {str(e)}",
                        file_path=function.file_path,
                        line_number=function.line_number,
                        source="graph_sitter"
                    ))
            
            # Analyze classes
            for class_obj in codebase.classes:
                try:
                    # Check for potential issues
                    if not class_obj.usages:
                        warnings.append(CodeError(
                            error_type="unused_class",
                            severity="warning",
                            message=f"Class '{class_obj.name}' appears to be unused",
                            file_path=class_obj.file_path,
                            line_number=class_obj.line_number,
                            source="graph_sitter"
                        ))
                        
                except Exception as e:
                    errors.append(CodeError(
                        error_type="analysis_error",
                        severity="error",
                        message=f"Failed to analyze class '{class_obj.name}': {str(e)}",
                        file_path=class_obj.file_path,
                        line_number=class_obj.line_number,
                        source="graph_sitter"
                    ))
            
            # Analyze imports
            for import_obj in codebase.imports:
                try:
                    if not import_obj.usages:
                        warnings.append(CodeError(
                            error_type="unused_import",
                            severity="warning",
                            message=f"Import '{import_obj.name}' appears to be unused",
                            file_path=import_obj.file_path,
                            line_number=import_obj.line_number,
                            source="graph_sitter"
                        ))
                        
                except Exception as e:
                    errors.append(CodeError(
                        error_type="analysis_error",
                        severity="error",
                        message=f"Failed to analyze import '{import_obj.name}': {str(e)}",
                        file_path=import_obj.file_path,
                        line_number=import_obj.line_number,
                        source="graph_sitter"
                    ))
            
            return CodeAnalysisResult(
                success=True,
                errors=errors,
                warnings=warnings,
                info=info,
                files_analyzed=files_analyzed,
                lines_analyzed=lines_analyzed,
                language_stats=language_stats,
                dependencies=dependencies
            )
            
        except Exception as e:
            return CodeAnalysisResult(
                success=False,
                error_message=f"Graph-sitter analysis failed: {str(e)}"
            )
    
    async def _analyze_with_serena(
        self,
        code_path: str,
        languages: Optional[List[str]]
    ) -> SerenaAnalysisResult:
        """Analyze code using Serena LSP extension"""
        try:
            from graph_sitter.extensions.serena import SerenaAnalyzer
            
            # Initialize Serena analyzer
            analyzer = SerenaAnalyzer(
                timeout=self.graph_sitter_config.lsp_timeout,
                languages=languages or self.graph_sitter_config.languages
            )
            
            # Perform analysis
            runtime_errors = []
            type_errors = []
            lsp_diagnostics = []
            symbol_information = []
            
            # Analyze each file in the path
            path_obj = Path(code_path)
            if path_obj.is_file():
                files_to_analyze = [path_obj]
            else:
                files_to_analyze = []
                for lang in languages or self.graph_sitter_config.languages:
                    if lang == "python":
                        files_to_analyze.extend(path_obj.rglob("*.py"))
                    elif lang in ["javascript", "typescript"]:
                        files_to_analyze.extend(path_obj.rglob("*.js"))
                        files_to_analyze.extend(path_obj.rglob("*.ts"))
                        files_to_analyze.extend(path_obj.rglob("*.jsx"))
                        files_to_analyze.extend(path_obj.rglob("*.tsx"))
            
            for file_path in files_to_analyze:
                try:
                    # Get LSP diagnostics
                    diagnostics = await analyzer.get_diagnostics(str(file_path))
                    
                    for diagnostic in diagnostics:
                        error = CodeError(
                            error_type="lsp_diagnostic",
                            severity=diagnostic.get("severity", "error"),
                            message=diagnostic.get("message", "Unknown error"),
                            file_path=str(file_path),
                            line_number=diagnostic.get("line", 0),
                            column_number=diagnostic.get("column", 0),
                            source="serena",
                            code=diagnostic.get("code")
                        )
                        
                        if diagnostic.get("severity") == "error":
                            if "runtime" in diagnostic.get("message", "").lower():
                                runtime_errors.append(error)
                            else:
                                type_errors.append(error)
                        
                        lsp_diagnostics.append(diagnostic)
                    
                    # Get symbol information
                    symbols = await analyzer.get_symbols(str(file_path))
                    symbol_information.extend(symbols)
                    
                except Exception as e:
                    self.logger.warning(f"Serena analysis failed for {file_path}: {e}")
            
            return SerenaAnalysisResult(
                runtime_errors=runtime_errors,
                type_errors=type_errors,
                lsp_diagnostics=lsp_diagnostics,
                symbol_information=symbol_information
            )
            
        except Exception as e:
            self.logger.error(f"Serena analysis failed: {e}")
            return SerenaAnalysisResult()
    
    def _merge_analysis_results(
        self,
        graph_sitter_result: CodeAnalysisResult,
        serena_result: SerenaAnalysisResult
    ) -> CodeAnalysisResult:
        """Merge results from graph-sitter and Serena analysis"""
        
        # Add Serena errors to the main result
        graph_sitter_result.errors.extend(serena_result.runtime_errors)
        graph_sitter_result.errors.extend(serena_result.type_errors)
        
        # Add metadata about Serena analysis
        graph_sitter_result.complexity_metrics["serena_diagnostics"] = len(serena_result.lsp_diagnostics)
        graph_sitter_result.complexity_metrics["runtime_errors"] = len(serena_result.runtime_errors)
        graph_sitter_result.complexity_metrics["type_errors"] = len(serena_result.type_errors)
        graph_sitter_result.complexity_metrics["symbols_found"] = len(serena_result.symbol_information)
        
        return graph_sitter_result
    
    async def _fallback_analysis(
        self,
        code_path: str,
        languages: Optional[List[str]]
    ) -> CodeAnalysisResult:
        """Fallback analysis when graph-sitter is not available"""
        start_time = time.time()
        
        try:
            errors = []
            warnings = []
            files_analyzed = 0
            lines_analyzed = 0
            language_stats = {}
            
            path_obj = Path(code_path)
            
            if path_obj.is_file():
                files_to_analyze = [path_obj]
            else:
                files_to_analyze = list(path_obj.rglob("*.py")) + list(path_obj.rglob("*.js")) + list(path_obj.rglob("*.ts"))
            
            for file_path in files_to_analyze:
                try:
                    content = file_path.read_text(encoding='utf-8')
                    lines = content.split('\n')
                    lines_analyzed += len(lines)
                    files_analyzed += 1
                    
                    # Basic syntax checking
                    if file_path.suffix == '.py':
                        language_stats['python'] = language_stats.get('python', 0) + 1
                        errors.extend(await self._check_python_syntax(str(file_path), content))
                    elif file_path.suffix in ['.js', '.ts', '.jsx', '.tsx']:
                        language_stats['javascript'] = language_stats.get('javascript', 0) + 1
                        errors.extend(await self._check_javascript_syntax(str(file_path), content))
                    
                except Exception as e:
                    errors.append(CodeError(
                        error_type="file_read_error",
                        severity="error",
                        message=f"Failed to read file: {str(e)}",
                        file_path=str(file_path),
                        line_number=1,
                        source="fallback"
                    ))
            
            return CodeAnalysisResult(
                success=True,
                errors=errors,
                warnings=warnings,
                files_analyzed=files_analyzed,
                lines_analyzed=lines_analyzed,
                language_stats=language_stats,
                analysis_time=time.time() - start_time
            )
            
        except Exception as e:
            return CodeAnalysisResult(
                success=False,
                error_message=f"Fallback analysis failed: {str(e)}",
                analysis_time=time.time() - start_time
            )
    
    async def _check_python_syntax(self, file_path: str, content: str) -> List[CodeError]:
        """Check Python syntax using AST"""
        errors = []
        
        try:
            import ast
            ast.parse(content)
        except SyntaxError as e:
            errors.append(CodeError(
                error_type="syntax_error",
                severity="error",
                message=f"Python syntax error: {e.msg}",
                file_path=file_path,
                line_number=e.lineno or 1,
                column_number=e.offset or 0,
                source="fallback"
            ))
        except Exception as e:
            errors.append(CodeError(
                error_type="parse_error",
                severity="error",
                message=f"Failed to parse Python file: {str(e)}",
                file_path=file_path,
                line_number=1,
                source="fallback"
            ))
        
        return errors
    
    async def _check_javascript_syntax(self, file_path: str, content: str) -> List[CodeError]:
        """Check JavaScript/TypeScript syntax"""
        errors = []
        
        # Basic pattern matching for common issues
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Check for common syntax issues
            if re.search(r'console\.log\(.*\);?$', line.strip()):
                # This is just an example - in practice you'd want more sophisticated checks
                pass
            
            # Check for missing semicolons (basic check)
            if re.search(r'^\s*(var|let|const|function)\s+.*[^;{}\s]$', line.strip()):
                errors.append(CodeError(
                    error_type="missing_semicolon",
                    severity="warning",
                    message="Possible missing semicolon",
                    file_path=file_path,
                    line_number=i,
                    source="fallback"
                ))
        
        return errors
    
    async def get_runtime_errors(self, code_path: str) -> List[CodeError]:
        """Get runtime errors using Serena LSP integration"""
        try:
            if not await self._check_serena_availability():
                return []
            
            serena_result = await self._analyze_with_serena(code_path, None)
            return serena_result.runtime_errors
            
        except Exception as e:
            self.logger.error(f"Failed to get runtime errors: {e}")
            return []
    
    async def analyze_swe_bench_features(self, code_path: str) -> Dict[str, Any]:
        """Analyze code using SWE-bench features"""
        try:
            # This would integrate with SWE-bench evaluation framework
            # For now, return basic metrics
            
            analysis_result = await self.analyze_code(code_path)
            
            swe_metrics = {
                "total_errors": len(analysis_result.errors),
                "total_warnings": len(analysis_result.warnings),
                "files_analyzed": analysis_result.files_analyzed,
                "lines_analyzed": analysis_result.lines_analyzed,
                "language_distribution": analysis_result.language_stats,
                "complexity_score": self._calculate_complexity_score(analysis_result),
                "maintainability_score": self._calculate_maintainability_score(analysis_result),
                "error_density": len(analysis_result.errors) / max(analysis_result.lines_analyzed, 1),
                "dependency_count": len(analysis_result.dependencies)
            }
            
            return swe_metrics
            
        except Exception as e:
            self.logger.error(f"SWE-bench analysis failed: {e}")
            return {}
    
    def _calculate_complexity_score(self, analysis_result: CodeAnalysisResult) -> float:
        """Calculate complexity score based on analysis results"""
        if analysis_result.lines_analyzed == 0:
            return 0.0
        
        # Simple complexity calculation
        error_weight = len(analysis_result.errors) * 2
        warning_weight = len(analysis_result.warnings) * 1
        dependency_weight = len(analysis_result.dependencies) * 0.5
        
        complexity = (error_weight + warning_weight + dependency_weight) / analysis_result.lines_analyzed
        return min(complexity * 100, 100.0)  # Cap at 100
    
    def _calculate_maintainability_score(self, analysis_result: CodeAnalysisResult) -> float:
        """Calculate maintainability score"""
        if analysis_result.lines_analyzed == 0:
            return 100.0
        
        # Higher errors/warnings = lower maintainability
        error_penalty = len(analysis_result.errors) * 5
        warning_penalty = len(analysis_result.warnings) * 2
        
        base_score = 100.0
        penalty = (error_penalty + warning_penalty) / analysis_result.lines_analyzed * 100
        
        return max(base_score - penalty, 0.0)
    
    async def health_check(self) -> ServiceResponse:
        """Check graph-sitter integration health"""
        try:
            graph_sitter_available = await self._check_graph_sitter_availability()
            serena_available = await self._check_serena_availability()
            
            # Test basic analysis
            with tempfile.TemporaryDirectory() as temp_dir:
                test_file = Path(temp_dir) / "test.py"
                test_file.write_text("def test_function():\n    return 'health check'")
                
                result = await self.analyze_code(temp_dir)
                
                return ServiceResponse(
                    success=result.success,
                    data={
                        "graph_sitter_available": graph_sitter_available,
                        "serena_available": serena_available,
                        "test_analysis": result.success,
                        "supported_languages": self.graph_sitter_config.languages
                    }
                )
                
        except Exception as e:
            return ServiceResponse(
                success=False,
                error=f"Health check failed: {str(e)}"
            )

# Global instance
_graph_sitter_integration: Optional[GraphSitterIntegration] = None

def get_graph_sitter_integration() -> GraphSitterIntegration:
    """Get the global graph-sitter integration instance"""
    global _graph_sitter_integration
    if _graph_sitter_integration is None:
        _graph_sitter_integration = GraphSitterIntegration()
    return _graph_sitter_integration
