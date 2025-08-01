# CodegenApp CI/CD Flow Testing Instructions

## Overview
This document provides comprehensive instructions for testing the complete CI/CD flow of CodegenApp using web-eval-agent. The test validates the entire workflow from project setup to automated PR validation and merging.

## Prerequisites
- CodegenApp running on localhost (port will be detected)
- All environment variables configured
- GitHub repository access
- Cloudflare worker configured

## Test Environment Variables
The following environment variables must be configured in the CodegenApp settings:

```
CODEGEN_ORG_ID=323
CODEGEN_API_TOKEN=sk-ce027fa7-[REDACTED]
GITHUB_TOKEN=github_pat_11BPJSHDQ0[REDACTED]
GEMINI_API_KEY=AIzaSyBXmhlHudrD4zXiv-[REDACTED]
CLOUDFLARE_API_KEY=eae82cf159577a8838cc83612104c09c5a0d6
CLOUDFLARE_ACCOUNT_ID=2b2a1d3effa7f7fe4fe2a8c4e48681e3
CLOUDFLARE_WORKER_NAME=webhook-gateway
CLOUDFLARE_WORKER_URL=https://webhook-gateway.pixeliumperfecto.workers.dev
```

## Detailed Test Steps

### Step 1: Open Application URL
- **Action**: Navigate to the CodegenApp interface
- **Expected**: Application loads successfully
- **Validation**: Check for React dashboard with project management interface

### Step 2: Open Settings Dialog
- **Action**: Click on the settings/configuration button (usually gear icon or settings menu)
- **Expected**: Settings dialog opens
- **Validation**: Settings panel displays with various configuration sections

### Step 3: Input Environment Variables
Configure all required environment variables in the settings:

#### Codegen API Configuration
- **CODEGEN_ORG_ID**: `323`
- **CODEGEN_API_TOKEN**: `sk-ce027fa7-[REDACTED]`

#### GitHub Integration
- **GITHUB_TOKEN**: `github_pat_11BPJSHDQ0[REDACTED]`

#### AI Services
- **GEMINI_API_KEY**: `AIzaSyBXmhlHudrD4zXiv-[REDACTED]`

#### Cloudflare Configuration
- **CLOUDFLARE_API_KEY**: `eae82cf159577a8838cc83612104c09c5a0d6`
- **CLOUDFLARE_ACCOUNT_ID**: `2b2a1d3effa7f7fe4fe2a8c4e48681e3`
- **CLOUDFLARE_WORKER_NAME**: `webhook-gateway`
- **CLOUDFLARE_WORKER_URL**: `https://webhook-gateway.pixeliumperfecto.workers.dev`

**Validation**: All fields populated correctly, no validation errors

### Step 4: Add Project from Dropdown
- **Action**: Locate project selection dropdown
- **Target**: Select "web-eval-agent" from available projects
- **Expected**: Project appears in dropdown list
- **Validation**: Project successfully added to dashboard

### Step 5: Access Project Settings
- **Action**: Click the gear icon on the "web-eval-agent" project card
- **Expected**: Project-specific settings panel opens
- **Validation**: Settings panel shows project configuration options

### Step 6: Configure Automation Settings
- **Action**: Navigate to the "Automation" tab in project settings
- **Expected**: Automation configuration options displayed
- **Validation**: Three automation checkboxes are visible

#### Enable All Automation Features
Select all three checkboxes:
1. **Auto-merge PRs**: Automatically merge successful PRs
2. **Auto-confirm plans**: Skip manual plan confirmation
3. **Enhanced validation**: Enable comprehensive testing

**Validation**: All three checkboxes are checked/enabled

### Step 7: Save Configuration Changes
- **Action**: Click "Save Changes" button
- **Expected**: Settings saved successfully
- **Validation**: Success message displayed, settings persist

### Step 8: Initiate Agent Run
- **Action**: Click "Agent Run" button on the web-eval-agent project card
- **Expected**: Agent run dialog opens
- **Validation**: Input field for target/goal text is available

### Step 9: Input Agent Task
- **Action**: Enter the following task in the input field:
  ```
  Create PLAN.md in project's root
  ```
- **Expected**: Text input accepted
- **Validation**: Task description clearly visible in input field

### Step 10: Confirm Agent Execution
- **Action**: Click confirm/execute button to start the agent run
- **Expected**: Agent run begins processing
- **Validation**: Status indicator shows "running" or "in progress"

### Step 11: Verify PR Notification Counter
- **Action**: Monitor the GitHub icon on the project card
- **Expected**: PR notification counter increases by 1
- **Validation**: Counter shows new PR created (e.g., changes from 0 to 1)

### Step 12: Verify PR Validation Flow
- **Action**: Observe the validation pipeline status
- **Expected**: PR validation flow starts automatically
- **Validation**: Logs show validation process beginning

#### Validation Pipeline Checks:
1. **Snapshot Creation**: Grainchain creates isolated environment
2. **Code Deployment**: PR code deployed to test environment
3. **Setup Commands**: Project setup commands executed
4. **Validation Tests**: Web-eval-agent runs comprehensive tests
5. **Results Processing**: Test results analyzed

### Step 13: Monitor Validation Logs
- **Action**: Watch validation progress in real-time
- **Expected**: Detailed logs showing each validation step
- **Validation**: Logs indicate successful progression through pipeline

#### Expected Log Entries:
- "Creating snapshot for PR validation"
- "Cloning PR branch to test environment"
- "Running setup commands"
- "Starting web-eval-agent validation"
- "Validation tests completed"
- "Processing test results"

### Step 14: Verify PR Merge to Main
- **Action**: Monitor GitHub repository for PR merge
- **Expected**: PR automatically merged to main branch
- **Validation**: GitHub shows PR merged, main branch updated

#### Merge Validation Checks:
1. **PR Status**: Shows as "Merged"
2. **Main Branch**: Contains new PLAN.md file
3. **Commit History**: Shows merge commit
4. **Branch Cleanup**: Feature branch deleted (if configured)

### Step 15: Validate Requirements Completion
- **Action**: Verify that the original requirements were fully met
- **Expected**: PLAN.md file exists in project root with appropriate content
- **Validation**: File contains project planning information

#### Requirements Verification:
1. **File Existence**: PLAN.md present in repository root
2. **File Content**: Contains meaningful project planning content
3. **File Format**: Properly formatted Markdown
4. **Completeness**: Addresses the original task requirements

### Step 16: Verify Continuous Validation Loop
- **Action**: Check if system validates requirements completion
- **Expected**: System automatically verifies task completion
- **Validation**: No additional agent runs triggered (requirements fully met)

#### Completion Validation:
1. **Task Status**: Marked as "Completed"
2. **Requirements Check**: System confirms all requirements met
3. **No Further Actions**: No additional agent runs needed
4. **Final State**: Project in stable, completed state

## Success Criteria

### Primary Success Indicators
- ✅ All environment variables configured correctly
- ✅ Project successfully added and configured
- ✅ Agent run initiated and completed
- ✅ PR created and notification counter updated
- ✅ Validation pipeline executed successfully
- ✅ PR automatically merged to main branch
- ✅ Requirements fully satisfied (PLAN.md created)

### Secondary Success Indicators
- ✅ Real-time status updates throughout process
- ✅ Comprehensive logging of all steps
- ✅ Proper error handling (if any issues occur)
- ✅ Clean final state with no pending actions

### Failure Scenarios to Monitor
- ❌ Environment variable configuration errors
- ❌ GitHub API authentication failures
- ❌ Cloudflare worker communication issues
- ❌ Agent run execution failures
- ❌ PR creation or validation failures
- ❌ Merge conflicts or merge failures
- ❌ Incomplete requirement satisfaction

## Expected Timeline
- **Setup Phase**: 2-3 minutes (steps 1-7)
- **Execution Phase**: 5-10 minutes (steps 8-11)
- **Validation Phase**: 10-15 minutes (steps 12-14)
- **Completion Phase**: 2-3 minutes (steps 15-16)
- **Total Duration**: 20-30 minutes

## Troubleshooting

### Common Issues
1. **Authentication Errors**: Verify all API tokens are valid and have proper permissions
2. **Network Issues**: Check Cloudflare worker connectivity
3. **Validation Timeouts**: Monitor for long-running validation processes
4. **Merge Conflicts**: Ensure clean repository state before testing

### Debug Information to Collect
- Browser console logs
- Network request/response details
- Server-side application logs
- GitHub webhook delivery logs
- Cloudflare worker execution logs

## Post-Test Verification

### Repository State Check
1. Verify PLAN.md exists in main branch
2. Check commit history for proper merge
3. Confirm no orphaned branches
4. Validate webhook configurations remain intact

### System State Check
1. Verify all services remain operational
2. Check for any error logs or warnings
3. Confirm project settings persist correctly
4. Validate notification counters are accurate

## Test Completion Report

Upon successful completion, the test should demonstrate:
1. **Full CI/CD Pipeline**: Complete workflow from task input to deployed code
2. **Automated Validation**: AI-powered testing and validation
3. **Seamless Integration**: GitHub, Cloudflare, and Codegen working together
4. **Real-time Monitoring**: Live updates and status tracking
5. **Requirement Satisfaction**: Original task fully completed

This comprehensive test validates that the CodegenApp CI/CD flow works as designed, providing automated development workflow capabilities with intelligent validation and seamless integration across multiple services.
