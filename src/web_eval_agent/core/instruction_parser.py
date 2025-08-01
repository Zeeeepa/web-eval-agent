"""
Instruction file parser for Web Eval Agent

Parses instruction files in various formats (Markdown, YAML, JSON) to extract
test scenarios, validation criteria, and expected behaviors.
"""

import json
import re
import yaml
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Optional, Union


@dataclass
class TestScenario:
    """Represents a single test scenario."""
    name: str
    description: str
    steps: List[str]
    validations: List[str]
    expected_outcomes: List[str]
    timeout: Optional[int] = None
    priority: str = "medium"  # low, medium, high, critical
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


@dataclass
class ValidationRule:
    """Represents a validation rule."""
    type: str  # element_exists, text_contains, url_matches, etc.
    target: str  # CSS selector, URL pattern, text content
    expected: Union[str, bool, int]
    description: str


class InstructionParser:
    """Parser for instruction files in various formats."""
    
    def __init__(self):
        self.supported_formats = ['.md', '.yaml', '.yml', '.json']
    
    async def parse_file(self, filepath: str) -> List[TestScenario]:
        """Parse instruction file and return test scenarios."""
        path = Path(filepath)
        
        if not path.exists():
            raise FileNotFoundError(f"Instruction file not found: {filepath}")
        
        if path.suffix.lower() not in self.supported_formats:
            raise ValueError(f"Unsupported file format: {path.suffix}")
        
        content = path.read_text(encoding='utf-8')
        
        if path.suffix.lower() == '.md':
            return self._parse_markdown(content)
        elif path.suffix.lower() in ['.yaml', '.yml']:
            return self._parse_yaml(content)
        elif path.suffix.lower() == '.json':
            return self._parse_json(content)
        else:
            raise ValueError(f"Unsupported format: {path.suffix}")
    
    def _parse_markdown(self, content: str) -> List[TestScenario]:
        """Parse Markdown instruction file."""
        scenarios = []
        
        # Split content by test scenarios (looking for ## headers)
        scenario_pattern = r'^##\s+(.+?)$'
        sections = re.split(scenario_pattern, content, flags=re.MULTILINE)
        
        # If no ## headers found, treat entire content as one scenario
        if len(sections) == 1:
            return [self._parse_single_markdown_scenario("Main Test", content)]
        
        # Process each scenario section
        for i in range(1, len(sections), 2):
            if i + 1 < len(sections):
                scenario_name = sections[i].strip()
                scenario_content = sections[i + 1].strip()
                scenario = self._parse_single_markdown_scenario(scenario_name, scenario_content)
                scenarios.append(scenario)
        
        return scenarios
    
    def _parse_single_markdown_scenario(self, name: str, content: str) -> TestScenario:
        """Parse a single markdown scenario."""
        lines = content.split('\n')
        
        description = ""
        steps = []
        validations = []
        expected_outcomes = []
        timeout = None
        priority = "medium"
        tags = []
        
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check for section headers
            if line.lower().startswith('**description'):
                current_section = 'description'
                continue
            elif line.lower().startswith('**steps') or line.lower().startswith('**test steps'):
                current_section = 'steps'
                continue
            elif line.lower().startswith('**validation') or line.lower().startswith('**verify'):
                current_section = 'validations'
                continue
            elif line.lower().startswith('**expected') or line.lower().startswith('**outcome'):
                current_section = 'expected_outcomes'
                continue
            elif line.lower().startswith('**timeout'):
                timeout_match = re.search(r'(\d+)', line)
                if timeout_match:
                    timeout = int(timeout_match.group(1))
                continue
            elif line.lower().startswith('**priority'):
                priority_match = re.search(r'(low|medium|high|critical)', line.lower())
                if priority_match:
                    priority = priority_match.group(1)
                continue
            elif line.lower().startswith('**tags'):
                tag_match = re.findall(r'#(\w+)', line)
                tags.extend(tag_match)
                continue
            
            # Process content based on current section
            if current_section == 'description':
                if not description:
                    description = line
                else:
                    description += " " + line
            elif current_section == 'steps':
                if line.startswith(('-', '*', '1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.')):
                    # Remove list markers
                    step = re.sub(r'^[-*\d.]\s*', '', line)
                    steps.append(step)
                elif line and not line.startswith('**'):
                    steps.append(line)
            elif current_section == 'validations':
                if line.startswith(('-', '*', '1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.')):
                    validation = re.sub(r'^[-*\d.]\s*', '', line)
                    validations.append(validation)
                elif line and not line.startswith('**'):
                    validations.append(line)
            elif current_section == 'expected_outcomes':
                if line.startswith(('-', '*', '1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.')):
                    outcome = re.sub(r'^[-*\d.]\s*', '', line)
                    expected_outcomes.append(outcome)
                elif line and not line.startswith('**'):
                    expected_outcomes.append(line)
            elif current_section is None:
                # If no section specified, treat as description or steps
                if not description:
                    description = line
                elif line.startswith(('-', '*', '1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.')):
                    step = re.sub(r'^[-*\d.]\s*', '', line)
                    steps.append(step)
        
        # If no explicit description, use the scenario name
        if not description:
            description = f"Test scenario: {name}"
        
        # If no steps found, create a generic step
        if not steps:
            steps = [f"Navigate to the application and test {name.lower()}"]
        
        # If no validations, create basic ones
        if not validations:
            validations = ["Verify that the functionality works as expected", "Check for any console errors"]
        
        # If no expected outcomes, create basic ones
        if not expected_outcomes:
            expected_outcomes = ["All interactions should work smoothly", "No errors should occur"]
        
        return TestScenario(
            name=name,
            description=description,
            steps=steps,
            validations=validations,
            expected_outcomes=expected_outcomes,
            timeout=timeout,
            priority=priority,
            tags=tags
        )
    
    def _parse_yaml(self, content: str) -> List[TestScenario]:
        """Parse YAML instruction file."""
        try:
            data = yaml.safe_load(content)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML format: {e}")
        
        scenarios = []
        
        # Handle different YAML structures
        if isinstance(data, dict):
            if 'scenarios' in data:
                scenario_data = data['scenarios']
            elif 'tests' in data:
                scenario_data = data['tests']
            else:
                # Treat the entire dict as a single scenario
                scenario_data = [data]
        elif isinstance(data, list):
            scenario_data = data
        else:
            raise ValueError("Invalid YAML structure")
        
        for item in scenario_data:
            scenario = TestScenario(
                name=item.get('name', 'Unnamed Test'),
                description=item.get('description', ''),
                steps=item.get('steps', []),
                validations=item.get('validations', item.get('verify', [])),
                expected_outcomes=item.get('expected_outcomes', item.get('expected', [])),
                timeout=item.get('timeout'),
                priority=item.get('priority', 'medium'),
                tags=item.get('tags', [])
            )
            scenarios.append(scenario)
        
        return scenarios
    
    def _parse_json(self, content: str) -> List[TestScenario]:
        """Parse JSON instruction file."""
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")
        
        scenarios = []
        
        # Handle different JSON structures
        if isinstance(data, dict):
            if 'scenarios' in data:
                scenario_data = data['scenarios']
            elif 'tests' in data:
                scenario_data = data['tests']
            else:
                # Treat the entire dict as a single scenario
                scenario_data = [data]
        elif isinstance(data, list):
            scenario_data = data
        else:
            raise ValueError("Invalid JSON structure")
        
        for item in scenario_data:
            scenario = TestScenario(
                name=item.get('name', 'Unnamed Test'),
                description=item.get('description', ''),
                steps=item.get('steps', []),
                validations=item.get('validations', item.get('verify', [])),
                expected_outcomes=item.get('expected_outcomes', item.get('expected', [])),
                timeout=item.get('timeout'),
                priority=item.get('priority', 'medium'),
                tags=item.get('tags', [])
            )
            scenarios.append(scenario)
        
        return scenarios
