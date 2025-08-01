#!/usr/bin/env python3

"""
GitHub integration for web-eval-agent.
Provides functionality to test UI from GitHub PRs and branches.
"""

import asyncio
import os
import tempfile
import shutil
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from pathlib import Path
import subprocess
import json

from .logging_config import get_logger, StructuredLogger
from .session_manager import SessionConfig


@dataclass
class GitHubPRInfo:
    """Information about a GitHub PR."""
    repo: str
    pr_number: int
    branch: str
    commit_sha: str
    title: str
    description: str
    author: str
    base_branch: str
    url: str
    
    @classmethod
    def from_api_response(cls, repo: str, pr_data: Dict[str, Any]) -> 'GitHubPRInfo':
        """Create from GitHub API response."""
        return cls(
            repo=repo,
            pr_number=pr_data['number'],
            branch=pr_data['head']['ref'],
            commit_sha=pr_data['head']['sha'],
            title=pr_data['title'],
            description=pr_data['body'] or '',
            author=pr_data['user']['login'],
            base_branch=pr_data['base']['ref'],
            url=pr_data['html_url']
        )


@dataclass
class DeploymentInfo:
    """Information about a deployed application."""
    url: str
    status: str
    environment: str
    commit_sha: str
    deployment_id: Optional[str] = None
    logs_url: Optional[str] = None


class GitHubIntegration:
    """
    GitHub integration for testing UI from PRs and branches.
    """
    
    def __init__(self, github_token: Optional[str] = None):
        self.github_token = github_token or os.getenv('GITHUB_TOKEN')
        self.logger = get_logger("github-integration")
        
        if not self.github_token:
            self.logger.warning("No GitHub token provided. Some features may not work.")
    
    async def get_pr_info(self, repo: str, pr_number: int) -> GitHubPRInfo:
        """Get information about a GitHub PR."""
        if not self.github_token:
            raise ValueError("GitHub token required for PR operations")
        
        import aiohttp
        
        url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"
        headers = {
            'Authorization': f'token {self.github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 404:
                    raise ValueError(f"PR #{pr_number} not found in {repo}")
                elif response.status != 200:
                    raise RuntimeError(f"GitHub API error: {response.status}")
                
                pr_data = await response.json()
                return GitHubPRInfo.from_api_response(repo, pr_data)
    
    async def get_branch_info(self, repo: str, branch: str) -> Dict[str, Any]:
        """Get information about a GitHub branch."""
        if not self.github_token:
            raise ValueError("GitHub token required for branch operations")
        
        import aiohttp
        
        url = f"https://api.github.com/repos/{repo}/branches/{branch}"
        headers = {
            'Authorization': f'token {self.github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 404:
                    raise ValueError(f"Branch '{branch}' not found in {repo}")
                elif response.status != 200:
                    raise RuntimeError(f"GitHub API error: {response.status}")
                
                return await response.json()
    
    async def detect_deployment_url(self, repo: str, pr_number: Optional[int] = None, 
                                  branch: Optional[str] = None) -> Optional[str]:
        """
        Detect deployment URL for a PR or branch.
        This is a heuristic-based approach that looks for common deployment patterns.
        """
        if pr_number:
            # Common PR deployment URL patterns
            patterns = [
                f"https://pr-{pr_number}--{repo.split('/')[-1]}.netlify.app",
                f"https://{repo.split('/')[-1]}-pr-{pr_number}.vercel.app",
                f"https://pr-{pr_number}.{repo.split('/')[-1]}.pages.dev",
                f"https://{repo.split('/')[-1]}-git-pr-{pr_number}.vercel.app",
            ]
        elif branch:
            # Common branch deployment URL patterns
            branch_safe = branch.replace('/', '-').replace('_', '-')
            patterns = [
                f"https://{branch_safe}--{repo.split('/')[-1]}.netlify.app",
                f"https://{repo.split('/')[-1]}-git-{branch_safe}.vercel.app",
                f"https://{branch_safe}.{repo.split('/')[-1]}.pages.dev",
            ]
        else:
            return None
        
        # Try to find a working deployment URL
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            for url in patterns:
                try:
                    async with session.get(url, timeout=10) as response:
                        if response.status == 200:
                            self.logger.info(f"Found deployment URL: {url}")
                            return url
                except:
                    continue
        
        self.logger.warning(f"No deployment URL found for {repo} PR#{pr_number} branch:{branch}")
        return None
    
    async def get_deployment_status(self, repo: str, commit_sha: str) -> List[DeploymentInfo]:
        """Get deployment status for a commit."""
        if not self.github_token:
            return []
        
        import aiohttp
        
        url = f"https://api.github.com/repos/{repo}/deployments"
        headers = {
            'Authorization': f'token {self.github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        params = {'sha': commit_sha}
        
        deployments = []
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        deployment_data = await response.json()
                        
                        for deployment in deployment_data:
                            # Get deployment status
                            status_url = f"https://api.github.com/repos/{repo}/deployments/{deployment['id']}/statuses"
                            async with session.get(status_url, headers=headers) as status_response:
                                if status_response.status == 200:
                                    statuses = await status_response.json()
                                    if statuses:
                                        latest_status = statuses[0]
                                        deployments.append(DeploymentInfo(
                                            url=latest_status.get('target_url', ''),
                                            status=latest_status['state'],
                                            environment=deployment['environment'],
                                            commit_sha=commit_sha,
                                            deployment_id=str(deployment['id']),
                                            logs_url=latest_status.get('log_url')
                                        ))
        except Exception as e:
            self.logger.error(f"Error getting deployment status: {e}")
        
        return deployments
    
    async def create_session_config_for_pr(self, repo: str, pr_number: int, 
                                         task: str, **kwargs) -> SessionConfig:
        """Create a session config for testing a GitHub PR."""
        pr_info = await self.get_pr_info(repo, pr_number)
        
        # Try to detect deployment URL
        deployment_url = await self.detect_deployment_url(repo, pr_number=pr_number)
        
        if not deployment_url:
            # Check for deployments via API
            deployments = await self.get_deployment_status(repo, pr_info.commit_sha)
            active_deployments = [d for d in deployments if d.status == 'success' and d.url]
            
            if active_deployments:
                deployment_url = active_deployments[0].url
        
        if not deployment_url:
            raise ValueError(f"No deployment URL found for PR #{pr_number} in {repo}")
        
        # Create enhanced task description with PR context
        enhanced_task = f"""
GitHub PR Context:
- Repository: {repo}
- PR #{pr_number}: {pr_info.title}
- Branch: {pr_info.branch}
- Author: {pr_info.author}
- Commit: {pr_info.commit_sha}
- PR URL: {pr_info.url}

Task: {task}

Please test the application thoroughly, paying special attention to:
1. Any changes mentioned in the PR description
2. UI/UX functionality and responsiveness
3. Error handling and edge cases
4. Performance and loading times
5. Cross-browser compatibility issues

PR Description:
{pr_info.description}
"""
        
        return SessionConfig(
            url=deployment_url,
            task=enhanced_task,
            github_repo=repo,
            github_pr=pr_number,
            github_branch=pr_info.branch,
            **kwargs
        )
    
    async def create_session_config_for_branch(self, repo: str, branch: str, 
                                             task: str, **kwargs) -> SessionConfig:
        """Create a session config for testing a GitHub branch."""
        branch_info = await self.get_branch_info(repo, branch)
        
        # Try to detect deployment URL
        deployment_url = await self.detect_deployment_url(repo, branch=branch)
        
        if not deployment_url:
            # Check for deployments via API
            commit_sha = branch_info['commit']['sha']
            deployments = await self.get_deployment_status(repo, commit_sha)
            active_deployments = [d for d in deployments if d.status == 'success' and d.url]
            
            if active_deployments:
                deployment_url = active_deployments[0].url
        
        if not deployment_url:
            raise ValueError(f"No deployment URL found for branch '{branch}' in {repo}")
        
        # Create enhanced task description with branch context
        enhanced_task = f"""
GitHub Branch Context:
- Repository: {repo}
- Branch: {branch}
- Commit: {branch_info['commit']['sha']}
- Last commit message: {branch_info['commit']['commit']['message']}

Task: {task}

Please test the application thoroughly, focusing on:
1. Core functionality and features
2. UI/UX quality and responsiveness
3. Error handling and edge cases
4. Performance and loading times
5. Any recent changes or new features
"""
        
        return SessionConfig(
            url=deployment_url,
            task=enhanced_task,
            github_repo=repo,
            github_branch=branch,
            **kwargs
        )
    
    async def post_evaluation_comment(self, repo: str, pr_number: int, 
                                    evaluation_result: Dict[str, Any]) -> bool:
        """Post evaluation results as a comment on the PR."""
        if not self.github_token:
            self.logger.warning("Cannot post PR comment without GitHub token")
            return False
        
        import aiohttp
        
        # Format evaluation result as markdown comment
        comment = self._format_evaluation_comment(evaluation_result)
        
        url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
        headers = {
            'Authorization': f'token {self.github_token}',
            'Accept': 'application/vnd.github.v3+json',
            'Content-Type': 'application/json'
        }
        
        data = {'body': comment}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as response:
                    if response.status == 201:
                        self.logger.info(f"Posted evaluation comment to PR #{pr_number}")
                        return True
                    else:
                        self.logger.error(f"Failed to post PR comment: {response.status}")
                        return False
        except Exception as e:
            self.logger.error(f"Error posting PR comment: {e}")
            return False
    
    def _format_evaluation_comment(self, evaluation_result: Dict[str, Any]) -> str:
        """Format evaluation result as a markdown comment."""
        success = evaluation_result.get('success', False)
        summary = evaluation_result.get('summary', 'No summary available')
        metrics = evaluation_result.get('metrics', {})
        
        # Create status emoji
        status_emoji = "✅" if success else "❌"
        
        comment = f"""## {status_emoji} Web Evaluation Results

**Status:** {'Passed' if success else 'Failed'}

### Summary
{summary}

### Metrics
"""
        
        if metrics:
            comment += f"""
- **Duration:** {metrics.get('duration', 'N/A')} seconds
- **Actions Performed:** {metrics.get('total_actions', 'N/A')}
- **Successful Actions:** {metrics.get('successful_actions', 'N/A')}
- **Failed Actions:** {metrics.get('failed_actions', 'N/A')}
- **Screenshots Taken:** {metrics.get('screenshots_taken', 'N/A')}
- **Network Requests:** {metrics.get('network_requests', 'N/A')}
- **Console Errors:** {metrics.get('console_errors', 'N/A')}
"""
        
        # Add detailed results if available
        if 'detailed_results' in evaluation_result:
            comment += f"""
### Detailed Results
```
{evaluation_result['detailed_results']}
```
"""
        
        comment += f"""
---
*Automated evaluation by web-eval-agent*
"""
        
        return comment


# Convenience functions
async def test_github_pr(repo: str, pr_number: int, task: str, 
                        github_token: Optional[str] = None, **kwargs) -> Dict[str, Any]:
    """Test a GitHub PR with the web evaluation agent."""
    from .session_manager import get_session_manager
    from .tool_handlers import handle_web_evaluation
    
    integration = GitHubIntegration(github_token)
    session_manager = get_session_manager()
    
    # Create session config
    config = await integration.create_session_config_for_pr(repo, pr_number, task, **kwargs)
    
    # Run evaluation
    async with session_manager.evaluation_session(config) as session_id:
        result = await session_manager.run_evaluation(
            session_id,
            lambda browser_instance, config: handle_web_evaluation(
                {
                    'url': config.url,
                    'task': config.task,
                    'headless_browser': config.headless
                },
                None,  # context
                config.api_key
            )
        )
    
    return result


async def test_github_branch(repo: str, branch: str, task: str, 
                           github_token: Optional[str] = None, **kwargs) -> Dict[str, Any]:
    """Test a GitHub branch with the web evaluation agent."""
    from .session_manager import get_session_manager
    from .tool_handlers import handle_web_evaluation
    
    integration = GitHubIntegration(github_token)
    session_manager = get_session_manager()
    
    # Create session config
    config = await integration.create_session_config_for_branch(repo, branch, task, **kwargs)
    
    # Run evaluation
    async with session_manager.evaluation_session(config) as session_id:
        result = await session_manager.run_evaluation(
            session_id,
            lambda browser_instance, config: handle_web_evaluation(
                {
                    'url': config.url,
                    'task': config.task,
                    'headless_browser': config.headless
                },
                None,  # context
                config.api_key
            )
        )
    
    return result

