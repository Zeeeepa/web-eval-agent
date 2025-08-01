#!/usr/bin/env python3
"""
Comprehensive Codemod Analyzer for Web Eval Agent
Uses tree-sitter to analyze and fix import issues, validate code structure,
and generate codemods for LSP integration.
"""

import os
import sys
import ast
import json
import traceback
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from collections import defaultdict

try:
    import tree_sitter_python as tspython
    import tree_sitter_javascript as tsjavascript
    import tree_sitter_typescript as tstypescript
    import tree_sitter_yaml as tsyaml
    import tree_sitter_json as tsjson
    from tree_sitter import Language, Parser, Node
    TREE_SITTER_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Tree-sitter not available: {e}")
    TREE_SITTER_AVAILABLE = False


@dataclass
class ImportIssue:
    """Represents an import issue found in the code"""
    file_path: str
    line_number: int
    column: int
    issue_type: str  # 'missing_module', 'circular_import', 'invalid_import'
    import_statement: str
    module_name: str
    suggested_fix: str
    severity: str  # 'error', 'warning', 'info'


@dataclass
class CodeIssue:
    """Represents a general code issue"""
    file_path: str
    line_number: int
    column: int
    issue_type: str
    description: str
    suggested_fix: str
    severity: str
    code_snippet: str


@dataclass
class AnalysisResult:
    """Complete analysis result"""
    import_issues: List[ImportIssue]
    code_issues: List[CodeIssue]
    file_structure: Dict[str, Any]
    dependency_graph: Dict[str, List[str]]
    missing_files: List[str]
    circular_imports: List[List[str]]
    summary: Dict[str, int]


class TreeSitterAnalyzer:
    """Tree-sitter based code analyzer"""
    
    def __init__(self):
        if not TREE_SITTER_AVAILABLE:
            print("⚠️ Tree-sitter not available, using AST fallback")
            return
            
        try:
            self.python_language = Language(tspython.language())
            self.js_language = Language(tsjavascript.language())
            # Handle TypeScript differently
            try:
                self.ts_language = Language(tstypescript.language_typescript())
            except:
                self.ts_language = None
            try:
                self.yaml_language = Language(tsyaml.language())
            except:
                self.yaml_language = None
            try:
                self.json_language = Language(tsjson.language())
            except:
                self.json_language = None
        except Exception as e:
            print(f"⚠️ Error initializing tree-sitter languages: {e}")
            TREE_SITTER_AVAILABLE = False
            return
        
        self.python_parser = Parser(self.python_language)
        self.js_parser = Parser(self.js_language)
        self.ts_parser = Parser(self.ts_language)
        self.yaml_parser = Parser(self.yaml_language)
        self.json_parser = Parser(self.json_language)
        
        self.parsers = {
            '.py': self.python_parser,
            '.js': self.js_parser,
            '.ts': self.ts_parser,
            '.tsx': self.ts_parser,
            '.yaml': self.yaml_parser,
            '.yml': self.yaml_parser,
            '.json': self.json_parser,
        }
    
    def parse_file(self, file_path: str) -> Optional[Node]:
        """Parse a file using appropriate tree-sitter parser"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            
            ext = Path(file_path).suffix.lower()
            parser = self.parsers.get(ext)
            
            if not parser:
                return None
                
            tree = parser.parse(content)
            return tree.root_node
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return None
    
    def extract_python_imports(self, node: Node, source_code: bytes) -> List[Dict[str, Any]]:
        """Extract import statements from Python AST"""
        imports = []
        
        def visit_node(node: Node):
            if node.type == 'import_statement':
                import_text = source_code[node.start_byte:node.end_byte].decode('utf-8')
                imports.append({
                    'type': 'import',
                    'statement': import_text,
                    'line': node.start_point[0] + 1,
                    'column': node.start_point[1],
                    'modules': self._extract_import_modules(node, source_code)
                })
            elif node.type == 'import_from_statement':
                import_text = source_code[node.start_byte:node.end_byte].decode('utf-8')
                imports.append({
                    'type': 'from_import',
                    'statement': import_text,
                    'line': node.start_point[0] + 1,
                    'column': node.start_point[1],
                    'module': self._extract_from_import_module(node, source_code),
                    'names': self._extract_from_import_names(node, source_code)
                })
            
            for child in node.children:
                visit_node(child)
        
        visit_node(node)
        return imports
    
    def _extract_import_modules(self, node: Node, source_code: bytes) -> List[str]:
        """Extract module names from import statement"""
        modules = []
        for child in node.children:
            if child.type == 'dotted_name':
                module_name = source_code[child.start_byte:child.end_byte].decode('utf-8')
                modules.append(module_name)
        return modules
    
    def _extract_from_import_module(self, node: Node, source_code: bytes) -> str:
        """Extract module name from from-import statement"""
        for child in node.children:
            if child.type == 'dotted_name' or child.type == 'relative_import':
                return source_code[child.start_byte:child.end_byte].decode('utf-8')
        return ""
    
    def _extract_from_import_names(self, node: Node, source_code: bytes) -> List[str]:
        """Extract imported names from from-import statement"""
        names = []
        for child in node.children:
            if child.type == 'import_list':
                for name_node in child.children:
                    if name_node.type == 'dotted_name' or name_node.type == 'identifier':
                        name = source_code[name_node.start_byte:name_node.end_byte].decode('utf-8')
                        names.append(name)
        return names


class CodemodAnalyzer:
    """Main analyzer class for generating codemods"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.tree_sitter = TreeSitterAnalyzer()
        self.import_issues: List[ImportIssue] = []
        self.code_issues: List[CodeIssue] = []
        self.file_structure: Dict[str, Any] = {}
        self.dependency_graph: Dict[str, List[str]] = defaultdict(list)
        self.existing_files: Set[str] = set()
        self.python_modules: Set[str] = set()
        
    def analyze_project(self) -> AnalysisResult:
        """Perform comprehensive project analysis"""
        print("🔍 Starting comprehensive codebase analysis...")
        
        # Step 1: Discover all files
        self._discover_files()
        
        # Step 2: Analyze Python files for imports and structure
        self._analyze_python_files()
        
        # Step 3: Validate imports and dependencies
        self._validate_imports()
        
        # Step 4: Detect circular imports
        circular_imports = self._detect_circular_imports()
        
        # Step 5: Generate missing files list
        missing_files = self._find_missing_files()
        
        # Step 6: Create summary
        summary = self._create_summary()
        
        return AnalysisResult(
            import_issues=self.import_issues,
            code_issues=self.code_issues,
            file_structure=self.file_structure,
            dependency_graph=dict(self.dependency_graph),
            missing_files=missing_files,
            circular_imports=circular_imports,
            summary=summary
        )
    
    def _discover_files(self):
        """Discover all relevant files in the project"""
        print("📁 Discovering project files...")
        
        for root, dirs, files in os.walk(self.project_root):
            # Skip common ignore directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules', 'venv', 'env']]
            
            for file in files:
                file_path = Path(root) / file
                rel_path = file_path.relative_to(self.project_root)
                
                if file.endswith(('.py', '.js', '.ts', '.tsx', '.yaml', '.yml', '.json')):
                    self.existing_files.add(str(rel_path))
                    
                    if file.endswith('.py'):
                        # Track Python modules
                        module_path = str(rel_path).replace('/', '.').replace('.py', '')
                        if module_path.startswith('src.'):
                            module_path = module_path[4:]  # Remove 'src.' prefix
                        self.python_modules.add(module_path)
        
        print(f"📊 Found {len(self.existing_files)} files, {len(self.python_modules)} Python modules")
    
    def _analyze_python_files(self):
        """Analyze all Python files for structure and imports"""
        print("🐍 Analyzing Python files...")
        
        python_files = [f for f in self.existing_files if f.endswith('.py')]
        
        for file_path in python_files:
            full_path = self.project_root / file_path
            
            try:
                # Parse with tree-sitter
                root_node = self.tree_sitter.parse_file(str(full_path))
                if not root_node:
                    continue
                
                with open(full_path, 'rb') as f:
                    source_code = f.read()
                
                # Extract imports
                imports = self.tree_sitter.extract_python_imports(root_node, source_code)
                
                # Store file structure
                self.file_structure[file_path] = {
                    'imports': imports,
                    'functions': self._extract_functions(root_node, source_code),
                    'classes': self._extract_classes(root_node, source_code),
                    'variables': self._extract_variables(root_node, source_code)
                }
                
                # Build dependency graph
                for imp in imports:
                    if imp['type'] == 'from_import' and imp['module']:
                        self.dependency_graph[file_path].append(imp['module'])
                    elif imp['type'] == 'import':
                        for module in imp['modules']:
                            self.dependency_graph[file_path].append(module)
                            
            except Exception as e:
                self.code_issues.append(CodeIssue(
                    file_path=file_path,
                    line_number=1,
                    column=1,
                    issue_type='parse_error',
                    description=f"Failed to parse file: {str(e)}",
                    suggested_fix="Check file syntax and encoding",
                    severity='error',
                    code_snippet=""
                ))
    
    def _extract_functions(self, node: Node, source_code: bytes) -> List[Dict[str, Any]]:
        """Extract function definitions"""
        functions = []
        
        def visit_node(node: Node):
            if node.type == 'function_definition':
                name_node = node.child_by_field_name('name')
                if name_node:
                    name = source_code[name_node.start_byte:name_node.end_byte].decode('utf-8')
                    functions.append({
                        'name': name,
                        'line': node.start_point[0] + 1,
                        'column': node.start_point[1]
                    })
            
            for child in node.children:
                visit_node(child)
        
        visit_node(node)
        return functions
    
    def _extract_classes(self, node: Node, source_code: bytes) -> List[Dict[str, Any]]:
        """Extract class definitions"""
        classes = []
        
        def visit_node(node: Node):
            if node.type == 'class_definition':
                name_node = node.child_by_field_name('name')
                if name_node:
                    name = source_code[name_node.start_byte:name_node.end_byte].decode('utf-8')
                    classes.append({
                        'name': name,
                        'line': node.start_point[0] + 1,
                        'column': node.start_point[1]
                    })
            
            for child in node.children:
                visit_node(child)
        
        visit_node(node)
        return classes
    
    def _extract_variables(self, node: Node, source_code: bytes) -> List[Dict[str, Any]]:
        """Extract variable assignments at module level"""
        variables = []
        
        def visit_node(node: Node, depth: int = 0):
            if depth == 1 and node.type == 'assignment':
                # Only top-level assignments
                target = node.child_by_field_name('left')
                if target and target.type == 'identifier':
                    name = source_code[target.start_byte:target.end_byte].decode('utf-8')
                    variables.append({
                        'name': name,
                        'line': node.start_point[0] + 1,
                        'column': node.start_point[1]
                    })
            
            for child in node.children:
                visit_node(child, depth + 1)
        
        visit_node(node)
        return variables
    
    def _validate_imports(self):
        """Validate all import statements"""
        print("✅ Validating imports...")
        
        for file_path, file_info in self.file_structure.items():
            for imp in file_info['imports']:
                if imp['type'] == 'from_import':
                    self._validate_from_import(file_path, imp)
                elif imp['type'] == 'import':
                    self._validate_import(file_path, imp)
    
    def _validate_from_import(self, file_path: str, imp: Dict[str, Any]):
        """Validate a from-import statement"""
        module = imp['module']
        
        if not module:
            return
        
        # Handle relative imports
        if module.startswith('.'):
            resolved_module = self._resolve_relative_import(file_path, module)
            if not resolved_module:
                self.import_issues.append(ImportIssue(
                    file_path=file_path,
                    line_number=imp['line'],
                    column=imp['column'],
                    issue_type='invalid_relative_import',
                    import_statement=imp['statement'],
                    module_name=module,
                    suggested_fix=f"Check relative import path: {module}",
                    severity='error'
                ))
                return
            module = resolved_module
        
        # Check if module exists
        if not self._module_exists(module):
            # Try to suggest a fix
            suggested_fix = self._suggest_import_fix(module)
            
            self.import_issues.append(ImportIssue(
                file_path=file_path,
                line_number=imp['line'],
                column=imp['column'],
                issue_type='missing_module',
                import_statement=imp['statement'],
                module_name=module,
                suggested_fix=suggested_fix,
                severity='error'
            ))
    
    def _validate_import(self, file_path: str, imp: Dict[str, Any]):
        """Validate an import statement"""
        for module in imp['modules']:
            if not self._module_exists(module):
                suggested_fix = self._suggest_import_fix(module)
                
                self.import_issues.append(ImportIssue(
                    file_path=file_path,
                    line_number=imp['line'],
                    column=imp['column'],
                    issue_type='missing_module',
                    import_statement=imp['statement'],
                    module_name=module,
                    suggested_fix=suggested_fix,
                    severity='error'
                ))
    
    def _resolve_relative_import(self, file_path: str, relative_module: str) -> Optional[str]:
        """Resolve relative import to absolute module path"""
        try:
            # Get the directory of the current file
            file_dir = Path(file_path).parent
            
            # Count the number of dots to determine how many levels up
            dots = len(relative_module) - len(relative_module.lstrip('.'))
            module_name = relative_module.lstrip('.')
            
            # Go up the required number of levels
            target_dir = file_dir
            for _ in range(dots - 1):
                target_dir = target_dir.parent
            
            # Construct the absolute module path
            if module_name:
                absolute_path = target_dir / module_name.replace('.', '/')
            else:
                absolute_path = target_dir
            
            # Convert to module notation
            rel_to_src = absolute_path.relative_to(Path('src'))
            return str(rel_to_src).replace('/', '.')
            
        except Exception:
            return None
    
    def _module_exists(self, module_name: str) -> bool:
        """Check if a module exists"""
        # Check if it's a built-in or third-party module
        try:
            __import__(module_name)
            return True
        except ImportError:
            pass
        
        # Check if it's a local module
        if module_name in self.python_modules:
            return True
        
        # Check if it's a file-based module
        module_path = module_name.replace('.', '/')
        
        # Check for __init__.py
        init_path = f"src/{module_path}/__init__.py"
        if init_path in self.existing_files:
            return True
        
        # Check for .py file
        py_path = f"src/{module_path}.py"
        if py_path in self.existing_files:
            return True
        
        return False
    
    def _suggest_import_fix(self, module_name: str) -> str:
        """Suggest a fix for missing import"""
        # Look for similar module names
        similar_modules = []
        for existing_module in self.python_modules:
            if self._similarity_score(module_name, existing_module) > 0.7:
                similar_modules.append(existing_module)
        
        if similar_modules:
            return f"Did you mean: {', '.join(similar_modules[:3])}?"
        
        # Check if it's a missing file
        expected_path = f"src/{module_name.replace('.', '/')}.py"
        return f"Create missing file: {expected_path}"
    
    def _similarity_score(self, s1: str, s2: str) -> float:
        """Calculate similarity score between two strings"""
        if not s1 or not s2:
            return 0.0
        
        # Simple Levenshtein-based similarity
        def levenshtein(a, b):
            if len(a) < len(b):
                return levenshtein(b, a)
            if len(b) == 0:
                return len(a)
            
            previous_row = list(range(len(b) + 1))
            for i, c1 in enumerate(a):
                current_row = [i + 1]
                for j, c2 in enumerate(b):
                    insertions = previous_row[j + 1] + 1
                    deletions = current_row[j] + 1
                    substitutions = previous_row[j] + (c1 != c2)
                    current_row.append(min(insertions, deletions, substitutions))
                previous_row = current_row
            
            return previous_row[-1]
        
        distance = levenshtein(s1, s2)
        max_len = max(len(s1), len(s2))
        return 1 - (distance / max_len)
    
    def _detect_circular_imports(self) -> List[List[str]]:
        """Detect circular import dependencies"""
        print("🔄 Detecting circular imports...")
        
        def dfs(node, path, visited, rec_stack):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in self.dependency_graph.get(node, []):
                if neighbor not in visited:
                    cycle = dfs(neighbor, path.copy(), visited, rec_stack)
                    if cycle:
                        return cycle
                elif neighbor in rec_stack:
                    # Found a cycle
                    cycle_start = path.index(neighbor)
                    return path[cycle_start:] + [neighbor]
            
            rec_stack.remove(node)
            return None
        
        visited = set()
        cycles = []
        
        for node in self.dependency_graph:
            if node not in visited:
                cycle = dfs(node, [], visited, set())
                if cycle:
                    cycles.append(cycle)
        
        return cycles
    
    def _find_missing_files(self) -> List[str]:
        """Find files that are imported but don't exist"""
        missing = []
        
        for file_path, file_info in self.file_structure.items():
            for imp in file_info['imports']:
                if imp['type'] == 'from_import':
                    module = imp['module']
                    if module and not self._module_exists(module):
                        expected_path = f"src/{module.replace('.', '/')}.py"
                        if expected_path not in missing:
                            missing.append(expected_path)
        
        return missing
    
    def _create_summary(self) -> Dict[str, int]:
        """Create analysis summary"""
        return {
            'total_files': len(self.existing_files),
            'python_files': len([f for f in self.existing_files if f.endswith('.py')]),
            'import_issues': len(self.import_issues),
            'code_issues': len(self.code_issues),
            'missing_files': len(self._find_missing_files()),
            'circular_imports': len(self._detect_circular_imports()),
            'error_severity': len([i for i in self.import_issues if i.severity == 'error']),
            'warning_severity': len([i for i in self.import_issues if i.severity == 'warning'])
        }
    
    def generate_codemods(self, analysis: AnalysisResult) -> List[Dict[str, Any]]:
        """Generate codemods to fix identified issues"""
        print("🔧 Generating codemods...")
        
        codemods = []
        
        # Generate import fixes
        for issue in analysis.import_issues:
            if issue.issue_type == 'missing_module':
                codemod = self._generate_import_fix_codemod(issue)
                if codemod:
                    codemods.append(codemod)
        
        # Generate missing file creation codemods
        for missing_file in analysis.missing_files:
            codemod = self._generate_missing_file_codemod(missing_file)
            if codemod:
                codemods.append(codemod)
        
        return codemods
    
    def _generate_import_fix_codemod(self, issue: ImportIssue) -> Optional[Dict[str, Any]]:
        """Generate codemod to fix import issue"""
        if "Create missing file:" in issue.suggested_fix:
            file_path = issue.suggested_fix.replace("Create missing file: ", "")
            return {
                'type': 'create_file',
                'file_path': file_path,
                'content': self._generate_module_template(issue.module_name),
                'description': f"Create missing module {issue.module_name}"
            }
        
        return None
    
    def _generate_missing_file_codemod(self, file_path: str) -> Dict[str, Any]:
        """Generate codemod to create missing file"""
        module_name = file_path.replace('src/', '').replace('.py', '').replace('/', '.')
        
        return {
            'type': 'create_file',
            'file_path': file_path,
            'content': self._generate_module_template(module_name),
            'description': f"Create missing module file {file_path}"
        }
    
    def _generate_module_template(self, module_name: str) -> str:
        """Generate template content for a missing module"""
        return f'''"""
{module_name} module

This module was automatically generated to resolve import issues.
Please implement the required functionality.
"""

# TODO: Implement module functionality
'''
    
    def save_analysis_report(self, analysis: AnalysisResult, output_file: str = "codemod_analysis.json"):
        """Save analysis report to JSON file"""
        report = {
            'analysis_summary': analysis.summary,
            'import_issues': [asdict(issue) for issue in analysis.import_issues],
            'code_issues': [asdict(issue) for issue in analysis.code_issues],
            'file_structure': analysis.file_structure,
            'dependency_graph': analysis.dependency_graph,
            'missing_files': analysis.missing_files,
            'circular_imports': analysis.circular_imports
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📄 Analysis report saved to {output_file}")
    
    def print_analysis_summary(self, analysis: AnalysisResult):
        """Print a formatted analysis summary"""
        print("\n" + "="*80)
        print("📊 CODEBASE ANALYSIS SUMMARY")
        print("="*80)
        
        print(f"📁 Total Files: {analysis.summary['total_files']}")
        print(f"🐍 Python Files: {analysis.summary['python_files']}")
        print(f"❌ Import Issues: {analysis.summary['import_issues']}")
        print(f"⚠️  Code Issues: {analysis.summary['code_issues']}")
        print(f"📄 Missing Files: {analysis.summary['missing_files']}")
        print(f"🔄 Circular Imports: {analysis.summary['circular_imports']}")
        
        print(f"\n🚨 Severity Breakdown:")
        print(f"   Errors: {analysis.summary['error_severity']}")
        print(f"   Warnings: {analysis.summary['warning_severity']}")
        
        if analysis.import_issues:
            print(f"\n❌ Import Issues:")
            for issue in analysis.import_issues[:10]:  # Show first 10
                print(f"   {issue.file_path}:{issue.line_number} - {issue.module_name}")
                print(f"      {issue.suggested_fix}")
        
        if analysis.missing_files:
            print(f"\n📄 Missing Files:")
            for file in analysis.missing_files[:10]:  # Show first 10
                print(f"   {file}")
        
        if analysis.circular_imports:
            print(f"\n🔄 Circular Imports:")
            for cycle in analysis.circular_imports:
                print(f"   {' -> '.join(cycle)}")
        
        print("="*80)


def main():
    """Main function to run the codemod analyzer"""
    print("🚀 Web Eval Agent Codemod Analyzer")
    print("="*50)
    
    # Initialize analyzer
    analyzer = CodemodAnalyzer(".")
    
    # Run analysis
    analysis = analyzer.analyze_project()
    
    # Print summary
    analyzer.print_analysis_summary(analysis)
    
    # Generate codemods
    codemods = analyzer.generate_codemods(analysis)
    
    if codemods:
        print(f"\n🔧 Generated {len(codemods)} codemods:")
        for i, codemod in enumerate(codemods, 1):
            print(f"   {i}. {codemod['description']}")
    
    # Save detailed report
    analyzer.save_analysis_report(analysis)
    
    # Apply codemods if requested
    if codemods:
        apply = input(f"\n❓ Apply {len(codemods)} codemods? (y/N): ").lower().strip()
        if apply == 'y':
            apply_codemods(codemods)
    
    return analysis


def apply_codemods(codemods: List[Dict[str, Any]]):
    """Apply generated codemods"""
    print("🔧 Applying codemods...")
    
    for codemod in codemods:
        if codemod['type'] == 'create_file':
            file_path = codemod['file_path']
            content = codemod['content']
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Write file
            with open(file_path, 'w') as f:
                f.write(content)
            
            print(f"✅ Created {file_path}")
    
    print("🎉 All codemods applied successfully!")


if __name__ == "__main__":
    main()
