"""
Parser for instruction files (Markdown, JSON, YAML)
"""

import json
import yaml
import re
from pathlib import Path
from typing import Dict, List, Any, Optional


class InstructionParser:
    """Parse instruction files in various formats"""
    
    def __init__(self, debug: bool = False):
        self.debug = debug
    
    def parse_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Parse an instruction file and return test scenarios
        
        Args:
            file_path: Path to the instruction file
            
        Returns:
            List of test scenarios
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Instruction file not found: {file_path}")
        
        if self.debug:
            print(f"📖 Parsing instruction file: {file_path}")
        
        # Determine file type and parse accordingly
        if path.suffix.lower() == '.json':
            return self._parse_json(path)
        elif path.suffix.lower() in ['.yml', '.yaml']:
            return self._parse_yaml(path)
        elif path.suffix.lower() in ['.md', '.markdown']:
            return self._parse_markdown(path)
        else:
            # Try to auto-detect format
            content = path.read_text(encoding='utf-8')
            return self._auto_parse(content, path.name)
    
    def _parse_json(self, path: Path) -> List[Dict[str, Any]]:
        """Parse JSON instruction file"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, dict):
                # Single scenario or wrapper object
                if 'scenarios' in data:
                    return data['scenarios']
                else:
                    return [data]
            elif isinstance(data, list):
                return data
            else:
                raise ValueError("JSON must contain object or array")
                
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")
    
    def _parse_yaml(self, path: Path) -> List[Dict[str, Any]]:
        """Parse YAML instruction file"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if isinstance(data, dict):
                if 'scenarios' in data:
                    return data['scenarios']
                else:
                    return [data]
            elif isinstance(data, list):
                return data
            else:
                raise ValueError("YAML must contain object or array")
                
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML format: {e}")
    
    def _parse_markdown(self, path: Path) -> List[Dict[str, Any]]:
        """Parse Markdown instruction file"""
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        scenarios = []
        
        # Split by main headings (# or ##)
        sections = re.split(r'\n(?=#{1,2}\s)', content)
        
        current_scenario = None
        
        for section in sections:
            if not section.strip():
                continue
            
            lines = section.strip().split('\n')
            
            # Check if this is a scenario section
            if self._is_scenario_section(lines[0]):
                # Save previous scenario if exists
                if current_scenario:
                    scenarios.append(current_scenario)
                
                # Start new scenario
                current_scenario = {
                    'name': self._extract_heading_text(lines[0]),
                    'description': '',
                    'steps': [],
                    'success_criteria': []
                }
                
                # Process the rest of the section
                self._process_scenario_content(lines[1:], current_scenario)
            
            elif current_scenario:
                # Continue processing current scenario
                self._process_scenario_content(lines, current_scenario)
        
        # Add the last scenario
        if current_scenario:
            scenarios.append(current_scenario)
        
        # If no scenarios found, create a general one
        if not scenarios:
            scenarios = self._create_general_scenario(content)
        
        if self.debug:
            print(f"📋 Parsed {len(scenarios)} scenarios from Markdown")
        
        return scenarios
    
    def _is_scenario_section(self, line: str) -> bool:
        """Check if a line indicates a scenario section"""
        line_lower = line.lower()
        scenario_indicators = [
            'scenario', 'test', 'check', 'verify', 'evaluate', 
            'objective', 'goal', 'task', 'step'
        ]
        return any(indicator in line_lower for indicator in scenario_indicators)
    
    def _extract_heading_text(self, line: str) -> str:
        """Extract text from a markdown heading"""
        return re.sub(r'^#{1,6}\s*', '', line).strip()
    
    def _process_scenario_content(self, lines: List[str], scenario: Dict[str, Any]):
        """Process content lines for a scenario"""
        current_section = 'description'
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check for section headers
            line_lower = line.lower()
            if any(word in line_lower for word in ['step', 'action', 'task']):
                current_section = 'steps'
                continue
            elif any(word in line_lower for word in ['success', 'criteria', 'requirement']):
                current_section = 'success_criteria'
                continue
            elif any(word in line_lower for word in ['description', 'objective', 'goal']):
                current_section = 'description'
                continue
            
            # Process content based on current section
            if current_section == 'description':
                if scenario['description']:
                    scenario['description'] += ' ' + line
                else:
                    scenario['description'] = line
            
            elif current_section == 'steps':
                # Remove list markers and add to steps
                step_text = re.sub(r'^[-*+]\s*', '', line)
                step_text = re.sub(r'^\d+\.\s*', '', step_text)
                if step_text:
                    scenario['steps'].append(step_text)
            
            elif current_section == 'success_criteria':
                # Remove list markers and add to criteria
                criteria_text = re.sub(r'^[-*+]\s*', '', line)
                criteria_text = re.sub(r'^\d+\.\s*', '', criteria_text)
                if criteria_text:
                    scenario['success_criteria'].append(criteria_text)
    
    def _create_general_scenario(self, content: str) -> List[Dict[str, Any]]:
        """Create a general scenario from unstructured content"""
        # Extract any list items as steps
        steps = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if re.match(r'^[-*+]\s', line) or re.match(r'^\d+\.\s', line):
                step_text = re.sub(r'^[-*+]\s*', '', line)
                step_text = re.sub(r'^\d+\.\s*', '', step_text)
                if step_text:
                    steps.append(step_text)
        
        # If no steps found, create basic ones
        if not steps:
            steps = [
                "Navigate to the website",
                "Check page loads correctly",
                "Verify main content is visible",
                "Test basic functionality",
                "Look for any obvious errors"
            ]
        
        return [{
            'name': 'General Web Evaluation',
            'description': 'Comprehensive evaluation of website functionality and usability',
            'steps': steps,
            'success_criteria': [
                'Page loads without errors',
                'Main content is accessible',
                'Interactive elements work correctly',
                'No critical issues found'
            ]
        }]
    
    def _auto_parse(self, content: str, filename: str) -> List[Dict[str, Any]]:
        """Auto-detect format and parse"""
        content = content.strip()
        
        # Try JSON first
        if content.startswith('{') or content.startswith('['):
            try:
                data = json.loads(content)
                if isinstance(data, (dict, list)):
                    return self._normalize_data(data)
            except json.JSONDecodeError:
                pass
        
        # Try YAML
        try:
            data = yaml.safe_load(content)
            if isinstance(data, (dict, list)):
                return self._normalize_data(data)
        except yaml.YAMLError:
            pass
        
        # Default to markdown-style parsing
        return self._parse_markdown_content(content)
    
    def _normalize_data(self, data: Any) -> List[Dict[str, Any]]:
        """Normalize parsed data to list of scenarios"""
        if isinstance(data, dict):
            if 'scenarios' in data:
                return data['scenarios']
            else:
                return [data]
        elif isinstance(data, list):
            return data
        else:
            return []
    
    def _parse_markdown_content(self, content: str) -> List[Dict[str, Any]]:
        """Parse markdown content directly"""
        # This is a simplified version of _parse_markdown for string content
        return self._create_general_scenario(content)
