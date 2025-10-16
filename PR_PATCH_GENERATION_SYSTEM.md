# PR/Patch Generation System Design

## Overview

Design for automated PR/patch generation system that allows users to create GitHub Pull Requests directly from validation workflow. This enables collaborative timeline curation with proper version control integration.

## Architecture Components

### 1. Patch Generation API Endpoint

**Location**: `research_monitor/app_v2.py`

New endpoint for generating patches and PRs:

```python
@app.route('/api/validation/generate-patch', methods=['POST'])
@require_api_key
def generate_validation_patch():
    """Generate patch file or GitHub PR from validation data"""
    db = get_db()
    try:
        data = request.json or {}
        
        patch_type = data.get('type', 'validation')  # validation, enhancement, correction
        description = data.get('description', '')
        validation_data = data.get('validationData', {})
        event_data = data.get('event', {})
        create_pr = data.get('create_pr', False)
        
        generator = PatchGenerator(db)
        
        if create_pr:
            # Create GitHub PR
            pr_result = generator.create_github_pr(
                patch_type=patch_type,
                description=description,
                validation_data=validation_data,
                event_data=event_data
            )
            return jsonify(pr_result)
        else:
            # Generate patch file
            patch_result = generator.generate_patch_file(
                patch_type=patch_type,
                description=description,
                validation_data=validation_data,
                event_data=event_data
            )
            return jsonify(patch_result)
            
    except Exception as e:
        logger.error(f"Error generating patch: {e}")
        return jsonify({'error': 'Failed to generate patch'}), 500
    finally:
        db.close()
```

### 2. PatchGenerator Class

**Location**: `research_monitor/patch_generator.py`

```python
#!/usr/bin/env python3
"""
Patch Generation System - Create GitHub PRs and patch files from validation workflow
Enables collaborative timeline curation with proper version control
"""

import json
import os
import subprocess
import tempfile
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
import git
from github import Github
from jinja2 import Template

class PatchGenerator:
    """Generate patches and PRs from validation data"""
    
    def __init__(self, db_session):
        self.db = db_session
        self.repo_path = Path(__file__).parent.parent  # kleptocracy-timeline root
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.github_repo = os.getenv('GITHUB_REPO', 'user/kleptocracy-timeline')
        
    def create_github_pr(self, patch_type: str, description: str, 
                        validation_data: Dict, event_data: Dict) -> Dict[str, Any]:
        """Create a GitHub Pull Request with validation changes"""
        
        try:
            # Initialize GitHub client
            if not self.github_token:
                raise ValueError("GitHub token not configured")
            
            g = Github(self.github_token)
            repo = g.get_repo(self.github_repo)
            
            # Create branch name
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            branch_name = f"validation/{patch_type}-{event_data.get('id', 'unknown')}-{timestamp}"
            
            # Get main branch
            main_branch = repo.get_branch('main')
            
            # Create new branch
            repo.create_git_ref(
                ref=f"refs/heads/{branch_name}",
                sha=main_branch.commit.sha
            )
            
            # Generate changes
            changes = self._generate_changes(patch_type, validation_data, event_data)
            
            # Apply changes to repository
            for file_path, content in changes.items():
                try:
                    # Get existing file
                    file = repo.get_contents(file_path, ref=branch_name)
                    
                    # Update file
                    repo.update_file(
                        path=file_path,
                        message=f"{patch_type}: {description}",
                        content=content,
                        sha=file.sha,
                        branch=branch_name
                    )
                except Exception:
                    # File doesn't exist, create it
                    repo.create_file(
                        path=file_path,
                        message=f"{patch_type}: {description}",
                        content=content,
                        branch=branch_name
                    )
            
            # Create Pull Request
            pr_title = self._generate_pr_title(patch_type, validation_data, event_data)
            pr_body = self._generate_pr_body(patch_type, description, validation_data, event_data)
            
            pr = repo.create_pull(
                title=pr_title,
                body=pr_body,
                head=branch_name,
                base='main'
            )
            
            # Add labels
            labels = self._get_pr_labels(patch_type, validation_data)
            if labels:
                pr.add_to_labels(*labels)
            
            return {
                'success': True,
                'pr_url': pr.html_url,
                'pr_number': pr.number,
                'branch_name': branch_name,
                'changes': list(changes.keys()),
                'message': 'Pull Request created successfully'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to create Pull Request'
            }
    
    def generate_patch_file(self, patch_type: str, description: str,
                           validation_data: Dict, event_data: Dict) -> Dict[str, Any]:
        """Generate a patch file for manual application"""
        
        try:
            # Generate changes
            changes = self._generate_changes(patch_type, validation_data, event_data)
            
            # Create temporary directory for patch generation
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Create patch using git
                repo = git.Repo(self.repo_path)
                
                # Create temporary files with changes
                for file_path, content in changes.items():
                    full_path = temp_path / file_path
                    full_path.parent.mkdir(parents=True, exist_ok=True)
                    full_path.write_text(content)
                
                # Generate patch
                patch_content = self._generate_git_patch(changes, description)
                
                # Save patch file
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                patch_filename = f"validation-{patch_type}-{timestamp}.patch"
                patch_path = self.repo_path / "patches" / patch_filename
                patch_path.parent.mkdir(exist_ok=True)
                patch_path.write_text(patch_content)
                
                return {
                    'success': True,
                    'patch_file': str(patch_path),
                    'patch_content': patch_content,
                    'changes': list(changes.keys()),
                    'message': 'Patch file generated successfully'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to generate patch file'
            }
    
    def _generate_changes(self, patch_type: str, validation_data: Dict, 
                         event_data: Dict) -> Dict[str, str]:
        """Generate file changes based on patch type and validation data"""
        
        changes = {}
        
        if patch_type == 'validation':
            # Add validation log to validation_logs directory
            changes.update(self._create_validation_log_files(validation_data, event_data))
        
        elif patch_type == 'enhancement':
            # Update event file with improvements
            changes.update(self._enhance_event_file(validation_data, event_data))
            changes.update(self._create_validation_log_files(validation_data, event_data))
        
        elif patch_type == 'correction':
            # Fix event data and add validation log
            changes.update(self._correct_event_file(validation_data, event_data))
            changes.update(self._create_validation_log_files(validation_data, event_data))
        
        return changes
    
    def _create_validation_log_files(self, validation_data: Dict, event_data: Dict) -> Dict[str, str]:
        """Create validation log files"""
        
        changes = {}
        
        # Create validation log directory if it doesn't exist
        log_dir = f"validation_logs/{event_data.get('id', 'unknown')}"
        
        # Generate validation log file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_filename = f"{log_dir}/validation_{timestamp}.json"
        
        log_content = {
            'event_id': event_data.get('id'),
            'validation_date': datetime.now().isoformat(),
            'validator_type': 'human',
            'validator_id': validation_data.get('validator_id', 'web-user'),
            'status': validation_data.get('status'),
            'confidence': validation_data.get('confidence'),
            'notes': validation_data.get('notes'),
            'issues_found': validation_data.get('issues_found', []),
            'sources_verified': validation_data.get('sources_verified', []),
            'time_spent_minutes': validation_data.get('time_spent_minutes'),
            'validation_criteria': validation_data.get('validation_criteria', {}),
            'generated_by': 'web_ui_validation_workflow'
        }
        
        changes[log_filename] = json.dumps(log_content, indent=2)
        
        return changes
    
    def _enhance_event_file(self, validation_data: Dict, event_data: Dict) -> Dict[str, str]:
        """Enhance event file with validation improvements"""
        
        changes = {}
        event_id = event_data.get('id')
        
        if not event_id:
            return changes
        
        # Read current event file
        event_file = f"timeline_data/events/{event_id}.json"
        event_path = self.repo_path / event_file
        
        if event_path.exists():
            current_event = json.loads(event_path.read_text())
        else:
            current_event = event_data.copy()
        
        # Apply enhancements based on validation data
        corrections = validation_data.get('corrections_made', {})
        if corrections:
            for field, value in corrections.items():
                if field in current_event:
                    current_event[field] = value
        
        # Add validation metadata
        if 'validation_metadata' not in current_event:
            current_event['validation_metadata'] = {}
        
        current_event['validation_metadata'].update({
            'last_validated': datetime.now().isoformat(),
            'validation_status': validation_data.get('status'),
            'validation_confidence': validation_data.get('confidence')
        })
        
        changes[event_file] = json.dumps(current_event, indent=2)
        
        return changes
    
    def _correct_event_file(self, validation_data: Dict, event_data: Dict) -> Dict[str, str]:
        """Correct event file based on validation findings"""
        
        # Similar to enhance but focused on corrections
        return self._enhance_event_file(validation_data, event_data)
    
    def _generate_pr_title(self, patch_type: str, validation_data: Dict, event_data: Dict) -> str:
        """Generate PR title based on patch type and data"""
        
        event_title = event_data.get('title', 'Unknown Event')
        status = validation_data.get('status', 'validated')
        
        titles = {
            'validation': f"Validation: Mark '{event_title}' as {status}",
            'enhancement': f"Enhancement: Improve '{event_title}' based on validation",
            'correction': f"Correction: Fix issues in '{event_title}'"
        }
        
        return titles.get(patch_type, f"Update: '{event_title}'")
    
    def _generate_pr_body(self, patch_type: str, description: str, 
                         validation_data: Dict, event_data: Dict) -> str:
        """Generate PR body with validation details"""
        
        template = Template("""
## Validation Summary

**Event**: {{ event_title }}
**Date**: {{ event_date }}
**Validation Status**: {{ validation_status }}
**Confidence**: {{ confidence }}%

## Changes Made

{{ description }}

## Validation Details

**Notes**: {{ validation_notes }}

{% if issues_found %}
**Issues Found**:
{% for issue in issues_found %}
- {{ issue }}
{% endfor %}
{% endif %}

{% if sources_verified %}
**Sources Verified**:
{% for source in sources_verified %}
- {{ source }}
{% endfor %}
{% endif %}

**Time Spent**: {{ time_spent }} minutes
**Validator**: {{ validator_id }}

---
🤖 Generated from Timeline Validation Workflow
        """).strip()
        
        return template.render(
            event_title=event_data.get('title', 'Unknown'),
            event_date=event_data.get('date', 'Unknown'),
            validation_status=validation_data.get('status', 'unknown'),
            confidence=int((validation_data.get('confidence', 0) * 100)),
            description=description,
            validation_notes=validation_data.get('notes', ''),
            issues_found=validation_data.get('issues_found', []),
            sources_verified=validation_data.get('sources_verified', []),
            time_spent=validation_data.get('time_spent_minutes', 0),
            validator_id=validation_data.get('validator_id', 'web-user')
        )
    
    def _get_pr_labels(self, patch_type: str, validation_data: Dict) -> List[str]:
        """Get appropriate labels for the PR"""
        
        labels = ['validation']
        
        if patch_type == 'enhancement':
            labels.append('enhancement')
        elif patch_type == 'correction':
            labels.append('bug')
        
        status = validation_data.get('status')
        if status in ['flagged', 'needs_work']:
            labels.append('needs-review')
        elif status == 'rejected':
            labels.append('rejected')
        
        return labels
    
    def _generate_git_patch(self, changes: Dict[str, str], description: str) -> str:
        """Generate a git-style patch file"""
        
        patch_lines = [
            f"Subject: [PATCH] {description}",
            "",
            f"Generated on: {datetime.now().isoformat()}",
            f"Files changed: {len(changes)}",
            "",
            "---"
        ]
        
        for file_path, content in changes.items():
            patch_lines.extend([
                "",
                f"diff --git a/{file_path} b/{file_path}",
                f"--- a/{file_path}",
                f"+++ b/{file_path}",
                "@@ -0,0 +1,1 @@",
                f"+{content}"
            ])
        
        return "\n".join(patch_lines)
```

### 3. Environment Configuration

**Location**: `research_monitor/.env`

```bash
# GitHub Integration
GITHUB_TOKEN=your_github_personal_access_token
GITHUB_REPO=username/kleptocracy-timeline
GITHUB_BASE_BRANCH=main

# Patch Configuration  
ENABLE_PR_GENERATION=true
PATCH_DIRECTORY=patches
VALIDATION_LOGS_DIRECTORY=validation_logs
```

### 4. Web UI Integration

**Location**: `viewer/src/components/PatchGenerator.js`

```jsx
import React, { useState } from 'react';
import { GitPullRequest, Download, AlertCircle, CheckCircle } from 'lucide-react';
import { validationAPI } from '../services/validationService';

const PatchGenerator = ({ event, validationData, onCreatePatch }) => {
  const [patchType, setPatchType] = useState('validation');
  const [description, setDescription] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [result, setResult] = useState(null);

  const handleGeneratePatch = async (createPR = false) => {
    setIsGenerating(true);
    setResult(null);
    
    try {
      const patchData = {
        type: patchType,
        description: description || `${patchType} for ${event.title}`,
        validationData,
        event,
        create_pr: createPR
      };
      
      const response = await validationAPI.generatePatch(patchData);
      setResult(response);
      
      if (onCreatePatch) {
        onCreatePatch(response);
      }
    } catch (error) {
      setResult({
        success: false,
        error: error.message,
        message: 'Failed to generate patch'
      });
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="patch-generator border-t pt-4 mt-4">
      <h4 className="font-semibold mb-4">Generate Patch/PR</h4>
      
      {/* Patch Type Selection */}
      <div className="mb-4">
        <label className="block text-sm font-medium mb-2">Patch Type</label>
        <select 
          value={patchType}
          onChange={(e) => setPatchType(e.target.value)}
          className="w-full p-2 border rounded"
        >
          <option value="validation">Validation Only</option>
          <option value="enhancement">Enhancement</option>
          <option value="correction">Correction</option>
        </select>
      </div>
      
      {/* Description */}
      <div className="mb-4">
        <label className="block text-sm font-medium mb-2">Description</label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Describe the changes being made..."
          className="w-full p-2 border rounded"
          rows={3}
        />
      </div>
      
      {/* Action Buttons */}
      <div className="flex space-x-2 mb-4">
        <button
          onClick={() => handleGeneratePatch(false)}
          disabled={isGenerating}
          className="flex items-center px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700 disabled:opacity-50"
        >
          <Download className="w-4 h-4 mr-2" />
          {isGenerating ? 'Generating...' : 'Generate Patch File'}
        </button>
        
        <button
          onClick={() => handleGeneratePatch(true)}
          disabled={isGenerating}
          className="flex items-center px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
        >
          <GitPullRequest className="w-4 h-4 mr-2" />
          {isGenerating ? 'Creating...' : 'Create PR'}
        </button>
      </div>
      
      {/* Result Display */}
      {result && (
        <div className={`p-3 rounded ${result.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
          <div className="flex items-center">
            {result.success ? (
              <CheckCircle className="w-5 h-5 text-green-600 mr-2" />
            ) : (
              <AlertCircle className="w-5 h-5 text-red-600 mr-2" />
            )}
            <span className={result.success ? 'text-green-800' : 'text-red-800'}>
              {result.message}
            </span>
          </div>
          
          {result.success && result.pr_url && (
            <div className="mt-2">
              <a 
                href={result.pr_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:text-blue-800"
              >
                View Pull Request #{result.pr_number}
              </a>
            </div>
          )}
          
          {result.success && result.patch_file && (
            <div className="mt-2">
              <span className="text-sm text-gray-600">
                Patch saved to: {result.patch_file}
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default PatchGenerator;
```

### 5. Implementation Steps

1. **Backend Setup** (Day 1-2)
   - Add patch generation endpoint to Flask app
   - Implement PatchGenerator class
   - Set up GitHub API integration

2. **Frontend Integration** (Day 3-4)
   - Create PatchGenerator component
   - Add to ValidationPanel
   - Implement API service methods

3. **Testing & Refinement** (Day 5-6)
   - Test patch generation workflow
   - Test GitHub PR creation
   - Handle error cases and edge conditions

4. **Documentation** (Day 7)
   - Update user documentation
   - Add developer setup instructions
   - Document GitHub token configuration

This system provides a complete workflow from manual validation to automated PR creation, enabling seamless collaborative timeline curation.