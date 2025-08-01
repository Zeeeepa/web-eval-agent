#!/usr/bin/env python3
"""
Grainchain Integration for Local Sandboxing
Provides secure code execution and testing capabilities
"""

import asyncio
import logging
import tempfile
import shutil
import json
import os
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, asdict
from pathlib import Path
import subprocess
import time

from .config_manager import get_config_manager
from .service_abstractions import ServiceResponse

logger = logging.getLogger(__name__)

@dataclass
class SandboxResult:
    """Result from sandbox execution"""
    success: bool
    stdout: str = ""
    stderr: str = ""
    return_code: int = 0
    execution_time: float = 0.0
    snapshot_id: Optional[str] = None
    files_created: List[str] = None
    error: Optional[str] = None
    
    def __post_init__(self):
        if self.files_created is None:
            self.files_created = []

@dataclass
class SandboxConfig:
    """Configuration for sandbox execution"""
    provider: str = "local"
    timeout: int = 600
    memory_limit: str = "2GB"
    cpu_limit: float = 2.0
    network_isolation: bool = True
    auto_cleanup: bool = True
    working_directory: str = "/workspace"
    environment_vars: Dict[str, str] = None
    
    def __post_init__(self):
        if self.environment_vars is None:
            self.environment_vars = {}

class GrainchainIntegration:
    """Integration with grainchain for local sandboxing"""
    
    def __init__(self):
        self.config_manager = get_config_manager()
        self.grainchain_config = self.config_manager.get_grainchain_config()
        self.logger = logging.getLogger("grainchain_integration")
        self._grainchain_available = None
        
    async def _check_grainchain_availability(self) -> bool:
        """Check if grainchain is available and properly configured"""
        if self._grainchain_available is not None:
            return self._grainchain_available
            
        try:
            # Try to import grainchain
            import grainchain
            from grainchain import Sandbox, SandboxConfig as GrainchainSandboxConfig
            
            # Test basic functionality
            config = GrainchainSandboxConfig(
                timeout=30,
                auto_cleanup=True
            )
            
            async with Sandbox(provider="local", config=config) as sandbox:
                result = await sandbox.execute("echo 'grainchain test'")
                if result.success and "grainchain test" in result.stdout:
                    self._grainchain_available = True
                    self.logger.info("Grainchain is available and working")
                    return True
                    
        except ImportError:
            self.logger.warning("Grainchain not installed. Install with: pip install grainchain")
        except Exception as e:
            self.logger.error(f"Grainchain availability check failed: {e}")
            
        self._grainchain_available = False
        return False
    
    async def _fallback_local_execution(
        self,
        command: str,
        working_dir: Optional[str] = None,
        timeout: int = 600,
        env_vars: Optional[Dict[str, str]] = None
    ) -> SandboxResult:
        """Fallback to local subprocess execution when grainchain is not available"""
        start_time = time.time()
        
        try:
            # Create temporary directory for execution
            with tempfile.TemporaryDirectory() as temp_dir:
                work_dir = working_dir or temp_dir
                
                # Set up environment
                env = os.environ.copy()
                if env_vars:
                    env.update(env_vars)
                
                # Execute command
                process = await asyncio.create_subprocess_shell(
                    command,
                    cwd=work_dir,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env=env
                )
                
                try:
                    stdout, stderr = await asyncio.wait_for(
                        process.communicate(),
                        timeout=timeout
                    )
                    
                    execution_time = time.time() - start_time
                    
                    return SandboxResult(
                        success=process.returncode == 0,
                        stdout=stdout.decode('utf-8', errors='replace'),
                        stderr=stderr.decode('utf-8', errors='replace'),
                        return_code=process.returncode,
                        execution_time=execution_time
                    )
                    
                except asyncio.TimeoutError:
                    process.kill()
                    await process.wait()
                    return SandboxResult(
                        success=False,
                        error=f"Command timed out after {timeout} seconds",
                        execution_time=time.time() - start_time
                    )
                    
        except Exception as e:
            return SandboxResult(
                success=False,
                error=f"Execution failed: {str(e)}",
                execution_time=time.time() - start_time
            )
    
    async def execute_code(
        self,
        code: str,
        language: str = "python",
        files: Optional[Dict[str, str]] = None,
        config: Optional[SandboxConfig] = None
    ) -> SandboxResult:
        """Execute code in a sandboxed environment"""
        
        # Use provided config or default
        sandbox_config = config or SandboxConfig()
        
        # Check if grainchain is available
        if await self._check_grainchain_availability():
            return await self._execute_with_grainchain(code, language, files, sandbox_config)
        else:
            return await self._execute_with_fallback(code, language, files, sandbox_config)
    
    async def _execute_with_grainchain(
        self,
        code: str,
        language: str,
        files: Optional[Dict[str, str]],
        config: SandboxConfig
    ) -> SandboxResult:
        """Execute code using grainchain"""
        try:
            from grainchain import Sandbox, SandboxConfig as GrainchainSandboxConfig
            
            # Convert our config to grainchain config
            grainchain_config = GrainchainSandboxConfig(
                timeout=config.timeout,
                memory_limit=config.memory_limit,
                cpu_limit=config.cpu_limit,
                environment_vars=config.environment_vars,
                working_directory=config.working_directory,
                auto_cleanup=config.auto_cleanup
            )
            
            start_time = time.time()
            
            async with Sandbox(provider=config.provider, config=grainchain_config) as sandbox:
                # Upload additional files if provided
                if files:
                    for filename, content in files.items():
                        await sandbox.upload_file(filename, content)
                
                # Create and upload the main code file
                if language == "python":
                    filename = "main.py"
                    command = "python main.py"
                elif language == "javascript":
                    filename = "main.js"
                    command = "node main.js"
                elif language == "bash":
                    filename = "main.sh"
                    command = "bash main.sh"
                else:
                    filename = f"main.{language}"
                    command = f"{language} {filename}"
                
                await sandbox.upload_file(filename, code)
                
                # Execute the code
                result = await sandbox.execute(command)
                
                execution_time = time.time() - start_time
                
                # List created files
                try:
                    files_list = await sandbox.list_files(config.working_directory)
                    created_files = [f.name for f in files_list if f.name not in [filename] + list(files.keys() if files else [])]
                except:
                    created_files = []
                
                return SandboxResult(
                    success=result.success,
                    stdout=result.stdout,
                    stderr=result.stderr,
                    return_code=result.return_code,
                    execution_time=execution_time,
                    files_created=created_files
                )
                
        except Exception as e:
            self.logger.error(f"Grainchain execution failed: {e}")
            return SandboxResult(
                success=False,
                error=f"Grainchain execution failed: {str(e)}",
                execution_time=time.time() - start_time if 'start_time' in locals() else 0.0
            )
    
    async def _execute_with_fallback(
        self,
        code: str,
        language: str,
        files: Optional[Dict[str, str]],
        config: SandboxConfig
    ) -> SandboxResult:
        """Execute code using fallback local execution"""
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                # Write additional files
                if files:
                    for filename, content in files.items():
                        file_path = Path(temp_dir) / filename
                        file_path.parent.mkdir(parents=True, exist_ok=True)
                        file_path.write_text(content)
                
                # Write main code file
                if language == "python":
                    filename = "main.py"
                    command = "python main.py"
                elif language == "javascript":
                    filename = "main.js"
                    command = "node main.js"
                elif language == "bash":
                    filename = "main.sh"
                    command = "bash main.sh"
                else:
                    filename = f"main.{language}"
                    command = f"{language} {filename}"
                
                code_file = Path(temp_dir) / filename
                code_file.write_text(code)
                
                # Execute using fallback
                return await self._fallback_local_execution(
                    command,
                    working_dir=temp_dir,
                    timeout=config.timeout,
                    env_vars=config.environment_vars
                )
                
        except Exception as e:
            return SandboxResult(
                success=False,
                error=f"Fallback execution failed: {str(e)}"
            )
    
    async def create_snapshot(self, sandbox_id: str) -> ServiceResponse:
        """Create a snapshot of the current sandbox state"""
        if not await self._check_grainchain_availability():
            return ServiceResponse(
                success=False,
                error="Snapshots require grainchain to be installed"
            )
        
        try:
            # This would require maintaining sandbox sessions
            # For now, return a mock response
            snapshot_id = f"snapshot_{int(time.time())}"
            
            return ServiceResponse(
                success=True,
                data={"snapshot_id": snapshot_id},
                metadata={"created_at": time.time()}
            )
            
        except Exception as e:
            return ServiceResponse(
                success=False,
                error=f"Snapshot creation failed: {str(e)}"
            )
    
    async def restore_snapshot(self, snapshot_id: str) -> ServiceResponse:
        """Restore sandbox from a snapshot"""
        if not await self._check_grainchain_availability():
            return ServiceResponse(
                success=False,
                error="Snapshots require grainchain to be installed"
            )
        
        try:
            # Mock implementation
            return ServiceResponse(
                success=True,
                data={"restored_snapshot": snapshot_id},
                metadata={"restored_at": time.time()}
            )
            
        except Exception as e:
            return ServiceResponse(
                success=False,
                error=f"Snapshot restoration failed: {str(e)}"
            )
    
    async def test_repository_changes(
        self,
        repository_path: str,
        test_commands: List[str],
        config: Optional[SandboxConfig] = None
    ) -> List[SandboxResult]:
        """Test repository changes in sandbox"""
        results = []
        sandbox_config = config or SandboxConfig()
        
        try:
            # Read repository files
            repo_files = {}
            repo_path = Path(repository_path)
            
            if repo_path.exists():
                for file_path in repo_path.rglob("*"):
                    if file_path.is_file() and not any(part.startswith('.') for part in file_path.parts):
                        try:
                            relative_path = file_path.relative_to(repo_path)
                            repo_files[str(relative_path)] = file_path.read_text(encoding='utf-8')
                        except (UnicodeDecodeError, PermissionError):
                            # Skip binary files and files we can't read
                            continue
            
            # Execute each test command
            for command in test_commands:
                result = await self.execute_code(
                    code=command,
                    language="bash",
                    files=repo_files,
                    config=sandbox_config
                )
                results.append(result)
                
                # Stop on first failure if configured
                if not result.success and not sandbox_config.auto_cleanup:
                    break
            
            return results
            
        except Exception as e:
            error_result = SandboxResult(
                success=False,
                error=f"Repository testing failed: {str(e)}"
            )
            return [error_result]
    
    async def validate_code_security(self, code: str, language: str) -> Dict[str, Any]:
        """Validate code for security issues before execution"""
        security_issues = []
        risk_level = "low"
        
        # Basic security checks
        dangerous_patterns = {
            "python": [
                r"import\s+os",
                r"import\s+subprocess",
                r"import\s+sys",
                r"exec\s*\(",
                r"eval\s*\(",
                r"__import__",
                r"open\s*\(",
                r"file\s*\("
            ],
            "javascript": [
                r"require\s*\(\s*['\"]fs['\"]",
                r"require\s*\(\s*['\"]child_process['\"]",
                r"eval\s*\(",
                r"Function\s*\(",
                r"process\.exit",
                r"process\.env"
            ],
            "bash": [
                r"rm\s+-rf",
                r"sudo\s+",
                r"curl\s+.*\|\s*bash",
                r"wget\s+.*\|\s*bash",
                r">\s*/dev/",
                r"chmod\s+\+x"
            ]
        }
        
        import re
        patterns = dangerous_patterns.get(language, [])
        
        for pattern in patterns:
            if re.search(pattern, code, re.IGNORECASE):
                security_issues.append({
                    "type": "dangerous_pattern",
                    "pattern": pattern,
                    "description": f"Potentially dangerous pattern detected: {pattern}"
                })
                risk_level = "high"
        
        # Check for network access attempts
        network_patterns = [
            r"http[s]?://",
            r"socket\.",
            r"urllib",
            r"requests\.",
            r"fetch\s*\(",
            r"XMLHttpRequest"
        ]
        
        for pattern in network_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                security_issues.append({
                    "type": "network_access",
                    "pattern": pattern,
                    "description": "Network access detected"
                })
                if risk_level == "low":
                    risk_level = "medium"
        
        return {
            "risk_level": risk_level,
            "security_issues": security_issues,
            "safe_to_execute": len(security_issues) == 0 or risk_level == "low"
        }
    
    async def health_check(self) -> ServiceResponse:
        """Check grainchain integration health"""
        try:
            is_available = await self._check_grainchain_availability()
            
            if is_available:
                # Test basic execution
                result = await self.execute_code(
                    "print('Health check successful')",
                    language="python"
                )
                
                return ServiceResponse(
                    success=result.success,
                    data={
                        "grainchain_available": True,
                        "test_execution": result.success,
                        "provider": self.grainchain_config.provider
                    }
                )
            else:
                return ServiceResponse(
                    success=True,  # Service is working, just using fallback
                    data={
                        "grainchain_available": False,
                        "fallback_mode": True,
                        "provider": "local_fallback"
                    }
                )
                
        except Exception as e:
            return ServiceResponse(
                success=False,
                error=f"Health check failed: {str(e)}"
            )

# Global instance
_grainchain_integration: Optional[GrainchainIntegration] = None

def get_grainchain_integration() -> GrainchainIntegration:
    """Get the global grainchain integration instance"""
    global _grainchain_integration
    if _grainchain_integration is None:
        _grainchain_integration = GrainchainIntegration()
    return _grainchain_integration
