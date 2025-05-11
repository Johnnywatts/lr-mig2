# AI/Cursor Integration Specification

This document defines the standard formats and protocols for AI assistant interactions with the Cursor IDE. It ensures consistent and correct operation of AI-assisted development features, including file updates, command execution, and code block formatting.

## Purpose
This specification serves as the AI assistant's guide for:
- Correctly formatting file updates to work with Cursor IDE's Apply button
- Properly formatting bash commands for execution
- Structuring code blocks with correct file paths
- Following consistent documentation standards
- Maintaining proper error handling and validation

The AI assistant uses these standards to ensure reliable and consistent interaction with the codebase through Cursor IDE.

## Code Generation Standards

### 1. Command Execution
#### Bash Commands
- Use simple ```bash code blocks for executable commands
- These will show with a green $ prefix and four action icons:
  - Run (default)
  - Copy
  - Play
  - Apply
- Format:
  ```bash
  command_to_run
  ```
Example:
  ```bash
  mkdir new_directory
  ```

#### Apply Commands (for file changes)
- Use for file modifications
- Format:
  ```Apply
  Update file_path:
  - Change description
  - Line numbers affected
  ```

### 2. File Path Specifications
- Use ```language:filepath``` format for code that should be written to files
- Example:
  ```python:./example.py
  def example():
      pass
  ```
- Use absolute paths for global configs (~/...)
- Use relative paths for repository-specific files (./...)

### 3. Code Block Structure
- Start with file path comment
- Include purpose/description comment
- Group related functions/classes
- End with clear delineation
- Include version/update information

### 4. Directory Management
- ALWAYS validate directory existence before operations
- Use consistent path handling
- Document directory structure changes
- Handle directory-related errors gracefully

### 5. Error Handling
1. Check file existence
2. Validate paths
3. Handle missing dependencies
4. Provide clear error messages
5. Suggest recovery steps

### 6. Documentation Standards
1. File Headers
```python:./example_header.py
"""
File: example.py
Purpose: Clear description
Author: [AI Assistant Name]
Version: 1.0.0
Last Updated: YYYY-MM-DD
"""
```

2. Function Documentation
```python:./example_function.py
def function_name(param1: type, param2: type) -> return_type:
    """
    Clear description of function purpose.

    Args:
        param1 (type): description
        param2 (type): description

    Returns:
        return_type: description

    Raises:
        ErrorType: description
    """
```

### 7. Code Change Format
When suggesting code changes, use:
```language:path/to/file
// ... existing code ...
{{ change_description }}
// ... existing code ...
```

## Implementation Verification Checklist
- [ ] Correct file path format used
- [ ] Directory checks implemented
- [ ] Error handling in place
- [ ] Documentation complete
- [ ] Commands properly formatted
- [ ] Code changes clearly marked

## Security Considerations
1. Handle sensitive data appropriately
2. Validate input
3. Sanitize output
4. Manage permissions

### 8. Git Command Standards
- Use simple bash blocks for git commands
- Example:
  ```bash
  git add .
  git commit -m "commit message"
  ```
- No need to include cd commands unless changing directories
- Commands will execute in workspace root by default 

### 9. GitHub Standards
- Default branch name: `master` (to maintain consistency with existing repositories)
- Branch naming conventions:
  - Feature branches: `feature/description`
  - Bug fixes: `fix/description`
  - Hotfixes: `hotfix/description`
- Tag format: `vX.Y.Z` (following semantic versioning)
- Commit messages: Clear, concise, present tense 